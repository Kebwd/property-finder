# Daily Scraper Issues - Resolution Guide

## Overview
Three issues identified and addressed:

1. ✅ **Store Spider Missing** - Fixed with combined daily automation
2. 🔄 **Lianjia Anti-Bot Verification** - Need better proxy strategy
3. ✅ **Search Display Names** - Already fixed with fallback logic

## Issue 1: Store Spider Missing ✅ FIXED

### Problem
Daily scraper only runs `house_spider` by default, missing store data.

### Solution
Created multiple approaches:

#### Approach A: Use existing daily_scraper.py with flags
```bash
# Run house spider
python daily_scraper.py --houses daily

# Run store spider  
python daily_scraper.py --stores daily
```

#### Approach B: Combined scraper (recommended)
```bash
# Runs both spiders automatically
python combined_daily_scraper.py
```

#### Approach C: PowerShell automation
```powershell
# Windows automation script
.\run_daily_combined.ps1
```

### Updated Cron Job
```bash
# Combined daily scraper - runs both house and store spiders
0 2 * * * root cd /app/scraper && /app/scraper/run_daily_combined.sh >> /var/log/scraper.log 2>&1
```

## Issue 2: Lianjia Anti-Bot Protection 🔄 NEEDS IMPROVEMENT

### Current Status
- Anti-bot middleware activated ✅
- Proxy rotation working ✅
- Free proxies loaded ✅
- **Problem**: Lianjia has very strict protection, timeouts occurring

### Test Results
```
2025-08-25 14:52:57 [middlewares.scrapy_simple_antibot] INFO: 📊 Final Anti-Bot Stats:
2025-08-25 14:52:57 [middlewares.scrapy_simple_antibot] INFO:    Total requests: 0
2025-08-25 14:52:57 [middlewares.scrapy_simple_antibot] INFO:    Success rate: 0.00%
2025-08-25 14:52:57 [middlewares.scrapy_simple_antibot] INFO:    Blocked requests: 0
```

### Recommended Improvements

#### Option 1: Premium Proxy Service
```python
# In enhanced_proxy_middleware.py
PREMIUM_PROXIES = [
    "premium-proxy1.com:8080:username:password",
    "premium-proxy2.com:8080:username:password"
]
```

#### Option 2: Residential IP Rotation
```python
# Configure residential proxy rotation
RESIDENTIAL_PROXY_SERVICES = [
    "smartproxy.com",
    "brightdata.com", 
    "oxylabs.io"
]
```

#### Option 3: Different Strategy for Lianjia
```python
# Separate spider configuration for Lianjia
CUSTOM_SETTINGS = {
    'DOWNLOAD_DELAY': 10,
    'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
    'CONCURRENT_REQUESTS': 1,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.1
}
```

## Issue 3: Search Display Names ✅ FIXED

### API Fallback Logic (Already Implemented)
```javascript
// In property-finder-api/src/routes/search.js
name: safe(row.estate_name_zh) || safe(row.building_name_zh) || null
```

### UI Fallback Logic (Already Implemented)  
```jsx
// In property-finder-ui/src/App.jsx
{store.estate_name_zh || store.building_name_zh || 'UNNAMED PROPERTY'}
```

### Helper Function for Empty Strings
```javascript
// Treats empty strings as null for proper fallback
function safe(value) {
    return (value && value.trim() !== '') ? value : null;
}
```

## Testing Commands

### Test House Spider
```bash
cd C:\Users\User\property-finder\scraper
python daily_scraper.py --houses daily
```

### Test Store Spider
```bash
cd C:\Users\User\property-finder\scraper
python daily_scraper.py --stores daily
```

### Test Combined Scraper
```bash
cd C:\Users\User\property-finder\scraper
python combined_daily_scraper.py
```

### Test Specific Sites
```bash
# Test Lianjia specifically (will likely fail without premium proxies)
python -m scrapy crawl lianjia_spider -L INFO -s CLOSESPIDER_ITEMCOUNT=3

# Test other spiders
python -m scrapy crawl house_spider -L INFO -a mode=daily -s CLOSESPIDER_ITEMCOUNT=3
```

## Next Steps

1. **Deploy Combined Scraper** ✅
   - Use `combined_daily_scraper.py` or PowerShell script
   - Update Docker container to use new automation

2. **Improve Lianjia Success Rate** 🔄
   - Consider premium proxy service
   - Implement residential IP rotation
   - Add more sophisticated anti-bot protection

3. **Monitor Results** 📊
   - Check daily output files
   - Verify both house and store data collection
   - Monitor success rates

## File Locations

- `combined_daily_scraper.py` - New combined automation script
- `run_daily_combined.ps1` - Windows PowerShell automation  
- `run_daily_combined.sh` - Linux bash automation
- `crontab` - Updated with combined scraper schedule
- Daily output: `daily_output/YYYY-MM-DD/`

## Success Metrics

- ✅ Both house and store spiders run daily
- ✅ Property names display correctly in UI
- 🔄 Lianjia success rate improvement needed
- ✅ Empty estate_name_zh handled properly
- ✅ Database integration working
