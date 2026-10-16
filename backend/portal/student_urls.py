from django.urls import path
from . import student_views

app_name = 'student_portal'

urlpatterns = [
    # Dashboard
    path('dashboard/', student_views.dashboard_view, name='dashboard'),

    # Courses
    path('courses/', student_views.courses_list_view, name='courses'),
    path('courses/<int:course_id>/', student_views.course_detail_view, name='course_detail'),

    # Assessment Engine
    path('quiz/<int:quiz_id>/take/', student_views.quiz_take_view, name='quiz_take'),
    path('quiz/<int:attempt_id>/security-event/', student_views.quiz_security_event_view, name='quiz_security_event'),
    path('quiz/<int:attempt_id>/submit/', student_views.quiz_submit_view, name='quiz_submit'),

    # Results & Progress
    path('results/<int:attempt_id>/', student_views.result_detail_view, name='result_detail'),
    path('history/', student_views.history_view, name='history'),
    path('progress/', student_views.progress_view, name='progress'),
    path('profile/', student_views.profile_view, name='profile'),

    # Coding Lab & AI Tutor
    path('compiler/', student_views.compiler_view, name='compiler'),
    path('coding/', student_views.coding_problems_list_view, name='coding_problems'),
    path('coding/<slug:slug>/', student_views.coding_problem_solve_view, name='coding_problem_solve'),
]
