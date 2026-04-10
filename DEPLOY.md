# 🚀 Cosmetica — Deployment Guide
### Vercel (hosting) + Supabase (PostgreSQL database)

---

## 📋 Prerequisites

- GitHub account
- Vercel account (free) → vercel.com
- Supabase account (free) → supabase.com
- Python 3.11+ installed locally

---

## STEP 1 — Supabase Database Setup

### 1.1 Create a Supabase project
1. Go to **supabase.com** → New Project
2. Choose a name: `cosmetica`
3. Set a strong database password (save it!)
4. Select region closest to Nigeria: **EU West** or **US East**
5. Wait ~2 minutes for project to be ready

### 1.2 Get your connection string
1. In Supabase → **Settings** → **Database**
2. Scroll to **Connection String**
3. Select **URI** tab
4. Copy the string — it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.abcxyz.supabase.co:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with your actual password

---

## STEP 2 — Local Setup & Migrations

```bash
# 1. Unzip the project
unzip cosmetica_final.zip
cd cosmetica

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env
# Now edit .env and fill in DATABASE_URL, SECRET_KEY, OPENAI_API_KEY

# 5. Generate a secret key
python -c "from django.core.utils.crypto import get_random_string; print(get_random_string(50))"
# Paste the output into SECRET_KEY in your .env

# 6. Run migrations (this creates all tables in Supabase)
python manage.py makemigrations accounts branches products stock sales ai_scanner
python manage.py migrate

# 7. Create your admin/superuser account
python manage.py createsuperuser

# 8. Test locally
python manage.py runserver
# Visit http://127.0.0.1:8000
```

---

## STEP 3 — Push to GitHub

```bash
# In the cosmetica/ folder:
git init
git add .
git commit -m "Initial Cosmetica deploy"

# Create a new repo on github.com (name it cosmetica)
# Then:
git remote add origin https://github.com/YOUR-USERNAME/cosmetica.git
git branch -M main
git push -u origin main
```

---

## STEP 4 — Deploy to Vercel

### 4.1 Import project
1. Go to **vercel.com** → Add New Project
2. Click **Import Git Repository**
3. Select your `cosmetica` GitHub repo
4. Vercel auto-detects the `vercel.json` config

### 4.2 Set Environment Variables
In Vercel project → **Settings** → **Environment Variables**, add:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Your generated secret key |
| `DATABASE_URL` | Your Supabase connection string |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `DEBUG` | `False` |
| `DJANGO_SETTINGS_MODULE` | `cosmetica.settings` |
| `CUSTOM_DOMAIN` | Your domain (optional) |

### 4.3 Deploy
1. Click **Deploy**
2. Vercel runs `build_files.sh` → installs deps → collects static files
3. Your app goes live at `https://cosmetica-xxx.vercel.app`

---

## STEP 5 — Post-Deploy Setup

After first deploy, you need to run migrations on the live database.
Do this from your local machine (connected to Supabase via .env):

```bash
# Already done in Step 2 — migrations already ran against Supabase!
# Just create the superuser if you haven't:
python manage.py createsuperuser
```

Then visit your Vercel URL and log in.

---

## ⚠️ Important Notes

### Media Files (Product Images)
Vercel is **stateless** — uploaded images will disappear on redeploy.
For production, use **Supabase Storage**:
1. Supabase → Storage → Create bucket `cosmetica-media`
2. Make it public
3. Install `django-storages[supabase]` and configure `DEFAULT_FILE_STORAGE`

For now, images won't break the app — they just won't persist.

### Free Tier Limits
| Service | Free Limit |
|---------|------------|
| Vercel | 100GB bandwidth/month |
| Supabase | 500MB database, 1GB storage |
| OpenAI | Pay per use (receipt scanning) |

### Custom Domain
1. Vercel → Project → Settings → Domains → Add your domain
2. Follow DNS instructions
3. Add your domain to `CUSTOM_DOMAIN` env variable

---

## 🔧 Useful Commands

```bash
# View logs
vercel logs your-project.vercel.app

# Redeploy
git add . && git commit -m "Update" && git push

# Connect to Supabase DB directly
# Supabase → SQL Editor → run queries

# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 🆘 Troubleshooting

**"Application Error" on Vercel**
→ Check Vercel Function Logs for the actual Python error

**"Database connection refused"**
→ Check DATABASE_URL is correct and password has no special characters that need URL-encoding

**Static files not loading (CSS broken)**
→ Make sure `DEBUG=False` and run `python manage.py collectstatic` locally first

**CSRF verification failed**
→ Add your Vercel domain to `ALLOWED_HOSTS` in settings.py and redeploy

**Migrations error**
→ Run `python manage.py migrate --run-syncdb` once if tables are missing
