# Property Finder - Hong Kong & China Real Estate Platform

A comprehensive real estate search platform with advanced web scraping capabilities for Hong Kong and China property markets. Features modern React frontend, robust Node.js API backend, and sophisticated scraping infrastructure.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.11+
- Git
- Database (Supabase/PostgreSQL)

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/Kebwd/property-finder.git
cd property-finder

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 2. Frontend Deployment (Vercel)

```bash
cd property-finder-ui
npm install
npm run build

# Deploy to Vercel
vercel --prod
```

### 3. API Deployment (Vercel)

```bash
cd property-finder-api
npm install

# Deploy to Vercel (API routes automatically detected)
vercel --prod
```

### 4. Scraper Setup

```bash
cd scraper
pip install -r requirements.txt

# Configure scraper credentials
cp secrets/example_config.txt secrets/geocode_api_key.txt
# Add your ScraperAPI key and database URL
```

## 📁 Project Structure

```
property-finder/
├── property-finder-ui/          # React frontend (Vercel deployment)
│   ├── src/
│   │   ├── App.jsx             # Main application component
│   │   ├── DataImportExport.jsx # Data management interface
│   │   └── StoreList.jsx        # Property listings display
│   ├── package.json
│   └── Dockerfile
├── property-finder-api/         # Node.js API backend (Vercel API routes)
│   ├── src/
│   │   ├── server.js           # Express server setup
│   │   ├── db.js               # Database configuration
│   │   └── routes/             # API endpoints
│   │       ├── search.js       # Property search API
│   │       ├── business.js     # Business listings API
│   │       └── health.js       # Health check endpoint
│   ├── migrations/             # Database schema
│   └── package.json
└── scraper/                     # Python scraping infrastructure
    ├── scraper/
    │   ├── spiders/
    │   │   ├── house_spider.py  # Hong Kong property scraper
    │   │   ├── store_spider.py  # Business listings scraper
    │   │   ├── lianjia_spider.py # China property scraper (advanced)
    │   │   └── lianjia_simple.py # China property scraper (production)
    │   ├── pipelines/           # Data processing pipelines
    │   └── middlewares/         # Anti-bot protection
    ├── config/                  # Scraper configurations
    ├── daily_scraper.py        # Automated daily runs
    └── requirements.txt
```

## 🗄️ Database Schema

### Core Tables

**houses** - Property listings
```sql
- id (primary key)
- name (property name)
- building_name_zh (Chinese building name)
- estate_name_zh (Chinese estate name)  
- deal_price (price in HKD/CNY)
- area (square meters)
- district, subdistrict (location)
- url (source URL)
- type (house/apartment)
```

**business** - Commercial listings
```sql
- id (primary key)
- name (business name)
- category (business type)
- district, area (location)
- deal_price (rental/sale price)
- url (source URL)
```

## 🌐 Deployment Architecture

### Frontend (Vercel)
- **Directory**: `property-finder-ui/`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Framework**: React + Vite
- **Domain**: Auto-assigned vercel.app domain

### Backend API (Vercel)
- **Directory**: `property-finder-api/`
- **Deployment**: Vercel API routes (serverless functions)
- **Build Command**: Automatic API detection
- **Framework**: Express.js + Serverless
- **Database**: Supabase PostgreSQL
- **Health Check**: `/api/health`

### Scraper Infrastructure (Self-hosted/Cloud)
- **Runtime**: Python 3.11+ with Scrapy
- **Deployment**: Docker containers or cloud VPS
- **Scheduling**: Cron jobs for daily scraping
- **Storage**: Direct database insertion

## 🕷️ Scraping Capabilities

### 1. Hong Kong Properties (`house_spider`)
- **Source**: Multiple Hong Kong real estate sites
- **Data**: Prices, areas, locations, property details
- **Frequency**: Daily updates
- **Status**: ✅ Production ready

### 2. Business Listings (`store_spider`) 
- **Source**: Hong Kong commercial property sites
- **Data**: Rental prices, business categories, locations
- **Frequency**: Weekly updates
- **Status**: ✅ Production ready

### 3. China Properties (`lianjia_simple`)
- **Source**: Lianjia (链家) - China's largest real estate platform
- **Data**: Property prices, areas, locations across major Chinese cities
- **Challenge**: Advanced anti-bot protection with CAPTCHA
- **Status**: ⚠️ Requires manual CAPTCHA solving

## 🔧 Running Scrapers

### Basic Hong Kong Scraping
```bash
cd scraper

# Scrape Hong Kong properties
python -m scrapy crawl house -s LOG_LEVEL=INFO

# Scrape business listings
python -m scrapy crawl store -s LOG_LEVEL=INFO
```

### China Property Scraping (Lianjia)
```bash
# Test connectivity (expect CAPTCHA)
python -m scrapy crawl lianjia_simple -a city=guangzhou -a max_pages=1

# Supported cities: beijing, shanghai, guangzhou, shenzhen, hangzhou, nanjing, etc.
```

### Daily Automated Scraping
```bash
# Set up cron job
python daily_scraper.py
```

## ⚠️ Lianjia CAPTCHA Challenge

### Current Status
Lianjia implements sophisticated anti-bot protection:
- CAPTCHA verification for all requests
- IP-based blocking
- Behavioral analysis
- Mobile API deprecation

### Solution Options

#### Option 1: Manual CAPTCHA Solving
1. Run spider to get CAPTCHA URL
2. Open browser and solve CAPTCHA manually
3. Extract session cookies
4. Re-run spider with valid session

#### Option 2: Residential Proxy Service
```bash
# Use rotating residential IPs
python -m scrapy crawl lianjia_simple -s PROXY_POOL='residential'
```

#### Option 3: CAPTCHA Solving Services
- Integrate 2captcha or Anti-Captcha services
- Automatic CAPTCHA solving (paid service)
- Requires API key configuration

### Recommended Approach
For production stability, use **manual CAPTCHA solving** during off-peak hours:
1. Run scraper 2-3 times per week
2. Solve CAPTCHAs manually when required
3. Use long delays (60+ seconds between requests)
4. Monitor success rates and adjust frequency

## 🔐 Environment Variables

### Frontend (Vercel)
```env
VITE_API_BASE_URL=https://your-vercel-app.vercel.app
```

### Backend API (Vercel)
```env
DATABASE_URL=postgresql://user:pass@host:port/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
NODE_ENV=production
```

### Scraper
```env
DATABASE_URL=postgresql://user:pass@host:port/db
SCRAPERAPI_KEY=your_scraperapi_key
GEOCODING_API_KEY=your_geocoding_key
```

## 🔑 How to Get API Keys

### Supabase
1. Go to [supabase.com](https://supabase.com) and log in.
2. Select your project.
3. Click on `Project Settings` > `API`.
4. Copy the `Project URL` and `anon` public API key (SUPABASE_ANON_KEY).
5. Use these in your `.env` and Vercel environment settings.

### Vercel
1. Go to [vercel.com](https://vercel.com) and log in.
2. Select your project.
3. Click on `Settings` > `Environment Variables`.
4. Add your API keys and secrets here (e.g., VITE_API_BASE_URL, SUPABASE_URL, SUPABASE_ANON_KEY).

### ScraperAPI
1. Go to [scraperapi.com](https://www.scraperapi.com/) and sign up for an account.
2. After logging in, go to the dashboard.
3. Copy your personal API key from the dashboard.
4. Add this key to your `.env` file as `SCRAPERAPI_KEY`.

### Geocoding API (e.g., Google Maps)
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Enable the `Geocoding API` from the API Library.
4. Go to `APIs & Services` > `Credentials`.
5. Click `Create Credentials` > `API key`.
6. Copy the API key and add it to your `.env` file as `GEOCODING_API_KEY`.

> **Note:** Never commit your API keys to public repositories. Use environment variables and Vercel/Supabase secret management for production deployments.

## 📊 API Endpoints

### Property Search
```
GET /api/search?query=keyword&type=house
```

### Business Search
```
GET /api/business/search?category=retail&district=central
```

### Data Export
```
GET /api/export/houses
GET /api/export/business
```

### Health Check
```
GET /api/health
```

## 🚨 Common Issues & Solutions

### 1. CAPTCHA Blocking (Lianjia)
**Problem**: All Lianjia requests return CAPTCHA page  
**Solution**: Use manual CAPTCHA solving or residential proxies

### 2. Database Connection Issues
**Problem**: Scraper can't connect to database  
**Solution**: Check DATABASE_URL and network connectivity

### 3. Property Name Display Issues
**Problem**: Chinese properties show empty names  
**Solution**: Fixed in current version - uses `building_name_zh` fallback

### 4. API Response Format
**Problem**: Frontend expects `{success: true, data: [...]}`  
**Solution**: All APIs now return standardized format

## 🔄 Maintenance Tasks

### Weekly
- Monitor scraper success rates
- Check for blocked IPs/CAPTCHAs
- Review data quality and completeness

### Monthly  
- Update scraper selectors if sites change
- Optimize database queries and indexes
- Review proxy service usage and costs

### As Needed
- Add new cities for China scraping
- Implement new data sources
- Update anti-bot countermeasures

## 📈 Performance Optimization

### Scraping
- Use ScraperAPI for IP rotation
- Implement intelligent delays
- Monitor success rates and adjust

### Database
- Add indexes on frequently searched fields
- Use connection pooling
- Regular vacuum and analyze

### Frontend
- Enable Vercel CDN caching
- Implement lazy loading for large datasets
- Use React Query for data caching

## 🛠️ Development Workflow

### Adding New Cities (China)
1. Add city domain to `CITY_DOMAINS` in spider
2. Test connectivity and CAPTCHA handling
3. Adjust selectors if needed for city-specific layouts

### Adding New Data Sources
1. Create new spider in `scraper/spiders/`
2. Implement data extraction logic
3. Configure pipeline for data processing
4. Add to daily scraper schedule

### Frontend Changes
1. Develop in `property-finder-ui/`
2. Test locally with `npm run dev`  
3. Deploy to Vercel with `vercel --prod`

### API Changes
1. Develop in `property-finder-api/src/`
2. Test locally with `npm run dev`
3. Deploy to Vercel with `vercel --prod`

## 📞 Support & Handover Notes

### Critical Information
- **Lianjia Integration**: Fully implemented but requires CAPTCHA handling
- **Database**: All schemas and pipelines are production-ready on Supabase
- **Deployment**: Both frontend and API are deployed on Vercel for seamless integration

### Known Limitations
- Lianjia requires manual intervention for CAPTCHA
- ScraperAPI credits needed for high-volume scraping
- Some Hong Kong sites may implement new anti-bot measures

### Next Steps Recommendations
1. Implement automated CAPTCHA solving for Lianjia
2. Add more Chinese cities (Beijing, Shanghai priority)
3. Explore alternative China property data sources
4. Implement user authentication and saved searches

### Emergency Contacts
- Scraper Issues: Check ScraperAPI dashboard and server logs
- Database Issues: Monitor Supabase dashboard and connection health
- Deployment Issues: Review Vercel deployment logs and function analytics

---

**Last Updated**: August 26, 2025  
**System Status**: ✅ Production Ready (with CAPTCHA considerations)  
**Handover Status**: Complete - All documentation and systems operational
