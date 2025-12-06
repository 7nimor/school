# راهنمای انتقال داده‌ها به دیتابیس لیارا

## مشکل
دیتابیس لیارا از خارج از شبکه لیارا قابل دسترسی نیست (نیاز به whitelist IP یا استفاده از شبکه داخلی).

## راه حل‌ها

### روش 1: استفاده از Console لیارا (پیشنهادی)

1. **Export داده‌ها از SQLite محلی:**
```bash
# در سیستم محلی خود
unset DATABASE_URL
python manage.py dumpdata --natural-foreign --natural-primary \
    --exclude contenttypes --exclude auth.Permission --exclude sessions \
    --indent 2 --output data_export.json
```

2. **آپلود فایل `data_export.json` به لیارا:**
   - از طریق پنل لیارا یا Git

3. **در Console لیارا (Terminal در پنل):**
```bash
# تنظیم DATABASE_URL
export DATABASE_URL="postgresql://root:T7XfIPAcCii9z96VzkpLJ8mQ@apo.liara.cloud:33022/postgres"

# اجرای Migration
python manage.py migrate

# Import داده‌ها
python manage.py loaddata data_export.json
```

### روش 2: استفاده از SSH Tunnel (اگر دسترسی دارید)

اگر به سرور لیارا دسترسی SSH دارید، می‌توانید از tunnel استفاده کنید.

### روش 3: تنظیم DATABASE_URL در پنل لیارا

1. در پنل لیارا، به بخش Environment Variables بروید
2. متغیر زیر را اضافه کنید:
```
DATABASE_URL=postgresql://root:T7XfIPAcCii9z96VzkpLJ8mQ@apo.liara.cloud:33022/postgres
```

3. Deploy را اجرا کنید - Migration‌ها به صورت خودکار اجرا می‌شوند

4. سپس از Console لیارا برای import داده‌ها استفاده کنید:
```bash
python manage.py loaddata data_export.json
```

## فایل‌های آماده

- `data_export.json`: فایل export شده از SQLite (باید ایجاد شود)
- `migrate_data.sh`: اسکریپت انتقال (برای استفاده محلی)

## نکات مهم

1. **SECRET_KEY**: حتماً در Environment Variables لیارا تنظیم کنید
2. **DEBUG**: باید `False` باشد در production
3. **ALLOWED_HOSTS**: در settings.py تنظیم شده است

