from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.courses.models import Course, CourseEnrollment
from apps.curriculum.models import CourseWeek, Topic
from apps.questions.models import Question
from apps.quizzes.models import Quiz, QuizQuestion
from apps.batches.models import Batch
from apps.students.models import StudentProfile

User = get_user_model()

class QuestionSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin_qsec',
            email='admin@kdtechx.com',
            password='AdminPass123!',
            role='ADMIN'
        )
        self.batch = Batch.objects.create(name='Batch Alpha', code='BA1', status='active')
        self.student_user = User.objects.create_user(
            username='student_qsec',
            email='student@kdtechx.com',
            password='StudentPass123!',
            role='STUDENT'
        )
        self.profile = StudentProfile.objects.create(
            user=self.student_user,
            student_id='SEC001',
            batch=self.batch
        )
        self.course = Course.objects.create(
            name='Python Core',
            code='PY101',
            status='PUBLISHED',
            created_by=self.admin
        )
        CourseEnrollment.objects.create(
            student=self.profile,
            course=self.course,
            assigned_by=self.admin
        )
        self.week = CourseWeek.objects.create(course=self.course, week_number=1, title='Intro')
        self.topic = Topic.objects.create(week=self.week, title='Basics', order=1)
        self.question = Question.objects.create(
            course=self.course,
            topic=self.topic,
            question_text='What is the keyword for function in Python?',
            option_a='function',
            option_b='def',
            option_c='fun',
            option_d='define',
            correct_answer='B',
            difficulty='EASY',
            explanation='Python uses def to define functions.',
            marks=1,
            created_by=self.admin
        )
        now = timezone.now()
        self.quiz = Quiz.objects.create(
            course=self.course,
            week=self.week,
            title='Week 1 Quiz',
            duration_minutes=15,
            pass_percentage=50,
            start_at=now - timedelta(hours=1),
            deadline=now + timedelta(days=7),
            status='PUBLISHED',
            created_by=self.admin
        )
        QuizQuestion.objects.create(quiz=self.quiz, question=self.question, order=1)

    def test_student_cannot_list_questions_admin_api(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get('/api/questions/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_sees_correct_answer(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/questions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.data
        if isinstance(res_data, dict) and 'results' in res_data:
            data = res_data['results']
        elif isinstance(res_data, list):
            data = res_data
        else:
            data = []
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        first_q = data[0]
        self.assertIsInstance(first_q, dict)
        self.assertIn('correct_answer', first_q)
        self.assertEqual(first_q['correct_answer'], 'B')
        self.assertIn('explanation', first_q)

    def test_quiz_start_snapshot_hides_correct_answer(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.post(f'/api/attempts/quiz/{self.quiz.id}/start/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        res_data = response.data if isinstance(response.data, dict) else {}
        questions = res_data.get('questions', [])
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)
        for q in questions:
            self.assertNotIn('correct_answer', q, "CRITICAL: Student received correct_answer before submission!")
            self.assertNotIn('explanation', q, "CRITICAL: Student received explanation before submission!")
            self.assertIn('question_text', q)
            self.assertIn('options', q)
            self.assertEqual(len(q['options']), 4)

    def test_portal_admin_question_import_csv(self):
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_authenticate(user=self.admin)
        self.client.force_login(self.admin)
        
        csv_content = (
            "question,option_a,option_b,option_c,option_d,answer,difficulty,marks,topic\n"
            "What is 2+2?,1,2,3,4,D,easy,1,Basics\n"
            "What is 3+3?,6,5,4,3,A,medium,2,Basics\n"
        )
        csv_file = SimpleUploadedFile("questions.csv", csv_content.encode('utf-8'), content_type="text/csv")
        
        response = self.client.post('/portal/admin/questions/import/', {
            'course_id': self.course.id,
            'file': csv_file
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Question.objects.filter(question_text='What is 2+2?').exists())
        self.assertTrue(Question.objects.filter(question_text='What is 3+3?').exists())

    def test_portal_admin_bulk_delete_questions(self):
        self.client.force_authenticate(user=self.admin)
        self.client.force_login(self.admin)
        
        q1 = Question.objects.create(
            course=self.course,
            question_text='Bulk Q1',
            option_a='1', option_b='2', option_c='3', option_d='4',
            correct_answer='A',
            created_by=self.admin
        )
        q2 = Question.objects.create(
            course=self.course,
            question_text='Bulk Q2',
            option_a='1', option_b='2', option_c='3', option_d='4',
            correct_answer='B',
            created_by=self.admin
        )
        
        response = self.client.post('/portal/admin/questions/bulk-delete/', {
            'question_ids_str': f"{q1.id},{q2.id}"
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Question.objects.filter(id=q1.id).exists())
        self.assertFalse(Question.objects.filter(id=q2.id).exists())

    def test_portal_admin_question_template_csv(self):
        self.client.force_authenticate(user=self.admin)
        self.client.force_login(self.admin)
        
        response = self.client.get('/portal/admin/questions/template/csv/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('question,option_a', response.content.decode('utf-8'))


