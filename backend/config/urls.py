from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import (
    HealthCheckView,
    landing_page_view,
    error_403_view,
    error_404_view,
    error_500_view,
)

public_patterns = [
    path('', landing_page_view, name='landing'),
]

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public & Landing
    path('', include((public_patterns, 'public'), namespace='public')),

    # Full-Stack Authentication & Session Web Views
    path('accounts/', include('apps.accounts.web_urls')),

    # Full-Stack Workspaces
    path('portal/admin/', include('portal.admin_urls')),
    path('portal/student/', include('portal.student_urls')),

    # System & Health
    path('api/health/', HealthCheckView.as_view(), name='health-check'),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Modular Domain APIs (Preserved for backwards compatibility)
    path('api/auth/', include('apps.accounts.urls')),
    path('api/batches/', include('apps.batches.urls')),
    path('api/students/', include('apps.students.urls')),
    path('api/courses/', include('apps.courses.urls')),
    path('api/curriculum/', include('apps.curriculum.urls')),
    path('api/questions/', include('apps.questions.urls')),
    path('api/quizzes/', include('apps.quizzes.urls')),
    path('api/attempts/', include('apps.attempts.urls')),
    path('api/results/', include('apps.results.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/announcements/', include('apps.announcements.urls')),
    path('api/audit/', include('apps.audit.urls')),
    path('api/compiler/', include('apps.compiler.urls')),
    path('api/ai-tutor/', include('apps.ai_tutor.urls')),
]

handler403 = 'config.views.error_403_view'
handler404 = 'config.views.error_404_view'
handler500 = 'config.views.error_500_view'
