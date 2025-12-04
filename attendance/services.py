"""
سرویس ارسال پیامک
"""
import requests
import urllib.parse
from django.conf import settings
from django.utils import timezone
from excelstyler import shamsi_date
from .models import Attendance


# تنظیمات سرویس پیامک ساهند
SMS_USERNAME = 'hamedan'
SMS_PASSWORD = 'hamedan12345'
SMS_SENDER = '30002501'
SMS_API_URL = 'http://webservice.sahandsms.com/newsmswebservice.asmx/SendPostUrl'


def check_mobile_number(mobile):
    """بررسی صحت شماره موبایل"""
    import re
    if mobile and re.match(r'^09\d{9}$', mobile):
        return True
    return False


def format_persian_date(date_obj):
    """فرمت تاریخ شمسی با استفاده از excelstyler"""
    return str(shamsi_date(date_obj))


def send_sms(phone_number, message):
    """
    ارسال پیامک به شماره تلفن با استفاده از سرویس ساهند
    """
    if not check_mobile_number(phone_number):
        print(f"[SMS] شماره موبایل نامعتبر: {phone_number}")
        return False

    try:
        # انکود کردن پیام برای URL
        encoded_message = urllib.parse.quote(message)
        
        # ساخت URL درخواست
        url = (
            f"{SMS_API_URL}?"
            f"username={SMS_USERNAME}&"
            f"password={SMS_PASSWORD}&"
            f"from={SMS_SENDER}&"
            f"to={phone_number}&"
            f"message={encoded_message}"
        )
        
        response = requests.get(url, timeout=15)
        
        print(f"[SMS] ارسال به {phone_number} - Status: {response.status_code}")
        
        if response.status_code == 200:
            return True
        else:
            print(f"[SMS] خطا در ارسال: {response.text}")
            return False
            
    except Exception as e:
        print(f"[SMS] خطا در ارسال پیامک: {str(e)}")
        return False


def send_absence_sms(attendance, school_name=None):
    """
    ارسال پیامک غیبت/تاخیر به اولیا دانش‌آموز
    """
    if attendance.sms_sent:
        return True  # قبلاً ارسال شده
    
    student = attendance.student
    parent = student.parent
    
    # دریافت نام مدرسه از پروفایل کاربر (اگر وجود داشته باشد)
    if not school_name:
        school_name = "مدرسه"
    elif "مدرسه" not in school_name:
        school_name = f"مدرسه {school_name}"
    
    # تعیین نوع وضعیت
    status_text = ""
    if attendance.status == Attendance.ABSENT:
        status_text = "غیبت غیرموجه"
    elif attendance.status == Attendance.EXCUSED:
        status_text = "غیبت موجه"
    elif attendance.status == Attendance.LATE:
        status_text = "تاخیر"
    else:
        return False  # وضعیت نامعتبر
    
    # تاریخ شمسی
    persian_date = format_persian_date(attendance.date)
    
    # متن پیامک
    message = (
        f"اولیای محترم\n"
        f"فرزند گرامی شما {student.first_name} {student.last_name} "
        f"در تاریخ {persian_date} "
        f"{status_text} داشته است.\n"
        f"با احترام {school_name}"
    )
    
    # ارسال پیامک
    success = send_sms(parent.phone_number, message)
    
    if success:
        attendance.sms_sent = True
        attendance.save(update_fields=['sms_sent'])
    
    return success


def test_sms_simple():
    """
    تابع ساده برای تست ارسال پیامک
    """
    mobile = '09165597588'
    message = 'تست ارسال پیامک از سامانه حضور و غیاب'
    
    if check_mobile_number(mobile):
        try:
            encoded_message = urllib.parse.quote(message)
            url = (
                f"{SMS_API_URL}?"
                f"username={SMS_USERNAME}&"
                f"password={SMS_PASSWORD}&"
                f"from={SMS_SENDER}&"
                f"to={mobile}&"
                f"message={encoded_message}"
            )
            response = requests.get(url, timeout=15)
            print(f"SMS sent successfully. Status: {response.status_code}")
            return f"پیامک با موفقیت ارسال شد. Status: {response.status_code}"
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            return f"خطا در ارسال پیامک: {str(e)}"
    else:
        return "شماره موبایل معتبر نیست"
