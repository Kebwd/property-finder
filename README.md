# � Property Finder - Full Cloud Edition

A modern property finder application running 100% in the cloud with automated daily scraping. Built with Vercel + Supabase for zero localhost dependencies.

## ✨ Cloud-First Features

- **🌐 100% Cloud Native**: No localhost required - everything runs online
- **⚡ Serverless API**: Auto-scaling Vercel Functions
- **🗄️ Managed Database**: Supabase PostgreSQL with PostGIS
- **🔒 Enterprise Security**: Row Level Security + SSL/TLS
- **� Global CDN**: Lightning-fast worldwide access
- **📊 Real-time Analytics**: Built-in monitoring and insights
- **🤖 Automated Scraping**: GitHub Actions or cloud services
- **� Cost Effective**: Free tiers available

## 🚀 Quick Cloud Deploy (5 Minutes)

### 1. **Fork & Clone**
```bash
git clone https://github.com/yourusername/property-finder.git
cd property-finder
```

### 2. **Setup Supabase** (2 minutes)
- Go to [supabase.com](https://supabase.com) → Create project
- Copy SQL from `supabase/migrations/20240815000001_initial_setup.sql`
- Paste in Supabase SQL Editor → Run
- Note your project URL and keys

### 3. **Deploy to Vercel** (2 minutes)
- Go to [vercel.com](https://vercel.com) → New Project
- Import your GitHub repo
- Add environment variables from `.env.example`
- Deploy! 🚀

### 4. **Test Deployment** (1 minute)
```bash
python verify_cloud_deployment.py https://your-app.vercel.app
```

**🎉 Done! Your app is live at `https://your-app.vercel.app`**

## 📋 Environment Setup

All configuration is done via environment variables - no local setup needed!

**Vercel Environment Variables:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiI...
SUPABASE_DB_URL=postgresql://postgres:...
GEOCODING_API_KEY=AIzaSyC...
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiI...
VITE_API_URL=https://your-app.vercel.app/api
```

See `.env.example` for complete setup guide.

## 🕷️ Automated Scraping Options

Choose your preferred scraping deployment:

### Option 1: GitHub Actions (Recommended - FREE)
- ✅ Already configured in `.github/workflows/scraper.yml`
- ✅ Runs daily at 2 AM UTC automatically
- ✅ No additional cost
- ✅ Just add GitHub secrets

### Option 2: Cloud Function
- Deploy scraper to Google Cloud Run, AWS Lambda, etc.
- See `scraper/SUPABASE_SETUP.md`

## 📁 Project Structure

```
property-finder/
├── property-finder-api/     # Node.js API (Vercel Functions)
├── property-finder-ui/      # React frontend (Static build)
├── scraper/                 # Python web scraping (Optional external deployment)
├── supabase/               # Database migrations and config
├── .github/workflows/       # GitHub Actions automation
├── vercel.json             # Vercel deployment configuration
└── README.md               # This file
```

## 🔧 API Endpoints

- `GET /health` - System health check
- `GET /api/search` - Search properties
- `POST /api/house` - Add house record
- `POST /api/business` - Add business record
- `POST /api/scraper/start` - Trigger scraping
- `GET /api/scraper/status` - Check scraping status

## 🕷️ Automated Scraping Options

### Option 1: GitHub Actions (Recommended)
- **Schedule**: Daily at 2 AM UTC
- **Cost**: Free for public repos
- **Setup**: Already configured in `.github/workflows/scraper.yml`

### Option 2: External Service
- Deploy scraper to Railway, Google Cloud Run, or similar
- See `scraper/SUPABASE_SETUP.md` for instructions

## 🧪 Testing

After deployment, verify with:
```bash
python verify_deployment.py https://your-app.vercel.app your-api-key
```

## 📚 Documentation

- `VERCEL_DEPLOY.md` - Detailed deployment guide
- `DEPLOY_STEPS.md` - Step-by-step instructions  
- `SCRAPING_SETUP.md` - Scraping configuration
- `scraper/SUPABASE_SETUP.md` - Scraper deployment options

## 🔒 Security

- Environment variables for secrets
- Supabase Row Level Security
- API key authentication for scraping
- Rate limiting on endpoints
- CORS configuration
- SSL/TLS encryption

## 🌐 Live App

Once deployed, your app will be available at:
- Frontend: `https://your-app-name.vercel.app`
- API: `https://your-app-name.vercel.app/api`
- Database: Supabase Dashboard

## 🎯 Next Steps

1. **Deploy**: Follow the deployment guide in `VERCEL_DEPLOY.md`
2. **Configure**: Set environment variables in Vercel
3. **Database**: Run SQL migration in Supabase
4. **Test**: Run verification script
5. **Monitor**: Check daily scraping automation
6. **Use**: Start adding/searching properties!

---

Built with ❤️ using Node.js, React, Python, Vercel, and Supabase
