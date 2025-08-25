#!/usr/bin/env python3
"""
Daily Scrapy Automation Script
Runs spider daily and manages output files with timestamps
"""
import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path
import shutil

def run_daily_scrape(mode="daily", enable_database=True, spider_name="house_spider"):
    """Execute daily scraping with proper file management"""
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H-%M-%S")
    
    mode_suffix = f"_{mode}" if mode != "daily" else ""
    
    print(f"🕷️  {mode.upper()} SCRAPE STARTING: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 Using spider: {spider_name}")
    print(f"🛡️  Anti-bot protection: ENABLED")
    print("=" * 60)
    
    # Create daily output directory
    output_dir = Path("daily_output") / date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define output files based on spider type
    spider_prefix = "houses" if spider_name == "house_spider" else "deals"
    json_output = output_dir / f"{spider_prefix}_{time_str}{mode_suffix}.json"
    log_output = output_dir / f"scrape_{time_str}{mode_suffix}.log"
    
    print(f"📁 Output directory: {output_dir}")
    print(f"📄 JSON output: {json_output.name}")
    print(f"📋 Log output: {log_output.name}")
    print(f"🔄 Monitoring mode: {mode}")
    print(f"💾 Database enabled: {enable_database}")
    
    # Prepare scrapy command with enhanced anti-bot settings
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", spider_name,
        "-a", f"mode={mode}",  # Pass mode to spider
        "-L", "INFO",
        "-o", str(json_output),
        "--logfile", str(log_output),
        # Enhanced consistent anti-bot protection settings
        "-s", "DOWNLOAD_DELAY=0",  # Managed by ConsistentAntiBot
        "-s", "CONCURRENT_REQUESTS=1",
        "-s", "AUTOTHROTTLE_ENABLED=True",
        "-s", "AUTOTHROTTLE_TARGET_CONCURRENCY=0.3",
        "-s", "RETRY_TIMES=8",  # More retries for consistent success
        "-s", "DOWNLOAD_TIMEOUT=30"
    ]
    
    # Conditionally disable pipelines for testing
    if not enable_database:
        cmd.extend(["-s", "ITEM_PIPELINES={}"])
        print("⚠️  Database pipelines disabled for testing")
    
    print(f"\\n🚀 Running command: {' '.join(cmd)}")
    
    try:
        # Run the spider
        result = subprocess.run(
            cmd, 
            cwd=Path(__file__).parent,
            capture_output=True, 
            text=True, 
            timeout=300  # 5 minute timeout
        )
        
        # Check results
        if result.returncode == 0:
            print("✅ Spider completed successfully!")
            
            # Check if data was scraped
            if json_output.exists():
                with open(json_output, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        item_count = len(data) if data else 0
                        print(f"📊 New deals found: {item_count}")
                        
                        if item_count > 0:
                            # Show sample data based on spider type
                            sample = data[0]
                            if spider_name == "house_spider":
                                print(f"🏠 Sample: {sample.get('estate_name_zh', 'N/A')} - {sample.get('house_type', 'N/A')}")
                                print(f"💰 Price: ¥{sample.get('deal_price', 'N/A'):,}")
                                print(f"📐 Area: {sample.get('area', 'N/A')}㎡")
                            else:
                                print(f"🏢 Sample: {sample.get('building_name_zh', 'N/A')} - {sample.get('type_raw', 'N/A')}")
                                print(f"💰 Price: {sample.get('deal_price', 'N/A')}")
                            print(f"📅 Date: {sample.get('deal_date', 'N/A')}")
                            
                            if enable_database:
                                print(f"💾 Data saved to database and JSON file")
                            else:
                                print(f"📄 Data saved to JSON file only")
                            
                            # Create symlink to latest
                            latest_link = Path("daily_output") / f"latest{mode_suffix}.json"
                            if latest_link.exists() or latest_link.is_symlink():
                                latest_link.unlink()
                            try:
                                # Use relative path for symlink
                                relative_path = Path(date_str) / json_output.name
                                os.symlink(relative_path, latest_link)
                                print(f"🔗 Created symlink: latest{mode_suffix}.json -> {relative_path}")
                            except OSError:
                                # Fallback: copy file if symlink fails on Windows
                                shutil.copy2(json_output, latest_link)
                                print(f"📋 Copied to: latest{mode_suffix}.json")
                            
                            return True
                        else:
                            print(f"ℹ️  No new deals found in {mode} mode - this is normal if no new deals were posted")
                            return True  # This is success for change detection
                    except json.JSONDecodeError:
                        print("❌ Invalid JSON output")
                        return False
            else:
                print("❌ No output file created")
                return False
        else:
            print(f"❌ Spider failed with return code: {result.returncode}")
            if result.stderr:
                print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Spider timed out (>5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def cleanup_old_files(days_to_keep=7):
    """Clean up old daily output files"""
    print(f"\\n🧹 Cleaning up files older than {days_to_keep} days...")
    
    output_base = Path("daily_output")
    if not output_base.exists():
        return
    
    cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
    removed_count = 0
    
    for item in output_base.iterdir():
        if item.is_dir() and item.name != "latest.json":
            if item.stat().st_mtime < cutoff_date:
                shutil.rmtree(item)
                removed_count += 1
                print(f"🗑️  Removed old directory: {item.name}")
    
    if removed_count == 0:
        print("✅ No old files to clean up")
    else:
        print(f"✅ Cleaned up {removed_count} old directories")


def generate_daily_summary():
    """Generate a summary of today's scraping results"""
    today = datetime.now().strftime("%Y-%m-%d")
    today_dir = Path("daily_output") / today
    
    if not today_dir.exists():
        print("📋 No data for today yet")
        return
    
    print(f"\\n📊 TODAY'S SUMMARY ({today})")
    print("=" * 40)
    
    json_files = list(today_dir.glob("deals_*.json"))
    
    if not json_files:
        print("📋 No deal files found for today")
        return
    
    total_items = 0
    latest_file = None
    latest_time = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = len(data) if data else 0
                total_items += count
                
                # Track latest file
                file_time = json_file.stat().st_mtime
                if file_time > latest_time:
                    latest_time = file_time
                    latest_file = json_file
                
                run_time = datetime.fromtimestamp(file_time).strftime("%H:%M")
                print(f"  {run_time}: {count} items")
                
        except Exception as e:
            print(f"  ❌ Error reading {json_file.name}: {e}")
    
    print(f"\\n📈 Total items today: {total_items}")
    print(f"🕐 Total runs: {len(json_files)}")
    
    if latest_file and total_items > 0:
        print(f"🏆 Latest run: {latest_file.name}")


def main():
    """Main execution function"""
    print("🗓️  DAILY PROPERTY SCRAPER WITH ANTI-BOT PROTECTION")
    print(f"📅 Date: {datetime.now().strftime('%A, %B %d, %Y')}")
    print(f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Check if we're in the correct directory
    if not Path("scrapy.cfg").exists():
        print("❌ Error: Not in Scrapy project directory")
        print("Please run this script from the scraper directory")
        return False
    
    # Parse command line arguments
    enable_database = "--no-db" not in sys.argv
    force_mode = None
    spider_name = "house_spider"  # Default to house spider
    
    for arg in sys.argv[1:]:
        if arg in ["daily", "weekly"]:
            force_mode = arg
        elif arg in ["house_spider", "store_spider"]:
            spider_name = arg
        elif arg == "--houses":
            spider_name = "house_spider"
        elif arg == "--stores":
            spider_name = "store_spider"
    
    # Determine if this is a weekly run (e.g., Sundays)
    is_sunday = datetime.now().weekday() == 6
    
    print(f"🕷️  Selected spider: {spider_name}")
    print(f"🛡️  Anti-bot protection: ENABLED")
    print(f"💾 Database integration: {'ENABLED' if enable_database else 'DISABLED'}")
    
    if force_mode:
        print(f"🔧 Mode override: {force_mode.upper()}")
        success = run_daily_scrape(mode=force_mode, enable_database=enable_database, spider_name=spider_name)
    elif is_sunday:
        print("📅 Sunday detected - running WEEKLY comprehensive check")
        success = run_daily_scrape(mode="weekly", enable_database=enable_database, spider_name=spider_name)
    else:
        print("🗓️  Running DAILY new deals check")
        success = run_daily_scrape(mode="daily", enable_database=enable_database, spider_name=spider_name)
    
    # Generate summary
    generate_daily_summary()
    
    # Cleanup old files
    cleanup_old_files()
    
    # Final status
    if success:
        print("\\n🎉 Daily scraping completed successfully!")
        print("\\n💡 Usage examples:")
        print("  python daily_scraper.py --houses daily    # House spider with anti-bot protection")
        print("  python daily_scraper.py --stores weekly   # Store spider comprehensive mode")
        print("  python daily_scraper.py house_spider      # Direct spider name")
    else:
        print("\\n⚠️  Daily scraping completed with issues")
        print("\\n🔧 Troubleshooting:")
        print("  - Check if anti-bot protection is working properly")
        print("  - Consider using proxy rotation for better success")
        print("  - Increase delays if still getting blocked")
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n⛔ Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n💥 Fatal error: {e}")
        sys.exit(1)
