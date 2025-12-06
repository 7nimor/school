# اسکریپت رفع خطای migrations برای Windows PowerShell
# این اسکریپت تمام مراحل لازم برای رفع خطای django_session را انجام می‌دهد

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "رفع خطای Migration Django" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# بررسی وجود manage.py
if (-not (Test-Path "manage.py")) {
    Write-Host "❌ خطا: فایل manage.py یافت نشد!" -ForegroundColor Red
    Write-Host "لطفاً این اسکریپت را در مسیر ریشه پروژه اجرا کنید." -ForegroundColor Red
    exit 1
}

Write-Host "✓ فایل manage.py یافت شد" -ForegroundColor Green

# بررسی و نصب Django
Write-Host ""
Write-Host "بررسی نصب Django..." -ForegroundColor Yellow
try {
    $djangoVersion = python -c "import django; print(django.get_version())" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Django نصب شده است (نسخه: $djangoVersion)" -ForegroundColor Green
    } else {
        throw "Django not found"
    }
} catch {
    Write-Host "❌ Django نصب نشده است. در حال نصب..." -ForegroundColor Yellow
    Write-Host "نصب وابستگی‌ها از requirements.txt..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ خطا در نصب وابستگی‌ها!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ وابستگی‌ها با موفقیت نصب شدند" -ForegroundColor Green
}

# بررسی وجود فایل .env
Write-Host ""
Write-Host "بررسی فایل .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "⚠ فایل .env وجود ندارد. در حال ایجاد..." -ForegroundColor Yellow
    
    # تولید SECRET_KEY
    try {
        $secretKey = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
        
        $envContent = @"
SECRET_KEY=$secretKey
DEBUG=True
SMS_API_KEY=
SMS_API_URL=
SMS_SENDER_NUMBER=
"@
        
        $envContent | Out-File -FilePath ".env" -Encoding utf8 -NoNewline
        Write-Host "✓ فایل .env ایجاد شد" -ForegroundColor Green
    } catch {
        Write-Host "⚠ خطا در ایجاد .env. لطفاً به صورت دستی ایجاد کنید." -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ فایل .env موجود است" -ForegroundColor Green
}

# بررسی وضعیت migrations
Write-Host ""
Write-Host "بررسی وضعیت migrations..." -ForegroundColor Yellow
try {
    $migrationsStatus = python manage.py showmigrations 2>&1
    Write-Host $migrationsStatus
} catch {
    Write-Host "⚠ خطا در بررسی migrations" -ForegroundColor Yellow
}

# اجرای makemigrations
Write-Host ""
Write-Host "ایجاد migrations جدید..." -ForegroundColor Yellow
python manage.py makemigrations
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ هشدار: برخی migrations ایجاد نشدند (ممکن است طبیعی باشد)" -ForegroundColor Yellow
} else {
    Write-Host "✓ Migrations بررسی شدند" -ForegroundColor Green
}

# اجرای migrate (مهم‌ترین بخش)
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "اجرای migrations (این مرحله مهم است)..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
python manage.py migrate

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ Migrations با موفقیت اجرا شدند!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # بررسی وجود جدول django_session
    Write-Host "بررسی وجود جدول django_session..." -ForegroundColor Yellow
    try {
        python -c "import django; django.setup(); from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"django_session\"'); result = cursor.fetchone(); print('✓ جدول django_session وجود دارد' if result else '⚠ جدول django_session وجود ندارد')" 2>&1
    } catch {
        Write-Host "⚠ نتوانستیم وضعیت جدول را بررسی کنیم" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "مراحل بعدی:" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "1. ایجاد کاربر ادمین (اختیاری):" -ForegroundColor White
    Write-Host "   python manage.py createsuperuser" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. اجرای سرور:" -ForegroundColor White
    Write-Host "   python manage.py runserver" -ForegroundColor Gray
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "❌ خطا در اجرای migrations!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "راه‌حل‌های پیشنهادی:" -ForegroundColor Yellow
    Write-Host "1. بررسی لاگ‌های بالا برای یافتن خطا" -ForegroundColor White
    Write-Host "2. حذف db.sqlite3 و اجرای مجدد migrate" -ForegroundColor White
    Write-Host "3. بررسی فایل FIX_MIGRATION_ERROR.md برای راهنمای کامل" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "انجام شد!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

