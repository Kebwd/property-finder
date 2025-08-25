#!/usr/bin/env python3
"""
Combined Daily Scraper for both House and Store properties
Runs both spiders automatically for comprehensive data collection
"""

import os
import sys
import subprocess
import json
from datetime import datetime, timedelta
import time

def run_spider(spider_name, mode="daily", delay_between=300):
    """Run a spider with proper anti-bot protection"""
    print(f"\n🕷️  Starting {spider_name} spider...")
    
    # Create output directory
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = f"daily_output/{today}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamped filenames
    timestamp = datetime.now().strftime("%H-%M-%S")
    spider_type = spider_name.replace("_spider", "")
    json_file = f"{output_dir}/{spider_type}_{timestamp}.json"
    log_file = f"{output_dir}/{spider_type}_{timestamp}.log"
    
    # Build scrapy command with anti-bot protection
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", spider_name,
        "-a", f"mode={mode}",
        "-L", "INFO",
        "-o", json_file,
        "--logfile", log_file,
        # Anti-bot settings
        "-s", "DOWNLOAD_DELAY=0",  # Let anti-bot middleware handle delays
        "-s", "CONCURRENT_REQUESTS=1",
        "-s", "AUTOTHROTTLE_ENABLED=True",
        "-s", "AUTOTHROTTLE_TARGET_CONCURRENCY=0.3",
        "-s", "RETRY_TIMES=8",
        "-s", "DOWNLOAD_TIMEOUT=30"
    ]
    
    print(f"🚀 Command: {' '.join(cmd)}")
    
    try:
        # Run the spider
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print(f"✅ {spider_name} completed successfully!")
            
            # Check if data was scraped
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content and content != "[]":
                            data = json.loads(content)
                            print(f"📊 {spider_name} found: {len(data)} items")
                        else:
                            print(f"ℹ️  {spider_name}: No new items found (normal for daily mode)")
                except Exception as e:
                    print(f"⚠️  Could not parse {spider_name} output: {e}")
            
            return True
        else:
            print(f"❌ {spider_name} failed!")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"💥 Error running {spider_name}: {e}")
        return False
    
    finally:
        if delay_between > 0:
            print(f"⏳ Waiting {delay_between} seconds before next spider...")
            time.sleep(delay_between)

def cleanup_old_files():
    """Clean up files older than 7 days"""
    print("\n🧹 Cleaning up files older than 7 days...")
    
    cutoff_date = datetime.now() - timedelta(days=7)
    cleaned_count = 0
    
    if os.path.exists("daily_output"):
        for date_dir in os.listdir("daily_output"):
            try:
                dir_date = datetime.strptime(date_dir, "%Y-%m-%d")
                if dir_date < cutoff_date:
                    import shutil
                    shutil.rmtree(f"daily_output/{date_dir}")
                    cleaned_count += 1
                    print(f"🗑️  Removed: {date_dir}")
            except ValueError:
                continue
    
    if cleaned_count == 0:
        print("✅ No old files to clean up")
    else:
        print(f"✅ Cleaned up {cleaned_count} old directories")

def show_daily_summary():
    """Show summary of today's scraping results"""
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = f"daily_output/{today}"
    
    print(f"\n📊 TODAY'S SUMMARY ({today})")
    print("=" * 40)
    
    if not os.path.exists(output_dir):
        print("📋 No data collected today")
        return
    
    total_houses = 0
    total_stores = 0
    
    for filename in os.listdir(output_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(output_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content and content != "[]":
                        data = json.loads(content)
                        count = len(data)
                        if "house" in filename:
                            total_houses += count
                        elif "store" in filename:
                            total_stores += count
                        print(f"📄 {filename}: {count} items")
            except Exception as e:
                print(f"⚠️  Could not read {filename}: {e}")
    
    print(f"\n🏠 Total Houses: {total_houses}")
    print(f"🏪 Total Stores: {total_stores}")
    print(f"📦 Total Items: {total_houses + total_stores}")

def main():
    """Main execution function"""
    print("🗓️  COMBINED DAILY PROPERTY SCRAPER")
    print("=" * 50)
    print(f"📅 Date: {datetime.now().strftime('%A, %B %d, %Y')}")
    print(f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}")
    print("🛡️  Anti-bot protection: ENABLED")
    print("💾 Database integration: ENABLED")
    print("🕷️  Running: house_spider + store_spider")
    
    success_count = 0
    total_spiders = 2
    
    # Run house spider first
    if run_spider("house_spider", mode="daily", delay_between=300):
        success_count += 1
    
    # Run store spider second  
    if run_spider("store_spider", mode="daily", delay_between=0):
        success_count += 1
    
    # Show results
    show_daily_summary()
    
    # Cleanup old files
    cleanup_old_files()
    
    # Final status
    print(f"\n🎉 Combined scraping completed!")
    print(f"✅ Success rate: {success_count}/{total_spiders} spiders")
    
    if success_count == total_spiders:
        print("🎯 All spiders completed successfully!")
        return True
    else:
        print("⚠️  Some spiders failed - check logs for details")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⛔ Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)
