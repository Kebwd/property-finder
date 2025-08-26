# Quick Deployment Guide

This guide provides step-by-step instructions for your co-worker to deploy the complete Property Finder system.

## 🎯 Deployment Overview

1. **Frontend**: Deployed to Vercel (React app)
2. **API**: Deployed to Railway (Node.js backend)  
3. **Database**: Supabase (PostgreSQL)
4. **Scraper**: Self-hosted or cloud VPS

## 📋 Pre-deployment Checklist

### Required Accounts
- [ ] GitHub account with repository access
- [ ] Vercel account (free tier available)
- [ ] Railway account (free tier available)
- [ ] Supabase account (free tier available)
- [ ] ScraperAPI account (for web scraping)

### Required Information
- [ ] Database connection string
- [ ] ScraperAPI key
- [ ] Geocoding API key (optional)

## 🚀 Step-by-Step Deployment

### Step 1: Database Setup (Supabase)

1. **Create Supabase Project**
   ```
   1. Go to https://supabase.com
   2. Click "New Project"
   3. Choose organization and project name
   4. Select region closest to users
   5. Set database password
   ```

2. **Run Database Migrations**
   ```sql
   -- Go to SQL Editor in Supabase
   -- Run each migration file in order:
   -- 1. V1__create_stores.sql
   -- 2. V2__add_category_filter.sql  
   -- 3. V3__add_deal_price.sql
   ```

3. **Get Connection Details**
   ```
   Project Settings → API → Connection parameters
   - Host: db.xxx.supabase.co
   - Database: postgres
   - Username: postgres
   - Password: [your password]
   - Port: 5432
   ```

### Step 2: Backend API Deployment (Railway)

1. **Connect GitHub Repository**
   ```
   1. Go to https://railway.app
   2. Click "Deploy from GitHub repo"
   3. Select property-finder repository
   4. Choose property-finder-api folder as root
   ```

2. **Configure Environment Variables**
   ```env
   DATABASE_URL=postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
   PORT=3000
   NODE_ENV=production
   ```

3. **Deploy**
   ```
   Railway will automatically:
   - Install dependencies (npm install)
   - Start the server (npm start)
   - Provide a public URL
   ```

### Step 3: Frontend Deployment (Vercel)

1. **Connect GitHub Repository**
   ```
   1. Go to https://vercel.com
   2. Click "New Project"  
   3. Import property-finder repository
   4. Set Root Directory to "property-finder-ui"
   ```

2. **Configure Build Settings**
   ```
   Framework Preset: Vite
   Build Command: npm run build
   Output Directory: dist
   Install Command: npm install
   ```

3. **Set Environment Variables**
   ```env
   VITE_API_BASE_URL=https://your-railway-app.railway.app
   ```

4. **Deploy**
   ```
   Vercel will automatically:
   - Install dependencies
   - Build the React app
   - Deploy to CDN
   - Provide a public URL
   ```

### Step 4: Scraper Setup (Cloud VPS)

1. **Set Up Cloud Server**
   ```bash
   # Choose a cloud provider (DigitalOcean, AWS, etc.)
   # Create Ubuntu 20.04+ instance
   # SSH into the server
   
   # Install Python and dependencies
   sudo apt update
   sudo apt install python3-pip git
   ```

2. **Deploy Scraper Code**
   ```bash
   # Clone repository
   git clone https://github.com/Kebwd/property-finder.git
   cd property-finder/scraper
   
   # Install Python dependencies
   pip3 install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   # Create environment file
   cat > .env << EOF
   DATABASE_URL=postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
   SCRAPERAPI_KEY=your_scraperapi_key
   EOF
   ```

4. **Test Scrapers**
   ```bash
   # Test Hong Kong scraper
   python3 -m scrapy crawl house -s LOG_LEVEL=INFO
   
   # Test business scraper  
   python3 -m scrapy crawl store -s LOG_LEVEL=INFO
   
   # Test China scraper (expect CAPTCHA)
   python3 -m scrapy crawl lianjia_simple -a city=guangzhou
   ```

5. **Set Up Automated Scraping**
   ```bash
   # Add cron job for daily scraping
   crontab -e
   
   # Add this line (runs daily at 2 AM):
   0 2 * * * cd /path/to/property-finder/scraper && python3 daily_scraper.py
   ```

## ✅ Verification Steps

### 1. Test Frontend
```
Visit your Vercel URL
- Check property search works
- Verify data loads correctly
- Test data export functionality
```

### 2. Test API
```
Visit https://your-railway-app.railway.app/api/health
- Should return: {"status": "ok", "timestamp": "..."}

Test search: /api/search?query=central&type=house
- Should return: {"success": true, "data": [...]}
```

### 3. Test Database Connection
```sql
-- In Supabase SQL Editor
SELECT COUNT(*) FROM houses;
SELECT COUNT(*) FROM business;
-- Should return current data counts
```

### 4. Test Scraper Integration
```bash
# Run a test scrape
python3 -m scrapy crawl house -s LOG_LEVEL=INFO

# Check data appeared in database
# Should see new entries in Supabase
```

## 🔧 Troubleshooting

### Common Issues

**Frontend not loading data**
- Check VITE_API_BASE_URL is correct
- Verify API is responding at /api/health
- Check browser developer console for errors

**API connection errors**
- Verify DATABASE_URL format
- Check Supabase connection limits
- Ensure Railway service is running

**Scraper CAPTCHA issues**
- Expected for Lianjia - use manual solving
- For other sites, check proxy settings
- Review ScraperAPI quota and limits

**Database connection timeouts**
- Check Supabase project is active
- Verify connection string format
- Consider connection pooling settings

## 📞 Support Resources

### Documentation
- Vercel: https://vercel.com/docs
- Railway: https://docs.railway.app
- Supabase: https://supabase.com/docs
- Scrapy: https://docs.scrapy.org

### Monitoring
- **Frontend**: Vercel Dashboard → Analytics
- **API**: Railway Dashboard → Deployments
- **Database**: Supabase Dashboard → Database
- **Scraper**: Server logs and cron job output

## 🎉 Post-Deployment

### Immediate Tasks
1. [ ] Verify all services are running
2. [ ] Test complete user workflow
3. [ ] Set up monitoring alerts
4. [ ] Document any custom configurations

### Ongoing Maintenance
1. **Weekly**: Check scraper success rates
2. **Monthly**: Review service usage and costs
3. **Quarterly**: Update dependencies and security patches

---

**Deployment Status**: Ready for production handover
**Estimated Setup Time**: 2-3 hours
**Skill Level Required**: Intermediate (with documentation support)
