# راهنمای Deploy روی لیارا

## فایل‌های مورد نیاز

1. **liara.json**: فایل تنظیمات لیارا
2. **requirements.txt**: وابستگی‌های Python
3. **runtime.txt**: نسخه Python (اختیاری)

## متغیرهای محیطی مورد نیاز

در پنل لیارا، متغیرهای زیر را تنظیم کنید:

### ضروری:
- `SECRET_KEY`: کلید امنیتی Django (یک رشته تصادفی)
- `DEBUG`: `False` برای production
- `DATABASE_URL`: آدرس دیتابیس PostgreSQL لیارا (به صورت خودکار تنظیم می‌شود)

### اختیاری (برای SMS):
- `SMS_API_KEY`: کلید API سرویس SMS
- `SMS_API_URL`: آدرس API سرویس SMS
- `SMS_SENDER_NUMBER`: شماره فرستنده SMS

## مراحل Deploy

1. پروژه را به Git اضافه کنید:
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

2. در پنل لیارا:
   - یک اپلیکیشن Django جدید ایجاد کنید
   - پروژه را از Git متصل کنید
   - متغیرهای محیطی را تنظیم کنید
   - Deploy را اجرا کنید

## نکات مهم

- دیتابیس PostgreSQL به صورت خودکار توسط لیارا ایجاد می‌شود
- فایل‌های static به صورت خودکار جمع‌آوری می‌شوند
- Migration‌ها به صورت خودکار اجرا می‌شوند
- برای ایجاد superuser، از Console لیارا استفاده کنید:
  ```bash
  python manage.py createsuperuser
  ```

