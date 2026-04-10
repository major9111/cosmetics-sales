# Cosmetica - Multi-Branch Cosmetics Store Manager
### Django · PostgreSQL (Supabase) · AI Receipt Scanner · Vercel Hosting

---

## LOCAL DEVELOPMENT

### 1. Setup
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit .env with your values
```

### 2. Migrate + run
```bash
python manage.py makemigrations accounts branches products stock sales ai_scanner
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000

---

## DEPLOY: SUPABASE + VERCEL

### PART A — Supabase (Database)

1. Go to https://supabase.com → New Project
2. Name: cosmetica, choose a strong DB password, pick closest region
3. Once created → Settings → Database → Connection string → URI tab
4. Select "Transaction pooler" (port 6543) — REQUIRED for Vercel
5. Copy the URI:
   postgresql://postgres.XXXX:[PASSWORD]@aws-0-REGION.pooler.supabase.com:6543/postgres

### PART B — GitHub

```bash
git init && git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/cosmetica.git
git push -u origin main
```

### PART C — Vercel

1. Go to https://vercel.com → Add New Project → import your GitHub repo
2. Add these Environment Variables BEFORE deploying:

   SECRET_KEY     = (generate at djecrety.ir)
   DATABASE_URL   = (your Supabase URI from Part A)
   DEBUG          = False
   OPENAI_API_KEY = (from platform.openai.com/api-keys)

3. Click Deploy → wait ~2 minutes

4. Run migrations with Supabase DATABASE_URL set in your local .env:
   python manage.py migrate
   python manage.py createsuperuser

5. Open your live URL e.g. cosmetica.vercel.app

---

## USER ROLES

| Role           | Access                                      |
|----------------|---------------------------------------------|
| super_admin    | Everything - all branches, reports, users   |
| branch_manager | Own branch stock, sales, transfers          |
| cashier        | POS / sales only for their branch           |

---

## AI RECEIPT SCANNER

1. Sidebar → Receipt Scanner
2. Select the branch to restock
3. Camera photo OR file upload of supplier receipt
4. AI reads all products from the receipt
5. Approve / Reject / Edit each item one by one
6. Commit → stock updated automatically

---

## ENVIRONMENT VARIABLES

| Variable        | Required   | Description                          |
|-----------------|------------|--------------------------------------|
| SECRET_KEY      | Yes        | Django secret key                    |
| DATABASE_URL    | Yes (prod) | Supabase PostgreSQL URI              |
| DEBUG           | Yes        | True (local) / False (production)    |
| OPENAI_API_KEY  | AI scanner | OpenAI key for receipt scanning      |
| CUSTOM_DOMAIN   | Optional   | Your domain e.g. cosmetica.com       |

---

## NOTE ON MEDIA FILES

Vercel is stateless - uploaded images (product photos, receipt scans)
won't persist between deployments. For production, integrate Supabase
Storage or Cloudinary for file uploads.
