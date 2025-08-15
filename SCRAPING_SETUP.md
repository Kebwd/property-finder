# 🕷️ Scheduled Scraping Setup

This setup provides automated daily property scraping using GitHub Actions and API endpoints.

## 🚀 Quick Setup

### 1. Configure Environment Variables

Add these to your Railway app environment:

```env
SCRAPER_API_KEY=your-secure-api-key-here
SCRAPER_PATH=../scraper
```

### 2. Configure GitHub Secrets

In your GitHub repository, add these secrets:

- `SCRAPER_API_KEY`: Same as above (for authentication)
- `API_BASE_URL`: Your Railway app URL (e.g., `https://your-app.railway.app`)

### 3. Deploy and Test

1. Push the code to GitHub
2. The workflow will run daily at 2 AM UTC
3. You can also trigger it manually from GitHub Actions tab

## 📡 API Endpoints

### Trigger Scraping
```http
POST /api/scraper/start
Headers:
  X-API-Key: your-scraper-api-key
```

### Check Status
```http
GET /api/scraper/status
```

### Get Logs
```http
GET /api/scraper/logs?limit=20
```

## 🔧 Manual Testing

Test the scraping endpoint locally:

```bash
# Start scraping
curl -X POST \
  -H "X-API-Key: your-scraper-api-key" \
  http://localhost:5000/api/scraper/start

# Check status
curl http://localhost:5000/api/scraper/status

# Get logs
curl http://localhost:5000/api/scraper/logs
```

## ⚙️ Configuration

### Timing
- Default: Daily at 2 AM UTC
- Edit `.github/workflows/daily-scraping.yml` to change schedule
- Use [crontab.guru](https://crontab.guru) for cron syntax help

### Rate Limiting
- Minimum 30 minutes between scraping runs
- Prevents spam and resource abuse
- Can be overridden with force_run parameter

### Timeout
- Scraping process times out after 30 minutes
- Prevents hanging processes
- Adjust in `routes/scraper.js` if needed

## 🛠️ Troubleshooting

### Common Issues

1. **"Scraper directory not found"**
   - Check `SCRAPER_PATH` environment variable
   - Ensure scraper folder is included in deployment

2. **"daily_scraper.py not found"**
   - Verify scraper files are in the repository
   - Check file permissions

3. **Python/Scrapy errors**
   - Check scraper dependencies in `requirements.txt`
   - Verify database connection settings

4. **Rate limiting**
   - Normal for frequent manual triggers
   - Scheduled runs should work fine

### Debug Steps

1. Check API health: `GET /health`
2. Check scraper status: `GET /api/scraper/status`
3. View recent logs: `GET /api/scraper/logs`
4. Check GitHub Actions logs in repository

## 📊 Monitoring

### GitHub Actions
- View workflow runs in GitHub repository
- Check logs for each step
- Set up notifications for failures

### API Monitoring
- `/health` endpoint shows system status
- `/api/scraper/status` shows scraping status
- Logs track all scraping activity

## 🔒 Security

- API key required for triggering scraping
- Rate limiting prevents abuse
- Logs don't expose sensitive data
- GitHub secrets protect credentials

## 🎯 Next Steps

1. **Test the setup**:
   ```bash
   # Deploy to Railway
   git add .
   git commit -m "Add scheduled scraping"
   git push
   ```

2. **Configure secrets** in GitHub repository settings

3. **Test manually** from GitHub Actions tab

4. **Monitor** the daily runs

The scraping will now run automatically every day at 2 AM UTC! 🎉
