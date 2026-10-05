from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

# Python 3.14 compatibility patch for Django Context.__copy__
from django.template import context as django_context
def _safe_context_copy(self):
    duplicate = self.__class__.__new__(self.__class__)
    duplicate.dicts = self.dicts[:]
    return duplicate
django_context.BaseContext.__copy__ = _safe_context_copy

from apps.batches.models import Batch
from apps.students.models import StudentProfile
from apps.courses.models import Course, CourseEnrollment
from apps.curriculum.models import CourseWeek, Topic
from apps.questions.models import Question
from apps.quizzes.models import Quiz, QuizQuestion
from apps.attempts.models import QuizAttempt, AttemptQuestion, AttemptAnswer

User = get_user_model()

class UltraPremiumQuizWorkspaceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@kdtechx.com',
            password='AdminPass123!',
            role='ADMIN'
        )
        self.batch = Batch.objects.create(name='Batch Alpha', code='BA1', status='active')
        self.student_user = User.objects.create_user(
            username='student_ux',
            email='student_ux@kdtechx.com',
            password='StudentPass123!',
            role='STUDENT'
        )
        self.profile = StudentProfile.objects.create(
            user=self.student_user,
            student_id='KDX-TEST-001',
            batch=self.batch
        )
        self.course = Course.objects.create(
            name='Modern Distributed Systems',
            code='CS-SYS-501',
            status='PUBLISHED',
            created_by=self.admin
        )
        CourseEnrollment.objects.create(
            student=self.profile,
            course=self.course,
            assigned_by=self.admin
        )
        self.week = CourseWeek.objects.create(course=self.course, week_number=1, title='Consensus')
        self.topic = Topic.objects.create(week=self.week, title='Raft & Paxos', order=1)

        # 3 Technical questions
        self.q1 = Question.objects.create(
            course=self.course,
            topic=self.topic,
            question_text='Which consensus algorithm decomposes consensus into leader election and log replication?',
            option_a='Byzantine Agreement',
            option_b='Raft',
            option_c='Two-Phase Commit',
            option_d='Gossip Protocol',
            correct_answer='B',
            marks=2.00,
            difficulty='medium',
            created_by=self.admin
        )
        self.q2 = Question.objects.create(
            course=self.course,
            topic=self.topic,
            question_text='What is the minimum quorum size for a Raft cluster of 5 nodes?',
            option_a='2 nodes',
            option_b='3 nodes',
            option_c='4 nodes',
            option_d='5 nodes',
            correct_answer='B',
            marks=2.00,
            difficulty='easy',
            created_by=self.admin
        )
        self.q3 = Question.objects.create(
            course=self.course,
            topic=self.topic,
            question_text='In vector clocks, what indicates that two events are concurrent?',
            option_a='Neither vector dominates the other',
            option_b='All timestamps are strictly equal',
            option_c='One vector is strictly greater',
            option_d='Both timestamps are 0',
            correct_answer='A',
            marks=2.00,
            difficulty='hard',
            created_by=self.admin
        )

        now = timezone.now()
        self.quiz = Quiz.objects.create(
            course=self.course,
            week=self.week,
            title='Distributed Consensus Certification Exam',
            duration_minutes=45,
            total_marks=6.00,
            pass_percentage=66.67,
            negative_marking=True,
            negative_marks=0.50,
            require_fullscreen=True,
            prevent_copy=True,
            tab_warning_limit=3,
            start_at=now - timedelta(hours=1),
            deadline=now + timedelta(days=5),
            status='published',
            created_by=self.admin
        )
        QuizQuestion.objects.create(quiz=self.quiz, question=self.q1, order=1, marks=2.00)
        QuizQuestion.objects.create(quiz=self.quiz, question=self.q2, order=2, marks=2.00)
        QuizQuestion.objects.create(quiz=self.quiz, question=self.q3, order=3, marks=2.00)

    def test_workspace_page_rendering_and_architecture(self):
        self.client.login(username='student_ux', password='StudentPass123!')
        res = self.client.get(f'/portal/student/quiz/{self.quiz.id}/take/')
        self.assertEqual(res.status_code, 200)

        html = res.content.decode('utf-8')

        # 1. Verify Command Bar
        self.assertIn('kd-assess-command-bar', html)
        self.assertIn('Assessment', html)
        self.assertIn('Distributed Consensus Certification Exam', html)
        self.assertIn('CS-SYS-501', html)
        self.assertIn('quiz-timer-capsule', html)
        self.assertIn('timer-display', html)
        self.assertIn('btn-fullscreen-toggle', html)
        self.assertIn('btn-submit-assessment-top', html)

        # 2. Verify Question Workspace
        self.assertIn('kd-question-surface', html)
        self.assertIn('Q01', html)
        self.assertIn('Q02', html)
        self.assertIn('Q03', html)
        self.assertIn('kd-options-container', html)
        self.assertIn('kd-assessment-option', html)
        self.assertIn('kd-native-radio', html)
        self.assertIn('kd-option-badge-key', html)
        self.assertIn('kd-option-custom-radio', html)

        # 3. Verify Metadata Badges
        self.assertIn('Single Choice', html)
        self.assertIn('2.00 Marks', html)
        self.assertIn('-0.50 Neg', html)
        self.assertIn('Raft &amp; Paxos', html)

        # 4. Verify Question Palette Navigation Rail & Matrix
        self.assertIn('kd-assessment-rail', html)
        self.assertIn('Question Palette', html)
        self.assertIn('kd-matrix-pill', html)
        self.assertIn('kd-matrix-legend', html)

        # 5. Verify Persistent Bottom Action Bar
        self.assertIn('kd-assess-action-bar', html)
        self.assertIn('btn-mark-review', html)
        self.assertIn('kd-autosave-indicator', html)
        self.assertIn('quiz-next-btn', html)

        # 6. Verify Mobile Controls & Offcanvas
        self.assertIn('kd-mobile-sticky-bar', html)
        self.assertIn('mobileQuestionSheet', html)
        self.assertIn('mobile-btn-palette', html)

        # 7. Verify Review & Submit Modal
        self.assertIn('quizReviewModal', html)
        self.assertIn('modal-stat-total', html)
        self.assertIn('modal-stat-answered', html)
        self.assertIn('modal-stat-unanswered', html)
        self.assertIn('modal-stat-review', html)
        self.assertIn('modal-unanswered-alert', html)
        self.assertIn('btn-confirm-finalize', html)

        # 8. Verify Engine & Config Scripts
        self.assertIn('exam-config', html)
        self.assertIn('saveAnswerUrl', html)
        self.assertIn('quiz-engine.js', html)
        self.assertIn('quiz-security.js', html)
        self.assertIn('quiz-workspace.css', html)

    def test_progressive_autosave_and_atomic_submit_lifecycle(self):
        self.client.login(username='student_ux', password='StudentPass123!')
        res = self.client.get(f'/portal/student/quiz/{self.quiz.id}/take/')
        self.assertEqual(res.status_code, 200)

        attempt = QuizAttempt.objects.get(student=self.profile, quiz=self.quiz)
        self.assertEqual(attempt.status, QuizAttempt.Status.IN_PROGRESS)

        snapshots = list(attempt.question_snapshots.order_by('display_order'))
        self.assertEqual(len(snapshots), 3)

        # Simulate progressive autosave for question 1 (snap 1 -> option B)
        save_url = f'/api/attempts/{attempt.id}/save-answer/'
        save_res = self.client.post(
            save_url,
            data=json.dumps({'snapshot_id': snapshots[0].id, 'selected_option': 'B'}),
            content_type='application/json'
        )
        self.assertEqual(save_res.status_code, 200)

        # Verify AttemptAnswer record was created
        ans1 = AttemptAnswer.objects.get(attempt_question=snapshots[0])
        self.assertEqual(ans1.selected_option, 'B')

        # Test refresh: take view should prefetch and mark saved_answer in HTML
        res_refresh = self.client.get(f'/portal/student/quiz/{self.quiz.id}/take/')
        self.assertEqual(res_refresh.status_code, 200)
        html_refresh = res_refresh.content.decode('utf-8')
        self.assertIn(f'name="question_{snapshots[0].id}"', html_refresh)
        self.assertIn('value="B"', html_refresh)
        self.assertIn('checked', html_refresh)
        self.assertIn('is-selected', html_refresh)

        # Test security telemetry event logging
        sec_url = f'/portal/student/quiz/{attempt.id}/security-event/'
        sec_res = self.client.post(
            sec_url,
            data=json.dumps({'event_type': 'TAB_SWITCH', 'metadata': {'count': 1}}),
            content_type='application/json'
        )
        self.assertEqual(sec_res.status_code, 200)
        attempt.refresh_from_db()
        self.assertEqual(attempt.tab_violations, 1)

        # Final Atomic Evaluation Submission via standard POST
        # Q1: B (Correct -> +2)
        # Q2: A (Wrong -> -0.50)
        # Q3: Unanswered -> 0
        submit_url = f'/portal/student/quiz/{attempt.id}/submit/'
        submit_res = self.client.post(submit_url, {
            f'question_{snapshots[0].id}': 'B',
            f'question_{snapshots[1].id}': 'A',
        }, follow=True)
        self.assertEqual(submit_res.status_code, 200)

        attempt.refresh_from_db()
        self.assertEqual(attempt.status, QuizAttempt.Status.SUBMITTED)
        self.assertEqual(attempt.correct_count, 1)
        self.assertEqual(attempt.wrong_count, 1)
        self.assertEqual(attempt.unanswered_count, 1)
        # Score: 2.00 - 0.50 = 1.50
        self.assertEqual(attempt.score, Decimal('1.50'))
