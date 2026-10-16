import logging
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.compiler.models import CodingProblem
from apps.ai_tutor.models import AITutorConversation, AITutorMessage
from apps.ai_tutor.services.tutor_service import AITutorService
from apps.ai_tutor.services.exceptions import AITutorException

logger = logging.getLogger(__name__)


def _handle_tutor_action(request, feature_type: str):
    """
    Helper function to authenticate student, extract common context fields,
    invoke the AI Tutor service, and return consistent structured responses.
    """
    student_profile = getattr(request.user, 'student_profile', None)
    if not student_profile:
        return Response({
            'success': False,
            'error': {
                'code': 'UNAUTHORIZED_ROLE',
                'message': 'Only registered students can access the AI Coding Tutor.'
            }
        }, status=status.HTTP_403_FORBIDDEN)

    data = request.data or {}
    code = data.get('code', '')
    language = data.get('language', 'python')
    selected_code = data.get('selected_code', '')
    question = data.get('question', '')
    problem_id = data.get('problem_id')
    learning_mode = data.get('learning_mode', 'intermediate')
    conversation_id = data.get('conversation_id')

    # Compiler diagnostics if available
    compiler_stdout = data.get('compiler_stdout', '')
    compiler_stderr = data.get('compiler_stderr', '')
    compiler_exit_code = data.get('compiler_exit_code')
    failed_test_case = data.get('failed_test_case')

    problem = None
    if problem_id:
        try:
            problem = CodingProblem.objects.get(pk=problem_id, is_active=True)
        except CodingProblem.DoesNotExist:
            problem = None

    tutor_service = AITutorService()

    try:
        result = tutor_service.process_tutor_request(
            student_profile=student_profile,
            feature_type=feature_type,
            code=code,
            language=language,
            selected_code=selected_code,
            question=question,
            problem=problem,
            compiler_stdout=compiler_stdout,
            compiler_stderr=compiler_stderr,
            compiler_exit_code=compiler_exit_code,
            failed_test_case=failed_test_case,
            learning_mode=learning_mode,
            conversation_id=conversation_id
        )
        return Response(result, status=status.HTTP_200_OK)

    except AITutorException as ex:
        logger.warning(f"AI Tutor handled error [{ex.code}]: {ex.message}")
        return Response({
            'success': False,
            'error': {
                'code': ex.code,
                'message': ex.message,
                'retryable': getattr(ex, 'retryable', False)
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as ex:
        logger.error(f"AI Tutor unexpected error: {ex}", exc_info=True)
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred while communicating with the AI service. Please try again.',
                'retryable': True
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def explain_code_view(request):
    """Feature A: Explain entire current source code."""
    return _handle_tutor_action(request, 'explain_code')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def explain_selection_view(request):
    """Feature B: Explain specifically highlighted snippet."""
    return _handle_tutor_action(request, 'explain_selection')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def debug_code_view(request):
    """Feature C: Debug code with available compiler output."""
    return _handle_tutor_action(request, 'debug_code')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def explain_error_view(request):
    """Feature D: Explain compiler/interpreter errors."""
    return _handle_tutor_action(request, 'explain_error')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def explain_test_view(request):
    """Feature E: Explain failed public test case mismatch."""
    return _handle_tutor_action(request, 'explain_test')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ask_question_view(request):
    """Feature F: Intelligent doubt-clearing conversational Q&A."""
    return _handle_tutor_action(request, 'ask_question')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_hint_view(request):
    """Progressive hint without revealing full solution."""
    return _handle_tutor_action(request, 'hint')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_complexity_view(request):
    """Feature G: Time and auxiliary space complexity analysis."""
    return _handle_tutor_action(request, 'analyze_complexity')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def improve_solution_view(request):
    """Feature H: Propose optimization and algorithmic alternatives."""
    return _handle_tutor_action(request, 'improve_solution')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_conversations_view(request):
    """List recent AI Tutor conversations belonging to the authenticated student."""
    student_profile = getattr(request.user, 'student_profile', None)
    if not student_profile:
        return Response({'success': False, 'conversations': []}, status=status.HTTP_200_OK)

    convs = AITutorConversation.objects.filter(student=student_profile).order_by('-updated_at')[:20]
    data = [
        {
            'id': c.id,
            'title': c.title,
            'language': c.language,
            'problem_id': c.problem_id,
            'problem_title': c.problem.title if c.problem else None,
            'updated_at': c.updated_at.strftime('%b %d, %H:%M')
        }
        for c in convs
    ]
    return Response({'success': True, 'conversations': data}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_messages_view(request, conversation_id: int):
    """Retrieve message history for an authorized conversation."""
    student_profile = getattr(request.user, 'student_profile', None)
    if not student_profile:
        return Response({'success': False, 'error': {'message': 'Student profile required.'}}, status=status.HTTP_403_FORBIDDEN)

    conv = get_object_or_404(AITutorConversation, pk=conversation_id, student=student_profile)
    messages = conv.messages.order_by('created_at')[:50]
    data = [
        {
            'id': m.id,
            'role': m.role,
            'content': m.content,
            'feature_type': m.feature_type,
            'learning_mode': m.learning_mode,
            'created_at': m.created_at.strftime('%H:%M')
        }
        for m in messages
    ]
    return Response({
        'success': True,
        'conversation_id': conv.id,
        'title': conv.title,
        'messages': data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_conversation_view(request, conversation_id: int):
    """Clears all messages within an authorized conversation."""
    student_profile = getattr(request.user, 'student_profile', None)
    if not student_profile:
        return Response({'success': False, 'error': {'message': 'Student profile required.'}}, status=status.HTTP_403_FORBIDDEN)

    conv = get_object_or_404(AITutorConversation, pk=conversation_id, student=student_profile)
    conv.messages.all().delete()
    return Response({'success': True, 'message': 'Conversation cleared successfully.'}, status=status.HTTP_200_OK)
