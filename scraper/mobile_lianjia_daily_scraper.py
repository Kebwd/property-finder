"""
Mobile Lianjia Daily Scraper - Production automation system
Based on CaoZ/Fast-LianJia-Crawler approach with mobile API
"""

import asyncio
import logging
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.config_loader import load_config
from utils.http_helpers import test_mobile_api_connection
from command.metrics_tracker import MetricsTracker


class MobileLianjiaDailyScraper:
    def __init__(self):
        self.config = load_config('mobile_lianjia.yaml')
        self.metrics = MetricsTracker('mobile_lianjia_daily')
        self.log_file = Path('logs') / f'mobile_lianjia_daily_{datetime.now().strftime("%Y%m%d")}.log'
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('MobileLianjiaScraper')
        
    async def test_mobile_api(self):
        """Test mobile API connectivity and authentication"""
        self.logger.info("🔍 Testing mobile API connectivity...")
        
        test_result = await test_mobile_api_connection(
            endpoint=self.config['auth_test']['endpoint'],
            city_id=self.config['auth_test']['city_id'],
            app_config=self.config['mobile_config']
        )
        
        if test_result['success']:
            self.logger.info("✅ Mobile API authentication successful")
            return True
        else:
            self.logger.error(f"❌ Mobile API test failed: {test_result['error']}")
            return False
    
    async def run_city_scraper(self, city, mode='communities'):
        """Run scraper for a specific city"""
        start_time = time.time()
        
        self.logger.info(f"🏙️ Starting {city} scraping in {mode} mode...")
        
        try:
            # Build command
            cmd = [
                'python', '-m', 'scrapy', 'crawl', 'mobile_lianjia',
                '-a', f'city={city}',
                '-a', f'mode={mode}',
                '-s', 'LOG_LEVEL=INFO',
                '-o', f'output/mobile_lianjia_{city}_{mode}_{datetime.now().strftime("%Y%m%d")}.json'
            ]
            
            # Run spider
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            stdout, stderr = process.communicate()
            duration = time.time() - start_time
            
            if process.returncode == 0:
                # Parse output for metrics
                items_scraped = self.extract_item_count(stdout)
                
                self.logger.info(f"✅ {city} completed: {items_scraped} items in {duration:.1f}s")
                
                # Update metrics
                await self.metrics.record_scraping_session({
                    'spider': 'mobile_lianjia',
                    'city': city,
                    'mode': mode,
                    'items_scraped': items_scraped,
                    'duration': duration,
                    'success': True,
                    'timestamp': datetime.now().isoformat()
                })
                
                return {'success': True, 'items': items_scraped, 'duration': duration}
                
            else:
                self.logger.error(f"❌ {city} failed: {stderr}")
                
                await self.metrics.record_scraping_session({
                    'spider': 'mobile_lianjia',
                    'city': city,
                    'mode': mode,
                    'success': False,
                    'error': stderr[:200],
                    'timestamp': datetime.now().isoformat()
                })
                
                return {'success': False, 'error': stderr}
                
        except Exception as e:
            self.logger.error(f"❌ Exception during {city} scraping: {e}")
            return {'success': False, 'error': str(e)}
    
    def extract_item_count(self, output):
        """Extract item count from scrapy output"""
        for line in output.split('\n'):
            if 'item_scraped_count' in line:
                try:
                    return int(line.split('item_scraped_count')[1].split()[0].strip(':'))
                except:
                    continue
        return 0
    
    async def run_daily_cycle(self, mode='communities'):
        """Run daily scraping cycle for all cities"""
        self.logger.info("🚀 Starting Mobile Lianjia daily scraping cycle...")
        
        # Test API first
        if not await self.test_mobile_api():
            self.logger.error("❌ API test failed, aborting daily cycle")
            return
        
        cities = list(self.config['cities'].keys())
        results = {}
        
        start_time = time.time()
        total_items = 0
        successful_cities = 0
        
        for i, city in enumerate(cities, 1):
            self.logger.info(f"📍 Processing city {i}/{len(cities)}: {city}")
            
            result = await self.run_city_scraper(city, mode)
            results[city] = result
            
            if result['success']:
                successful_cities += 1
                total_items += result.get('items', 0)
            
            # Rate limiting between cities
            if i < len(cities):
                await asyncio.sleep(2)
        
        total_duration = time.time() - start_time
        
        # Final summary
        self.logger.info("📊 Daily cycle completed!")
        self.logger.info(f"✅ Successful cities: {successful_cities}/{len(cities)}")
        self.logger.info(f"📦 Total items scraped: {total_items}")
        self.logger.info(f"⏱️ Total duration: {total_duration:.1f}s")
        
        # Save summary
        summary = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'mode': mode,
            'total_cities': len(cities),
            'successful_cities': successful_cities,
            'total_items': total_items,
            'total_duration': total_duration,
            'city_results': results,
            'api_approach': 'mobile_api'
        }
        
        summary_file = Path('output') / f'mobile_lianjia_daily_summary_{datetime.now().strftime("%Y%m%d")}.json'
        summary_file.parent.mkdir(exist_ok=True)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary
    
    async def run_community_details_cycle(self):
        """Run detailed community information scraping"""
        self.logger.info("🔍 Starting community details scraping cycle...")
        return await self.run_daily_cycle(mode='details')
    
    async def run_priority_cities(self, priority_cities=None):
        """Run scraping for priority cities only"""
        if priority_cities is None:
            priority_cities = ['beijing', 'shanghai', 'guangzhou', 'shenzhen']
        
        self.logger.info(f"⭐ Running priority cities: {priority_cities}")
        
        results = {}
        for city in priority_cities:
            if city in self.config['cities']:
                result = await self.run_city_scraper(city, 'communities')
                results[city] = result
            else:
                self.logger.warning(f"⚠️ Priority city {city} not found in config")
        
        return results


async def main():
    """Main function for daily scraper"""
    scraper = MobileLianjiaDailyScraper()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == 'test':
            await scraper.test_mobile_api()
        elif mode == 'priority':
            await scraper.run_priority_cities()
        elif mode == 'details':
            await scraper.run_community_details_cycle()
        elif mode == 'single':
            city = sys.argv[2] if len(sys.argv) > 2 else 'beijing'
            result = await scraper.run_city_scraper(city)
            print(json.dumps(result, indent=2))
        else:
            await scraper.run_daily_cycle(mode)
    else:
        # Default: run communities mode
        await scraper.run_daily_cycle('communities')


if __name__ == '__main__':
    # Create necessary directories
    Path('logs').mkdir(exist_ok=True)
    Path('output').mkdir(exist_ok=True)
    
    asyncio.run(main())
