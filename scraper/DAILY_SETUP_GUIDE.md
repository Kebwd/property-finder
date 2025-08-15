# Daily Property Scraper Setup Guide - NEW APPROACH

## 🎯 Overview
Your spider now uses **INCREMENTAL CHANGE DETECTION** instead of date filtering:
- ✅ **Monitors for newly posted deals** (regardless of transaction date)
- ✅ **Compares with previous runs** to detect new additions
- ✅ **Captures historical deals** when they're newly added to the website
- ✅ **Two monitoring modes**: Daily (last 7 days) and Weekly (last 14 days)

## 🔄 How It Works

### **The New Approach:**
1. **Daily Mode**: Checks last 7 days for deals, compares with previous run
2. **Weekly Mode**: Checks last 14 days for comprehensive coverage  
3. **Change Detection**: Only reports deals that weren't seen in previous runs
4. **Smart Tracking**: Creates unique IDs for each deal to avoid duplicates

### **Why This Is Better:**
- 🎯 **Catches all new content** regardless of transaction date
- 📈 **No missed deals** due to posting delays
- 🔍 **Efficient processing** (only new deals are yielded)
- 📊 **Historical coverage** for recently added old transactions

## 🚀 Quick Setup (Choose One Method)

### Method 1: Windows Task Scheduler (Recommended)

1. **Run as Administrator**:
   ```powershell
   # Open PowerShell as Administrator
   Set-Location "C:\Users\User\storefinder\scraper"
   .\setup_daily_task.ps1
   ```

2. **Customize the schedule** (optional):
   ```powershell
   # Run at different time (e.g., 6 AM)
   .\setup_daily_task.ps1 -Time "06:00"
   ```

### Method 2: Manual Daily Run

1. **Run daily scraper directly**:
   ```bash
   cd C:\Users\User\storefinder\scraper
   python daily_scraper.py
   ```

## 📊 Understanding the Output

### **Successful Run Example:**
```
🗓️  DAILY PROPERTY DEAL SCRAPER
📅 Date: Monday, August 11, 2025
� Monitoring mode: daily
📍 Daily monitoring: checking last 7 days (04/08/2025-11/08/2025)
🆕 NEW DEAL: 達成商業大廈 - 商舖 - 售$1,013萬
🆕 NEW DEAL: 達成商業大廈 - 商舖 - 售$763萬
📊 New deals found: 2
💾 Saved 2 current deals for next comparison
```

### **No New Deals (Normal):**
```
📊 New deals found: 0
ℹ️  No new deals found in daily mode - this is normal if no new deals were posted
```

### **File Structure:**
```
daily_output/
├── 2025-08-11/
│   ├── deals_18-18-25.json       # Only NEW deals (may be empty)
│   └── scrape_18-18-25.log       # Full logs
├── 2025-08-12/                   # Next day
│   └── deals_09-00-00.json
└── latest.json -> 2025-08-12/deals_09-00-00.json
```

## ⚙️ Advanced Configuration

### 1. **Monitoring Modes**

```bash
# Daily mode (default) - checks last 7 days
python -m scrapy crawl store_spider -a mode=daily

# Weekly mode - checks last 14 days  
python -m scrapy crawl store_spider -a mode=weekly

# Test mode - disable pipelines
python -m scrapy crawl store_spider -a mode=daily -s "ITEM_PIPELINES={}"
```

### 2. **Automatic Mode Selection**
The daily script automatically chooses:
- **Monday-Saturday**: Daily mode (last 7 days)
- **Sunday**: Weekly mode (last 14 days for comprehensive check)

### 3. **Change Detection Settings**

Edit the spider for different timeframes:
```python
# Daily mode: check last 7 days (current)
start_date = today - timedelta(days=7)

# More conservative: check last 3 days
start_date = today - timedelta(days=3)

# More comprehensive: check last 14 days
start_date = today - timedelta(days=14)
```

## 🔧 Management Commands

### **Daily Operations**
```bash
# Test daily monitoring
python -m scrapy crawl store_spider -a mode=daily -s CLOSESPIDER_ITEMCOUNT=10

# Test weekly monitoring  
python -m scrapy crawl store_spider -a mode=weekly -s CLOSESPIDER_ITEMCOUNT=50

# Run full automation
python daily_scraper.py

# Check tracking file
cat deal_tracking.json
```

### **Task Scheduler Management**
```powershell
# Run immediately (test)
Start-ScheduledTask -TaskName "DailyPropertyScraper"

# View task status
Get-ScheduledTask -TaskName "DailyPropertyScraper"

# Disable/Enable
Disable-ScheduledTask -TaskName "DailyPropertyScraper"
Enable-ScheduledTask -TaskName "DailyPropertyScraper"
```

## 📈 Monitoring Results

### **Key Log Messages:**
```
🗓️  Daily mode: Checking for newly posted deals
📋 Loaded 24 previously seen deals  
🆕 NEW DEAL: [Building] - [Type] - [Price]
📊 Total deals checked: 18
🆕 New deals found: 2
💾 Saved 18 current deals for next comparison
```

### **Success Metrics:**
- ✅ **Change detection working**: "Loaded X previously seen deals"
- ✅ **New deals identified**: "NEW DEAL: ..." messages
- ✅ **Tracking updated**: "Saved X current deals for next comparison"

## 🎯 Expected Behavior

### **First Run:**
- Finds all deals in date range as "new"
- Creates deal_tracking.json baseline
- Future runs compare against this baseline

### **Subsequent Runs:**
- Only yields deals not seen before
- Updates tracking file with current state
- Empty results are normal (no new deals posted)

### **Weekly vs Daily:**
- **Daily**: More frequent, smaller date range (7 days)
- **Weekly**: Less frequent, larger date range (14 days)
- Both use same change detection logic

## ✅ Verification Checklist

- [ ] Spider correctly loads previous deals tracking
- [ ] URLs generated with proper date ranges (daily: 7 days, weekly: 14 days)
- [ ] Only new deals are yielded (not all deals in range)
- [ ] deal_tracking.json is updated after each run
- [ ] Daily automation script works with both modes
- [ ] Task scheduler created successfully
- [ ] Log shows "NEW DEAL" only for actually new deals

## 🎉 Success!

Your spider now intelligently monitors for **newly posted deals** rather than just today's transaction dates. This approach:

1. **Never misses new content** regardless of when deals are posted
2. **Avoids duplicates** through smart change detection  
3. **Adapts to posting patterns** (captures delayed historical entries)
4. **Runs efficiently** (only processes truly new deals)
5. **Provides comprehensive coverage** with dual daily/weekly modes

**The system will now capture ALL newly posted property deals automatically!** 🏠✨
