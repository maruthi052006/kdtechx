import json
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.accounts.decorators import student_required
from apps.compiler.models import CodingProblem, CodeSubmission
from apps.compiler.runner import execute_code, evaluate_test_cases


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_code_api(request):
    """
    Executes source code with optional custom input in the sandbox.
    """
    data = request.data
    language = data.get('language', 'python')
    code = data.get('code', '')
    custom_input = data.get('input', '')

    if not code or not code.strip():
        return Response({
            'success': False,
            'error': {'message': 'Source code cannot be empty.'}
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(code) > 100000:
        return Response({
            'success': False,
            'error': {'message': 'Source code exceeds maximum permitted size (100KB).'}
        }, status=status.HTTP_400_BAD_REQUEST)

    result = execute_code(language=language, source_code=code, stdin_input=custom_input)
    res_dict = result.to_dict()
    res_dict['success'] = True
    return Response(res_dict, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_code_api(request):
    """
    Executes code against public test cases for a specific problem.
    """
    data = request.data
    problem_id = data.get('problem_id')
    language = data.get('language', 'python')
    code = data.get('code', '')

    if not code or not code.strip():
        return Response({
            'success': False,
            'error': {'message': 'Source code cannot be empty.'}
        }, status=status.HTTP_400_BAD_REQUEST)

    if problem_id:
        problem = get_object_or_404(CodingProblem, pk=problem_id, is_active=True)
        public_cases = problem.public_test_cases or []
    else:
        # Custom public test cases provided in payload
        public_cases = data.get('test_cases', [])

    if not public_cases:
        return Response({
            'success': False,
            'error': {'message': 'No public test cases found to evaluate.'}
        }, status=status.HTTP_400_BAD_REQUEST)

    eval_result = evaluate_test_cases(
        language=language,
        source_code=code,
        test_cases=public_cases,
        timeout_per_case=3.0
    )
    eval_result['success'] = True
    return Response(eval_result, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_solution_api(request):
    """
    Official server-authoritative submission evaluation.
    Evaluates against both public and hidden test cases, records official CodeSubmission,
    and returns sanitized verdict without leaking hidden test data.
    """
    data = request.data
    problem_id = data.get('problem_id')
    language = data.get('language', 'python')
    code = data.get('code', '')

    if not code or not code.strip():
        return Response({
            'success': False,
            'error': {'message': 'Source code cannot be empty.'}
        }, status=status.HTTP_400_BAD_REQUEST)

    student_profile = getattr(request.user, 'student_profile', None)
    if not student_profile:
        return Response({
            'success': False,
            'error': {'message': 'Only registered students can submit solutions.'}
        }, status=status.HTTP_403_FORBIDDEN)

    problem = None
    all_test_cases = []
    public_cases = []

    if problem_id:
        problem = get_object_or_404(CodingProblem, pk=problem_id, is_active=True)
        public_cases = problem.public_test_cases or []
        hidden_cases = problem.hidden_test_cases or []
        all_test_cases = public_cases + hidden_cases
    else:
        public_cases = data.get('test_cases', [])
        all_test_cases = public_cases

    if not all_test_cases:
        return Response({
            'success': False,
            'error': {'message': 'No test cases configured for this problem.'}
        }, status=status.HTTP_400_BAD_REQUEST)

    eval_result = evaluate_test_cases(
        language=language,
        source_code=code,
        test_cases=all_test_cases,
        timeout_per_case=3.0
    )

    # Sanitize test results: Only expose inputs/outputs for PUBLIC test cases
    sanitized_cases = []
    num_public = len(public_cases)
    for idx, tc in enumerate(eval_result.get('test_cases', [])):
        is_public = (idx < num_public)
        if is_public:
            sanitized_cases.append(tc)
        else:
            # Mask hidden test inputs and expected outputs
            sanitized_cases.append({
                'case_index': tc.get('case_index'),
                'passed': tc.get('passed'),
                'is_hidden': True,
                'execution_time_ms': tc.get('execution_time_ms'),
                'error': "Hidden test case" if not tc.get('passed') else ""
            })

    # Persist official submission
    status_map = {
        'accepted': CodeSubmission.Status.ACCEPTED,
        'wrong_answer': CodeSubmission.Status.WRONG_ANSWER,
        'time_limit_exceeded': CodeSubmission.Status.TIME_LIMIT_EXCEEDED,
        'runtime_error': CodeSubmission.Status.RUNTIME_ERROR,
        'compile_error': CodeSubmission.Status.COMPILE_ERROR,
    }
    submission_status = status_map.get(eval_result['status'], CodeSubmission.Status.WRONG_ANSWER)

    sub = CodeSubmission.objects.create(
        student=student_profile,
        problem=problem,
        language=language,
        code=code,
        status=submission_status,
        passed_test_cases=eval_result['passed_count'],
        total_test_cases=eval_result['total_count'],
        execution_time_ms=eval_result['total_time_ms']
    )

    return Response({
        'success': True,
        'submission_id': sub.id,
        'status': eval_result['status'],
        'passed_count': eval_result['passed_count'],
        'total_count': eval_result['total_count'],
        'total_time_ms': eval_result['total_time_ms'],
        'test_cases': sanitized_cases
    }, status=status.HTTP_201_CREATED)
