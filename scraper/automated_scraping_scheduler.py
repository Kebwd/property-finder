import schedule
import time
import logging
import json
import os
from datetime import datetime, timedelta
import smtplib
try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
except ImportError:
    # Fallback for systems with email import issues
    MimeText = None
    MimeMultipart = None
import sys
import traceback

# Import our scrapers
from expanded_city_scraper import ExpandedCityPropertyScraper
from practical_property_scraper import PracticalPropertyScraper

class AutomatedScrapingScheduler:
    """
    Automated daily property scraping system
    Runs multiple scrapers on schedule with monitoring and alerts
    """
    
    def __init__(self, config_file='scraping_config.json'):
        self.config_file = config_file
        self.load_config()
        self.setup_logging()
        self.scrapers = {
            'expanded_city': ExpandedCityPropertyScraper(),
            'practical': PracticalPropertyScraper()
        }
        
    def load_config(self):
        """Load configuration for automated scraping"""
        default_config = {
            'schedules': {
                'morning_scrape': '08:00',      # 8 AM daily
                'afternoon_scrape': '14:00',    # 2 PM daily  
                'evening_scrape': '20:00'       # 8 PM daily
            },
            'notification': {
                'email_enabled': False,
                'email_to': 'your-email@example.com',
                'email_from': 'scraper@property-finder.com',
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_user': '',
                'smtp_password': ''
            },
            'data_retention': {
                'keep_days': 30,  # Keep data for 30 days
                'archive_path': './data/archive/'
            },
            'thresholds': {
                'min_properties_per_run': 10,
                'max_failures_per_day': 3
            }
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    def setup_logging(self):
        """Setup logging for monitoring"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('automated_scraping.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def daily_morning_scrape(self):
        """Morning scraping routine - focus on news and updates"""
        self.logger.info("🌅 Starting morning scraping routine")
        
        try:
            results = {
                'timestamp': datetime.now().isoformat(),
                'routine': 'morning',
                'scrapers': {}
            }
            
            # Run practical scraper for news updates
            practical_results = self.scrapers['practical'].run_complete_scraping()
            results['scrapers']['practical'] = {
                'properties_count': len(practical_results),
                'success': len(practical_results) > 0
            }
            
            # Save morning results
            morning_file = f"morning_scrape_{datetime.now().strftime('%Y%m%d')}.json"
            with open(morning_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': results,
                    'properties': practical_results
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ Morning scrape complete: {len(practical_results)} properties")
            
            # Check thresholds
            if len(practical_results) < self.config['thresholds']['min_properties_per_run']:
                self.logger.warning(f"⚠️ Low property count: {len(practical_results)}")
                self.send_alert(f"Morning scrape yielded only {len(practical_results)} properties")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Morning scrape failed: {e}")
            self.send_alert(f"Morning scrape failed: {str(e)}")
            return {'error': str(e)}
    
    def daily_afternoon_scrape(self):
        """Afternoon scraping routine - comprehensive city scraping"""
        self.logger.info("🌞 Starting afternoon scraping routine")
        
        try:
            # Run expanded city scraper
            expanded_results = self.scrapers['expanded_city'].run_expanded_scraping()
            
            total_properties = expanded_results['summary']['totals']['total_properties']
            success_rate = expanded_results['summary']['totals']['success_rate']
            
            self.logger.info(f"✅ Afternoon scrape complete: {total_properties} properties from {expanded_results['total_cities']} cities")
            self.logger.info(f"📊 Success rate: {success_rate}")
            
            # Save afternoon results with timestamp
            afternoon_file = f"afternoon_scrape_{datetime.now().strftime('%Y%m%d')}.json"
            with open(afternoon_file, 'w', encoding='utf-8') as f:
                json.dump(expanded_results, f, ensure_ascii=False, indent=2)
            
            # Check thresholds
            if total_properties < self.config['thresholds']['min_properties_per_run']:
                self.logger.warning(f"⚠️ Low property count: {total_properties}")
            
            return expanded_results
            
        except Exception as e:
            self.logger.error(f"❌ Afternoon scrape failed: {e}")
            self.send_alert(f"Afternoon scrape failed: {str(e)}")
            return {'error': str(e)}
    
    def daily_evening_scrape(self):
        """Evening scraping routine - data validation and cleanup"""
        self.logger.info("🌙 Starting evening scraping routine")
        
        try:
            # Run validation on today's data
            today = datetime.now().strftime('%Y%m%d')
            morning_file = f"morning_scrape_{today}.json"
            afternoon_file = f"afternoon_scrape_{today}.json"
            
            validation_results = {
                'timestamp': datetime.now().isoformat(),
                'routine': 'evening_validation',
                'daily_summary': {}
            }
            
            total_daily_properties = 0
            
            # Validate morning data
            if os.path.exists(morning_file):
                with open(morning_file, 'r', encoding='utf-8') as f:
                    morning_data = json.load(f)
                    morning_count = len(morning_data.get('properties', []))
                    total_daily_properties += morning_count
                    validation_results['daily_summary']['morning'] = morning_count
            
            # Validate afternoon data  
            if os.path.exists(afternoon_file):
                with open(afternoon_file, 'r', encoding='utf-8') as f:
                    afternoon_data = json.load(f)
                    afternoon_count = afternoon_data.get('summary', {}).get('totals', {}).get('total_properties', 0)
                    total_daily_properties += afternoon_count
                    validation_results['daily_summary']['afternoon'] = afternoon_count
            
            validation_results['daily_summary']['total'] = total_daily_properties
            
            # Generate daily report
            daily_report_file = f"daily_report_{today}.json"
            with open(daily_report_file, 'w', encoding='utf-8') as f:
                json.dump(validation_results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ Evening validation complete: {total_daily_properties} total properties today")
            
            # Send daily summary
            if total_daily_properties > 0:
                self.send_daily_summary(validation_results)
            
            # Cleanup old files
            self.cleanup_old_files()
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"❌ Evening validation failed: {e}")
            return {'error': str(e)}
    
    def send_alert(self, message):
        """Send alert notification"""
        if not self.config['notification']['email_enabled']:
            self.logger.info(f"📧 Alert (email disabled): {message}")
            return
        
        try:
            self.send_email(f"Property Scraper Alert", message)
        except Exception as e:
            self.logger.error(f"Failed to send alert email: {e}")
    
    def send_daily_summary(self, validation_results):
        """Send daily summary email"""
        if not self.config['notification']['email_enabled']:
            return
        
        try:
            summary = validation_results['daily_summary']
            subject = f"Daily Property Scraping Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
            message = f"""
Daily Property Scraping Summary
===============================

Morning Scrape: {summary.get('morning', 0)} properties
Afternoon Scrape: {summary.get('afternoon', 0)} properties
Total Daily Properties: {summary.get('total', 0)}

Timestamp: {validation_results['timestamp']}

Best regards,
Property Scraper Bot
            """
            
            self.send_email(subject, message)
            
        except Exception as e:
            self.logger.error(f"Failed to send daily summary: {e}")
    
    def send_email(self, subject, message):
        """Send email notification"""
        if not MimeText or not MimeMultipart:
            self.logger.info(f"📧 Email (not available): {subject} - {message}")
            return
            
        config = self.config['notification']
        
        msg = MimeMultipart()
        msg['From'] = config['email_from']
        msg['To'] = config['email_to']
        msg['Subject'] = subject
        
        msg.attach(MimeText(message, 'plain'))
        
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        server.login(config['smtp_user'], config['smtp_password'])
        text = msg.as_string()
        server.sendmail(config['email_from'], config['email_to'], text)
        server.quit()
    
    def cleanup_old_files(self):
        """Cleanup old scraping files based on retention policy"""
        try:
            keep_days = self.config['data_retention']['keep_days']
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            # Create archive directory if it doesn't exist
            archive_path = self.config['data_retention']['archive_path']
            os.makedirs(archive_path, exist_ok=True)
            
            # Find files older than retention period
            for filename in os.listdir('.'):
                if any(filename.startswith(prefix) for prefix in ['morning_scrape_', 'afternoon_scrape_', 'daily_report_']):
                    file_path = os.path.join('.', filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        # Move to archive
                        archive_file = os.path.join(archive_path, filename)
                        os.rename(file_path, archive_file)
                        self.logger.info(f"📦 Archived old file: {filename}")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
    
    def setup_schedules(self):
        """Setup automated scraping schedules"""
        schedules = self.config['schedules']
        
        # Schedule morning scrape
        schedule.every().day.at(schedules['morning_scrape']).do(self.daily_morning_scrape)
        
        # Schedule afternoon scrape
        schedule.every().day.at(schedules['afternoon_scrape']).do(self.daily_afternoon_scrape)
        
        # Schedule evening validation
        schedule.every().day.at(schedules['evening_scrape']).do(self.daily_evening_scrape)
        
        self.logger.info("📅 Automated schedules configured:")
        self.logger.info(f"   Morning scrape: {schedules['morning_scrape']}")
        self.logger.info(f"   Afternoon scrape: {schedules['afternoon_scrape']}")
        self.logger.info(f"   Evening validation: {schedules['evening_scrape']}")
    
    def run_scheduler(self):
        """Run the automated scheduler"""
        self.logger.info("🤖 Starting automated property scraping scheduler")
        self.setup_schedules()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Scheduler error: {e}")
            self.send_alert(f"Scheduler crashed: {str(e)}")
    
    def run_manual_test(self):
        """Run manual test of all scraping routines"""
        self.logger.info("🧪 Running manual test of all scraping routines")
        
        print("🤖 AUTOMATED SCRAPING SYSTEM TEST")
        print("=" * 50)
        
        # Test morning routine
        print("\n🌅 Testing morning scraping routine...")
        morning_results = self.daily_morning_scrape()
        print(f"✅ Morning test complete")
        
        # Wait a bit
        time.sleep(5)
        
        # Test afternoon routine
        print("\n🌞 Testing afternoon scraping routine...")
        afternoon_results = self.daily_afternoon_scrape()
        print(f"✅ Afternoon test complete")
        
        # Wait a bit
        time.sleep(5)
        
        # Test evening routine
        print("\n🌙 Testing evening validation routine...")
        evening_results = self.daily_evening_scrape()
        print(f"✅ Evening test complete")
        
        print(f"\n🎉 ALL AUTOMATED ROUTINES TESTED SUCCESSFULLY")
        print("🚀 Ready for production scheduling!")
        
        return {
            'morning': morning_results,
            'afternoon': afternoon_results,
            'evening': evening_results
        }

def main():
    """Main function to run automated scraping"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Property Scraping System')
    parser.add_argument('--mode', choices=['schedule', 'test'], default='test',
                        help='Run in scheduler mode or test mode')
    parser.add_argument('--config', default='scraping_config.json',
                        help='Configuration file path')
    
    args = parser.parse_args()
    
    scheduler = AutomatedScrapingScheduler(args.config)
    
    if args.mode == 'schedule':
        print("🤖 Starting automated scraping scheduler...")
        print("Press Ctrl+C to stop")
        scheduler.run_scheduler()
    else:
        print("🧪 Running test mode...")
        scheduler.run_manual_test()

if __name__ == "__main__":
    main()
