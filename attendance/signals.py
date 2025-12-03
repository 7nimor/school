from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Teacher


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """ایجاد خودکار پروفایل کاربر هنگام ساخت کاربر جدید"""
    if created:
        UserProfile.objects.get_or_create(user=instance, defaults={'role': 'teacher'})


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """ذخیره خودکار پروفایل کاربر"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.get_or_create(user=instance, defaults={'role': 'teacher'})


@receiver(post_save, sender=UserProfile)
def create_teacher_for_user(sender, instance, created, **kwargs):
    """ایجاد خودکار معلم برای کاربر با نقش معلم"""
    # استفاده از update_fields برای جلوگیری از loop
    update_fields = kwargs.get('update_fields', None)
    if update_fields and 'teacher' in update_fields:
        return  # اگر teacher در حال به‌روزرسانی است، signal را اجرا نکن
    
    # اگر نقش معلم است و معلم مرتبط ندارد
    if instance.role == 'teacher' and not instance.teacher:
        user = instance.user
        # استفاده از نام و نام خانوادگی کاربر، یا username اگر خالی باشد
        first_name = user.first_name.strip() if user.first_name else user.username
        last_name = user.last_name.strip() if user.last_name else ''
        
        # اگر last_name خالی است، از username استفاده کن
        if not last_name:
            # اگر username شامل فاصله یا underscore است، تقسیم کن
            username_parts = user.username.replace('_', ' ').split()
            if len(username_parts) > 1:
                first_name = username_parts[0]
                last_name = ' '.join(username_parts[1:])
            else:
                first_name = user.username
                last_name = ''
        
        # استفاده از شماره تلفن پروفایل کاربر یا None
        # ابتدا از دیتابیس refresh کن تا مطمئن شویم که phone_number به‌روز است
        instance.refresh_from_db()
        phone_number = instance.phone_number if instance.phone_number else None
        
        # ایجاد معلم جدید
        # ابتدا بررسی کن که آیا معلمی با همین نام وجود دارد
        teacher = Teacher.objects.filter(
            first_name=first_name,
            last_name=last_name
        ).first()
        
        if not teacher:
            # ایجاد معلم جدید
            teacher = Teacher.objects.create(
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number
            )
        else:
            # اگر معلم از قبل وجود داشت و شماره تلفن نداشت، شماره تلفن را به‌روزرسانی کن
            if not teacher.phone_number and phone_number:
                teacher.phone_number = phone_number
                teacher.save(update_fields=['phone_number'])
            # اگر معلم شماره تلفن داشت اما phone_number جدید متفاوت است، به‌روزرسانی کن
            elif teacher.phone_number != phone_number and phone_number:
                teacher.phone_number = phone_number
                teacher.save(update_fields=['phone_number'])
        
        # اتصال معلم به پروفایل کاربر (با استفاده از update برای جلوگیری از loop)
        UserProfile.objects.filter(id=instance.id).update(teacher=teacher)
        
        # به‌روزرسانی شماره تلفن معلم اگر لازم باشد (بعد از اتصال)
        # refresh از دیتابیس برای اطمینان از آخرین وضعیت
        teacher.refresh_from_db()
        instance.refresh_from_db()
        
        # اگر phone_number در پروفایل تنظیم شده اما معلم phone_number ندارد یا متفاوت است
        if instance.phone_number:
            if not teacher.phone_number or teacher.phone_number != instance.phone_number:
                teacher.phone_number = instance.phone_number
                teacher.save(update_fields=['phone_number'])

