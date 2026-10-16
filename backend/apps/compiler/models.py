from django.db import models
from django.conf import settings
from apps.courses.models import Course
from apps.students.models import StudentProfile


class CodingProblem(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Easy'
        MEDIUM = 'medium', 'Medium'
        HARD = 'hard', 'Hard'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    description = models.TextField(help_text="Detailed problem statement with input/output format")
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.MEDIUM, db_index=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='coding_problems')
    topic_name = models.CharField(max_length=150, blank=True, null=True)
    
    # Pre-populated boilerplates per language
    starter_codes = models.JSONField(
        default=dict,
        help_text="Dictionary of starter codes keyed by language (python, javascript, cpp, c, java)"
    )
    constraints = models.TextField(blank=True, default="", help_text="Input range and performance constraints")
    
    # Test cases: public (visible to student) vs hidden (strictly private, used for evaluation)
    public_test_cases = models.JSONField(
        default=list,
        help_text="List of public test cases: [{'input': '...', 'expected_output': '...', 'explanation': '...'}]"
    )
    hidden_test_cases = models.JSONField(
        default=list,
        help_text="List of private test cases: [{'input': '...', 'expected_output': '...'}]"
    )
    
    hints = models.JSONField(default=list, blank=True, help_text="Progressive conceptual hints")
    time_limit_seconds = models.FloatField(default=3.0)
    memory_limit_mb = models.IntegerField(default=128)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['difficulty', 'is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"[{self.difficulty.upper()}] {self.title}"


class CodeSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted (All Passed)'
        WRONG_ANSWER = 'wrong_answer', 'Wrong Answer'
        TIME_LIMIT_EXCEEDED = 'time_limit_exceeded', 'Time Limit Exceeded'
        RUNTIME_ERROR = 'runtime_error', 'Runtime Error'
        COMPILE_ERROR = 'compile_error', 'Compilation Error'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='code_submissions')
    problem = models.ForeignKey(CodingProblem, on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
    language = models.CharField(max_length=30, default='python')
    code = models.TextField()
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING, db_index=True)
    passed_test_cases = models.IntegerField(default=0)
    total_test_cases = models.IntegerField(default=0)
    execution_time_ms = models.IntegerField(default=0)
    memory_kb = models.IntegerField(default=0)
    stdout = models.TextField(blank=True, default="")
    stderr = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.user.username} - {self.language} - {self.status} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
