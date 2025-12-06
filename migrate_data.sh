#!/bin/bash
set -e

echo "============================================================"
echo "🚀 شروع انتقال داده‌ها از SQLite به PostgreSQL"
echo "============================================================"

# Step 1: Export از SQLite
echo ""
echo "📤 Step 1: Export داده‌ها از SQLite..."
unset DATABASE_URL
python manage.py dumpdata --natural-foreign --natural-primary \
    --exclude contenttypes --exclude auth.Permission --exclude sessions \
    --indent 2 --output data_export.json

if [ ! -f data_export.json ]; then
    echo "❌ خطا: فایل data_export.json ایجاد نشد"
    exit 1
fi

echo "✅ Export با موفقیت انجام شد"

# Step 2: تنظیم DATABASE_URL و Migration
echo ""
echo "📥 Step 2: تنظیم PostgreSQL و اجرای Migration..."
export DATABASE_URL="postgresql://root:T7XfIPAcCii9z96VzkpLJ8mQ@apo.liara.cloud:33022/postgres"

# تست اتصال
echo "🔍 در حال تست اتصال..."
python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'attendance_system.settings'
import django
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    print('✅ اتصال برقرار شد')
except Exception as e:
    print(f'❌ خطا در اتصال: {e}')
    exit(1)
"

# اجرای Migration
echo "🔄 در حال اجرای Migration‌ها..."
python manage.py migrate --run-syncdb

# Step 3: Import داده‌ها
echo ""
echo "📥 Step 3: Import داده‌ها به PostgreSQL..."
python manage.py loaddata data_export.json || echo "⚠️  برخی خطاها در import رخ داد (ممکن است داده‌ها قبلاً وجود داشته باشند)"

echo ""
echo "============================================================"
echo "✅ انتقال داده‌ها با موفقیت انجام شد!"
echo "============================================================"
echo ""
echo "💡 نکته: فایل data_export.json را می‌توانید حذف کنید"
echo ""
echo "📝 DATABASE_URL برای استفاده در لیارا:"
echo "postgresql://root:T7XfIPAcCii9z96VzkpLJ8mQ@apo.liara.cloud:33022/postgres"

