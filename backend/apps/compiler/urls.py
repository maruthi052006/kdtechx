from django.urls import path
from . import views

app_name = 'compiler'

urlpatterns = [
    path('run/', views.run_code_api, name='run'),
    path('test/', views.test_code_api, name='test'),
    path('submit/', views.submit_solution_api, name='submit'),
]
