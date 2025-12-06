# 🚀 راهنمای سریع رفع خطا

## مشکل
```
django.db.utils.OperationalError: no such table: django_session
```

## ✅ راه حل سریع (3 مرحله)

### 1️⃣ نصب وابستگی‌ها
```powershell
pip install -r requirements.txt
```

### 2️⃣ اجرای Migrations
```powershell
python manage.py migrate
```

### 3️⃣ بررسی موفقیت
```powershell
python manage.py runserver
```

اگر سرور بدون خطا اجرا شد، مشکل حل شده است! ✅

---

## 🔧 اگر مرحله 2 خطا داد

### گزینه A: ایجاد مجدد دیتابیس (⚠️ تمام داده‌ها پاک می‌شوند)

```powershell
# حذف دیتابیس قدیمی
del db.sqlite3

# اجرای مجدد migrations
python manage.py migrate
```

### گزینه B: استفاده از اسکریپت خودکار

```powershell
.\fix_migrations.ps1
```

---

## 📝 دستورات کامل (کپی کنید)

```powershell
# 1. نصب وابستگی‌ها
pip install -r requirements.txt

# 2. اجرای migrations
python manage.py migrate

# 3. ایجاد کاربر ادمین (اختیاری)
python manage.py createsuperuser

# 4. اجرای سرور
python manage.py runserver
```

---

## ❓ سوالات متداول

**Q: اگر فایل .env ندارم چه کنم؟**  
A: فایل `.env` در ریشه پروژه ایجاد کنید و این محتوا را در آن قرار دهید:
```
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
SMS_API_KEY=
SMS_API_URL=
SMS_SENDER_NUMBER=
```

**Q: اگر virtual environment دارم چه کنم؟**  
A: ابتدا آن را فعال کنید:
```powershell
.\venv\Scripts\Activate.ps1
```

**Q: هنوز خطا می‌گیرم**  
A: فایل `FIX_MIGRATION_ERROR.md` را برای راهنمای کامل بخوانید.

---

## 🆘 نیاز به کمک بیشتر؟

فایل‌های راهنما:
- `FIX_MIGRATION_ERROR.md` - راهنمای کامل
- `fix_migrations.ps1` - اسکریپت خودکار
- `PROJECT_ANALYSIS.md` - آنالیز کامل پروژه

