# راهنمای رفع خطای `django.db.utils.OperationalError: no such table: django_session`

## 🔍 مشکل

خطا نشان می‌دهد که جدول‌های دیتابیس Django (مثل `django_session`) ایجاد نشده‌اند. این معمولاً به این معنی است که:
1. Migrations اجرا نشده‌اند
2. یا دیتابیس به درستی راه‌اندازی نشده است

## ✅ راه حل

### مرحله 1: فعال‌سازی Virtual Environment (اگر وجود دارد)

اگر virtual environment دارید، ابتدا آن را فعال کنید:

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

اگر virtual environment ندارید، به مرحله 2 بروید.

### مرحله 2: نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

### مرحله 3: ایجاد فایل .env (اگر وجود ندارد)

اگر فایل `.env` ندارید، آن را ایجاد کنید:

**Windows (PowerShell):**
```powershell
$secret = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
@"
SECRET_KEY=$secret
DEBUG=True
SMS_API_KEY=
SMS_API_URL=
SMS_SENDER_NUMBER=
"@ | Out-File -FilePath .env -Encoding utf8
```

**Linux/Mac:**
```bash
cat > .env << EOF
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=True
SMS_API_KEY=
SMS_API_URL=
SMS_SENDER_NUMBER=
EOF
```

یا به صورت دستی فایل `.env` را در ریشه پروژه ایجاد کنید:

```
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
SMS_API_KEY=
SMS_API_URL=
SMS_SENDER_NUMBER=
```

### مرحله 4: اجرای Migrations

این مهم‌ترین مرحله است:

```bash
# ایجاد migrations جدید (در صورت نیاز)
python manage.py makemigrations

# اجرای migrations برای ایجاد جدول‌ها
python manage.py migrate
```

این دستورات باید تمام جدول‌های لازم از جمله `django_session` را ایجاد کنند.

### مرحله 5: بررسی وضعیت Migrations

برای اطمینان از اجرای موفق migrations:

```bash
python manage.py showmigrations
```

همه migrations باید با `[X]` علامت خورده باشند.

### مرحله 6: ایجاد Superuser (اگر نیاز دارید)

اگر کاربر ادمین ندارید:

```bash
python manage.py createsuperuser
```

## 🔧 اگر مشکل ادامه داشت

### گزینه 1: حذف و ایجاد مجدد دیتابیس (⚠️ تمام داده‌ها پاک می‌شوند)

```bash
# حذف فایل دیتابیس
del db.sqlite3  # Windows
rm db.sqlite3   # Linux/Mac

# اجرای مجدد migrations
python manage.py migrate
```

### گزینه 2: بررسی وجود فایل db.sqlite3

اگر فایل `db.sqlite3` وجود ندارد یا آسیب دیده است:

1. فایل `db.sqlite3` را حذف کنید (اگر وجود دارد)
2. دستور `python manage.py migrate` را اجرا کنید

### گزینه 3: بررسی تنظیمات دیتابیس

مطمئن شوید که در `attendance_system/settings.py` دیتابیس به درستی تنظیم شده:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

## 📝 دستورات سریع (کپی و پیست)

```powershell
# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرای migrations
python manage.py migrate

# ایجاد superuser (اختیاری)
python manage.py createsuperuser

# اجرای سرور
python manage.py runserver
```

## ✅ بررسی موفقیت

بعد از اجرای `migrate`، باید پیام‌هایی شبیه این را ببینید:

```
Operations to perform:
  Apply all migrations: admin, attendance, auth, contenttypes, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
  Applying sessions.0001_initial... OK  # این خط مهم است!
```

اگر این خطا را دیدید:
```
django.db.utils.OperationalError: no such table: django_session
```

بعد از اجرای `migrate`، این خطا باید برطرف شود.

## 🆘 اگر هنوز مشکل دارید

1. مطمئن شوید Django نصب شده: `python -c "import django; print(django.get_version())"`
2. مطمئن شوید در مسیر درست هستید (همان مسیری که `manage.py` وجود دارد)
3. مطمئن شوید فایل `.env` وجود دارد و SECRET_KEY دارد
4. لاگ‌های کامل را بررسی کنید

