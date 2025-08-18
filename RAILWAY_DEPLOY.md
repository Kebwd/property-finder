# 🚀 Railway Deployment Guide

## Quick Deploy to Railway

### Prerequisites
- GitHub account
- Railway account (free tier available)
- Google Maps API key (for geocoding)

### Step 1: Prepare Repository

Since git is not installed locally, you can use GitHub's web interface:

1. **Create a new repository on GitHub**
   - Go to [github.com](https://github.com) and create a new repo
   - Name it something like `property-finder`

2. **Upload your code**
   - Use GitHub's "upload files" feature
   - Upload all files from your `property-finder` folder
   - Or use GitHub Desktop if you prefer a GUI

### Step 2: Deploy to Railway

1. **Go to [railway.app](https://railway.app)**
2. **Sign up/Login** with your GitHub account
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your property-finder repository**

### Step 3: Configure Services

Railway will automatically detect the Dockerfile and start building. You need to add a database:

1. **Add PostgreSQL**:
   - Click "New" → "Database" → "PostgreSQL"
   - Railway will auto-generate `DATABASE_URL`

2. **Add Redis** (optional but recommended):
   - Click "New" → "Database" → "Redis"
   - Railway will auto-generate `REDIS_URL`

### Step 4: Set Environment Variables

In your Railway project dashboard, add these environment variables:

```env
NODE_ENV=production
SCRAPER_API_KEY=your-secure-scraper-key-here
SCRAPER_PATH=../scraper
GEOCODING_API_KEY=your-google-maps-api-key
```

### Step 5: Configure GitHub Secrets (for scheduled scraping)

In your GitHub repository settings → Secrets and variables → Actions:

```env
SCRAPER_API_KEY=your-secure-scraper-key-here
API_BASE_URL=https://your-app-name.railway.app
```

## 🔧 Post-Deployment Setup

### 1. Test Your Deployment

Once deployed, test these endpoints:

```bash
# Health check
https://your-app.railway.app/health

# API status
https://your-app.railway.app/api/scraper/status
```

### 2. Initialize Database

Your database will be empty initially. You can:

1. **Use the CSV upload feature** in your app to import data
2. **Run scrapers manually** to populate with fresh data
3. **Import existing data** if you have any

### 3. Test Scheduled Scraping

1. Go to your GitHub repository
2. Click "Actions" tab
3. Find "Daily Property Scraping" workflow
4. Click "Run workflow" to test manually

## 📱 Access Your App

- **API**: `https://your-app-name.railway.app`
- **Frontend**: You may need to deploy the UI separately or serve it from the API

## 🛠️ Alternative: Simple Railway CLI Deploy

If you can install Railway CLI:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

## 📊 Monitoring

- **Railway Dashboard**: Monitor CPU, memory, and logs
- **GitHub Actions**: Monitor scraping workflow
- **Health Endpoint**: `/health` shows system status

## 🔍 Troubleshooting

### Common Issues:

1. **Build Fails**:
   - Check Dockerfile syntax
   - Verify all dependencies are listed

2. **Database Connection**:
   - Ensure `DATABASE_URL` is set by Railway
   - Check PostgreSQL service is running

3. **Scraping Fails**:
   - Verify Python dependencies in scraper/requirements.txt
   - Check `SCRAPER_PATH` environment variable

4. **API Key Issues**:
   - Make sure GitHub secrets match Railway environment variables
   - Check API key authentication in logs

### Getting Help:

- **Railway Logs**: Check deployment and runtime logs
- **GitHub Actions Logs**: Check scraping workflow logs
- **API Logs**: Use `/api/scraper/logs` endpoint

## 🎉 Success!

Once deployed, your property finder will:
- ✅ Serve the API on Railway
- ✅ Run scheduled scraping daily at 2 AM UTC
- ✅ Store data in PostgreSQL
- ✅ Provide health monitoring
- ✅ Handle CSV imports and exports

Your app is now live and will automatically collect property data daily! 🏠📊
