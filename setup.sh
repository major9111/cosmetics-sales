#!/bin/bash
# Quick local setup script
set -e

echo "==> Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Copying .env.example to .env..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    ✓ .env created — please fill in your DATABASE_URL and SECRET_KEY"
else
  echo "    .env already exists, skipping"
fi

echo ""
echo "Next steps:"
echo "  1. Edit .env with your Supabase DATABASE_URL and a SECRET_KEY"
echo "  2. Run: source venv/bin/activate"
echo "  3. Run: python manage.py makemigrations accounts branches products stock sales ai_scanner"
echo "  4. Run: python manage.py migrate"
echo "  5. Run: python manage.py createsuperuser"
echo "  6. Run: python manage.py runserver"
echo ""
echo "Done! See DEPLOY.md for Vercel + Supabase deployment guide."
