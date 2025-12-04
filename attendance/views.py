from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta
from .models import Student, Attendance, Parent, UserProfile
from .services import send_absence_sms
from .decorators import admin_required
from .excel import export_students_excel, export_attendance_excel


def login_view(request):
    """صفحه لاگین"""
    import random
    
    if request.user.is_authenticated:
        return redirect('attendance:student_list')
    
    # تولید کپچا
    if 'captcha_answer' not in request.session:
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        request.session['captcha_answer'] = num1 + num2
        request.session['captcha_question'] = f"{num1} + {num2}"
    
    if request.method == 'POST':
        # بررسی کپچا
        user_captcha = request.POST.get('captcha', '').strip()
        try:
            user_captcha_int = int(user_captcha)
            if user_captcha_int != request.session.get('captcha_answer'):
                messages.error(request, 'پاسخ کپچا اشتباه است. لطفاً دوباره تلاش کنید.')
                # تولید کپچای جدید
                num1 = random.randint(1, 10)
                num2 = random.randint(1, 10)
                request.session['captcha_answer'] = num1 + num2
                request.session['captcha_question'] = f"{num1} + {num2}"
                form = AuthenticationForm()
                return render(request, 'attendance/login.html', {
                    'form': form,
                    'captcha_question': request.session['captcha_question']
                })
        except ValueError:
            messages.error(request, 'لطفاً یک عدد معتبر وارد کنید.')
            form = AuthenticationForm()
            return render(request, 'attendance/login.html', {
                'form': form,
                'captcha_question': request.session.get('captcha_question', '')
            })
        
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # حذف کپچا از session بعد از لاگین موفق
            if 'captcha_answer' in request.session:
                del request.session['captcha_answer']
            if 'captcha_question' in request.session:
                del request.session['captcha_question']
            
            user = form.get_user()
            login(request, user)
            # نمایش نام و نام خانوادگی یا username
            full_name = user.get_full_name().strip()
            display_name = full_name if full_name else user.username
            messages.success(request, f'خوش آمدید {display_name}!')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('attendance:student_list')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'attendance/login.html', {
        'form': form,
        'captcha_question': request.session.get('captcha_question', '')
    })


def logout_view(request):
    """خروج از سیستم"""
    logout(request)
    messages.success(request, 'با موفقیت خارج شدید.')
    return redirect('attendance:login')


@login_required
def student_list(request):
    """لیست دانش‌آموزان"""
    from .models import Class
    
    user_profile = request.user.profile
    is_teacher = user_profile.is_teacher()
    
    # مرتب‌سازی بر اساس جدیدترین (created_at نزولی)
    students = Student.objects.filter(is_active=True).select_related('parent', 'class_room', 'class_room__teacher')
    
    # اگر کاربر معلم است، فقط دانش‌آموزان کلاس‌های خودش را نشان بده
    if is_teacher and user_profile.teacher:
        students = students.filter(class_room__teacher=user_profile.teacher)
    
    students = students.order_by('-created_at')
    
    # فیلتر بر اساس کلاس
    class_filter = request.GET.get('class', '')
    if class_filter:
        students = students.filter(class_room_id=class_filter)
    
    # جستجو
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(student_id__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(students, 10)  # 10 دانش‌آموز در هر صفحه
    page = request.GET.get('page', 1)
    
    try:
        students_page = paginator.page(page)
    except PageNotAnInteger:
        students_page = paginator.page(1)
    except EmptyPage:
        students_page = paginator.page(paginator.num_pages)
    
    # اگر کاربر معلم است، فقط کلاس‌های خودش را نشان بده
    if is_teacher and user_profile.teacher:
        classes = Class.objects.filter(teacher=user_profile.teacher, is_active=True).select_related('teacher')
    else:
        classes = Class.objects.filter(is_active=True).select_related('teacher')
    
    context = {
        'students': students_page,
        'search_query': search_query,
        'classes': classes,
        'class_filter': class_filter,
    }
    return render(request, 'attendance/student_list.html', context)


@login_required
def export_students_excel_view(request):
    """Export لیست دانش‌آموزان به Excel"""
    class_filter = request.GET.get('class', '')
    search_query = request.GET.get('search', '')
    
    # اگر کاربر معلم است، فقط دانش‌آموزان کلاس‌های خودش را نشان بده
    user_profile = request.user.profile
    if user_profile.is_teacher() and user_profile.teacher:
        students_query = Student.objects.filter(class_room__teacher=user_profile.teacher)
    else:
        students_query = Student.objects.all()
    
    return export_students_excel(
        students_query=students_query,
        class_filter=class_filter,
        search_query=search_query
    )


@login_required
def student_edit(request, student_id):
    """ویرایش دانش‌آموز"""
    from .models import Class, Parent
    
    user_profile = request.user.profile
    is_teacher = user_profile.is_teacher()
    
    student = get_object_or_404(Student, id=student_id)
    
    # اگر کاربر معلم است، فقط دانش‌آموزان کلاس‌های خودش را می‌تواند ویرایش کند
    if is_teacher and user_profile.teacher:
        if not student.class_room or student.class_room.teacher != user_profile.teacher:
            messages.error(request, 'شما اجازه ویرایش این دانش‌آموز را ندارید.')
            return redirect('attendance:student_list')
    
    classes = Class.objects.filter(is_active=True).order_by('grade', 'name')
    
    if request.method == 'POST':
        # اطلاعات دانش‌آموز
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        student_id_field = request.POST.get('student_id', '').strip()
        class_id = request.POST.get('class_id', '')
        phone_number = request.POST.get('phone_number', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        # اطلاعات اولیا
        parent_first_name = request.POST.get('parent_first_name', '').strip()
        parent_last_name = request.POST.get('parent_last_name', '').strip()
        parent_phone = request.POST.get('parent_phone', '').strip()
        
        # اعتبارسنجی
        if not first_name or not last_name:
            messages.error(request, 'نام و نام خانوادگی دانش‌آموز الزامی است.')
            return redirect('attendance:student_edit', student_id=student.id)
        
        if not student_id_field:
            messages.error(request, 'شماره دانش‌آموزی الزامی است.')
            return redirect('attendance:student_edit', student_id=student.id)
        
        # بررسی تکراری نبودن شماره دانش‌آموزی
        if student_id_field != student.student_id:
            if Student.objects.filter(student_id=student_id_field).exists():
                messages.error(request, 'این شماره دانش‌آموزی قبلاً استفاده شده است.')
                return redirect('attendance:student_edit', student_id=student.id)
        
        # اعتبارسنجی شماره تلفن دانش‌آموز
        if phone_number:
            import re
            if not re.match(r'^09\d{9}$', phone_number):
                messages.error(request, 'شماره تلفن دانش‌آموز باید با فرمت 09123456789 باشد.')
                return redirect('attendance:student_edit', student_id=student.id)
        
        # اعتبارسنجی اطلاعات اولیا
        if not parent_first_name or not parent_last_name:
            messages.error(request, 'نام و نام خانوادگی اولیا الزامی است.')
            return redirect('attendance:student_edit', student_id=student.id)
        
        if not parent_phone:
            messages.error(request, 'شماره تلفن اولیا الزامی است.')
            return redirect('attendance:student_edit', student_id=student.id)
        
        import re
        if not re.match(r'^09\d{9}$', parent_phone):
            messages.error(request, 'شماره تلفن اولیا باید با فرمت 09123456789 باشد.')
            return redirect('attendance:student_edit', student_id=student.id)
        
        # بررسی تکراری نبودن شماره تلفن اولیا
        if parent_phone != student.parent.phone_number:
            if Parent.objects.filter(phone_number=parent_phone).exists():
                messages.error(request, 'این شماره تلفن اولیا قبلاً استفاده شده است.')
                return redirect('attendance:student_edit', student_id=student.id)
        
        try:
            # به‌روزرسانی اطلاعات اولیا
            student.parent.first_name = parent_first_name
            student.parent.last_name = parent_last_name
            student.parent.phone_number = parent_phone
            student.parent.save()
            
            # به‌روزرسانی اطلاعات دانش‌آموز
            student.first_name = first_name
            student.last_name = last_name
            student.student_id = student_id_field
            student.phone_number = phone_number if phone_number else None
            student.is_active = is_active
            student.updated_by = request.user  # ثبت کاربر ویرایش‌کننده
            
            # معلم نمی‌تواند کلاس دانش‌آموز را تغییر دهد
            if not is_teacher:
                if class_id:
                    student.class_room = Class.objects.get(id=class_id)
                else:
                    student.class_room = None
            
            student.save()
            
            messages.success(request, f'اطلاعات دانش‌آموز {student.first_name} {student.last_name} با موفقیت به‌روزرسانی شد.')
            return redirect('attendance:student_list')
            
        except Exception as e:
            messages.error(request, f'خطا در به‌روزرسانی: {str(e)}')
            return redirect('attendance:student_edit', student_id=student.id)
    
    context = {
        'student': student,
        'classes': classes,
        'is_teacher': is_teacher,
    }
    return render(request, 'attendance/student_form.html', context)


@login_required
def attendance_list(request):
    """لیست حضور و غیاب"""
    attendances = Attendance.objects.select_related('student', 'student__parent', 'student__class_room', 'student__class_room__teacher').all()
    
    # اگر کاربر معلم است، فقط حضور و غیاب دانش‌آموزان کلاس‌های خودش را نشان بده
    user_profile = request.user.profile
    if user_profile.is_teacher() and user_profile.teacher:
        attendances = attendances.filter(student__class_room__teacher=user_profile.teacher)
    
    # تاریخ امروز
    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    
    # فیلتر بر اساس تاریخ
    date_filter = request.GET.get('date', '')
    date_filter_obj = None
    if date_filter:
        try:
            filter_date = timezone.datetime.strptime(date_filter, '%Y-%m-%d').date()
            date_filter_obj = filter_date
            attendances = attendances.filter(date=filter_date)
        except ValueError:
            pass
    
    # فیلتر بر اساس وضعیت
    status_filter = request.GET.get('status', '')
    if status_filter:
        attendances = attendances.filter(status=status_filter)
    
    # فقط غایب‌ها
    absent_only = request.GET.get('absent_only', '')
    if absent_only:
        attendances = attendances.filter(status=Attendance.ABSENT)
    
    # مرتب‌سازی
    attendances = attendances.order_by('-date', 'student')
    
    # Pagination
    paginator = Paginator(attendances, 20)  # 20 رکورد در هر صفحه
    page = request.GET.get('page', 1)
    
    try:
        attendances_page = paginator.page(page)
    except PageNotAnInteger:
        attendances_page = paginator.page(1)
    except EmptyPage:
        attendances_page = paginator.page(paginator.num_pages)
    
    context = {
        'attendances': attendances_page,
        'date_filter': date_filter,
        'date_filter_obj': date_filter_obj,  # date object برای استفاده در template
        'status_filter': status_filter,
        'absent_only': absent_only,
        'status_choices': Attendance.STATUS_CHOICES,
        'today': today,  # تاریخ امروز برای پیش‌فرض تقویم
        'today_str': today_str,  # تاریخ امروز به فرمت string برای JavaScript
    }
    return render(request, 'attendance/attendance_list.html', context)


@login_required
def export_attendance_excel_view(request):
    """Export لیست حضور و غیاب به Excel"""
    # دریافت فیلترها
    date_filter = request.GET.get('date', '')
    date_filter_obj = None
    if date_filter:
        try:
            date_filter_obj = timezone.datetime.strptime(date_filter, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    status_filter = request.GET.get('status', '')
    absent_only = request.GET.get('absent_only', '') == '1'
    
    # اگر کاربر معلم است، فقط حضور و غیاب دانش‌آموزان کلاس‌های خودش را نشان بده
    user_profile = request.user.profile
    if user_profile.is_teacher() and user_profile.teacher:
        attendances_query = Attendance.objects.filter(student__class_room__teacher=user_profile.teacher)
    else:
        attendances_query = Attendance.objects.all()
    
    return export_attendance_excel(
        attendances_query=attendances_query,
        date_filter=date_filter_obj,
        status_filter=status_filter,
        absent_only=absent_only
    )


@login_required
def mark_attendance(request):
    """ثبت حضور و غیاب"""
    from .models import Class, Teacher
    
    user_profile = request.user.profile
    is_teacher = user_profile.is_teacher()
    
    if request.method == 'POST':
        persian_date_str = request.POST.get('persian_date', '').strip()
        student_id = request.POST.get('student_id')
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        student_phone = request.POST.get('student_phone', '').strip()
        
        # DEBUG: بررسی مقدار تاریخ دریافت شده
        print(f"DEBUG - persian_date_str: '{persian_date_str}'")
        
        # تبدیل تاریخ شمسی به میلادی
        def persian_to_gregorian(jy, jm, jd):
            """تبدیل تاریخ شمسی به میلادی"""
            jy += 1595
            days = -355668 + (365 * jy) + (jy // 33) * 8 + ((jy % 33) + 3) // 4 + jd
            if jm < 7:
                days += (jm - 1) * 31
            else:
                days += ((jm - 7) * 30) + 186
            gy = 400 * (days // 146097)
            days %= 146097
            if days > 36524:
                days -= 1
                gy += 100 * (days // 36524)
                days %= 36524
                if days >= 365:
                    days += 1
            gy += 4 * (days // 1461)
            days %= 1461
            if days > 365:
                gy += (days - 1) // 365
                days = (days - 1) % 365
            gd = days + 1
            sal_a = [0, 31, 28 if not ((gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)) else 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            gm = 0
            while gm < 13 and gd > sal_a[gm]:
                gd -= sal_a[gm]
                gm += 1
            return gy, gm, gd
        
        try:
            # پارس کردن تاریخ شمسی (فرمت: 1403/09/14 یا 14 / آذر / 1403)
            import re
            # حذف فاصله‌ها و تبدیل به فرمت استاندارد
            persian_date_clean = persian_date_str.replace(' ', '')
            
            # اگر فرمت عددی است (1403/09/14)
            if re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', persian_date_clean):
                parts = persian_date_clean.split('/')
                jy, jm, jd = int(parts[0]), int(parts[1]), int(parts[2])
            # اگر فرمت با نام ماه است (14/آذر/1403)
            else:
                persian_months = {
                    'فروردین': 1, 'اردیبهشت': 2, 'خرداد': 3, 'تیر': 4,
                    'مرداد': 5, 'شهریور': 6, 'مهر': 7, 'آبان': 8,
                    'آذر': 9, 'دی': 10, 'بهمن': 11, 'اسفند': 12
                }
                parts = persian_date_clean.split('/')
                if len(parts) == 3:
                    jd = int(parts[0])
                    jm = persian_months.get(parts[1], 0)
                    jy = int(parts[2])
                else:
                    raise ValueError(f"فرمت تاریخ نامعتبر: {persian_date_str}")
            
            # تبدیل به میلادی
            gy, gm, gd = persian_to_gregorian(jy, jm, jd)
            attendance_date = date(gy, gm, gd)
            print(f"DEBUG - تاریخ میلادی: {attendance_date}")
            
            student = Student.objects.select_related('parent').get(id=student_id, is_active=True)
            
            # بررسی اینکه آیا شماره تلفن اولیا وجود دارد یا نه
            parent_has_phone = student.parent and student.parent.phone_number
            
            # اگر شماره تلفن اولیا وجود نداشت و شماره تلفن دانش‌آموز هم وارد نشده
            if not parent_has_phone and not student_phone:
                messages.error(request, '⚠️ شماره تلفن اولیا وجود ندارد. لطفاً شماره تلفن دانش‌آموز را وارد کنید.')
                return redirect('attendance:mark_attendance')
            
            # ذخیره یا به‌روزرسانی شماره تلفن دانش‌آموز
            if student_phone:
                import re
                if re.match(r'^09\d{9}$', student_phone):
                    student.phone_number = student_phone
                    student.save(update_fields=['phone_number'])
                else:
                    messages.error(request, 'شماره تلفن باید با فرمت 09123456789 باشد.')
                    return redirect('attendance:mark_attendance')
            
            attendance, created = Attendance.objects.get_or_create(
                student=student,
                date=attendance_date,
                defaults={
                    'status': status,
                    'notes': notes,
                }
            )
            
            if not created:
                attendance.status = status
                attendance.notes = notes
                attendance.save()
            
            # برای غیبت، تاخیر و غیبت موجه پیامک ارسال کن
            if status in [Attendance.ABSENT, Attendance.EXCUSED, Attendance.LATE] and not attendance.sms_sent:
                # دریافت نام مدرسه از پروفایل کاربر
                school_name = user_profile.get_school_name() if hasattr(user_profile, 'get_school_name') else "مدرسه"
                
                # ارسال پیامک به اولیا
                parent_sms_success = send_absence_sms(attendance, school_name)
                if parent_sms_success:
                    messages.success(request, f'حضور و غیاب ثبت شد و پیامک به اولیا ارسال شد.')
                else:
                    messages.success(request, 'حضور و غیاب ثبت شد. (خطا در ارسال پیامک)')
            else:
                messages.success(request, 'حضور و غیاب با موفقیت ثبت شد.')
            
            return redirect('attendance:attendance_list')
            
        except Student.DoesNotExist:
            messages.error(request, 'دانش‌آموز یافت نشد.')
        except ValueError as e:
            print(f"DEBUG - ValueError: {e}")
            print(f"DEBUG - persian_date_str was: '{persian_date_str}'")
            messages.error(request, f'تاریخ نامعتبر است: {persian_date_str}')
        except Exception as e:
            print(f"DEBUG - Exception: {e}")
            messages.error(request, f'خطا: {str(e)}')
    
    # نمایش فرم
    today = date.today()
    
    # دریافت فیلترها از GET
    selected_teacher_id = request.GET.get('teacher_id', '')
    selected_class_id = request.GET.get('class_id', '')
    
    # اگر کاربر معلم است، فقط کلاس‌های خودش را نشان بده
    if is_teacher and user_profile.teacher:
        teacher = user_profile.teacher
        classes = Class.objects.filter(teacher=teacher, is_active=True).select_related('teacher')
        
        # اگر فقط یک کلاس دارد و کلاس انتخاب نشده، به صورت خودکار انتخاب کن
        if classes.count() == 1 and not selected_class_id:
            selected_class_id = str(classes.first().id)
        
        students_query = Student.objects.filter(
            class_room__teacher=teacher,
            is_active=True
        ).select_related('class_room', 'class_room__teacher', 'parent')
        
        # فیلتر بر اساس کلاس انتخاب شده
        if selected_class_id:
            students_query = students_query.filter(class_room_id=selected_class_id)
        
        students = students_query.order_by('class_room__grade', 'class_room__name', 'last_name', 'first_name')
    else:
        # برای نقش‌های دیگر، همه کلاس‌ها و معلمان را نشان بده
        classes_query = Class.objects.filter(is_active=True).select_related('teacher')
        
        # فیلتر بر اساس معلم انتخاب شده
        if selected_teacher_id:
            classes_query = classes_query.filter(teacher_id=selected_teacher_id)
        
        classes = classes_query.order_by('grade', 'name')
        
        students_query = Student.objects.filter(is_active=True).select_related('class_room', 'class_room__teacher', 'parent')
        
        # فیلتر بر اساس کلاس انتخاب شده
        if selected_class_id:
            students_query = students_query.filter(class_room_id=selected_class_id)
        # اگر معلم انتخاب شده اما کلاس انتخاب نشده، دانش‌آموزان کلاس‌های آن معلم را نشان بده
        elif selected_teacher_id:
            students_query = students_query.filter(class_room__teacher_id=selected_teacher_id)
        
        students = students_query.order_by('class_room__grade', 'class_room__name', 'last_name', 'first_name')
    
    teachers = Teacher.objects.all().order_by('last_name', 'first_name')
    
    context = {
        'students': students,
        'classes': classes,
        'teachers': teachers,
        'today': today,
        'status_choices': Attendance.STATUS_CHOICES,
        'is_teacher': is_teacher,
        'user_teacher': user_profile.teacher if is_teacher else None,
        'selected_teacher_id': selected_teacher_id,
        'selected_class_id': selected_class_id,
    }
    return render(request, 'attendance/mark_attendance.html', context)


@login_required
def send_sms_manually(request, attendance_id):
    """ارسال دستی پیامک برای یک غیبت"""
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    if attendance.status == Attendance.ABSENT:
        success = send_absence_sms(attendance)
        if success:
            messages.success(request, 'پیامک با موفقیت ارسال شد.')
        else:
            messages.error(request, 'خطا در ارسال پیامک.')
    else:
        messages.warning(request, 'این رکورد غیبت نیست.')
    
    return redirect('attendance:attendance_list')



@admin_required
def user_list(request):
    """لیست کاربران - فقط برای مدیران"""
    users = User.objects.select_related('profile').all().order_by('-date_joined')
    
    # جستجو
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(profile__phone_number__icontains=search_query)
        )
    
    # فیلتر بر اساس نقش
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    # Pagination
    paginator = Paginator(users, 20)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'role_choices': UserProfile.ROLE_CHOICES,
    }
    return render(request, 'attendance/user_list.html', context)


@admin_required
def user_create(request):
    """ایجاد کاربر جدید - فقط برای مدیران"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()
        role = request.POST.get('role', 'teacher')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        
        # بررسی‌های اولیه
        if not username:
            messages.error(request, 'نام کاربری الزامی است.')
            context = {
                'role_choices': UserProfile.ROLE_CHOICES,
            }
            return render(request, 'attendance/user_form.html', context)
        
        if not password1:
            messages.error(request, 'رمز عبور الزامی است.')
            context = {
                'role_choices': UserProfile.ROLE_CHOICES,
            }
            return render(request, 'attendance/user_form.html', context)
        
        if password1 != password2:
            messages.error(request, 'رمز عبور و تکرار آن باید یکسان باشند.')
            context = {
                'role_choices': UserProfile.ROLE_CHOICES,
            }
            return render(request, 'attendance/user_form.html', context)
        
        # بررسی تکراری نبودن نام کاربری
        if User.objects.filter(username=username).exists():
            messages.error(request, 'این نام کاربری قبلاً استفاده شده است.')
            context = {
                'role_choices': UserProfile.ROLE_CHOICES,
            }
            return render(request, 'attendance/user_form.html', context)
        
        # بررسی تکراری نبودن شماره تلفن
        if phone_number:
            if UserProfile.objects.filter(phone_number=phone_number).exists():
                messages.error(request, 'این شماره تلفن قبلاً استفاده شده است.')
                context = {
                    'role_choices': UserProfile.ROLE_CHOICES,
                }
                return render(request, 'attendance/user_form.html', context)
            
            # اعتبارسنجی شماره تلفن
            import re
            if not re.match(r'^09\d{9}$', phone_number):
                messages.error(request, 'شماره تلفن باید با فرمت 09123456789 باشد.')
                context = {
                    'role_choices': UserProfile.ROLE_CHOICES,
                }
                return render(request, 'attendance/user_form.html', context)
        
        # ایجاد کاربر بدون اعتبارسنجی رمز عبور
        try:
            user = User.objects.create_user(
                username=username,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # ایجاد یا به‌روزرسانی پروفایل (signal ممکن است قبلاً آن را ایجاد کرده باشد)
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': role,
                    'phone_number': phone_number if phone_number else None
                }
            )
            
            # اگر پروفایل قبلاً وجود داشت، آن را به‌روزرسانی کن
            if not created:
                profile.role = role
                profile.phone_number = phone_number if phone_number else None
                profile.save()
            
            messages.success(request, f'کاربر {user.username} با موفقیت ایجاد شد.')
            return redirect('attendance:user_list')
        except Exception as e:
            messages.error(request, f'خطا در ایجاد کاربر: {str(e)}')
            context = {
                'role_choices': UserProfile.ROLE_CHOICES,
            }
            return render(request, 'attendance/user_form.html', context)
    else:
        context = {
            'role_choices': UserProfile.ROLE_CHOICES,
        }
        return render(request, 'attendance/user_form.html', context)


@admin_required
def user_edit(request, user_id):
    """ویرایش کاربر - فقط برای مدیران"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role', 'teacher')
        phone_number = request.POST.get('phone_number', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        # بررسی اینکه username تکراری نباشد
        if username != user.username:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'این نام کاربری قبلاً استفاده شده است.')
                return redirect('attendance:user_edit', user_id=user_id)
        
        # بررسی اینکه phone_number تکراری نباشد (اگر وارد شده)
        if phone_number:
            existing_profile = UserProfile.objects.filter(phone_number=phone_number).exclude(user=user).first()
            if existing_profile:
                messages.error(request, 'این شماره تلفن قبلاً استفاده شده است.')
                return redirect('attendance:user_edit', user_id=user_id)
        
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = is_active
        user.save()
        
        # به‌روزرسانی نقش و شماره تلفن
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': role,
                'phone_number': phone_number if phone_number else None
            }
        )
        # اگر پروفایل قبلاً وجود داشت، آن را به‌روزرسانی کن
        if not created:
            old_role = profile.role
            profile.role = role
            profile.phone_number = phone_number if phone_number else None
            profile.save()  # این signal را trigger می‌کند
            
            # اگر نقش به معلم تغییر کرد و معلم مرتبط ندارد، signal را دوباره trigger کن
            if role == 'teacher' and not profile.teacher:
                from attendance.signals import create_teacher_for_user
                # refresh برای اطمینان از آخرین وضعیت
                profile.refresh_from_db()
                if not profile.teacher:
                    create_teacher_for_user(UserProfile, profile, False)
                    profile.refresh_from_db()
        
        messages.success(request, f'کاربر {user.username} با موفقیت به‌روزرسانی شد.')
        return redirect('attendance:user_list')
    
    context = {
        'user_obj': user,
        'role_choices': UserProfile.ROLE_CHOICES,
    }
    return render(request, 'attendance/user_form.html', context)


@admin_required
def user_delete(request, user_id):
    """حذف کاربر - فقط برای مدیران"""
    user = get_object_or_404(User, id=user_id)
    
    # جلوگیری از حذف خود کاربر
    if user == request.user:
        messages.error(request, 'شما نمی‌توانید خودتان را حذف کنید.')
        return redirect('attendance:user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'کاربر {username} با موفقیت حذف شد.')
        return redirect('attendance:user_list')
    
    context = {
        'user_obj': user,
    }
    return render(request, 'attendance/user_confirm_delete.html', context)
