import csv
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Avg, Q
from django.http import HttpResponse

from apps.accounts.decorators import admin_required
from apps.accounts.models import User
from apps.batches.models import Batch
from apps.students.models import StudentProfile
from apps.courses.models import Course, CourseEnrollment
from apps.curriculum.models import CourseWeek, Topic
from apps.questions.models import Question
from apps.questions.excel_handler import parse_and_validate_file
from apps.quizzes.models import Quiz, QuizQuestion
from apps.attempts.models import QuizAttempt
from apps.announcements.models import Announcement

@admin_required
def dashboard_view(request):
    total_students = StudentProfile.objects.filter(status='active').count()
    active_courses = Course.objects.filter(status='published').count()
    total_quizzes = Quiz.objects.filter(status='published').count()

    attempts_qs = QuizAttempt.objects.filter(status=QuizAttempt.Status.SUBMITTED)
    avg_score = attempts_qs.aggregate(avg=Avg('percentage'))['avg']
    avg_score = round(float(avg_score), 1) if avg_score else 0.0

    total_attempts = QuizAttempt.objects.count()
    submitted_attempts = attempts_qs.count()
    completion_rate = round((submitted_attempts / total_attempts * 100), 1) if total_attempts > 0 else 100.0

    now = timezone.now()
    upcoming_quizzes = Quiz.objects.filter(
        status='published',
        deadline__gte=now
    ).select_related('course').order_by('deadline')[:4]

    recent_attempts = QuizAttempt.objects.select_related(
        'student__user', 'quiz', 'quiz__course'
    ).order_by('-started_at')[:6]

    courses = Course.objects.annotate(
        student_count=Count('enrollments', distinct=True),
        quiz_count=Count('quizzes', distinct=True)
    ).order_by('-created_at')[:4]

    context = {
        'active_nav': 'dashboard',
        'page_title': 'Admin Executive Dashboard',
        'total_students': total_students,
        'active_courses': active_courses,
        'total_quizzes': total_quizzes,
        'avg_score': avg_score,
        'completion_rate': completion_rate,
        'upcoming_quizzes': upcoming_quizzes,
        'recent_attempts': recent_attempts,
        'courses': courses,
    }
    return render(request, 'admin/dashboard.html', context)

@admin_required
def batch_list_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        description = request.POST.get('description', '').strip()
        status = request.POST.get('status', 'active')

        if not name or not code:
            messages.error(request, "Batch name and code are required.")
        elif Batch.objects.filter(code__iexact=code).exists():
            messages.error(request, f"Batch code '{code}' already exists.")
        else:
            Batch.objects.create(name=name, code=code, description=description, status=status)
            messages.success(request, f"Batch '{name}' created successfully.")
        return redirect('admin_portal:batches')

    batches = Batch.objects.annotate(student_count=Count('students')).order_by('-created_at')
    return render(request, 'admin/batches/index.html', {
        'active_nav': 'batches',
        'page_title': 'Batch Cohorts',
        'batches': batches,
    })

@admin_required
def batch_toggle_view(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    batch.status = 'completed' if batch.status == 'active' else 'active'
    batch.save()
    messages.success(request, f"Batch '{batch.name}' status updated to {batch.status}.")
    return redirect('admin_portal:batches')

@admin_required
def student_list_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        student_id = request.POST.get('student_id', '').strip()
        batch_id = request.POST.get('batch_id', '').strip()
        password = request.POST.get('password', '').strip() or 'Kdtechx@2026'

        if not username or not email or not student_id:
            messages.error(request, "Username, email, and Student ID are required.")
        elif User.objects.filter(username__iexact=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, f"Email '{email}' is already in use.")
        elif StudentProfile.objects.filter(student_id__iexact=student_id).exists():
            messages.error(request, f"Student ID '{student_id}' already exists.")
        else:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=User.Role.STUDENT
                )
                batch = Batch.objects.filter(pk=batch_id).first() if batch_id else None
                StudentProfile.objects.create(
                    user=user,
                    student_id=student_id,
                    batch=batch,
                    status=StudentProfile.Status.ACTIVE
                )
            messages.success(request, f"Student '{first_name or username}' ({student_id}) enrolled successfully.")
        return redirect('admin_portal:students')

    students = StudentProfile.objects.select_related('user', 'batch').annotate(
        enrollment_count=Count('enrollments')
    ).order_by('student_id')
    batches = Batch.objects.filter(status='active').order_by('name')

    return render(request, 'admin/students/index.html', {
        'active_nav': 'students',
        'page_title': 'Student Directory',
        'students': students,
        'batches': batches,
    })

@admin_required
def course_list_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        category = request.POST.get('category', '').strip()
        level = request.POST.get('level', 'intermediate')
        duration_weeks = int(request.POST.get('duration_weeks', 8))
        description = request.POST.get('description', '').strip()
        status = request.POST.get('status', 'draft')

        if not name or not code:
            messages.error(request, "Course name and code are required.")
        elif Course.objects.filter(code__iexact=code).exists():
            messages.error(request, f"Course code '{code}' already exists.")
        else:
            Course.objects.create(
                name=name,
                code=code,
                category=category,
                level=level,
                duration_weeks=duration_weeks,
                description=description,
                status=status,
                created_by=request.user
            )
            messages.success(request, f"Course '{name}' ({code}) created successfully.")
        return redirect('admin_portal:courses')

    courses = Course.objects.annotate(
        student_count=Count('enrollments', distinct=True),
        week_count=Count('weeks', distinct=True),
        quiz_count=Count('quizzes', distinct=True)
    ).order_by('-created_at')

    return render(request, 'admin/courses/index.html', {
        'active_nav': 'courses',
        'page_title': 'Course Management',
        'courses': courses,
    })

@admin_required
def course_curriculum_view(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_week':
            week_number = int(request.POST.get('week_number', 1))
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            if CourseWeek.objects.filter(course=course, week_number=week_number).exists():
                messages.error(request, f"Week {week_number} already exists for this course.")
            else:
                CourseWeek.objects.create(course=course, week_number=week_number, title=title, description=description)
                messages.success(request, f"Week {week_number} added.")
        elif action == 'add_topic':
            week_id = request.POST.get('week_id')
            week = get_object_or_404(CourseWeek, pk=week_id, course=course)
            title = request.POST.get('title', '').strip()
            summary = request.POST.get('summary', '').strip()
            if title:
                Topic.objects.create(week=week, title=title, summary=summary)
                messages.success(request, f"Topic '{title}' added to Week {week.week_number}.")
        return redirect('admin_portal:course_curriculum', course_id=course.id)

    weeks = course.weeks.prefetch_related('topics', 'quizzes').order_by('week_number')
    next_week = (weeks.last().week_number + 1) if weeks.exists() else 1

    return render(request, 'admin/courses/curriculum.html', {
        'active_nav': 'courses',
        'page_title': f"{course.name} - Curriculum",
        'course': course,
        'weeks': weeks,
        'next_week': next_week,
    })

@admin_required
def course_students_view(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'enroll_student':
            student_id = request.POST.get('student_id')
            student = get_object_or_404(StudentProfile, pk=student_id)
            CourseEnrollment.objects.get_or_create(
                student=student,
                course=course,
                defaults={'assigned_by': request.user, 'status': CourseEnrollment.Status.ENROLLED}
            )
            messages.success(request, f"Enrolled {student.user.get_full_name() or student.student_id} in {course.code}.")
        elif action == 'enroll_batch':
            batch_id = request.POST.get('batch_id')
            batch = get_object_or_404(Batch, pk=batch_id)
            students = batch.students.all()
            created_count = 0
            for stu in students:
                _, created = CourseEnrollment.objects.get_or_create(
                    student=stu,
                    course=course,
                    defaults={'assigned_by': request.user, 'status': CourseEnrollment.Status.ENROLLED}
                )
                if created:
                    created_count += 1
            messages.success(request, f"Enrolled {created_count} students from batch '{batch.name}'.")
        elif action == 'remove_student':
            enrollment_id = request.POST.get('enrollment_id')
            CourseEnrollment.objects.filter(pk=enrollment_id, course=course).delete()
            messages.info(request, "Student enrollment removed.")
        return redirect('admin_portal:course_students', course_id=course.id)

    enrollments = course.enrollments.select_related('student__user', 'student__batch').order_by('-assigned_at')
    enrolled_student_ids = enrollments.values_list('student_id', flat=True)
    available_students = StudentProfile.objects.exclude(id__in=enrolled_student_ids).select_related('user', 'batch')
    batches = Batch.objects.filter(status='active').order_by('name')

    return render(request, 'admin/courses/students.html', {
        'active_nav': 'courses',
        'page_title': f"{course.name} - Enrolled Students",
        'course': course,
        'enrollments': enrollments,
        'available_students': available_students,
        'batches': batches,
    })

@admin_required
def question_list_view(request):
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        topic_id = request.POST.get('topic_id') or None
        question_text = request.POST.get('question_text', '').strip()
        option_a = request.POST.get('option_a', '').strip()
        option_b = request.POST.get('option_b', '').strip()
        option_c = request.POST.get('option_c', '').strip()
        option_d = request.POST.get('option_d', '').strip()
        correct_answer = request.POST.get('correct_answer', 'A')
        difficulty = request.POST.get('difficulty', 'medium')
        marks = Decimal(request.POST.get('marks', '1.00'))
        explanation = request.POST.get('explanation', '').strip()

        course = get_object_or_404(Course, pk=course_id)
        topic = Topic.objects.filter(pk=topic_id).first() if topic_id else None

        Question.objects.create(
            course=course,
            topic=topic,
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            difficulty=difficulty,
            marks=marks,
            explanation=explanation,
            created_by=request.user
        )
        messages.success(request, "Question added to Question Bank successfully.")
        return redirect('admin_portal:questions')

    course_filter = request.GET.get('course')
    difficulty_filter = request.GET.get('difficulty')

    questions = Question.objects.select_related('course', 'topic').order_by('-created_at')
    if course_filter:
        questions = questions.filter(course_id=course_filter)
    if difficulty_filter:
        questions = questions.filter(difficulty=difficulty_filter)

    courses = Course.objects.all().order_by('name')
    topics = Topic.objects.select_related('week__course').order_by('title')

    return render(request, 'admin/questions/index.html', {
        'active_nav': 'questions',
        'page_title': 'Question Bank',
        'questions': questions,
        'courses': courses,
        'topics': topics,
        'selected_course': course_filter,
        'selected_difficulty': difficulty_filter,
    })

@admin_required
def question_delete_view(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    question.delete()
    messages.info(request, "Question deleted from Question Bank.")
    return redirect('admin_portal:questions')

@admin_required
def question_bulk_delete_view(request):
    if request.method == 'POST':
        question_ids = request.POST.getlist('question_ids')
        if not question_ids:
            raw_ids = request.POST.get('question_ids_str', '')
            if raw_ids:
                question_ids = [q_id.strip() for q_id in raw_ids.split(',') if q_id.strip()]

        if question_ids:
            deleted_count, _ = Question.objects.filter(id__in=question_ids).delete()
            messages.success(request, f"Successfully deleted {deleted_count} question(s) from Question Bank.")
        else:
            messages.warning(request, "No questions were selected for deletion.")

    return redirect('admin_portal:questions')

@admin_required
def question_template_csv_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="question_import_template.csv"'

    writer = csv.writer(response)
    writer.writerow(['question', 'option_a', 'option_b', 'option_c', 'option_d', 'answer', 'difficulty', 'marks', 'topic', 'explanation'])
    writer.writerow([
        'What is the keyword used to define a function in Python?',
        'func',
        'def',
        'function',
        'define',
        'B',
        'easy',
        '1.00',
        'Functions',
        'Python uses the def keyword to define callable functions.'
    ])
    writer.writerow([
        'Which standard data type in Python is immutable?',
        'List',
        'Dictionary',
        'Tuple',
        'Set',
        'C',
        'medium',
        '1.00',
        'Data Structures',
        'Tuples cannot be altered after instantiation.'
    ])
    return response

@admin_required
def question_import_view(request):
    courses = Course.objects.all().order_by('name')

    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        uploaded_file = request.FILES.get('file')

        if not course_id:
            messages.error(request, "Please select a target course for the imported questions.")
            return render(request, 'admin/questions/import.html', {'courses': courses})

        if not uploaded_file:
            messages.error(request, "Please choose an .xlsx or .csv spreadsheet file.")
            return render(request, 'admin/questions/import.html', {'courses': courses})

        course = get_object_or_404(Course, pk=course_id)
        result = parse_and_validate_file(uploaded_file, uploaded_file.name)

        if not result.get('success') and not result.get('valid_rows'):
            err_msg = str(result.get('error') or 'Spreadsheet validation failed.')
            messages.error(request, err_msg)
            return render(request, 'admin/questions/import.html', {
                'courses': courses,
                'validation_errors': result.get('errors', []),
                'selected_course': course,
            })

        valid_rows = result.get('valid_rows')
        if not isinstance(valid_rows, list) or len(valid_rows) == 0:
            messages.error(request, "No valid question rows found in file.")
            return render(request, 'admin/questions/import.html', {
                'courses': courses,
                'validation_errors': result.get('errors', []),
                'selected_course': course,
            })

        # Commit questions in atomic transaction
        created_count = 0
        with transaction.atomic():
            for row in list(valid_rows):
                topic = None
                raw_topic = row.get('topic_name') or row.get('topic')
                if raw_topic:
                    topic = Topic.objects.filter(
                        week__course=course,
                        title__iexact=str(raw_topic).strip()
                    ).first()

                Question.objects.create(
                    course=course,
                    topic=topic,
                    topic_name=str(raw_topic).strip() if not topic and raw_topic else None,
                    question_text=row.get('question_text') or row.get('question', ''),
                    option_a=row.get('option_a') or row.get('optiona', ''),
                    option_b=row.get('option_b') or row.get('optionb', ''),
                    option_c=row.get('option_c') or row.get('optionc', ''),
                    option_d=row.get('option_d') or row.get('optiond', ''),
                    correct_answer=row.get('correct_answer') or row.get('answer', 'A'),
                    difficulty=row.get('difficulty', 'medium'),
                    marks=Decimal(str(row.get('marks', 1.00))),
                    explanation=row.get('explanation', ''),
                    created_by=request.user
                )
                created_count += 1

        messages.success(request, f"Successfully imported {created_count} questions into {course.name}!")
        return redirect('admin_portal:questions')

    return render(request, 'admin/questions/import.html', {'courses': courses})

@admin_required
def quiz_list_view(request):
    quizzes = Quiz.objects.select_related('course', 'week').annotate(
        question_count=Count('quiz_questions', distinct=True),
        attempt_count=Count('attempts', distinct=True)
    ).order_by('-start_at')

    return render(request, 'admin/quizzes/index.html', {
        'active_nav': 'quizzes',
        'page_title': 'Weekly Quizzes & Assessments',
        'quizzes': quizzes,
    })

@admin_required
def quiz_create_view(request):
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        week_id = request.POST.get('week_id') or None
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        duration_minutes = int(request.POST.get('duration_minutes', 30))
        pass_percentage = Decimal(request.POST.get('pass_percentage', '60.00'))
        start_at = request.POST.get('start_at')
        deadline = request.POST.get('deadline')
        negative_marking = request.POST.get('negative_marking') == 'on'
        negative_marks = Decimal(request.POST.get('negative_marks', '0.25'))
        random_questions = request.POST.get('random_questions') == 'on'
        random_options = request.POST.get('random_options') == 'on'
        require_fullscreen = request.POST.get('require_fullscreen') == 'on'
        prevent_copy = request.POST.get('prevent_copy') == 'on'
        question_ids = request.POST.getlist('questions')

        course = get_object_or_404(Course, pk=course_id)
        week = CourseWeek.objects.filter(pk=week_id, course=course).first() if week_id else None

        with transaction.atomic():
            quiz = Quiz.objects.create(
                course=course,
                week=week,
                title=title,
                description=description,
                duration_minutes=duration_minutes,
                pass_percentage=pass_percentage,
                start_at=start_at,
                deadline=deadline,
                negative_marking=negative_marking,
                negative_marks=negative_marks,
                random_questions=random_questions,
                random_options=random_options,
                require_fullscreen=require_fullscreen,
                prevent_copy=prevent_copy,
                status=Quiz.Status.PUBLISHED,
                created_by=request.user
            )

            total_marks = Decimal('0.00')
            for order, q_id in enumerate(question_ids, start=1):
                question = Question.objects.filter(pk=q_id, course=course).first()
                if question:
                    QuizQuestion.objects.create(
                        quiz=quiz,
                        question=question,
                        order=order,
                        marks=question.marks
                    )
                    total_marks += question.marks

            quiz.total_marks = total_marks if total_marks > 0 else Decimal('100.00')
            quiz.save()

        messages.success(request, f"Assessment '{title}' created and published successfully with {len(question_ids)} questions.")
        return redirect('admin_portal:quiz_detail', quiz_id=quiz.id)

    courses = Course.objects.prefetch_related('weeks', 'questions').order_by('name')
    return render(request, 'admin/quizzes/create.html', {
        'active_nav': 'quizzes',
        'page_title': 'Create Weekly Assessment',
        'courses': courses,
    })

@admin_required
def quiz_detail_view(request, quiz_id):
    quiz = get_object_or_404(
        Quiz.objects.select_related('course', 'week'),
        pk=quiz_id
    )
    quiz_questions = quiz.quiz_questions.select_related('question').order_by('order')
    attempts = quiz.attempts.select_related('student__user').order_by('-started_at')

    # Aggregates
    submitted_attempts = attempts.filter(status=QuizAttempt.Status.SUBMITTED)
    passed_count = submitted_attempts.filter(is_passed=True).count()
    pass_rate = round((passed_count / submitted_attempts.count() * 100), 1) if submitted_attempts.exists() else 0.0
    avg_score = submitted_attempts.aggregate(avg=Avg('percentage'))['avg']
    avg_score = round(float(avg_score), 1) if avg_score else 0.0

    return render(request, 'admin/quizzes/detail.html', {
        'active_nav': 'quizzes',
        'page_title': f"{quiz.title} - Overview",
        'quiz': quiz,
        'quiz_questions': quiz_questions,
        'attempts': attempts,
        'pass_rate': pass_rate,
        'avg_score': avg_score,
    })

@admin_required
def results_overview_view(request):
    attempts = QuizAttempt.objects.select_related(
        'student__user', 'student__batch', 'quiz', 'quiz__course'
    ).order_by('-started_at')

    quiz_filter = request.GET.get('quiz')
    batch_filter = request.GET.get('batch')

    if quiz_filter:
        attempts = attempts.filter(quiz_id=quiz_filter)
    if batch_filter:
        attempts = attempts.filter(student__batch_id=batch_filter)

    quizzes = Quiz.objects.all().order_by('-start_at')
    batches = Batch.objects.all().order_by('name')

    return render(request, 'admin/results/index.html', {
        'active_nav': 'results',
        'page_title': 'Cohort Results Overview',
        'attempts': attempts,
        'quizzes': quizzes,
        'batches': batches,
        'selected_quiz': quiz_filter,
        'selected_batch': batch_filter,
    })

@admin_required
def results_export_csv_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="kdtechx_results_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Student ID', 'Student Name', 'Username', 'Email', 'Batch',
        'Course', 'Quiz Title', 'Score', 'Percentage', 'Status',
        'Time Taken (s)', 'Violations', 'Date Submitted'
    ])

    attempts = QuizAttempt.objects.select_related(
        'student__user', 'student__batch', 'quiz', 'quiz__course'
    ).filter(status=QuizAttempt.Status.SUBMITTED).order_by('-submitted_at')

    for a in attempts:
        user = a.student.user
        writer.writerow([
            a.student.student_id,
            user.get_full_name() or user.username,
            user.username,
            user.email,
            a.student.batch.name if a.student.batch else 'None',
            a.quiz.course.code,
            a.quiz.title,
            a.score,
            f"{a.percentage}%",
            "PASSED" if a.is_passed else "FAILED",
            a.time_taken_seconds,
            a.tab_violations,
            a.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if a.submitted_at else ''
        ])

    return response

@admin_required
def analytics_view(request):
    courses = Course.objects.all().order_by('name')
    quizzes = Quiz.objects.annotate(
        sub_count=Count('attempts', filter=Q(attempts__status=QuizAttempt.Status.SUBMITTED)),
        avg_score=Avg('attempts__percentage', filter=Q(attempts__status=QuizAttempt.Status.SUBMITTED))
    ).order_by('-start_at')[:8]

    total_submissions = QuizAttempt.objects.filter(status=QuizAttempt.Status.SUBMITTED).count()
    passed_submissions = QuizAttempt.objects.filter(status=QuizAttempt.Status.SUBMITTED, is_passed=True).count()
    overall_pass_rate = round((passed_submissions / total_submissions * 100), 1) if total_submissions > 0 else 0.0

    quiz_labels = [q.title[:18] for q in quizzes] if quizzes.exists() else ['No Data']
    quiz_scores = [round(float(q.avg_score or 0), 1) for q in quizzes] if quizzes.exists() else [0]

    import json
    return render(request, 'admin/analytics/index.html', {
        'active_nav': 'analytics',
        'page_title': 'Cohort Performance Analytics',
        'courses': courses,
        'quizzes': quizzes,
        'total_submissions': total_submissions,
        'overall_pass_rate': overall_pass_rate,
        'quiz_labels_json': json.dumps(quiz_labels),
        'quiz_scores_json': json.dumps(quiz_scores),
    })

@admin_required
def announcements_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        priority = request.POST.get('priority', 'normal')
        batch_id = request.POST.get('batch_id') or None
        course_id = request.POST.get('course_id') or None

        if title and content:
            batch = Batch.objects.filter(pk=batch_id).first() if batch_id else None
            course = Course.objects.filter(pk=course_id).first() if course_id else None

            Announcement.objects.create(
                title=title,
                content=content,
                priority=priority,
                batch=batch,
                course=course,
                created_by=request.user
            )
            messages.success(request, f"Announcement '{title}' published.")
        else:
            messages.error(request, "Title and content are required.")
        return redirect('admin_portal:announcements')

    announcements = Announcement.objects.select_related('batch', 'course', 'created_by').order_by('-created_at')
    batches = Batch.objects.filter(status='active').order_by('name')
    courses = Course.objects.filter(status='published').order_by('name')

    return render(request, 'admin/announcements/index.html', {
        'active_nav': 'announcements',
        'page_title': 'Cohort Announcements',
        'announcements': announcements,
        'batches': batches,
        'courses': courses,
    })

@admin_required
def settings_view(request):
    from django.conf import settings
    import sys
    import django

    system_info = {
        'django_version': django.get_version(),
        'python_version': sys.version.split(' ')[0],
        'debug_mode': settings.DEBUG,
        'timezone': settings.TIME_ZONE,
        'default_database': settings.DATABASES['default']['ENGINE'],
        'auth_user_model': settings.AUTH_USER_MODEL,
        'session_engine': settings.SESSION_ENGINE,
    }

    return render(request, 'admin/settings/index.html', {
        'active_nav': 'settings',
        'page_title': 'Portal System Settings',
        'system_info': system_info,
    })
