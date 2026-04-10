#!/bin/bash
set -e

echo "==> Installing Python dependencies..."
pip install -r requirements.txt --break-system-packages

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "==> Build complete!"
