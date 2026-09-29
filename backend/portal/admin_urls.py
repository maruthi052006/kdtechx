from django.urls import path
from . import admin_views

app_name = 'admin_portal'

urlpatterns = [
    # Dashboard
    path('dashboard/', admin_views.dashboard_view, name='dashboard'),

    # Batches
    path('batches/', admin_views.batch_list_view, name='batches'),
    path('batches/<int:batch_id>/toggle/', admin_views.batch_toggle_view, name='batch_toggle'),

    # Students
    path('students/', admin_views.student_list_view, name='students'),

    # Courses & Curriculum
    path('courses/', admin_views.course_list_view, name='courses'),
    path('courses/<int:course_id>/curriculum/', admin_views.course_curriculum_view, name='course_curriculum'),
    path('courses/<int:course_id>/students/', admin_views.course_students_view, name='course_students'),

    # Question Bank & Excel
    path('questions/', admin_views.question_list_view, name='questions'),
    path('questions/<int:question_id>/delete/', admin_views.question_delete_view, name='question_delete'),
    path('questions/bulk-delete/', admin_views.question_bulk_delete_view, name='questions_bulk_delete'),
    path('questions/import/', admin_views.question_import_view, name='questions_import'),
    path('questions/template/csv/', admin_views.question_template_csv_view, name='questions_template_csv'),

    # Quizzes
    path('quizzes/', admin_views.quiz_list_view, name='quizzes'),
    path('quizzes/create/', admin_views.quiz_create_view, name='quiz_create'),
    path('quizzes/<int:quiz_id>/', admin_views.quiz_detail_view, name='quiz_detail'),

    # Results & Analytics
    path('results/', admin_views.results_overview_view, name='results'),
    path('results/export/csv/', admin_views.results_export_csv_view, name='results_export_csv'),
    path('analytics/', admin_views.analytics_view, name='analytics'),

    # Announcements & Settings
    path('announcements/', admin_views.announcements_view, name='announcements'),
    path('settings/', admin_views.settings_view, name='settings'),
]
