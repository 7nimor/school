from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


class AdminAccessMiddleware:
    """Middleware برای محدود کردن دسترسی به پنل مدیریت فقط برای مدیران"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # بررسی اینکه آیا درخواست به admin است
        if request.path.startswith('/admin/'):
            # اجازه دسترسی به login و logout و static files
            if (request.path.startswith('/admin/login/') or 
                request.path.startswith('/admin/logout/') or
                request.path.startswith('/admin/static/') or
                request.path.startswith('/admin/jsi18n/')):
                response = self.get_response(request)
                return response
            
            # اگر کاربر لاگین کرده است
            if request.user.is_authenticated:
                # بررسی اینکه کاربر پروفایل دارد و نقش admin دارد
                try:
                    # بررسی وجود پروفایل
                    if not hasattr(request.user, 'profile'):
                        messages.error(request, 'شما دسترسی به پنل مدیریت را ندارید.')
                        return redirect('attendance:student_list')
                    
                    # بررسی نقش کاربر
                    profile = request.user.profile
                    if not hasattr(profile, 'role') or profile.role != 'admin':
                        messages.error(request, 'شما دسترسی به پنل مدیریت را ندارید. فقط مدیران می‌توانند به پنل مدیریت دسترسی داشته باشند.')
                        return redirect('attendance:student_list')
                    
                    # اگر کاربر admin است، اجازه دسترسی بده
                    # (در اینجا response را اجرا می‌کنیم)
                except Exception as e:
                    # اگر مشکلی در بررسی پروفایل بود
                    messages.error(request, 'شما دسترسی به پنل مدیریت را ندارید.')
                    return redirect('attendance:student_list')
            # اگر کاربر لاگین نکرده باشد، اجازه می‌دهیم به صفحه لاگین admin برود
            # (Django خودش این کار را می‌کند)
        
        response = self.get_response(request)
        return response

