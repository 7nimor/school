#!/bin/bash
# اسکریپت راه‌اندازی پروژه

echo "در حال نصب وابستگی‌ها..."
pip install -r requirements.txt

echo "ایجاد فایل .env..."
if [ ! -f .env ]; then
    cat > .env << EOF
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=True
SMS_API_KEY=
SMS_API_URL=
SMS_SENDER_NUMBER=
EOF
    echo "فایل .env ایجاد شد."
else
    echo "فایل .env از قبل وجود دارد."
fi

echo "اجرای migrations..."
python manage.py makemigrations
python manage.py migrate

echo "✅ راه‌اندازی کامل شد!"
echo ""
echo "برای ایجاد کاربر ادمین، این دستور را اجرا کنید:"
echo "python manage.py createsuperuser"
echo ""
echo "برای اجرای سرور:"
echo "python manage.py runserver"

