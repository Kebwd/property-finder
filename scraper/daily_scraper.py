#!/usr/bin/env python3
"""
Daily Scrapy Automation Script
Runs spider daily and manages output files with timestamps
"""
import os
import sys
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_scraper.log'),
        logging.StreamHandler()
    ]
)

def validate_environment(enable_database=True):
    """Validate required environment variables and dependencies"""
    errors = []
    
    # Check DATABASE_URL if database is enabled
    if enable_database:
        if not os.getenv('DATABASE_URL') and os.getenv('SCRAPER_MODE') != 'test':
            errors.append("DATABASE_URL environment variable not set")
    
    # Check if scrapy is available
    try:
        subprocess.run([sys.executable, "-m", "scrapy", "--help"], 
                      capture_output=True, check=True, timeout=10)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        errors.append("Scrapy is not available or not working")
    
    # Check if required directories can be created
    try:
        test_dir = Path("daily_output/test")
        test_dir.mkdir(parents=True, exist_ok=True)
        test_dir.rmdir()
    except Exception as e:
        errors.append(f"Cannot create output directories: {e}")
    
    if errors:
        logging.error("Environment validation failed:")
        for error in errors:
            logging.error(f"  - {error}")
        return False
    
    logging.info("Environment validation passed")
    return True

def run_daily_scrape(mode="daily", enable_database=True, spider_name="house_spider", max_retries=2):
    """Execute daily scraping with proper file management and error handling"""
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H-%M-%S")
    
    mode_suffix = f"_{mode}" if mode != "daily" else ""
    
    logging.info(f"SCRAPE STARTING: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Using spider: {spider_name}")
    logging.info(f"Anti-bot protection: ENABLED")
    logging.info("=" * 60)
    
    # Validate environment first
    if not validate_environment(enable_database):
        logging.error("Environment validation failed, aborting")
        return False
    
    # Create daily output directory
    output_dir = Path("daily_output") / date_str
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to create output directory: {e}")
        return False
    
    # Define output files based on spider type
    spider_prefix = "houses" if spider_name == "house_spider" else "deals"
    json_output = output_dir / f"{spider_prefix}_{time_str}{mode_suffix}.json"
    log_output = output_dir / f"scrape_{time_str}{mode_suffix}.log"
    
    logging.info(f"Output directory: {output_dir}")
    logging.info(f"JSON output: {json_output.name}")
    logging.info(f"Log output: {log_output.name}")
    logging.info(f"Monitoring mode: {mode}")
    logging.info(f"Database enabled: {enable_database}")
    
    # Prepare scrapy command with enhanced anti-bot settings
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", spider_name,
        "-a", f"mode={mode}",  # Pass mode to spider
        "-L", "INFO",
        "-o", str(json_output),
        "--logfile", str(log_output),
        # Enhanced consistent anti-bot protection settings
    "-s", "DOWNLOAD_DELAY=5",  # Conservative delay
        "-s", "CONCURRENT_REQUESTS=1",
        "-s", "AUTOTHROTTLE_ENABLED=True",
        "-s", "AUTOTHROTTLE_TARGET_CONCURRENCY=0.3",
        "-s", "RETRY_TIMES=5",  # Reasonable retry count
    "-s", "DOWNLOAD_TIMEOUT=180"  # 180s timeout (3 minutes)
    ]
    
    # Conditionally disable pipelines for testing
    if not enable_database:
        cmd.extend(["-s", "ITEM_PIPELINES={}"])
        logging.warning("Database pipelines disabled for testing")
    
    # Add Chrome options for CI environments
    if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
        cmd.extend([
            "-s", "SELENIUM_DRIVER_NAME=chrome",
            "-s", "SELENIUM_DRIVER_ARGUMENTS=['--headless', '--no-sandbox', '--disable-dev-shm-usage']"
        ])
        logging.info("CI environment detected, using headless Chrome")
    
    logging.info(f"Running command: {' '.join(cmd)}")
    
    # Retry mechanism
    for attempt in range(max_retries + 1):
        if attempt > 0:
            logging.info(f"Retry attempt {attempt}/{max_retries}")
            time.sleep(30)  # Wait before retry
        
        try:
            # Run the spider with extended timeout for stability
            result = subprocess.run(
                cmd, 
                cwd=Path(__file__).parent,
                capture_output=True, 
                text=True, 
                timeout=180  # 3 minute timeout to match DOWNLOAD_TIMEOUT
            )
            
            # Check results
            if result.returncode == 0:
                logging.info("Spider completed successfully!")
                
                # Check if data was scraped
                if json_output.exists():
                    return process_results(json_output, spider_name, mode, enable_database, mode_suffix, date_str)
                else:
                    logging.warning("No output file created, but spider returned success")
                    if attempt < max_retries:
                        continue
                    return False
            else:
                logging.error(f"Spider failed with return code: {result.returncode}")
                if result.stderr:
                    logging.error(f"Error output: {result.stderr}")
                if attempt < max_retries:
                    continue
                return False
                
        except subprocess.TimeoutExpired:
            logging.error(f"Spider timed out (>5 minutes) - site may be unresponsive")
            if attempt < max_retries:
                continue
            return False
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            if attempt < max_retries:
                continue
            return False
    
    logging.error(f"All {max_retries + 1} attempts failed")
    return False


def process_results(json_output, spider_name, mode, enable_database, mode_suffix, date_str):
    """Process spider results and handle output"""
    try:
        with open(json_output, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                item_count = len(data) if data else 0
                logging.info(f"New deals found: {item_count}")
                
                if item_count > 0:
                    # Show sample data based on spider type
                    sample = data[0]
                    if spider_name == "house_spider":
                        logging.info(f"Sample: {sample.get('estate_name_zh', 'N/A')} - {sample.get('house_type', 'N/A')}")
                        logging.info(f"Price: ¥{sample.get('deal_price', 'N/A'):,}")
                        logging.info(f"Area: {sample.get('area', 'N/A')}㎡")
                    else:
                        logging.info(f"Sample: {sample.get('building_name_zh', 'N/A')} - {sample.get('type_raw', 'N/A')}")
                        logging.info(f"Price: {sample.get('deal_price', 'N/A')}")
                    logging.info(f"Date: {sample.get('deal_date', 'N/A')}")
                    
                    if enable_database:
                        logging.info("Data saved to database and JSON file")
                    else:
                        logging.info("Data saved to JSON file only")
                    
                    # Create symlink to latest
                    latest_link = Path("daily_output") / f"latest{mode_suffix}.json"
                    try:
                        if latest_link.exists() or latest_link.is_symlink():
                            latest_link.unlink()
                        
                        # Use relative path for symlink
                        relative_path = Path(date_str) / json_output.name
                        os.symlink(relative_path, latest_link)
                        logging.info(f"Created symlink: latest{mode_suffix}.json -> {relative_path}")
                    except OSError:
                        # Fallback: copy file if symlink fails on Windows
                        try:
                            shutil.copy2(json_output, latest_link)
                            logging.info(f"Copied to: latest{mode_suffix}.json")
                        except Exception as e:
                            logging.warning(f"Failed to create symlink/copy: {e}")
                    
                    return True
                else:
                    logging.info(f"No new deals found in {mode} mode - this is normal if no new deals were posted")
                    return True  # This is success for change detection
                    
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON output: {e}")
                return False
                
    except Exception as e:
        logging.error(f"Failed to process results: {e}")
        return False


def cleanup_old_files(days_to_keep=7):
    """Clean up old daily output files"""
    logging.info(f"Cleaning up files older than {days_to_keep} days...")
    
    output_base = Path("daily_output")
    if not output_base.exists():
        logging.warning("Output directory does not exist")
        return 0
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for date_folder in output_base.iterdir():
            if not date_folder.is_dir():
                continue
                
            try:
                # Parse folder date
                folder_date = datetime.strptime(date_folder.name, "%Y%m%d")
                
                if folder_date < cutoff_date:
                    logging.info(f"Deleting old folder: {date_folder.name}")
                    shutil.rmtree(date_folder)
                    deleted_count += 1
                    
            except ValueError:
                # Skip folders that don't match date format
                logging.debug(f"Skipping non-date folder: {date_folder.name}")
                continue
            except Exception as e:
                logging.error(f"Failed to delete folder {date_folder.name}: {e}")
                continue
        
        logging.info(f"Cleanup completed: {deleted_count} folders deleted")
        return deleted_count
        
    except Exception as e:
        logging.error(f"Cleanup process failed: {e}")
        return 0


def generate_daily_summary():
    """Generate a summary of today's scraping results"""
    today = datetime.now().strftime("%Y%m%d")
    today_dir = Path("daily_output") / today
    
    if not today_dir.exists():
        logging.info("No data for today yet")
        return
    
    logging.info(f"TODAY'S SUMMARY ({today})")
    logging.info("=" * 40)
    
    try:
        json_files = list(today_dir.glob("deals_*.json"))
        
        if not json_files:
            logging.info("No deal files found for today")
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
                    logging.info(f"  {run_time}: {count} items")
                    
            except json.JSONDecodeError as e:
                logging.error(f"Error reading {json_file.name}: Invalid JSON - {e}")
            except Exception as e:
                logging.error(f"Error reading {json_file.name}: {e}")
        
        logging.info(f"Total items today: {total_items}")
        logging.info(f"Total runs: {len(json_files)}")
        
        if latest_file and total_items > 0:
            logging.info(f"Latest run: {latest_file.name}")
            
    except Exception as e:
        logging.error(f"Failed to generate summary: {e}")


def main():
    """Main execution function"""
    logging.info("DAILY PROPERTY SCRAPER WITH ANTI-BOT PROTECTION")
    logging.info(f"Date: {datetime.now().strftime('%A, %B %d, %Y')}")
    logging.info(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Check if we're in the correct directory
    if not Path("scrapy.cfg").exists():
        logging.error("Error: Not in Scrapy project directory")
        logging.error("Please run this script from the scraper directory")
        return False
    
    # Parse command line arguments with error handling
    try:
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

        logging.info(f"Selected spider: {spider_name}")
        logging.info("Anti-bot protection: ENABLED")
        logging.info(f"Database integration: {'ENABLED' if enable_database else 'DISABLED'}")

        # Validate environment before starting
        if not validate_environment(enable_database):
            logging.error("Environment validation failed")
            return False

        # Execute scraping based on mode
        if force_mode:
            logging.info(f"Mode override: {force_mode.upper()}")
            success = run_daily_scrape(mode=force_mode, enable_database=enable_database, spider_name=spider_name)
        elif is_sunday:
            logging.info("Sunday detected - running WEEKLY comprehensive check")
            success = run_daily_scrape(mode="weekly", enable_database=enable_database, spider_name=spider_name)
        else:
            logging.info("Running DAILY new deals check")
            success = run_daily_scrape(mode="daily", enable_database=enable_database, spider_name=spider_name)

        # Generate summary and cleanup
        try:
            generate_daily_summary()
        except Exception as e:
            logging.error(f"Failed to generate summary: {e}")

        try:
            cleanup_old_files()
        except Exception as e:
            logging.error(f"Failed to cleanup old files: {e}")

        # Final status
        if success:
            logging.info("Daily scraping completed successfully!")
            logging.info("Usage examples:")
            logging.info("  python daily_scraper.py --houses daily    # House spider with anti-bot protection")
            logging.info("  python daily_scraper.py --stores weekly   # Store spider comprehensive mode")
            logging.info("  python daily_scraper.py house_spider      # Direct spider name")
        else:
            logging.warning("Daily scraping completed with issues")
            logging.info("Troubleshooting:")
            logging.info("  - Check if anti-bot protection is working properly")
            logging.info("  - Consider using proxy rotation for better success")
            logging.info("  - Increase delays if still getting blocked")

        return success

    except Exception as e:
        logging.error(f"Critical error in main execution: {e}")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logging.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)
