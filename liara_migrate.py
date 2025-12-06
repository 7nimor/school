#!/usr/bin/env python
"""
اسکریپت کامل برای Migration و Import داده‌ها در لیارا
این اسکریپت باید در Console لیارا اجرا شود
"""
import os
import sys
import django

# تنظیم Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')

# تنظیم DATABASE_URL برای لیارا
os.environ['DATABASE_URL'] = 'postgresql://root:T7XfIPAcCii9z96VzkpLJ8mQ@apo.liara.cloud:33022/postgres'

django.setup()

from django.core.management import call_command
from django.db import connection

def main():
    print("=" * 60)
    print("🚀 شروع Migration و Import داده‌ها")
    print("=" * 60)
    
    # تست اتصال
    print("\n🔍 در حال تست اتصال به دیتابیس...")
    try:
        connection.ensure_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print(f"✅ اتصال برقرار شد - PostgreSQL {version[0][:50]}...")
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")
        sys.exit(1)
    
    # اجرای Migration
    print("\n🔄 در حال اجرای Migration‌ها...")
    try:
        call_command('migrate', '--run-syncdb', verbosity=1)
        print("✅ Migration‌ها با موفقیت اجرا شدند")
    except Exception as e:
        print(f"❌ خطا در Migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Import داده‌ها
    print("\n📥 در حال import داده‌ها...")
    if os.path.exists('data_export.json'):
        try:
            call_command('loaddata', 'data_export.json', verbosity=1)
            print("✅ Import داده‌ها با موفقیت انجام شد")
        except Exception as e:
            print(f"⚠️  خطا در import (ممکن است برخی داده‌ها قبلاً وجود داشته باشند): {e}")
            # ادامه می‌دهیم حتی اگر خطا باشد
    else:
        print("⚠️  فایل data_export.json یافت نشد")
        print("💡 لطفاً فایل را آپلود کنید و دوباره اجرا کنید")
    
    print("\n" + "=" * 60)
    print("✅ تمام مراحل با موفقیت انجام شد!")
    print("=" * 60)

if __name__ == '__main__':
    main()

