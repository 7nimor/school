from django.contrib.admin import AdminSite
from django.shortcuts import redirect
from django.contrib import messages


class AdminOnlySite(AdminSite):
    """AdminSite سفارشی که فقط مدیران می‌توانند به آن دسترسی داشته باشند"""
    
    def has_permission(self, request):
        """بررسی دسترسی - فقط مدیران"""
        if not request.user.is_authenticated:
            return False
        
        # بررسی اینکه کاربر پروفایل دارد
        if not hasattr(request.user, 'profile'):
            return False
        
        # فقط مدیران می‌توانند دسترسی داشته باشند
        return request.user.profile.is_admin()
    
    def login(self, request, extra_context=None):
        """Override login برای redirect کاربران غیرمدیر"""
        if request.user.is_authenticated:
            if not self.has_permission(request):
                messages.error(request, 'شما دسترسی به پنل مدیریت را ندارید.')
                return redirect('attendance:student_list')
        return super().login(request, extra_context)
    
    def index(self, request, extra_context=None):
        """Override index برای بررسی دسترسی"""
        if not self.has_permission(request):
            messages.error(request, 'شما دسترسی به پنل مدیریت را ندارید.')
            return redirect('attendance:student_list')
        return super().index(request, extra_context)
    
    def each_context(self, request):
        """Override each_context برای بررسی دسترسی در همه صفحات"""
        context = super().each_context(request)
        if not self.has_permission(request):
            messages.error(request, 'شما دسترسی به پنل مدیریت را ندارید.')
        return context


# ایجاد instance از AdminSite سفارشی
admin_site = AdminOnlySite(name='admin')

