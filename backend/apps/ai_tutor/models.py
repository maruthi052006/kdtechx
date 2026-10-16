from django.db import models
from django.conf import settings
from apps.students.models import StudentProfile
from apps.compiler.models import CodingProblem


class AITutorConversation(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        db_index=True
    )
    problem = models.ForeignKey(
        CodingProblem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_conversations'
    )
    title = models.CharField(max_length=200, default="Coding Session")
    language = models.CharField(max_length=30, default="python")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['student', '-updated_at']),
        ]

    def __str__(self):
        return f"Conv #{self.id} - {self.student.user.username} ({self.title})"


class AITutorMessage(models.Model):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'AI Tutor'
        SYSTEM = 'system', 'System Context'

    class FeatureType(models.TextChoices):
        EXPLAIN_CODE = 'explain_code', 'Explain Code'
        EXPLAIN_SELECTION = 'explain_selection', 'Explain Selection'
        DEBUG_CODE = 'debug_code', 'Debug Code'
        EXPLAIN_ERROR = 'explain_error', 'Explain Compiler Error'
        EXPLAIN_TEST = 'explain_test', 'Explain Failed Test'
        ASK_QUESTION = 'ask_question', 'Ask Question'
        HINT = 'hint', 'Progressive Hint'
        ANALYZE_COMPLEXITY = 'analyze_complexity', 'Complexity Analysis'
        IMPROVE_SOLUTION = 'improve_solution', 'Improve Solution'

    conversation = models.ForeignKey(
        AITutorConversation,
        on_delete=models.CASCADE,
        related_name='messages',
        db_index=True
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    content = models.TextField()
    feature_type = models.CharField(
        max_length=30,
        choices=FeatureType.choices,
        default=FeatureType.ASK_QUESTION
    )
    learning_mode = models.CharField(max_length=30, default='intermediate')
    code_context = models.TextField(blank=True, default="")
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f"[{self.role}] Conv #{self.conversation_id}: {self.content[:40]}..."
