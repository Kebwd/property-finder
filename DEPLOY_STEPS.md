# 🚀 Railway Deployment - Step by Step

Since you don't have git installed locally, here's how to deploy using GitHub's web interface:

## Method 1: GitHub Web Upload (Recommended)

### Step 1: Create GitHub Repository
1. Go to https://github.com
2. Click "New repository"
3. Name it "property-finder"
4. Make it public or private
5. Don't initialize with README (we have files already)

### Step 2: Upload Files
1. Click "uploading an existing file"
2. Drag and drop ALL files from your `c:\Users\User\property-finder` folder
3. Or use "choose your files" to select all
4. Add commit message: "Initial commit - Property finder with scheduled scraping"
5. Click "Commit changes"

### Step 3: Deploy to Railway
1. Go to https://railway.app
2. Sign up/login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your "property-finder" repository
6. Click "Deploy"

### Step 4: Add Database
1. In Railway dashboard, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway auto-creates DATABASE_URL

### Step 5: Set Environment Variables
In Railway project settings, add:
```
NODE_ENV=production
SCRAPER_API_KEY=<YOUR_SCRAPER_API_KEY>
SCRAPER_PATH=../scraper
GEOCODING_API_KEY=your-google-maps-api-key
```

### Step 6: Configure GitHub Secrets
In GitHub repo → Settings → Secrets and variables → Actions:
```
SCRAPER_API_KEY=<YOUR_SCRAPER_API_KEY>
API_BASE_URL=https://your-app-name.railway.app
```

## Method 2: GitHub Desktop (Alternative)

1. Download GitHub Desktop
2. Clone the repository
3. Copy your files
4. Commit and push
5. Deploy to Railway

## Method 3: Railway CLI (If you want to install tools)

```powershell
# Install Railway CLI
npm install -g @railway/cli

# Install Git (optional)
winget install Git.Git

# Deploy
railway login
railway init
railway up
```

## ✅ Verification

After deployment, check:
- https://your-app.railway.app/health
- https://your-app.railway.app/api/scraper/status

## 🎯 Next Steps

1. Test the API endpoints
2. Upload sample CSV data
3. Trigger manual scraping from GitHub Actions
4. Monitor daily automation

Your property finder will be live with automated daily scraping! 🎉
