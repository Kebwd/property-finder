# Scraper Configuration for Supabase

## Environment Variables
Add these to your scraper environment:

```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
SUPABASE_DB_URL=your_supabase_database_url
```

## Deployment Options

### Option 1: Keep on Railway (Simple)
1. Update environment variables on Railway
2. The scraper will continue to work with Supabase database

### Option 2: Move to Google Cloud Run
1. Build Docker image: `docker build -t scraper .`
2. Deploy to Google Cloud Run
3. Set environment variables

### Option 3: Move to GitHub Actions (Scheduled)
1. Create `.github/workflows/scraper.yml`
2. Run scraper on schedule using GitHub Actions
3. Store environment variables as GitHub secrets

## Database Connection
The scraper will connect to the same Supabase PostgreSQL database that your main application uses. No changes needed to the scraping logic itself.

## Notes
- The scraper Dockerfile is already configured
- Just update the environment variables to point to Supabase
- Consider using Supabase service role key for the scraper (not anon key)
