#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced Lianjia Daily Scraper
Integrates the waugustus/lianjia-spider approach with existing property-finder infrastructure
"""

import subprocess
import sys
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_lianjia_daily.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedLianjiaDailyScraper:
    """Daily scraper for Lianjia properties using enhanced spider"""
    
    def __init__(self):
        self.scraper_dir = Path(__file__).parent.absolute()
        self.results = {
            'start_time': datetime.now().isoformat(),
            'cities_scraped': [],
            'total_properties': 0,
            'successful_cities': 0,
            'failed_cities': 0,
            'errors': []
        }
        
        # Default configurations (based on waugustus project)
        self.default_configs = {
            'beijing': {
                'city': 'beijing',
                'districts': ['朝阳', '海淀', '西城', '东城'],
                'max_items_per_district': 50,
                'house_types': 'l2l3l4',  # 2-4 bedrooms
                'price_range': {'min': 200, 'max': 1000}  # 200-1000万
            },
            'shanghai': {
                'city': 'shanghai', 
                'districts': ['浦东', '徐汇', '长宁', '静安'],
                'max_items_per_district': 50,
                'house_types': 'l2l3l4',
                'price_range': {'min': 300, 'max': 1200}
            },
            'guangzhou': {
                'city': 'guangzhou',
                'districts': ['天河', '越秀', '海珠', '荔湾'],
                'max_items_per_district': 30,
                'house_types': 'l2l3l4', 
                'price_range': {'min': 150, 'max': 800}
            },
            'shenzhen': {
                'city': 'shenzhen',
                'districts': ['南山', '福田', '罗湖', '宝安'],
                'max_items_per_district': 30,
                'house_types': 'l2l3l4',
                'price_range': {'min': 400, 'max': 1500}
            }
        }

    def scrape_city(self, city_config, city_name):
        """Scrape a single city with all its districts"""
        logger.info(f"🏙️  Starting {city_name} scraping")
        
        city_results = {
            'city': city_name,
            'start_time': datetime.now().isoformat(),
            'districts': [],
            'total_properties': 0,
            'success': False
        }
        
        try:
            # Scrape each district
            for district in city_config['districts']:
                district_result = self.scrape_district(city_config, city_name, district)
                city_results['districts'].append(district_result)
                city_results['total_properties'] += district_result.get('properties_scraped', 0)
            
            # Also scrape city-wide (no district filter) for comparison
            citywide_result = self.scrape_district(city_config, city_name, None, is_citywide=True)
            city_results['citywide'] = citywide_result
            city_results['total_properties'] += citywide_result.get('properties_scraped', 0)
            
            city_results['success'] = True
            city_results['end_time'] = datetime.now().isoformat()
            
            logger.info(f"✅ {city_name} completed: {city_results['total_properties']} properties")
            
        except Exception as e:
            logger.error(f"❌ Error scraping {city_name}: {e}")
            city_results['error'] = str(e)
            city_results['end_time'] = datetime.now().isoformat()
        
        return city_results

    def scrape_district(self, city_config, city_name, district=None, is_citywide=False):
        """Scrape a specific district or citywide"""
        district_name = district or f"{city_name}_citywide"
        max_items = city_config['max_items_per_district']
        
        if is_citywide:
            max_items = max_items // 2  # Fewer items for citywide to avoid duplicates
        
        logger.info(f"📍 Scraping {district_name} (max {max_items} items)")
        
        district_result = {
            'district': district_name,
            'start_time': datetime.now().isoformat(),
            'properties_scraped': 0,
            'success': False
        }
        
        try:
            # Build command (based on waugustus approach)
            command = [
                'python', '-m', 'scrapy', 'crawl', 'enhanced_lianjia',
                '-a', f'city={city_name}',
                '-a', f'house_type={city_config["house_types"]}',
                '-a', f'min_price={city_config["price_range"]["min"]}',
                '-a', f'max_price={city_config["price_range"]["max"]}',
                '-s', f'CLOSESPIDER_ITEMCOUNT={max_items}',
                '-L', 'INFO'
            ]
            
            # Add district filter if specified
            if district and not is_citywide:
                command.extend(['-a', f'district={district}'])
            
            # Run scraper
            logger.info(f"🚀 Running: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes per district
                cwd=self.scraper_dir
            )
            
            # Parse results
            if result.returncode == 0:
                # Extract items scraped
                items_scraped = self.extract_items_scraped(result.stdout)
                district_result['properties_scraped'] = items_scraped
                district_result['success'] = True
                
                logger.info(f"✅ {district_name}: {items_scraped} properties scraped")
            else:
                logger.error(f"❌ {district_name} failed with return code: {result.returncode}")
                if result.stderr:
                    logger.error(f"💥 Error: {result.stderr[:200]}...")
                district_result['error'] = f"Return code: {result.returncode}"
            
        except subprocess.TimeoutExpired:
            logger.warning(f"⏰ {district_name} timed out after 5 minutes")
            district_result['error'] = "Timeout"
        except Exception as e:
            logger.error(f"💥 Error scraping {district_name}: {e}")
            district_result['error'] = str(e)
        
        district_result['end_time'] = datetime.now().isoformat()
        return district_result

    def extract_items_scraped(self, output):
        """Extract number of items scraped from Scrapy output"""
        lines = output.split('\n')
        for line in lines:
            if 'item_scraped_count' in line:
                try:
                    # Extract number from line like "item_scraped_count': 25"
                    count = int(line.split('item_scraped_count')[1].split(':')[1].split('}')[0].strip())
                    return count
                except:
                    continue
        return 0

    def run_daily_scraping(self, cities=None):
        """Run daily scraping for specified cities"""
        if cities is None:
            cities = ['beijing', 'shanghai']  # Default cities
        
        logger.info(f"🚀 Starting Enhanced Lianjia Daily Scraping")
        logger.info(f"🌆 Cities to scrape: {', '.join(cities)}")
        logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        # Scrape each city
        for city in cities:
            if city not in self.default_configs:
                logger.warning(f"⚠️  Unsupported city: {city}")
                continue
            
            try:
                city_config = self.default_configs[city]
                city_result = self.scrape_city(city_config, city)
                
                self.results['cities_scraped'].append(city_result)
                self.results['total_properties'] += city_result['total_properties']
                
                if city_result['success']:
                    self.results['successful_cities'] += 1
                else:
                    self.results['failed_cities'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Failed to scrape {city}: {e}")
                self.results['errors'].append(f"{city}: {str(e)}")
                self.results['failed_cities'] += 1
        
        # Finalize results
        self.results['end_time'] = datetime.now().isoformat()
        
        # Generate summary
        self.generate_summary()
        
        # Save results
        self.save_results()
        
        return self.results

    def generate_summary(self):
        """Generate scraping summary"""
        logger.info("=" * 60)
        logger.info("📊 ENHANCED LIANJIA DAILY SCRAPING SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
        logger.info(f"⏰ Duration: {self.calculate_duration()}")
        logger.info(f"🌆 Cities attempted: {len(self.results['cities_scraped'])}")
        logger.info(f"✅ Successful cities: {self.results['successful_cities']}")
        logger.info(f"❌ Failed cities: {self.results['failed_cities']}")
        logger.info(f"🏠 Total properties scraped: {self.results['total_properties']}")
        
        # City breakdown
        for city_result in self.results['cities_scraped']:
            city_name = city_result['city']
            properties = city_result['total_properties']
            status = "✅" if city_result['success'] else "❌"
            logger.info(f"   {status} {city_name}: {properties} properties")
        
        # Errors
        if self.results['errors']:
            logger.info(f"\n🔥 Errors encountered:")
            for error in self.results['errors']:
                logger.info(f"   💥 {error}")

    def calculate_duration(self):
        """Calculate scraping duration"""
        try:
            start = datetime.fromisoformat(self.results['start_time'])
            end = datetime.fromisoformat(self.results['end_time'])
            duration = end - start
            return str(duration).split('.')[0]  # Remove microseconds
        except:
            return "Unknown"

    def save_results(self):
        """Save results to JSON file"""
        filename = f"enhanced_lianjia_daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Results saved to: {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")

def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='Enhanced Lianjia Daily Scraper')
    parser.add_argument('--cities', nargs='+', 
                       choices=['beijing', 'shanghai', 'guangzhou', 'shenzhen'],
                       default=['beijing', 'shanghai'],
                       help='Cities to scrape (default: beijing shanghai)')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (scrape fewer items)')
    
    args = parser.parse_args()
    
    try:
        scraper = EnhancedLianjiaDailyScraper()
        
        # Modify configs for test mode
        if args.test:
            logger.info("🧪 Running in TEST mode")
            for city in scraper.default_configs:
                scraper.default_configs[city]['max_items_per_district'] = 5
                scraper.default_configs[city]['districts'] = scraper.default_configs[city]['districts'][:2]
        
        # Run scraping
        results = scraper.run_daily_scraping(args.cities)
        
        # Exit with success/failure code
        if results['successful_cities'] > 0:
            logger.info("🎉 Daily scraping completed successfully!")
            sys.exit(0)
        else:
            logger.error("💥 Daily scraping failed - no cities scraped successfully")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
