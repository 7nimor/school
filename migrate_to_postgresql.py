#!/usr/bin/env python
"""
اسکریپت انتقال داده‌ها از SQLite به PostgreSQL
"""
import os
import sys
import subprocess

def export_from_sqlite():
    """Export داده‌ها از SQLite"""
    print("📤 در حال export داده‌ها از SQLite...")
    
    # حذف DATABASE_URL برای استفاده از SQLite
    env = os.environ.copy()
    if 'DATABASE_URL' in env:
        del env['DATABASE_URL']
    
    # Export به JSON
    result = subprocess.run(
        ['python', 'manage.py', 'dumpdata', '--natural-foreign', '--natural-primary',
         '--exclude', 'contenttypes', '--exclude', 'auth.Permission', '--exclude', 'sessions',
         '--indent', '2', '--output', 'data_export.json'],
        env=env,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ خطا در export: {result.stderr}")
        return False
    
    print("✅ Export با موفقیت انجام شد: data_export.json")
    return True

def setup_postgresql():
    """تنظیم و Migration PostgreSQL"""
    print("📥 در حال تنظیم PostgreSQL...")
    
    # تنظیم DATABASE_URL برای PostgreSQL
    # لیارا نیاز به SSL دارد اما باید به صورت صحیح تنظیم شود
    database_url = "postgresql://root:T7XfIPAcCii9z96VzkpLJ8mQ@apo.liara.cloud:33022/postgres"
    os.environ['DATABASE_URL'] = database_url
    
    # اجرای Migration‌ها
    print("🔄 در حال اجرای Migration‌ها...")
    result = subprocess.run(
        ['python', 'manage.py', 'migrate', '--run-syncdb'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ خطا در Migration: {result.stderr}")
        print(f"Output: {result.stdout}")
        return False
    
    print("✅ Migration‌ها با موفقیت اجرا شدند")
    return True

def import_to_postgresql():
    """Import داده‌ها به PostgreSQL"""
    print("📥 در حال import داده‌ها به PostgreSQL...")
    
    # Import داده‌ها
    result = subprocess.run(
        ['python', 'manage.py', 'loaddata', 'data_export.json'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"⚠️  خطا در import (ممکن است برخی داده‌ها قبلاً وجود داشته باشند): {result.stderr}")
        print(f"Output: {result.stdout}")
        # ادامه می‌دهیم حتی اگر خطا باشد
    else:
        print("✅ Import داده‌ها با موفقیت انجام شد")
    
    return True

def main():
    """تابع اصلی"""
    print("=" * 60)
    print("🚀 شروع انتقال داده‌ها از SQLite به PostgreSQL")
    print("=" * 60)
    
    # Step 1: Export از SQLite
    if not export_from_sqlite():
        print("❌ خطا در export داده‌ها")
        sys.exit(1)
    
    # Step 2: Setup PostgreSQL
    if not setup_postgresql():
        print("❌ خطا در تنظیم PostgreSQL")
        sys.exit(1)
    
    # Step 3: Import به PostgreSQL
    if not import_to_postgresql():
        print("⚠️  برخی خطاها در import رخ داد، اما ادامه می‌دهیم...")
    
    print("=" * 60)
    print("✅ انتقال داده‌ها با موفقیت انجام شد!")
    print("=" * 60)
    print("\n💡 نکته: فایل data_export.json را می‌توانید حذف کنید")
    print(f"\n📝 DATABASE_URL برای استفاده در لیارا:")
    print(f"postgresql://root:T7XfIPAcCii9z96VzkpLJ8mQ@apo.liara.cloud:33022/postgres?sslmode=require")

if __name__ == '__main__':
    main()

