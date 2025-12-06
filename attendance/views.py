from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import date, timedelta
from .models import Student, Attendance, Parent, UserProfile
from .services import send_absence_sms, upload_excel_file, upload_teachers_excel
from .decorators import admin_required
from .excel import export_students_excel, export_attendance_excel, export_student_attendance_excel


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
    
    students = Student.objects.filter(is_active=True).select_related('parent', 'class_room', 'class_room__teacher')
    
    # اگر کاربر معلم است، فقط دانش‌آموزان کلاس‌های خودش را نشان بده
    if is_teacher and user_profile.teacher:
        students = students.filter(class_room__teacher=user_profile.teacher)
        # برای معلم: فقط به ترتیب حروف الفبای فارسی روی نام خانوادگی
        students = students.order_by('last_name', 'first_name')
    else:
        # برای مدیر و معاون: اول به ترتیب کلاس و بعد به ترتیب حروف الفبای فارسی روی نام خانوادگی
        students = students.order_by('class_room__grade', 'class_room__name', 'last_name', 'first_name')
    
    # فیلتر بر اساس کلاس
    class_filter = request.GET.get('class', '')
    if class_filter:
        students = students.filter(class_room_id=class_filter)
    
    # جستجو
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
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
        'is_teacher': is_teacher,
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
    from .models import Class
    
    attendances = Attendance.objects.select_related('student', 'student__parent', 'student__class_room', 'student__class_room__teacher').all()
    
    user_profile = request.user.profile
    is_teacher = user_profile.is_teacher()
    
    # اگر کاربر معلم است، فقط حضور و غیاب دانش‌آموزان کلاس‌های خودش را نشان بده
    if is_teacher and user_profile.teacher:
        attendances = attendances.filter(student__class_room__teacher=user_profile.teacher)
        classes = Class.objects.filter(teacher=user_profile.teacher, is_active=True)
    else:
        # برای مدیر و معاون، همه کلاس‌ها
        classes = Class.objects.filter(is_active=True).select_related('teacher')
    
    # تاریخ امروز
    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    
    # فیلتر بر اساس کلاس (برای مدیر و معاون)
    class_filter = request.GET.get('class', '')
    if class_filter:
        attendances = attendances.filter(student__class_room_id=class_filter)
    
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
    
    # مرتب‌سازی بر اساس تاریخ و سپس id از آخری به اولی
    attendances = attendances.order_by('-date', '-id')
    
    # Pagination
    paginator = Paginator(attendances, 10)  # 10 رکورد در هر صفحه
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
        'date_filter_obj': date_filter_obj,
        'status_filter': status_filter,
        'absent_only': absent_only,
        'status_choices': Attendance.STATUS_CHOICES,
        'today': today,
        'today_str': today_str,
        'classes': classes,
        'class_filter': class_filter,
        'is_teacher': is_teacher,
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
    class_filter = request.GET.get('class', '')
    
    # اگر کاربر معلم است، فقط حضور و غیاب دانش‌آموزان کلاس‌های خودش را نشان بده
    user_profile = request.user.profile
    if user_profile.is_teacher() and user_profile.teacher:
        attendances_query = Attendance.objects.filter(student__class_room__teacher=user_profile.teacher)
    else:
        attendances_query = Attendance.objects.all()
    
    # فیلتر بر اساس کلاس
    if class_filter:
        attendances_query = attendances_query.filter(student__class_room_id=class_filter)
    
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
        student_id = request.POST.get('student_id')  # این ID دانش‌آموز است نه شماره دانش‌آموزی
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        parent_phone_input = request.POST.get('parent_phone', '').strip()
        
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
            
            # اگر شماره تلفن اولیا وجود نداشت و شماره تلفن هم وارد نشده
            if not parent_has_phone and not parent_phone_input:
                messages.error(request, '⚠️ شماره تلفن اولیا وجود ندارد. لطفاً شماره تلفن را وارد کنید.')
                return redirect('attendance:mark_attendance')
            
            # ذخیره یا به‌روزرسانی شماره تلفن اولیا
            if parent_phone_input:
                import re
                if re.match(r'^09\d{9}$', parent_phone_input):
                    # ذخیره شماره تلفن برای اولیا
                    student.parent.phone_number = parent_phone_input
                    student.parent.save(update_fields=['phone_number'])
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
            force_send = request.POST.get('force_send', '') == '1'
            attendance_id_resend = request.POST.get('attendance_id', '')
            
            # اگر attendance_id ارسال شده، از همان رکورد استفاده کن
            if attendance_id_resend:
                try:
                    attendance = Attendance.objects.get(id=attendance_id_resend)
                except Attendance.DoesNotExist:
                    pass
            
            if status in [Attendance.ABSENT, Attendance.EXCUSED, Attendance.LATE]:
                if attendance.sms_sent and not force_send:
                    # قبلاً پیامک ارسال شده، نیاز به تأیید کاربر
                    return JsonResponse({
                        'status': 'confirm_resend',
                        'message': 'برای این دانش‌آموز قبلاً پیامک ارسال شده است. آیا می‌خواهید دوباره ارسال شود؟',
                        'attendance_id': attendance.id
                    })
                
                # دریافت نام مدرسه از پروفایل کاربر
                school_name = user_profile.get_school_name() if hasattr(user_profile, 'get_school_name') else "مدرسه"
                
                # اگر force_send است، اول sms_sent را False کن
                if force_send and attendance.sms_sent:
                    attendance.sms_sent = False
                    attendance.save(update_fields=['sms_sent'])
                
                # ارسال پیامک به اولیا
                if not is_teacher:
                    parent_sms_success = send_absence_sms(attendance, school_name)
                    if parent_sms_success:
                        messages.success(request, f'حضور و غیاب ثبت شد و پیامک به اولیا ارسال شد.')
                    else:
                        messages.success(request, 'حضور و غیاب ثبت شد. (خطا در ارسال پیامک)')
                messages.success(request, 'حضور و غیاب با موفقیت ثبت شد.')

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
    
    teachers = Teacher.objects.prefetch_related('classes').all().order_by('last_name', 'first_name')
    
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
    """ارسال دستی پیامک برای غیبت، تاخیر یا غیبت موجه"""
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    if attendance.status in [Attendance.ABSENT, Attendance.EXCUSED, Attendance.LATE]:
        # دریافت نام مدرسه از پروفایل کاربر
        user_profile = request.user.profile
        school_name = user_profile.get_school_name() if hasattr(user_profile, 'get_school_name') else "مدرسه"
        
        # اگر resend است، ابتدا sms_sent را False کن
        resend = request.GET.get('resend', '') == '1'
        if resend and attendance.sms_sent:
            attendance.sms_sent = False
            attendance.save(update_fields=['sms_sent'])
        
        success = send_absence_sms(attendance, school_name)
        if success:
            messages.success(request, 'پیامک با موفقیت ارسال شد.')
        else:
            messages.error(request, 'خطا در ارسال پیامک.')
    else:
        messages.warning(request, 'این رکورد حضور است و نیازی به ارسال پیامک ندارد.')
    
    return redirect('attendance:attendance_list')


@login_required
def delete_attendance(request, attendance_id):
    """حذف رکورد حضور و غیاب - فقط اگر پیامک ارسال نشده باشد"""
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    # بررسی اینکه پیامک ارسال نشده باشد
    if attendance.sms_sent:
        messages.error(request, 'امکان حذف رکوردی که پیامک برای آن ارسال شده است وجود ندارد.')
        return redirect('attendance:attendance_list')
    
    # بررسی دسترسی - معلم فقط می‌تواند رکوردهای کلاس خودش را حذف کند
    user_profile = request.user.profile
    is_teacher = user_profile.is_teacher()
    
    if is_teacher and user_profile.teacher:
        if not attendance.student.class_room or attendance.student.class_room.teacher != user_profile.teacher:
            messages.error(request, 'شما اجازه حذف این رکورد را ندارید.')
            return redirect('attendance:attendance_list')
    
    # حذف رکورد
    student_name = f"{attendance.student.first_name} {attendance.student.last_name}"
    attendance.delete()
    messages.success(request, f'رکورد حضور و غیاب {student_name} با موفقیت حذف شد.')
    
    return redirect('attendance:attendance_list')


@login_required
def student_attendance_detail(request, student_id):
    """جزییات حضور و غیاب یک دانش‌آموز"""
    import jdatetime
    from collections import Counter
    
    user_profile = request.user.profile
    is_teacher = user_profile.is_teacher()
    
    student = get_object_or_404(Student, id=student_id)
    
    # اگر کاربر معلم است، فقط دانش‌آموزان کلاس‌های خودش را می‌تواند ببیند
    if is_teacher and user_profile.teacher:
        if not student.class_room or student.class_room.teacher != user_profile.teacher:
            messages.error(request, 'شما اجازه مشاهده این دانش‌آموز را ندارید.')
            return redirect('attendance:student_list')
    
    # دریافت تمام حضور و غیاب‌های دانش‌آموز
    attendances = Attendance.objects.filter(student=student).order_by('-date')
    
    # فیلتر بر اساس وضعیت
    status_filter = request.GET.get('status', '')
    if status_filter:
        attendances = attendances.filter(status=status_filter)
    
    # آمار کلی
    total_records = Attendance.objects.filter(student=student).count()
    absent_count = Attendance.objects.filter(student=student, status=Attendance.ABSENT).count()
    excused_count = Attendance.objects.filter(student=student, status=Attendance.EXCUSED).count()
    late_count = Attendance.objects.filter(student=student, status=Attendance.LATE).count()
    
    # تحلیل زمانی غیبت‌ها
    weekday_names = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']
    month_names = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 
                   'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    
    # شمارش غیبت‌ها بر اساس روز هفته و ماه
    weekday_absences = Counter()
    month_absences = Counter()
    
    absent_records = Attendance.objects.filter(student=student, status=Attendance.ABSENT)
    for record in absent_records:
        # روز هفته (شنبه = 0)
        jalali_date = jdatetime.date.fromgregorian(date=record.date)
        weekday = jalali_date.weekday()  # 0 = شنبه
        weekday_absences[weekday] += 1
        
        # ماه شمسی
        month_absences[jalali_date.month - 1] += 1
    
    # پیدا کردن بیشترین غیبت‌ها
    weekday_stats = []
    for i, name in enumerate(weekday_names):
        count = weekday_absences.get(i, 0)
        weekday_stats.append({'name': name, 'count': count})
    
    month_stats = []
    for i, name in enumerate(month_names):
        count = month_absences.get(i, 0)
        if count > 0:
            month_stats.append({'name': name, 'count': count})
    
    # مرتب‌سازی بر اساس تعداد (نزولی)
    month_stats.sort(key=lambda x: x['count'], reverse=True)
    
    # بیشترین روز غیبت
    max_weekday_count = max([s['count'] for s in weekday_stats]) if weekday_stats else 0
    max_weekday = [s['name'] for s in weekday_stats if s['count'] == max_weekday_count and max_weekday_count > 0]
    
    # Pagination
    paginator = Paginator(attendances, 20)
    page = request.GET.get('page', 1)
    
    try:
        attendances_page = paginator.page(page)
    except PageNotAnInteger:
        attendances_page = paginator.page(1)
    except EmptyPage:
        attendances_page = paginator.page(paginator.num_pages)
    
    context = {
        'student': student,
        'attendances': attendances_page,
        'status_filter': status_filter,
        'status_choices': Attendance.STATUS_CHOICES,
        'total_records': total_records,
        'absent_count': absent_count,
        'excused_count': excused_count,
        'late_count': late_count,
        'weekday_stats': weekday_stats,
        'month_stats': month_stats[:5],  # فقط 5 ماه برتر
        'max_weekday': max_weekday,
    }
    return render(request, 'attendance/student_attendance_detail.html', context)


@login_required
def export_student_attendance_excel_view(request, student_id):
    """Export حضور و غیاب یک دانش‌آموز به Excel"""
    user_profile = request.user.profile
    is_teacher = user_profile.is_teacher()
    
    student = get_object_or_404(Student, id=student_id)
    
    # اگر کاربر معلم است، فقط دانش‌آموزان کلاس‌های خودش را می‌تواند ببیند
    if is_teacher and user_profile.teacher:
        if not student.class_room or student.class_room.teacher != user_profile.teacher:
            messages.error(request, 'شما اجازه دسترسی به این دانش‌آموز را ندارید.')
            return redirect('attendance:student_list')
    
    # دریافت تمام حضور و غیاب‌های دانش‌آموز
    attendances = Attendance.objects.filter(student=student)
    
    # فیلتر بر اساس وضعیت
    status_filter = request.GET.get('status', '')
    
    return export_student_attendance_excel(student, attendances, status_filter)


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


@login_required
def statistics_view(request):
    """صفحه آمار کلی"""
    import jdatetime
    from collections import Counter
    from django.db.models import Count
    from .models import Class
    
    user_profile = request.user.profile
    is_teacher = user_profile.is_teacher()
    
    # دریافت بازه زمانی
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    date_from_obj = None
    date_to_obj = None
    
    if date_from:
        try:
            date_from_obj = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # فیلتر بر اساس نقش کاربر
    if is_teacher and user_profile.teacher:
        # معلم فقط کلاس‌های خودش رو می‌بینه
        classes = Class.objects.filter(teacher=user_profile.teacher, is_active=True)
        students = Student.objects.filter(class_room__teacher=user_profile.teacher, is_active=True)
        absences = Attendance.objects.filter(
            student__class_room__teacher=user_profile.teacher,
            status=Attendance.ABSENT
        )
        all_attendances = Attendance.objects.filter(student__class_room__teacher=user_profile.teacher)
    else:
        # مدیر و معاون همه چیز رو می‌بینن
        classes = Class.objects.filter(is_active=True)
        students = Student.objects.filter(is_active=True)
        absences = Attendance.objects.filter(status=Attendance.ABSENT)
        all_attendances = Attendance.objects.all()
    
    # اعمال فیلتر بازه زمانی
    if date_from_obj:
        absences = absences.filter(date__gte=date_from_obj)
        all_attendances = all_attendances.filter(date__gte=date_from_obj)
    if date_to_obj:
        absences = absences.filter(date__lte=date_to_obj)
        all_attendances = all_attendances.filter(date__lte=date_to_obj)
    
    # آمار کلی
    total_students = students.count()
    total_absences = absences.count()
    total_excused = all_attendances.filter(status=Attendance.EXCUSED).count()
    total_late = all_attendances.filter(status=Attendance.LATE).count()
    
    # کلاس‌های با بیشترین غیبت
    class_stats = []
    for cls in classes.select_related('teacher'):
        absence_count = absences.filter(student__class_room=cls).count()
        student_count = students.filter(class_room=cls).count()
        class_stats.append({
            'class': cls,
            'absence_count': absence_count,
            'student_count': student_count,
            'avg_per_student': round(absence_count / student_count, 1) if student_count > 0 else 0
        })
    class_stats.sort(key=lambda x: x['absence_count'], reverse=True)
    
    # دانش‌آموزان با بیشترین غیبت
    student_absence_counts = absences.values('student').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    top_students = []
    for item in student_absence_counts:
        student = students.filter(id=item['student']).select_related('class_room').first()
        if student:
            top_students.append({
                'student': student,
                'absence_count': item['count']
            })
    
    # تاریخ‌های با بیشترین غیبت
    date_counts = Counter()
    weekday_names = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']
    weekday_counts = Counter()
    month_counts = Counter()
    
    for absence in absences:
        date_counts[absence.date] += 1
        jalali_date = jdatetime.date.fromgregorian(date=absence.date)
        weekday_counts[jalali_date.weekday()] += 1
        month_counts[jalali_date.month] += 1
    
    # ۱۰ تاریخ با بیشترین غیبت
    top_dates = []
    for d, count in date_counts.most_common(10):
        jalali = jdatetime.date.fromgregorian(date=d)
        top_dates.append({
            'date': d,
            'jalali': jalali.strftime('%Y/%m/%d'),
            'weekday': weekday_names[jalali.weekday()],
            'count': count
        })
    
    # آمار روزهای هفته
    weekday_stats = []
    for i, name in enumerate(weekday_names):
        weekday_stats.append({
            'name': name,
            'count': weekday_counts.get(i, 0)
        })
    max_weekday_count = max([w['count'] for w in weekday_stats]) if weekday_stats else 0
    
    # آمار ماه‌ها
    month_names = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
                   'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    month_stats = []
    for i, name in enumerate(month_names):
        count = month_counts.get(i + 1, 0)
        if count > 0:
            month_stats.append({'name': name, 'count': count})
    month_stats.sort(key=lambda x: x['count'], reverse=True)
    
    # تبدیل تاریخ‌ها به شمسی برای نمایش
    date_from_jalali = None
    date_to_jalali = None
    if date_from_obj:
        date_from_jalali = jdatetime.date.fromgregorian(date=date_from_obj).strftime('%Y/%m/%d')
    if date_to_obj:
        date_to_jalali = jdatetime.date.fromgregorian(date=date_to_obj).strftime('%Y/%m/%d')
    
    context = {
        'is_teacher': is_teacher,
        'total_students': total_students,
        'total_absences': total_absences,
        'total_excused': total_excused,
        'total_late': total_late,
        'class_stats': class_stats,
        'top_students': top_students,
        'top_dates': top_dates,
        'weekday_stats': weekday_stats,
        'max_weekday_count': max_weekday_count,
        'month_stats': month_stats[:6],
        'date_from': date_from,
        'date_to': date_to,
        'date_from_jalali': date_from_jalali,
        'date_to_jalali': date_to_jalali,
    }
    return render(request, 'attendance/statistics.html', context)


@csrf_exempt
def upload_students_excel(request):
    """آپلود فایل اکسل برای ایجاد دانش‌آموزان (کلاس‌ها باید از قبل در سیستم وجود داشته باشند)"""
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'لطفاً یک فایل اکسل انتخاب کنید.')
            return render(request, 'attendance/upload_excel.html')
        
        # بررسی نوع فایل
        uploaded_file = request.FILES['file']
        if not uploaded_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'فقط فایل‌های اکسل (.xlsx, .xls) مجاز هستند.')
            return render(request, 'attendance/upload_excel.html')
        
        # پردازش فایل
        try:
            result = upload_excel_file(request)
            
            if result['success']:
                success_msg = (
                    f"✅ فایل با موفقیت پردازش شد!\n"
                    f"👨‍🎓 دانش‌آموزان ایجاد شده: {result['created_students']}\n"
                    f"👨‍👩‍👧 اولیا ایجاد شده: {result['created_parents']}"
                )
                messages.success(request, success_msg)
                
                if result['errors']:
                    error_msg = f"⚠️ خطاها ({len(result['errors'])} مورد):\n" + "\n".join(result['errors'][:10])
                    if len(result['errors']) > 10:
                        error_msg += f"\n... و {len(result['errors']) - 10} خطای دیگر"
                    messages.warning(request, error_msg)
            else:
                messages.error(request, result.get('message', 'خطا در پردازش فایل.'))
                if result.get('errors'):
                    messages.error(request, "\n".join(result['errors'][:5]))
        
        except Exception as e:
            messages.error(request, f'خطا در پردازش فایل: {str(e)}')
        
        return redirect('attendance:upload_students_excel')
    
    return render(request, 'attendance/upload_excel.html')


@csrf_exempt
def upload_teachers_excel_view(request):
    """آپلود فایل اکسل برای ایجاد معلمان و کاربران"""
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'لطفاً یک فایل اکسل انتخاب کنید.')
            return render(request, 'attendance/upload_teachers_excel.html')
        
        # بررسی نوع فایل
        uploaded_file = request.FILES['file']
        if not uploaded_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'فقط فایل‌های اکسل (.xlsx, .xls) مجاز هستند.')
            return render(request, 'attendance/upload_teachers_excel.html')
        
        # پردازش فایل
        try:
            result = upload_teachers_excel(request)
            
            if result['success']:
                success_msg = (
                    f"✅ فایل با موفقیت پردازش شد!\n"
                    f"👨‍🏫 معلمان ایجاد شده: {result['created_teachers']}\n"
                    f"👤 کاربران ایجاد شده: {result['created_users']}"
                )
                messages.success(request, success_msg)
                
                if result['errors']:
                    error_msg = f"⚠️ خطاها ({len(result['errors'])} مورد):\n" + "\n".join(result['errors'][:10])
                    if len(result['errors']) > 10:
                        error_msg += f"\n... و {len(result['errors']) - 10} خطای دیگر"
                    messages.warning(request, error_msg)
            else:
                messages.error(request, result.get('message', 'خطا در پردازش فایل.'))
                if result.get('errors'):
                    messages.error(request, "\n".join(result['errors'][:5]))
        
        except Exception as e:
            messages.error(request, f'خطا در پردازش فایل: {str(e)}')
        
        return redirect('attendance:upload_teachers_excel')
    
    return render(request, 'attendance/upload_teachers_excel.html')


@login_required
def user_profile(request):
    """صفحه پروفایل کاربر - تغییر نام کاربری و رمز عبور"""
    user = request.user
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        current_password = request.POST.get('current_password', '').strip()
        new_password1 = request.POST.get('new_password1', '').strip()
        new_password2 = request.POST.get('new_password2', '').strip()
        
        # بررسی نام کاربری
        if not username:
            messages.error(request, 'نام کاربری الزامی است.')
            return render(request, 'attendance/user_profile.html', {'user_obj': user})
        
        # اگر نام کاربری تغییر کرده
        if username != user.username:
            # بررسی تکراری نبودن نام کاربری
            if User.objects.filter(username=username).exists():
                messages.error(request, 'این نام کاربری قبلاً استفاده شده است.')
                return render(request, 'attendance/user_profile.html', {'user_obj': user})
            user.username = username
            user.save()
            messages.success(request, 'نام کاربری با موفقیت تغییر کرد.')
        
        # اگر رمز عبور جدید وارد شده
        if new_password1 or new_password2:
            # بررسی اینکه رمز عبور فعلی وارد شده باشد
            if not current_password:
                messages.error(request, 'برای تغییر رمز عبور، باید رمز عبور فعلی را وارد کنید.')
                return render(request, 'attendance/user_profile.html', {'user_obj': user})
            
            # بررسی صحت رمز عبور فعلی
            if not user.check_password(current_password):
                messages.error(request, 'رمز عبور فعلی اشتباه است.')
                return render(request, 'attendance/user_profile.html', {'user_obj': user})
            
            # بررسی اینکه رمز عبور جدید و تکرار آن یکسان باشند
            if new_password1 != new_password2:
                messages.error(request, 'رمز عبور جدید و تکرار آن باید یکسان باشند.')
                return render(request, 'attendance/user_profile.html', {'user_obj': user})
            
            # بررسی طول رمز عبور
            if len(new_password1) < 8:
                messages.error(request, 'رمز عبور باید حداقل 8 کاراکتر باشد.')
                return render(request, 'attendance/user_profile.html', {'user_obj': user})
            
            # تغییر رمز عبور
            user.set_password(new_password1)
            user.save()
            messages.success(request, 'رمز عبور با موفقیت تغییر کرد.')
        
        return redirect('attendance:user_profile')
    
    context = {
        'user_obj': user,
    }
    return render(request, 'attendance/user_profile.html', context)
