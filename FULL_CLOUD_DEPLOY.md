# 🚀 Full Cloud Deployment Guide - Vercel + Supabase

This guide will set up your Property Finder application to run 100% in the cloud with no localhost dependencies.

## 🌐 Architecture Overview

- **Frontend**: Vercel (Static hosting + CDN)
- **Backend API**: Vercel Serverless Functions
- **Database**: Supabase PostgreSQL
- **Scraper**: GitHub Actions (or Google Cloud Run)
- **File Storage**: Vercel Blob Storage (for uploads)
- **Caching**: Vercel Edge Cache

## 📋 Prerequisites

- GitHub account
- Vercel account (free tier available)
- Supabase account (free tier available)
- Google Maps API key

## 🚀 Step-by-Step Deployment

### Step 1: Setup Supabase Database

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Wait for database to initialize
4. Go to **SQL Editor** and run this migration:

```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create stores table
CREATE TABLE stores (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  address TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  deal_date DATE,
  category TEXT,
  deal_price NUMERIC(10,2),
  geom GEOGRAPHY(Point,4326),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create function to set geometry from lat/lng
CREATE OR REPLACE FUNCTION set_geom() RETURNS trigger AS $$
BEGIN
  NEW.geom := ST_SetSRID(
    ST_MakePoint(NEW.longitude, NEW.latitude), 4326
  )::geography;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically set geometry
CREATE TRIGGER trg_set_geom
  BEFORE INSERT OR UPDATE ON stores
  FOR EACH ROW EXECUTE PROCEDURE set_geom();

-- Create indexes for better performance
CREATE INDEX idx_stores_geom ON stores USING GIST(geom);
CREATE INDEX idx_stores_category ON stores(category);
CREATE INDEX idx_stores_deal_date ON stores(deal_date);
CREATE INDEX idx_stores_location ON stores(latitude, longitude);

-- Enable Row Level Security (RLS)
ALTER TABLE stores ENABLE ROW LEVEL SECURITY;

-- Create policy to allow read access to all users
CREATE POLICY "Allow read access to stores" ON stores
  FOR SELECT USING (true);

-- Create policy to allow insert/update/delete for authenticated users
CREATE POLICY "Allow all operations for service role" ON stores
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');
```

5. Go to **Settings > API** and copy:
   - Project URL
   - Project Reference
   - Anon public key
   - Service role key (keep this secret!)

### Step 2: Deploy to Vercel

1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Click **"New Project"**
4. Import your GitHub repository
5. Configure build settings:
   - **Framework Preset**: Other
   - **Root Directory**: `./`
   - **Build Command**: `npm run build`
   - **Output Directory**: `property-finder-ui/dist`
   - **Install Command**: `npm run install:ui`

### Step 3: Set Environment Variables in Vercel

Go to your Vercel project → **Settings** → **Environment Variables** and add:

```
NODE_ENV=production
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_DB_URL=postgresql://postgres:[password]@db.your-project-ref.supabase.co:5432/postgres
GEOCODING_API_KEY=your_google_maps_api_key
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_URL=https://your-vercel-domain.vercel.app/api
```

### Step 4: Setup GitHub Actions for Scraper

1. Go to your GitHub repository
2. Go to **Settings** → **Secrets and Variables** → **Actions**
3. Add these secrets:

```
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_DB_URL=postgresql://postgres:[password]@db.your-project-ref.supabase.co:5432/postgres
```

4. The scraper will now run automatically daily at 2 AM UTC

### Step 5: Configure Google Maps API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable **Geocoding API**
3. Create API key with appropriate restrictions
4. Add the key to Vercel environment variables

## 🔧 Production URLs

After deployment, your application will be available at:

- **Frontend**: `https://your-app-name.vercel.app`
- **API**: `https://your-app-name.vercel.app/api`
- **Database**: Managed by Supabase
- **Admin Panel**: `https://supabase.com/dashboard/project/your-project-ref`

## 🧪 Testing Your Deployment

Run this command to test your live deployment:

```bash
# Test API health
curl https://your-app-name.vercel.app/health

# Test search endpoint
curl "https://your-app-name.vercel.app/api/search?query=test"
```

## 🔒 Security Checklist

- [ ] Database passwords are secure
- [ ] API keys are stored in environment variables
- [ ] Supabase RLS policies are enabled
- [ ] Google Maps API has proper restrictions
- [ ] GitHub secrets are properly configured

## 🌟 Benefits of Full Cloud Setup

- **Zero localhost dependencies**
- **Automatic scaling**
- **Global CDN distribution**
- **Built-in SSL/TLS**
- **Automatic backups**
- **99.9% uptime SLA**
- **Cost-effective (free tiers available)**

## 🆘 Troubleshooting

### API Not Working
- Check Vercel function logs
- Verify environment variables
- Check database connection

### Database Connection Issues
- Verify Supabase connection string
- Check if database is active
- Verify SSL requirements

### Scraper Not Running
- Check GitHub Actions logs
- Verify secrets are set
- Check Supabase permissions

## 🔄 Updates and Maintenance

- **Code Updates**: Push to GitHub → Automatic Vercel deployment
- **Database Updates**: Use Supabase dashboard or SQL editor
- **Monitoring**: Use Vercel Analytics and Supabase monitoring
- **Logs**: Check Vercel function logs and GitHub Actions logs

Your application is now fully cloud-native and production-ready! 🎉
