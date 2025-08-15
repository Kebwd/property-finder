# Vercel + Supabase Deployment Guide

## Prerequisites

1. **Supabase Account**: Sign up at [supabase.com](https://supabase.com)
2. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
3. **Google Maps API Key**: Get from [Google Cloud Console](https://console.cloud.google.com)

## Step 1: Setup Supabase

1. Create a new Supabase project
2. Go to Settings > Database and note your connection string
3. Go to Settings > API and note your project URL and anon key
4. Enable PostGIS extension:
   - Go to Database > Extensions
   - Enable "postgis" extension
5. Run the database migration:
   - Copy the contents of `supabase/migrations/20240815000001_initial_setup.sql`
   - Go to SQL Editor in Supabase dashboard
   - Paste and run the SQL

## Step 2: Setup Vercel

1. Install Vercel CLI: `npm install -g vercel`
2. Connect your GitHub repository to Vercel
3. Set environment variables in Vercel dashboard:
   - `NODE_ENV=production`
   - `SUPABASE_URL=your_supabase_project_url`
   - `SUPABASE_ANON_KEY=your_supabase_anon_key`
   - `SUPABASE_DB_URL=your_supabase_database_url`
   - `GEOCODING_API_KEY=your_google_maps_api_key`
   - `VITE_SUPABASE_URL=your_supabase_project_url`
   - `VITE_SUPABASE_ANON_KEY=your_supabase_anon_key`
   - `VITE_API_URL=https://your-vercel-domain.vercel.app/api`

## Step 3: Deploy

1. Push your code to GitHub
2. Vercel will automatically deploy
3. Check the deployment logs for any issues

## Step 4: Update Scraper (Optional)

If you want to keep the scraper running:

1. Deploy the scraper to a separate service (e.g., Railway, Heroku, or Google Cloud Run)
2. Update the scraper to connect to your Supabase database
3. Use the same `SUPABASE_DB_URL` connection string

## Local Development

1. Install dependencies:
   ```bash
   npm run install:api
   npm run install:ui
   ```

2. Create environment files as shown in `.env.example`

3. Run the development servers:
   ```bash
   # Terminal 1 - API
   npm run dev
   
   # Terminal 2 - UI
   npm run dev:ui
   ```

## Key Changes Made

- Removed Redis dependency (using in-memory cache for geocoding)
- Removed Railway-specific configurations
- Added Supabase client integration
- Updated database configuration for Supabase
- Added Vercel configuration for serverless deployment
- Updated build scripts for Vercel compatibility
- Added Row Level Security policies for Supabase

## Monitoring

- Use Vercel Analytics for frontend monitoring
- Use Supabase Dashboard for database monitoring
- Set up alerts in both platforms for production issues
