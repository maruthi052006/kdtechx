import json
import random
from decimal import Decimal
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.http import JsonResponse, HttpResponseForbidden

from django.core.exceptions import ObjectDoesNotExist
from apps.accounts.decorators import student_required
from apps.courses.models import Course, CourseEnrollment
from apps.curriculum.models import CourseWeek
from apps.quizzes.models import Quiz
from apps.attempts.models import QuizAttempt, AttemptQuestion, AttemptAnswer
from apps.attempts.evaluation import evaluate_quiz_attempt
from apps.audit.models import SecurityEvent
from apps.announcements.models import Announcement

@student_required
def dashboard_view(request):
    profile = request.user.student_profile
    now = timezone.now()

    # Enrolled courses
    enrollments = CourseEnrollment.objects.filter(
        student=profile,
        status=CourseEnrollment.Status.ENROLLED
    ).select_related('course')
    enrolled_course_ids = enrollments.values_list('course_id', flat=True)

    # Active Quizzes available now
    all_quizzes = Quiz.objects.filter(
        course_id__in=enrolled_course_ids,
        status=Quiz.Status.PUBLISHED,
        start_at__lte=now,
        deadline__gte=now
    ).select_related('course', 'week').order_by('deadline')

    active_quizzes = []
    for q in all_quizzes:
        attempt_count = QuizAttempt.objects.filter(student=profile, quiz=q).count()
        latest_attempt = QuizAttempt.objects.filter(student=profile, quiz=q).order_by('-started_at').first()
        has_in_progress = latest_attempt and latest_attempt.status == QuizAttempt.Status.IN_PROGRESS
        can_attempt = has_in_progress or (attempt_count < q.max_attempts)

        active_quizzes.append({
            'quiz': q,
            'attempt_count': attempt_count,
            'can_attempt': can_attempt,
            'in_progress': has_in_progress,
            'latest_attempt': latest_attempt,
        })

    # Recent Results
    recent_attempts = QuizAttempt.objects.filter(
        student=profile,
        status=QuizAttempt.Status.SUBMITTED
    ).select_related('quiz', 'quiz__course').order_by('-submitted_at')[:4]

    # Metrics
    total_completed = QuizAttempt.objects.filter(student=profile, status=QuizAttempt.Status.SUBMITTED).count()
    avg_score = QuizAttempt.objects.filter(student=profile, status=QuizAttempt.Status.SUBMITTED).aggregate(avg=Avg('percentage'))['avg']
    avg_score = round(float(avg_score), 1) if avg_score else 0.0

    # Announcements
    batch = profile.batch
    announcements = Announcement.objects.filter(
        Q(batch=batch) | Q(course_id__in=enrolled_course_ids) | Q(batch__isnull=True, course__isnull=True)
    ).distinct().order_by('-created_at')[:3]

    return render(request, 'student/dashboard.html', {
        'active_nav': 'dashboard',
        'page_title': 'Student Learning Workspace',
        'enrollments': enrollments,
        'active_quizzes': active_quizzes,
        'recent_attempts': recent_attempts,
        'total_completed': total_completed,
        'avg_score': avg_score,
        'announcements': announcements,
    })

@student_required
def courses_list_view(request):
    profile = request.user.student_profile
    enrollments = CourseEnrollment.objects.filter(
        student=profile
    ).select_related('course').annotate(
        quiz_count=Count('course__quizzes')
    ).order_by('-assigned_at')

    return render(request, 'student/courses/index.html', {
        'active_nav': 'courses',
        'page_title': 'My Enrolled Courses',
        'enrollments': enrollments,
    })

@student_required
def course_detail_view(request, course_id):
    profile = request.user.student_profile
    enrollment = get_object_or_404(CourseEnrollment, student=profile, course_id=course_id)
    course = enrollment.course

    weeks = course.weeks.prefetch_related('topics', 'quizzes').order_by('week_number')
    quizzes = course.quizzes.filter(status=Quiz.Status.PUBLISHED).order_by('start_at')

    # Map quiz attempt status for student
    quiz_attempts = {
        qa.quiz_id: qa
        for qa in QuizAttempt.objects.filter(student=profile, quiz__course=course)
    }

    return render(request, 'student/courses/detail.html', {
        'active_nav': 'courses',
        'page_title': f"{course.name} ({course.code})",
        'course': course,
        'weeks': weeks,
        'quizzes': quizzes,
        'quiz_attempts': quiz_attempts,
    })

@student_required
def quiz_take_view(request, quiz_id):
    profile = request.user.student_profile
    quiz = get_object_or_404(Quiz.objects.select_related('course'), pk=quiz_id)
    now = timezone.now()

    # Verify enrollment
    if not CourseEnrollment.objects.filter(student=profile, course=quiz.course).exists():
        messages.error(request, "You are not enrolled in the course associated with this assessment.")
        return redirect('student_portal:dashboard')

    # Verify schedule
    if now < quiz.start_at:
        messages.warning(request, f"This assessment opens on {quiz.start_at.strftime('%b %d, %Y at %H:%M')}.")
        return redirect('student_portal:dashboard')

    if now > quiz.deadline:
        messages.error(request, "This assessment deadline has passed.")
        return redirect('student_portal:dashboard')

    # Check existing attempt
    active_attempt = QuizAttempt.objects.filter(
        student=profile,
        quiz=quiz,
        status=QuizAttempt.Status.IN_PROGRESS
    ).first()

    if not active_attempt:
        existing_count = QuizAttempt.objects.filter(student=profile, quiz=quiz).count()
        if existing_count >= quiz.max_attempts:
            messages.error(request, f"You have reached the maximum attempt limit ({quiz.max_attempts}) for this assessment.")
            return redirect('student_portal:dashboard')

        # Compute deadline: minimum of quiz deadline and duration
        duration_delta = timedelta(minutes=quiz.duration_minutes)
        attempt_deadline = min(quiz.deadline, now + duration_delta)

        with transaction.atomic():
            active_attempt = QuizAttempt.objects.create(
                quiz=quiz,
                student=profile,
                attempt_number=existing_count + 1,
                deadline_at=attempt_deadline,
                status=QuizAttempt.Status.IN_PROGRESS
            )

            # Build questions snapshot
            quiz_questions = list(quiz.quiz_questions.select_related('question').order_by('order'))
            if quiz.random_questions:
                random.shuffle(quiz_questions)

            for order, qq in enumerate(quiz_questions, start=1):
                q = qq.question
                mapping = {}
                if quiz.random_options:
                    keys = ['A', 'B', 'C', 'D']
                    shuffled_keys = keys.copy()
                    random.shuffle(shuffled_keys)
                    mapping = dict(zip(keys, shuffled_keys))
                else:
                    mapping = {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}

                AttemptQuestion.objects.create(
                    attempt=active_attempt,
                    question=q,
                    display_order=order,
                    option_mapping=mapping
                )

    # Check timeout
    if now > active_attempt.deadline_at + timedelta(seconds=15):
        evaluate_quiz_attempt(active_attempt, {})
        messages.warning(request, "Time expired. Your assessment has been evaluated.")
        return redirect('student_portal:result_detail', attempt_id=active_attempt.id)

    # Remaining seconds
    remaining_seconds = max(0, int((active_attempt.deadline_at - now).total_seconds()))

    snapshots = active_attempt.question_snapshots.select_related('question', 'answer').order_by('display_order')
    
    # Prepare candidate questions with scrambled options resolved
    candidate_questions = []
    for snap in snapshots:
        q = snap.question
        mapping = snap.option_mapping or {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}

        # Original options dict
        orig_options = {
            'A': q.option_a,
            'B': q.option_b,
            'C': q.option_c,
            'D': q.option_d,
        }

        # Resolve which option text goes to candidate choice A, B, C, D
        candidate_options = []
        for choice_key in ['A', 'B', 'C', 'D']:
            original_key = mapping.get(choice_key, choice_key)
            candidate_options.append({
                'key': choice_key,
                'text': orig_options.get(original_key, '')
            })

        saved_answer = None
        try:
            if hasattr(snap, 'answer') and snap.answer:
                saved_answer = snap.answer.selected_option
        except ObjectDoesNotExist:
            saved_answer = None

        candidate_questions.append({
            'snap_id': snap.id,
            'display_order': snap.display_order,
            'question_text': q.question_text,
            'marks': q.marks,
            'options': candidate_options,
            'saved_answer': saved_answer,
            'topic': q.topic_name or (q.topic.title if q.topic else ''),
            'difficulty': q.difficulty.title() if q.difficulty else '',
        })

    return render(request, 'student/quiz/take.html', {
        'quiz': quiz,
        'attempt': active_attempt,
        'remaining_seconds': remaining_seconds,
        'candidate_questions': candidate_questions,
        'total_questions': len(candidate_questions),
    })

@student_required
def quiz_security_event_view(request, attempt_id):
    if request.method != 'POST':
        return HttpResponseForbidden("POST required")

    profile = request.user.student_profile
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, student=profile)

    try:
        data = json.loads(request.body.decode('utf-8'))
        event_type = data.get('event_type', 'UNKNOWN')
        metadata = data.get('metadata', {})

        attempt.tab_violations += 1
        attempt.save(update_fields=['tab_violations'])

        SecurityEvent.objects.create(
            attempt=attempt,
            event_type=event_type,
            metadata=metadata
        )

        should_auto_submit = attempt.tab_violations >= attempt.quiz.tab_warning_limit

        return JsonResponse({
            'success': True,
            'violations': attempt.tab_violations,
            'auto_submit': should_auto_submit
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@student_required
def quiz_submit_view(request, attempt_id):
    if request.method != 'POST':
        return redirect('student_portal:dashboard')

    profile = request.user.student_profile
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, student=profile)

    if attempt.status != QuizAttempt.Status.IN_PROGRESS:
        return redirect('student_portal:result_detail', attempt_id=attempt.id)

    # Extract answers from POST data
    submitted_answers = {}
    for key, value in request.POST.items():
        if key.startswith('question_'):
            snap_id = key.replace('question_', '')
            submitted_answers[snap_id] = value

    # Server-Authoritative Evaluation Engine
    evaluated_attempt = evaluate_quiz_attempt(attempt, submitted_answers)

    messages.success(request, f"Assessment submitted! Your score: {evaluated_attempt.score} / {attempt.quiz.total_marks} ({evaluated_attempt.percentage}%)")
    return redirect('student_portal:result_detail', attempt_id=evaluated_attempt.id)

@student_required
def result_detail_view(request, attempt_id):
    profile = request.user.student_profile
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related('quiz', 'quiz__course'),
        pk=attempt_id,
        student=profile
    )

    snapshots = attempt.question_snapshots.select_related('question').prefetch_related('answer').order_by('display_order')

    reviews = []
    for snap in snapshots:
        q = snap.question
        answer = getattr(snap, 'answer', None)
        selected_option = answer.selected_option if answer else None
        mapping = snap.option_mapping or {}

        # Resolve original correct key into candidate view key
        inv_mapping = {v: k for k, v in mapping.items()}
        candidate_correct_key = inv_mapping.get(q.correct_answer, q.correct_answer)

        reviews.append({
            'question': q,
            'display_order': snap.display_order,
            'selected_option': selected_option,
            'candidate_correct_key': candidate_correct_key,
            'is_correct': answer.is_correct if answer else False,
            'marks_awarded': answer.marks_awarded if answer else Decimal('0.00'),
            'explanation': q.explanation,
        })

    return render(request, 'student/results/detail.html', {
        'active_nav': 'history',
        'page_title': f"Result: {attempt.quiz.title}",
        'attempt': attempt,
        'quiz': attempt.quiz,
        'reviews': reviews,
    })

@student_required
def history_view(request):
    profile = request.user.student_profile
    attempts = QuizAttempt.objects.filter(
        student=profile,
        status=QuizAttempt.Status.SUBMITTED
    ).select_related('quiz', 'quiz__course').order_by('-submitted_at')

    return render(request, 'student/history/index.html', {
        'active_nav': 'history',
        'page_title': 'My Assessment History',
        'attempts': attempts,
    })

@student_required
def progress_view(request):
    profile = request.user.student_profile
    attempts = QuizAttempt.objects.filter(
        student=profile,
        status=QuizAttempt.Status.SUBMITTED
    ).select_related('quiz', 'quiz__course').order_by('submitted_at')

    passed_count = attempts.filter(is_passed=True).count()
    total_count = attempts.count()
    pass_rate = round((passed_count / total_count * 100), 1) if total_count > 0 else 0.0

    avg_score = attempts.aggregate(avg=Avg('percentage'))['avg']
    avg_score = round(float(avg_score), 1) if avg_score else 0.0

    labels = [a.quiz.title[:15] for a in attempts] or ['No Data']
    scores = [float(a.percentage) for a in attempts] or [0]

    return render(request, 'student/progress/index.html', {
        'active_nav': 'progress',
        'page_title': 'Learning Progress & Performance',
        'attempts': attempts,
        'pass_rate': pass_rate,
        'avg_score': avg_score,
        'total_count': total_count,
        'labels_json': json.dumps(labels),
        'scores_json': json.dumps(scores),
    })

@student_required
def profile_view(request):
    profile = request.user.student_profile
    return render(request, 'student/profile/index.html', {
        'active_nav': 'profile',
        'page_title': 'Student Profile',
        'profile': profile,
        'user': request.user,
    })
