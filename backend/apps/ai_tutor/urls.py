from django.urls import path
from . import views

app_name = 'ai_tutor'

urlpatterns = [
    path('explain/', views.explain_code_view, name='explain'),
    path('explain-selection/', views.explain_selection_view, name='explain_selection'),
    path('debug/', views.debug_code_view, name='debug'),
    path('explain-error/', views.explain_error_view, name='explain_error'),
    path('explain-test/', views.explain_test_view, name='explain_test'),
    path('ask/', views.ask_question_view, name='ask'),
    path('hint/', views.request_hint_view, name='hint'),
    path('analyze-complexity/', views.analyze_complexity_view, name='analyze_complexity'),
    path('improve/', views.improve_solution_view, name='improve'),
    path('conversations/', views.list_conversations_view, name='list_conversations'),
    path('conversations/<int:conversation_id>/messages/', views.get_conversation_messages_view, name='conversation_messages'),
    path('conversations/<int:conversation_id>/clear/', views.clear_conversation_view, name='clear_conversation'),
]
