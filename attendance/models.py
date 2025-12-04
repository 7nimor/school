from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """پروفایل کاربر برای نقش‌ها"""
    ROLE_CHOICES = [
        ('admin', 'مدیر'),
        ('teacher', 'معلم'),
        ('deputy', 'معاون'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='کاربر'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='teacher',
        verbose_name='نقش'
    )
    phone_regex = RegexValidator(
        regex=r'^09\d{9}$',
        message="شماره تلفن باید با فرمت 09123456789 باشد"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=11,
        unique=True,
        blank=True,
        null=True,
        verbose_name='شماره تلفن'
    )
    teacher = models.ForeignKey(
        'Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_profiles',
        verbose_name='معلم مرتبط'
    )
    school_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='نام مدرسه',
        help_text='نام مدرسه برای نمایش در سیستم'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    
    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل‌های کاربران'
        ordering = ['user__username']
    
    def __str__(self):
        role_display = dict(self.ROLE_CHOICES).get(self.role, self.role)
        return f"{self.user.username} - {role_display}"
    
    def is_admin(self):
        """بررسی اینکه آیا کاربر مدیر است"""
        return self.role == 'admin'
    
    def is_teacher(self):
        """بررسی اینکه آیا کاربر معلم است"""
        return self.role == 'teacher'
    
    def is_deputy(self):
        """بررسی اینکه آیا کاربر معاون است"""
        return self.role == 'deputy'
    
    def get_school_name(self):
        """دریافت نام مدرسه یا نام پیش‌فرض"""
        return self.school_name if self.school_name else 'سیستم مدیریت حضور و غیاب'


class Teacher(models.Model):
    """مدل معلم"""
    first_name = models.CharField(max_length=100, verbose_name='نام')
    last_name = models.CharField(max_length=100, verbose_name='نام خانوادگی')
    phone_regex = RegexValidator(
        regex=r'^09\d{9}$',
        message="شماره تلفن باید با فرمت 09123456789 باشد"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=11,
        unique=True,
        blank=True,
        null=True,
        verbose_name='شماره تلفن'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'معلم'
        verbose_name_plural = 'معلمان'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Class(models.Model):
    """مدل کلاس"""
    name = models.CharField(max_length=50, verbose_name='نام کلاس')
    grade = models.CharField(max_length=20, verbose_name='پایه', help_text='مثال: اول، دوم، سوم')
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes',
        verbose_name='معلم'
    )
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'کلاس'
        verbose_name_plural = 'کلاس‌ها'
        ordering = ['grade', 'name']

    def __str__(self):
        teacher_name = f" - {self.teacher}" if self.teacher else ""
        return f"{self.grade} {self.name}{teacher_name}"


class Parent(models.Model):
    """مدل اولیا/سرپرست دانش‌آموز"""
    first_name = models.CharField(max_length=100, verbose_name='نام')
    last_name = models.CharField(max_length=100, verbose_name='نام خانوادگی')
    phone_regex = RegexValidator(
        regex=r'^09\d{9}$',
        message="شماره تلفن باید با فرمت 09123456789 باشد"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=11,
        unique=True,
        verbose_name='شماره تلفن'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'اولیا'
        verbose_name_plural = 'اولیا'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.phone_number}"


class Student(models.Model):
    """مدل دانش‌آموز"""
    first_name = models.CharField(max_length=100, verbose_name='نام')
    last_name = models.CharField(max_length=100, verbose_name='نام خانوادگی')
    student_id = models.CharField(max_length=20, unique=True, verbose_name='شماره دانش‌آموزی')
    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name='students',
        verbose_name='اولیا/سرپرست'
    )
    class_room = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='کلاس'
    )
    phone_regex = RegexValidator(
        regex=r'^09\d{9}$',
        message="شماره تلفن باید با فرمت 09123456789 باشد"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=11,
        blank=True,
        null=True,
        verbose_name='شماره تلفن دانش‌آموز'
    )
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ آخرین ویرایش')
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_students',
        verbose_name='آخرین ویرایش‌کننده'
    )

    class Meta:
        verbose_name = 'دانش‌آموز'
        verbose_name_plural = 'دانش‌آموزان'
        ordering = ['class_room__grade', 'class_room__name', 'last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.student_id}"


class Attendance(models.Model):
    """مدل حضور و غیاب"""
    PRESENT = 'present'
    ABSENT = 'absent'
    EXCUSED = 'excused'
    LATE = 'late'

    STATUS_CHOICES = [
        (PRESENT, 'حاضر'),
        (ABSENT, 'غایب'),
        (EXCUSED, 'غایب موجه'),
        (LATE, 'تأخیر'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='دانش‌آموز'
    )
    date = models.DateField(verbose_name='تاریخ')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PRESENT,
        verbose_name='وضعیت'
    )
    notes = models.TextField(blank=True, null=True, verbose_name='یادداشت')
    sms_sent = models.BooleanField(default=False, verbose_name='پیامک ارسال شده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'حضور و غیاب'
        verbose_name_plural = 'حضور و غیاب‌ها'
        ordering = ['-date', 'student']
        unique_together = ['student', 'date']

    def __str__(self):
        status_display = dict(self.STATUS_CHOICES).get(self.status, self.status)
        return f"{self.student} - {self.date} - {status_display}"
