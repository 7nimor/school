# راهنمای کامل Deploy روی لیارا

## فایل‌های آماده شده

✅ `data_export.json` - تمام داده‌های SQLite (365KB)
✅ `liara.json` - تنظیمات لیارا با DATABASE_URL
✅ `liara_migrate.py` - اسکریپت Migration و Import
✅ `requirements.txt` - وابستگی‌های Python

## مراحل Deploy

### 1. Commit و Push به Git

```bash
git add .
git commit -m "Prepare for Liara deployment with PostgreSQL"
git push
```

### 2. در پنل لیارا

#### الف) تنظیم Environment Variables:

در بخش Environment Variables، متغیرهای زیر را اضافه کنید:

```
DATABASE_URL=postgresql://root:T7XfIPAcCii9z96VzkpLJ8mQ@apo.liara.cloud:33022/postgres
SECRET_KEY=your-secret-key-here
DEBUG=False
```

**برای تولید SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### ب) Deploy پروژه

1. در پنل لیارا، به بخش Deployments بروید
2. Deploy جدید را اجرا کنید
3. Migration‌ها به صورت خودکار اجرا می‌شوند

### 3. Import داده‌ها (در Console لیارا)

بعد از deploy موفق، در Console لیارا (Terminal) اجرا کنید:

```bash
python liara_migrate.py
```

یا به صورت دستی:

```bash
# تنظیم DATABASE_URL (اگر در env نیست)
export DATABASE_URL="postgresql://root:T7XfIPAcCii9z96VzkpLJ8mQ@apo.liara.cloud:33022/postgres"

# اجرای Migration (اگر قبلاً انجام نشده)
python manage.py migrate

# Import داده‌ها
python manage.py loaddata data_export.json
```

## بررسی

بعد از import، می‌توانید بررسی کنید:

```bash
python manage.py shell
```

```python
from attendance.models import Student, Teacher, Class, Attendance
print(f"دانش‌آموزان: {Student.objects.count()}")
print(f"معلمان: {Teacher.objects.count()}")
print(f"کلاس‌ها: {Class.objects.count()}")
print(f"حضور و غیاب: {Attendance.objects.count()}")
```

## نکات مهم

1. ✅ `DATABASE_URL` در `liara.json` تنظیم شده است
2. ✅ Migration‌ها در build به صورت خودکار اجرا می‌شوند
3. ✅ فایل `data_export.json` باید در root پروژه باشد
4. ⚠️ بعد از import، فایل `data_export.json` را می‌توانید حذف کنید (اختیاری)

## عیب‌یابی

اگر مشکلی پیش آمد:

1. **خطای اتصال به دیتابیس:**
   - بررسی کنید که DATABASE_URL درست است
   - بررسی کنید که دیتابیس در لیارا فعال است

2. **خطای Migration:**
   - لاگ‌های build را بررسی کنید
   - در Console لیارا: `python manage.py migrate --verbosity 2`

3. **خطای Import:**
   - بررسی کنید که `data_export.json` وجود دارد
   - بررسی کنید که Migration‌ها اجرا شده‌اند

