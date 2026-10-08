from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    """
    Ensures the user is authenticated and has administrative / trainer privileges.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please log in with your trainer credentials.")
            return redirect('accounts:admin_login')
        if not request.user.is_admin_user:
            messages.error(request, "Access denied. Trainer privileges required.")
            return redirect('student_portal:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def student_required(view_func):
    """
    Ensures the user is authenticated and is a student / candidate.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to access your student portal.")
            return redirect('accounts:student_login')
        if not request.user.is_student_user:
            return redirect('admin_portal:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
