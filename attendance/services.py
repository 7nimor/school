"""
سرویس ارسال پیامک
"""
import requests
from django.conf import settings
from django.utils import timezone
from .models import Attendance


def send_sms(phone_number, message):
    """
    ارسال پیامک به شماره تلفن
    این تابع باید با سرویس پیامک شما سازگار شود
    """
    # اگر تنظیمات SMS تنظیم نشده باشد، فقط لاگ می‌کند
    if not settings.SMS_API_KEY or not settings.SMS_API_URL:
        print(f"[SMS] (در حالت تست) پیامک به {phone_number}: {message}")
        return True

    try:
        # این بخش باید با API سرویس پیامک شما سازگار شود
        # مثال برای استفاده از یک سرویس پیامک ایرانی:
        payload = {
            'api_key': settings.SMS_API_KEY,
            'sender': settings.SMS_SENDER_NUMBER,
            'receptor': phone_number,
            'message': message,
        }
        
        response = requests.post(settings.SMS_API_URL, data=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"خطا در ارسال پیامک: {e}")
        return False


def send_absence_sms(attendance):
    """
    ارسال پیامک غیبت به اولیا دانش‌آموز
    """
    if attendance.status != Attendance.ABSENT:
        return False
    
    if attendance.sms_sent:
        return True  # قبلاً ارسال شده
    
    student = attendance.student
    parent = student.parent
    
    # متن پیامک
    message = (
        f"اولیا گرامی {parent.first_name} {parent.last_name}\n"
        f"دانش‌آموز {student.first_name} {student.last_name} "
        f"در تاریخ {attendance.date.strftime('%Y/%m/%d')} غایب بوده است.\n"
        f"مدرسه"
    )
    
    # ارسال پیامک
    success = send_sms(parent.phone_number, message)
    
    if success:
        attendance.sms_sent = True
        attendance.save(update_fields=['sms_sent'])
    
    return success

