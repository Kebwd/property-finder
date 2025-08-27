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
