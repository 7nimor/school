# 🐘 راهنمای اتصال به PostgreSQL رایگان (Neon)

## مرحله 1: ساخت اکانت و دیتابیس در Neon

1. به سایت **[neon.tech](https://neon.tech)** بروید
2. روی **Sign Up** کلیک کنید
3. با **GitHub** یا **Google** وارد شوید
4. یک پروژه جدید بسازید:
   - **Project name**: `school-attendance`
   - **Database name**: `attendance_db`
   - **Region**: `AWS Frankfurt (eu-central-1)` یا نزدیک‌ترین منطقه
5. روی **Create Project** کلیک کنید

## مرحله 2: کپی کردن Connection String

بعد از ساخت پروژه:

1. در داشبورد Neon، به بخش **Connection Details** بروید
2. **Connection string** را کپی کنید

فرمت Connection string:
```
postgresql://[user]:[password]@[host]/[database]?sslmode=require
```

**مثال:**
```
postgresql://school_owner:abc123xyz@ep-cool-forest-123456.eu-central-1.aws.neon.tech/attendance_db?sslmode=require
```

## مرحله 3: تنظیم در پروژه

### گزینه A: استفاده از فایل .env (توصیه می‌شود)

فایل `.env` را در ریشه پروژه باز کنید و این خط را اضافه کنید:

```env
DATABASE_URL=postgresql://[user]:[password]@[host]/[database]?sslmode=require
```

**مثال کامل فایل .env:**
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
SMS_API_KEY=
SMS_API_URL=
SMS_SENDER_NUMBER=
DATABASE_URL=postgresql://school_owner:abc123xyz@ep-cool-forest-123456.eu-central-1.aws.neon.tech/attendance_db?sslmode=require
```

### گزینه B: استفاده مستقیم (فقط برای تست)

اگر فایل `.env` ندارید، می‌توانید مستقیماً در ترمینال تنظیم کنید:

**PowerShell:**
```powershell
$env:DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"
python manage.py migrate
```

## مرحله 4: اجرای Migrations

بعد از تنظیم DATABASE_URL:

```powershell
# فعال‌سازی virtual environment
D:\.school_env\Scripts\Activate.ps1

# اجرای migrations
python manage.py migrate

# ایجاد superuser
python manage.py createsuperuser

# اجرای سرور
python manage.py runserver
```

## مرحله 5: تأیید اتصال

برای بررسی اتصال به دیتابیس:

```powershell
python manage.py dbshell
```

یا:

```powershell
python -c "import django; django.setup(); from django.db import connection; print('✅ اتصال موفق!' if connection.ensure_connection() is None else '❌ خطا')"
```

---

## 🔧 عیب‌یابی

### خطا: "could not connect to server"
- بررسی کنید که CONNECTION_URL درست است
- بررسی کنید که اینترنت متصل است
- بررسی کنید که `?sslmode=require` در انتهای URL وجود دارد

### خطا: "password authentication failed"
- رمز عبور را دوباره از داشبورد Neon کپی کنید
- مطمئن شوید که کاراکترهای خاص در URL encode شده‌اند

### خطا: "database does not exist"
- نام دیتابیس را بررسی کنید
- از داشبورد Neon دوباره connection string را کپی کنید

---

## 📋 مقایسه سرویس‌های رایگان PostgreSQL

| سرویس | فضا رایگان | محدودیت | لینک |
|-------|-----------|---------|------|
| **Neon** | 512 MB | بدون کارت اعتباری | [neon.tech](https://neon.tech) |
| **Supabase** | 500 MB | 2 پروژه رایگان | [supabase.com](https://supabase.com) |
| **ElephantSQL** | 20 MB | 5 اتصال همزمان | [elephantsql.com](https://elephantsql.com) |
| **Railway** | $5 اعتبار | محدود | [railway.app](https://railway.app) |

**توصیه:** از **Neon** استفاده کنید - سریع، رایگان، و بدون نیاز به کارت اعتباری.

---

## ✅ بررسی نهایی

بعد از تنظیم، این موارد را بررسی کنید:

- [ ] فایل `.env` دارای `DATABASE_URL` است
- [ ] `python manage.py migrate` بدون خطا اجرا شد
- [ ] `python manage.py createsuperuser` کاربر ادمین ایجاد کرد
- [ ] سرور بدون خطا اجرا می‌شود
- [ ] می‌توانید وارد سیستم شوید

---

## 🔄 بازگشت به SQLite

اگر می‌خواهید به SQLite برگردید، کافیست `DATABASE_URL` را از فایل `.env` حذف کنید یا خالی بگذارید:

```env
DATABASE_URL=
```

سیستم به صورت خودکار از SQLite استفاده خواهد کرد.

