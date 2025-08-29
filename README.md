# 🏠 Property Finder — Handoff README

Short guide so a co-worker can pick up the project and run it locally or in CI.

This repo contains:
- a serverless API (`api/`) for search and health checks (Vercel-style)
- a React frontend (`property-finder-ui/` / `src/`)
- a Python Scrapy-based scraper (`scraper/`) with daily automation via GitHub Actions

## Quick checklist for handoff
- [ ] Create a Supabase project and run migrations (if using Postgres)
- [ ] Add required GitHub Actions repository secrets (see list below)
- [ ] Download GeoJSON district files into `scraper/config/ALS_GeoJSON_313`
- [ ] Run the scraper locally and verify `daily_output/` is created

## Required environment variables / repository secrets

Set these as GitHub repository secrets (Settings → Secrets and variables → Actions) and locally (PowerShell examples below).

- `DATABASE_URL` — Postgres connection string for DB writes (example: `postgresql://user:pass@host:5432/dbname`). Required by scraper when DB integration is enabled.
- `SUPABASE_URL` — Your Supabase project URL (if using Supabase).
- `SUPABASE_SERVICE_ROLE_KEY` — Supabase service role key (if using Supabase).
- `SCRAPER_API_KEY` — Secret key used to authenticate remote scraper triggers.
- `API_BASE_URL` — If you run a remote scraping API, set this to its base URL (workflow will call `${API_BASE_URL}/api/scraper/start`). If missing the workflow will run the scraper locally.
- `GEOCODING_API_KEY` — API key used by the search API when geocoding addresses (if required).
- `GITHUB_TOKEN` — (Optional) token for triggering GitHub Actions from `api/cron/daily-scraper.js`.

Notes:
- Secrets must be added at repository level (not just environment level) for scheduled workflows.
- Exact secret names are important; the workflows expect the names above.

## Where keys are referenced
Quick map so you know which files read which environment variables (edit these files only if you intend to change variable names or defaults).

- DATABASE_URL
  - `scraper/daily_scraper.py`, `scraper/scrapy_database_integration.py`, `scraper/scraper/pipelines/house_pipeline.py`, `scraper/scraper/pipelines/store_pipeline.py`
  - `api/search.js`, `api/export.js`, `api/types.js`, `pages/api/diagnose.js`, `property-finder-api/src/db.js`
  - various scraper utilities and checks: `scraper/check_db.py`, `scraper/test_db_connection.py`, `scraper/.env.template`

- SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY
  - `api/health.js`
  - deployment docs: `VERCEL_MIGRATION.md`
  - setup helpers: `scraper/setup_supabase.ps1`

- SCRAPER_API_KEY
  - cron trigger and API routes: `api/cron/daily-scraper.js`, `property-finder-api/src/routes/scraper.js`
  - CI workflow: `.github/workflows/daily-scraping.yml`

- API_BASE_URL
  - CI workflow: `.github/workflows/daily-scraping.yml`
  - tests: `test_scraper_api.py`

- GEOCODING_API_KEY / VITE_GEOCODING_API_KEY
  - backend: `api/search.js`, `property-finder-api/src/server.js`
  - frontend: `property-finder-ui/src/utils/geocode.js`, `property-finder-ui/src/config/api.js`

- VITE_API_URL
  - frontend production config: `property-finder-ui/.env.production`
  - frontend code: `property-finder-ui/src/config/api.js`, components that call the API

- GITHUB_TOKEN / GITHUB_REPO
  - used by the cron trigger: `api/cron/daily-scraper.js` (if you enable GitHub Actions dispatch from the API)

Notes:
- Search the repo for `process.env.<KEY>` or `${{ secrets.<KEY> }}` to find other occurrences before renaming keys.
- There are a few code fallbacks (for example `scraper-secret-key` in `property-finder-api/src/routes/scraper.js`) — remove or replace those defaults if you want to enforce secret usage.

## Local setup (Windows PowerShell)

1. Clone the repo and install Node dependencies (frontend & backend):

```powershell
git clone <repo-url>
cd property-finder
npm install
```

2. API / Frontend (Node)

- Frontend dev (inside `property-finder-ui/`):

```powershell
cd property-finder-ui
npm install
npm run dev
```

- Serverless API functions are under `api/` and are intended for Vercel. You can run local dev with Vercel CLI or test them with node.

3. Scraper (Python)

- Create virtualenv and install requirements:

```powershell
cd scraper
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

- GeoJSON district files: place them under `scraper/config/ALS_GeoJSON_313/` (the repo includes a `download_geojson.ps1` helper):

```powershell
powershell -ExecutionPolicy Bypass -File download_geojson.ps1
```

- Run the daily scraper locally (with DB enabled):

```powershell
# Powershell example
$env:DATABASE_URL = 'postgresql://user:pass@host:5432/db'
$env:SUPABASE_URL = 'https://your.supabase.co'
$env:SUPABASE_SERVICE_ROLE_KEY = 'service-role-key'
python .\daily_scraper.py --houses daily
```

- Run without DB (quick test):

```powershell
python .\daily_scraper.py --no-db --houses daily
```

Logs & outputs:
- Logs: `scraper/daily_scraper.log`
- Run artifacts: `scraper/daily_output/YYYY-MM-DD/` (JSON and log files)

If geopandas fails to install on Windows/CI, check `scraper/check_dependencies.py` for required system packages and consider using the manylinux wheels or a linux runner.

## GitHub Actions & CI notes

- Two workflows are relevant: `.github/workflows/daily-scraping.yml` (triggers remote scraping API or falls back to local-run) and `.github/workflows/daily-scraper.yml` (runs scraper directly in runner when configured).
- Behavior:
  - If both `API_BASE_URL` and `SCRAPER_API_KEY` are set, the CI will trigger the remote scraper API and exit.
  - If either is missing, the workflow falls back to install dependencies and run the scraper in the runner.
  - When running locally in CI, the job will export `DATABASE_URL`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY` into the shell environment so the Python process can access them.

Troubleshooting CI:
- If logs show `DATABASE_URL environment variable not set`, confirm the secret exists in the repository (not only in an environment) and is named exactly `DATABASE_URL`.
- If GeoPandas/pyogrio fail in CI, install system packages or run the scraper on a Linux runner with the proper binary wheels.

## Key files and where to look
- `api/` — serverless endpoints (search, health, cron triggers)
- `property-finder-ui/` — frontend app (Vite / React)
- `scraper/` — Scrapy spiders, pipelines, and orchestration (`daily_scraper.py`)
- `scraper/scraper/pipelines/store_pipeline.py` — GeoJSON loading and district assignment
- `.github/workflows/` — CI workflows for scraping

## Handover tips
- Add the repository secrets listed above before running scheduled workflows.
- Confirm the GeoJSON files exist at `scraper/config/ALS_GeoJSON_313/` (CI does not fetch them automatically unless you keep them in repo or add download steps).
- Use the masked presence checks in the workflows (they print `yes` when secrets are configured) to quickly verify secrets during CI runs.

If you want, I can also add a one-line PowerShell script `quick_start.ps1` that sets example env vars and runs the scraper for handoff convenience.

---

Built with ❤️ — contact the previous maintainer for credentials and deployment keys.

# 🏠 Property Finder - Cloud Native

A modern property finder application with automated daily scraping, built for Vercel + Supabase deployment.

## 🌟 Features

- **🔍 Property Search**: Search houses and businesses with advanced filters
- **📊 Data Visualization**: Interactive maps and charts
- **🕷️ Automated Scraping**: Daily property data collection via GitHub Actions  
- **📁 CSV Import/Export**: Bulk data management
- **🌐 RESTful API**: Serverless API functions
- **📱 Modern UI**: Responsive React frontend
- **☁️ Cloud-Native**: Full serverless deployment with Vercel + Supabase

## 🚀 Quick Deploy to Vercel + Supabase

### 1. Setup Supabase Database
- Go to [supabase.com](https://supabase.com) and create a new project
- Go to SQL Editor and run the migration scripts from `property-finder-api/migrations/`
- Get your Project URL and Service Role Key from Settings → API

### 2. Deploy to Vercel
- Fork this repository to your GitHub
- Go to [vercel.com](https://vercel.com) and import your fork
- Set environment variables:
  - `SUPABASE_URL`: Your Supabase project URL
  - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key

### 3. Configure GitHub Actions (Optional)

For automated scraping, set repository secrets:
- `VERCEL_DEPLOY_URL`: Your deployed Vercel app URL
- `SCRAPER_API_KEY`: Generate a secure API key for scraper authentication

## 🛠️ Environment Variables

### Required for Vercel Deployment:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### For Local Development:
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/property_finder
API_BASE_URL=http://localhost:5000
VITE_API_URL=http://localhost:5000
GEOCODING_API_KEY=your-google-maps-api-key
```

## 📁 Project Structure

```
property-finder/
├── api/                    # Vercel serverless functions
│   ├── health.js          # Health check endpoint
│   ├── debug.js           # Debug information
│   └── search.js          # Property search API
├── src/                   # React frontend
│   ├── App.jsx           # Main application component
│   ├── components/       # Reusable UI components
│   └── utils/           # Utility functions
├── property-finder-api/   # Original API (for reference)
├── scraper/              # Python scraping system
├── vercel.json           # Vercel deployment config
└── package.json          # Node.js dependencies
```

## 🔧 API Endpoints

- **GET** `/api/health` - Health check and database status
- **GET** `/api/debug` - Debug information and table counts
- **GET** `/api/search` - Property search with filters
  - Query parameters: `address`, `type`, `page`, `limit`, `category`, `filter_date`

## 🕷️ Automated Scraping

- **Schedule**: Daily at 2 AM UTC via GitHub Actions
- **Trigger**: Automated workflow or manual dispatch
- **Security**: API key authentication
- **Target**: Vercel deployment endpoint

## 📥 Download GeoJSON District Files

GeoJSON district files are not included in the repository. Download them before running the scraper:

1. Download with PowerShell:
   ```powershell
   powershell -ExecutionPolicy Bypass -File download_geojson.ps1
   ```
2. If you need to update the download links, edit `download_geojson.ps1` and replace the file IDs with your own from Google Drive.

Google Drive folder: https://drive.google.com/drive/folders/1ydSU3zDW35uPTvP1UbhAE0QxDsTtIMv0?usp=drive_link

## 🧪 Testing the Deployment

```bash
# Test health endpoint
curl https://your-app.vercel.app/api/health

# Test search endpoint
curl "https://your-app.vercel.app/api/search?address=香港&type=all&page=1"

# Test debug information
curl https://your-app.vercel.app/api/debug
```

## 📚 Documentation

- `RAILWAY_DEPLOY.md` - Detailed deployment guide
- `DEPLOY_STEPS.md` - Step-by-step instructions  
- `SCRAPING_SETUP.md` - Scraping configuration
- `scraper/DAILY_SETUP_GUIDE.md` - Scraper details

## 🔒 Security

- Environment variables for secrets
- API key authentication for scraping
- Rate limiting on endpoints
- CORS configuration

## 🌐 Live App

Once deployed, your app will be available at:
`https://your-app-name.railway.app`

## 🎯 Next Steps

1. **Deploy**: Follow the deployment guide
2. **Configure**: Set environment variables
3. **Test**: Run verification script
4. **Monitor**: Check daily scraping automation
5. **Use**: Start adding/searching properties!

---

Built with ❤️ using Node.js, React, Python, and Railway
