from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'attendance'

def home_redirect(request):
    """صفحه اصلی - redirect به لاگین یا لیست دانش‌آموزان"""
    if request.user.is_authenticated:
        return redirect('attendance:student_list')
    return redirect('attendance:login')

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.user_profile, name='user_profile'),
    path('', home_redirect, name='home'),
    path('students/', views.student_list, name='student_list'),
    path('students/<int:student_id>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:student_id>/attendance/', views.student_attendance_detail, name='student_attendance_detail'),
    path('students/<int:student_id>/attendance/export/', views.export_student_attendance_excel_view, name='export_student_attendance_excel'),
    path('students/export/', views.export_students_excel_view, name='export_students_excel'),
    path('students/upload/', views.upload_students_excel, name='upload_students_excel'),
    path('teachers/upload/', views.upload_teachers_excel_view, name='upload_teachers_excel'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/export/', views.export_attendance_excel_view, name='export_attendance_excel'),
    path('attendance/statistics/', views.statistics_view, name='statistics'),
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('send-sms/<int:attendance_id>/', views.send_sms_manually, name='send_sms'),
    path('attendance/<int:attendance_id>/delete/', views.delete_attendance, name='delete_attendance'),
    # مدیریت کاربران - فقط برای مدیران
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
]

