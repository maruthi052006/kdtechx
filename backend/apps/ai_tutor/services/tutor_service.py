from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.db import transaction

from apps.students.models import StudentProfile
from apps.compiler.models import CodingProblem
from apps.ai_tutor.models import AITutorConversation, AITutorMessage
from .provider import AIProviderClient
from .context_builder import build_system_prompt, build_safe_context
from .rate_limiter import check_and_record_rate_limit, get_user_usage_stats
from .exceptions import AITutorException, PolicyViolationError

logger = logging.getLogger(__name__)


class AITutorService:
    """
    Core AI Tutor service layer implementing all context-aware features,
    persistence, rate limiting, and assessment integrity checks.
    """

    def __init__(self):
        self.provider = AIProviderClient()

    def process_tutor_request(
        self,
        student_profile: StudentProfile,
        feature_type: str,
        code: str,
        language: str = 'python',
        selected_code: str = '',
        question: str = '',
        problem: Optional[CodingProblem] = None,
        compiler_stdout: str = '',
        compiler_stderr: str = '',
        compiler_exit_code: Optional[int] = None,
        failed_test_case: Optional[dict] = None,
        learning_mode: str = 'intermediate',
        conversation_id: Optional[int] = None
    ) -> dict:
        """
        Main entry point for handling an authenticated AI Tutor action.
        """
        # 1. Feature enablement check
        if not getattr(settings, 'AI_TUTOR_ENABLED', True):
            raise PolicyViolationError("The AI Coding Tutor is currently disabled by administrator policy.")

        # 2. Rate limit enforcement
        check_and_record_rate_limit(student_profile.user_id)

        # 3. Retrieve or create conversation record
        conversation = None
        if conversation_id:
            try:
                conversation = AITutorConversation.objects.get(
                    id=conversation_id,
                    student=student_profile
                )
            except AITutorConversation.DoesNotExist:
                conversation = None

        if not conversation:
            conv_title = (
                f"{problem.title} ({language})"
                if problem
                else f"Scratchpad {language.capitalize()}"
            )
            conversation = AITutorConversation.objects.create(
                student=student_profile,
                problem=problem,
                language=language,
                title=conv_title
            )

        # 4. Fetch bounded history from conversation (last 6 messages)
        history_records = list(conversation.messages.order_by('created_at')[:8])
        formatted_history = [
            {'role': m.role, 'content': m.content}
            for m in history_records
        ]

        # 5. Extract public problem details (never hidden test cases)
        problem_title = problem.title if problem else ""
        problem_desc = problem.description if problem else ""
        constraints = problem.constraints if problem else ""
        public_test_cases = problem.public_test_cases if problem else None

        # 6. Build prompt with safe context
        system_instruction = build_system_prompt(learning_mode=learning_mode)
        user_prompt = build_safe_context(
            feature=feature_type,
            code=code,
            language=language,
            selected_code=selected_code,
            question=question,
            problem_title=problem_title,
            problem_description=problem_desc,
            constraints=constraints,
            public_test_cases=public_test_cases,
            compiler_stdout=compiler_stdout,
            compiler_stderr=compiler_stderr,
            compiler_exit_code=compiler_exit_code,
            failed_test_case=failed_test_case,
            history=formatted_history,
            learning_mode=learning_mode
        )

        # 7. Generate response via AI provider
        ai_resp = self.provider.generate(system_instruction, user_prompt)
        response_text = ai_resp.get('text', '')
        tokens_used = ai_resp.get('tokens_used', 0)

        # 8. Persist conversation turn atomically
        with transaction.atomic():
            # Save student query / action message
            user_msg_content = question or f"[{feature_type.replace('_', ' ').title()}]"
            AITutorMessage.objects.create(
                conversation=conversation,
                role=AITutorMessage.Role.USER,
                content=user_msg_content,
                feature_type=feature_type,
                learning_mode=learning_mode,
                code_context=selected_code or (code[:1000] if code else "")
            )

            # Save assistant response
            AITutorMessage.objects.create(
                conversation=conversation,
                role=AITutorMessage.Role.ASSISTANT,
                content=response_text,
                feature_type=feature_type,
                learning_mode=learning_mode,
                tokens_used=tokens_used
            )

            # Touch conversation updated_at
            conversation.save(update_fields=['updated_at'])

        # 9. Return structured safe response
        usage_stats = get_user_usage_stats(student_profile.user_id)
        return {
            'success': True,
            'feature': feature_type,
            'learning_mode': learning_mode,
            'response': response_text,
            'conversation_id': conversation.id,
            'tokens_used': tokens_used,
            'model': ai_resp.get('model'),
            'usage': usage_stats
        }
