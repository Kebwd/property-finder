# 🏠 Property Finder - Production Ready

A modern property finder application with automated daily scraping, built for Railway deployment.

## 🌟 Features

- **🔍 Property Search**: Search houses and businesses with advanced filters
- **📊 Data Visualization**: Interactive maps and charts
- **🕷️ Automated Scraping**: Daily property data collection via GitHub Actions  
- **📁 CSV Import/Export**: Bulk data management
- **🌐 RESTful API**: Full-featured backend API
- **📱 Modern UI**: Responsive React frontend

## 🚀 Quick Deploy to Railway

### 1. Upload to GitHub
- Create new repository on GitHub
- Upload all files from this directory
- Commit with message: "Initial commit - Property finder app"

### 2. Deploy to Railway
- Go to [railway.app](https://railway.app)
- Connect GitHub account
- "New Project" → "Deploy from GitHub repo"
- Select your repository

### 3. Add Database
- In Railway: "New" → "Database" → "PostgreSQL"
- Railway auto-generates `DATABASE_URL`

### 4. Set Environment Variables
```env
NODE_ENV=production
SCRAPER_API_KEY=your-secure-key-here
SCRAPER_PATH=../scraper
GEOCODING_API_KEY=your-google-maps-api-key
```

### 5. Configure GitHub Secrets
For automated scraping:
```env
SCRAPER_API_KEY=your-secure-key-here
API_BASE_URL=https://your-app.railway.app
```

## 📁 Project Structure

```
property-finder/
├── property-finder-api/     # Node.js API server
├── property-finder-ui/      # React frontend
├── scraper/                 # Python web scraping
├── .github/workflows/       # GitHub Actions automation
├── Dockerfile              # Railway deployment
├── railway.toml            # Railway configuration
└── README.md               # This file
```

## 🔧 API Endpoints

- `GET /health` - System health check
- `GET /api/search` - Search properties
- `POST /api/house` - Add house record
- `POST /api/business` - Add business record
- `POST /api/scraper/start` - Trigger scraping
- `GET /api/scraper/status` - Check scraping status

## 🕷️ Automated Scraping

- **Schedule**: Daily at 2 AM UTC
- **Trigger**: GitHub Actions workflow
- **Security**: API key authentication
- **Monitoring**: Status and logs via API

## 🧪 Testing

After deployment, verify with:
```bash
python verify_deployment.py https://your-app.railway.app your-api-key
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
