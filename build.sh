#!/bin/bash
set -e

echo "> Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo "> Installing dependencies..."
pip install -r requirements.txt

echo "> Collecting static files..."
python manage.py collectstatic --noinput

echo "> Running migrations..."
python manage.py migrate --noinput

echo "> Build completed successfully!"

