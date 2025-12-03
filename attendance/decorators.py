from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def admin_required(view_func):
    """Decorator برای بررسی اینکه کاربر مدیر است"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'پروفایل کاربری شما یافت نشد. لطفاً با مدیر سیستم تماس بگیرید.')
            return redirect('attendance:student_list')
        
        if not request.user.profile.is_admin():
            messages.error(request, 'شما دسترسی به این بخش را ندارید.')
            return redirect('attendance:student_list')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def role_required(*allowed_roles):
    """Decorator برای بررسی نقش کاربر"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'پروفایل کاربری شما یافت نشد. لطفاً با مدیر سیستم تماس بگیرید.')
                return redirect('attendance:student_list')
            
            user_role = request.user.profile.role
            if user_role not in allowed_roles:
                messages.error(request, 'شما دسترسی به این بخش را ندارید.')
                return redirect('attendance:student_list')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

