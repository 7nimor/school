from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Student, Parent, Attendance, Teacher, Class, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline برای نمایش پروفایل کاربر در صفحه کاربر"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'پروفایل'


class CustomUserAdmin(BaseUserAdmin):
    """Admin سفارشی برای User با محدودیت دسترسی"""
    inlines = (UserProfileInline,)
    
    def has_add_permission(self, request):
        """فقط مدیران می‌توانند کاربر اضافه کنند"""
        if not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'profile') and request.user.profile.is_admin():
            return True
        return False
    
    def has_change_permission(self, request, obj=None):
        """فقط مدیران می‌توانند کاربر تغییر دهند"""
        if not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'profile') and request.user.profile.is_admin():
            return True
        return False
    
    def has_delete_permission(self, request, obj=None):
        """فقط مدیران می‌توانند کاربر حذف کنند"""
        if not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'profile') and request.user.profile.is_admin():
            return True
        return False
    
    def has_view_permission(self, request, obj=None):
        """فقط مدیران می‌توانند کاربران را ببینند"""
        if not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'profile') and request.user.profile.is_admin():
            return True
        return False


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin برای پروفایل کاربر"""
    list_display = ['user', 'role', 'school_name', 'phone_number', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number', 'school_name']
    readonly_fields = ['created_at', 'updated_at']
    fields = ['user', 'role', 'school_name', 'phone_number', 'teacher', 'created_at', 'updated_at']
    
    def has_add_permission(self, request):
        """فقط مدیران می‌توانند پروفایل اضافه کنند"""
        if not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'profile') and request.user.profile.is_admin():
            return True
        return False
    
    def has_change_permission(self, request, obj=None):
        """فقط مدیران می‌توانند پروفایل تغییر دهند"""
        if not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'profile') and request.user.profile.is_admin():
            return True
        return False
    
    def has_delete_permission(self, request, obj=None):
        """فقط مدیران می‌توانند پروفایل حذف کنند"""
        if not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'profile') and request.user.profile.is_admin():
            return True
        return False
    
    def has_view_permission(self, request, obj=None):
        """فقط مدیران می‌توانند پروفایل‌ها را ببینند"""
        if not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'profile') and request.user.profile.is_admin():
            return True
        return False


# محدود کردن دسترسی به سایر مدل‌ها
class RestrictedAdminMixin:
    """Mixin برای محدود کردن دسترسی به مدل‌ها"""
    def has_module_permission(self, request):
        """بررسی دسترسی به ماژول - فقط مدیران"""
        if not request.user.is_authenticated:
            return False
        # فقط مدیران می‌توانند ماژول را ببینند
        if hasattr(request.user, 'profile'):
            return request.user.profile.is_admin()
        return False
    
    def has_view_permission(self, request, obj=None):
        """بررسی دسترسی به مشاهده - فقط مدیران"""
        if not request.user.is_authenticated:
            return False
        # فقط مدیران می‌توانند مشاهده کنند
        if hasattr(request.user, 'profile'):
            return request.user.profile.is_admin()
        return False
    
    def has_add_permission(self, request):
        """بررسی دسترسی به افزودن"""
        if not request.user.is_authenticated:
            return False
        # مدیران و معاونان می‌توانند اضافه کنند
        if hasattr(request.user, 'profile'):
            return request.user.profile.is_admin() or request.user.profile.is_deputy()
        return False
    
    def has_change_permission(self, request, obj=None):
        """بررسی دسترسی به تغییر"""
        if not request.user.is_authenticated:
            return False
        # مدیران و معاونان می‌توانند تغییر دهند
        if hasattr(request.user, 'profile'):
            return request.user.profile.is_admin() or request.user.profile.is_deputy()
        return False
    
    def has_delete_permission(self, request, obj=None):
        """بررسی دسترسی به حذف"""
        if not request.user.is_authenticated:
            return False
        # فقط مدیران می‌توانند حذف کنند
        if hasattr(request.user, 'profile'):
            return request.user.profile.is_admin()
        return False


@admin.register(Teacher)
class TeacherAdmin(RestrictedAdminMixin, admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'phone_number', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone_number']
    list_filter = ['created_at']


@admin.register(Class)
class ClassAdmin(RestrictedAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'grade', 'teacher', 'is_active', 'created_at']
    search_fields = ['name', 'grade']
    list_filter = ['is_active', 'grade', 'teacher']
    raw_id_fields = ['teacher']


@admin.register(Parent)
class ParentAdmin(RestrictedAdminMixin, admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'phone_number', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone_number']
    list_filter = ['created_at']


@admin.register(Student)
class StudentAdmin(RestrictedAdminMixin, admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'class_room', 'parent', 'is_active']
    search_fields = ['first_name', 'last_name']
    list_filter = ['is_active', 'class_room', 'parent']
    raw_id_fields = ['parent', 'class_room']


@admin.register(Attendance)
class AttendanceAdmin(RestrictedAdminMixin, admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'sms_sent', 'created_at']
    list_filter = ['status', 'date', 'sms_sent']
    search_fields = ['student__first_name', 'student__last_name']
    date_hierarchy = 'date'
    raw_id_fields = ['student']
