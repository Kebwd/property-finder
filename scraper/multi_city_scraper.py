#!/usr/bin/env python3
"""
Multi-City Property Scraper for Chinese Cities
Supports all major cities and regions as specified by user
"""
import subprocess
import sys
import os
from datetime import datetime
import json
import yaml
import concurrent.futures
from threading import Lock
import time

class MultiCityPropertyScraper:
    def __init__(self):
        # Load city configuration
        config_path = os.path.join('config', 'lianjia.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.cities = self.config['cities']
        self.output_dir = 'daily_output'
        self.date_str = datetime.now().strftime('%Y-%m-%d')
        self.results_lock = Lock()
        self.all_results = []
        
        # Priority cities (major ones to scrape first)
        self.priority_cities = [
            'beijing', 'shanghai', 'shenzhen', 'guangzhou', 
            'chongqing', 'wuhan', 'xiamen', 'foshan'
        ]
        
        # Secondary cities
        self.secondary_cities = [
            'dongguan', 'zhuhai', 'zhongshan', 'huizhou', 
            'jiangmen', 'fuzhou', 'quanzhou'
        ]
    
    def run_comprehensive_scrape(self, max_items_per_city=30, max_workers=3):
        """Run comprehensive scrape across all cities"""
        print('🌏 MULTI-CITY PROPERTY SCRAPER')
        print(f'📅 Date: {self.date_str}')
        print(f'🏙️  Total cities: {len(self.cities)}')
        print('=' * 60)
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Scrape priority cities first
        print('🚀 Phase 1: Priority Cities')
        self.scrape_city_batch(self.priority_cities, max_items_per_city, max_workers)
        
        # Then scrape secondary cities
        print('\n🔄 Phase 2: Secondary Cities')
        self.scrape_city_batch(self.secondary_cities, max_items_per_city, max_workers)
        
        # Save results
        self.save_results()
        
        # Generate summary report
        self.generate_summary_report()
    
    def scrape_city_batch(self, city_list, max_items_per_city, max_workers):
        """Scrape a batch of cities with threading"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit scraping tasks
            future_to_city = {
                executor.submit(self.scrape_single_city, city, max_items_per_city): city 
                for city in city_list if city in self.cities
            }
            
            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_city):
                city = future_to_city[future]
                try:
                    results = future.result()
                    if results:
                        with self.results_lock:
                            self.all_results.extend(results)
                        print(f'✅ {city}: {len(results)} properties')
                    else:
                        print(f'⚠️  {city}: No properties found')
                except Exception as e:
                    print(f'❌ {city}: Error - {str(e)}')
    
    def scrape_single_city(self, city, max_items=30):
        """Scrape properties for a single city"""
        if city not in self.cities:
            print(f'⚠️  City {city} not configured')
            return []
        
        city_config = self.cities[city]
        print(f'🕷️  Scraping {city_config["name"]}...')
        
        try:
            # Create temporary output file
            output_file = f'temp_{city}_{int(time.time())}.json'
            
            # Build scrapy command
            cmd = [
                sys.executable, '-m', 'scrapy', 'crawl', 'lianjia_spider',
                '-a', f'city={city}',
                '-a', 'property_type=ershoufang',
                '-s', f'CLOSESPIDER_ITEMCOUNT={max_items}',
                '-s', 'DOWNLOAD_DELAY=3',  # Respectful delay
                '-s', 'RANDOMIZE_DOWNLOAD_DELAY=0.5',
                '-o', output_file,
                '-L', 'ERROR'  # Reduce log noise
            ]
            
            # Run scraper with timeout
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=os.getcwd(),
                timeout=300  # 5 minute timeout per city
            )
            
            # Load results
            if result.returncode == 0 and os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Add city metadata to each property
                if isinstance(data, list):
                    for item in data:
                        item['scraped_city'] = city
                        item['scraped_province'] = city_config.get('province', '未知省份')
                        item['scraped_timestamp'] = datetime.now().isoformat()
                
                # Clean up temp file
                os.remove(output_file)
                
                return data if isinstance(data, list) else []
            else:
                # Clean up temp file if exists
                if os.path.exists(output_file):
                    os.remove(output_file)
                return []
                
        except subprocess.TimeoutExpired:
            print(f'⏰ {city}: Timeout after 5 minutes')
            return []
        except Exception as e:
            print(f'❌ {city}: Exception - {str(e)}')
            return []
    
    def save_results(self):
        """Save all results to files"""
        if not self.all_results:
            print('❌ No properties found across all cities')
            return
        
        # Save by date
        main_output = os.path.join(self.output_dir, f'multi_city_{self.date_str}.json')
        with open(main_output, 'w', encoding='utf-8') as f:
            json.dump(self.all_results, f, ensure_ascii=False, indent=2)
        
        # Save latest copy
        latest_output = os.path.join(self.output_dir, 'latest_multi_city.json')
        with open(latest_output, 'w', encoding='utf-8') as f:
            json.dump(self.all_results, f, ensure_ascii=False, indent=2)
        
        print(f'💾 Results saved to: {main_output}')
        print(f'📊 Total properties scraped: {len(self.all_results)}')
    
    def generate_summary_report(self):
        """Generate summary report by city and province"""
        if not self.all_results:
            return
        
        # Group by city
        city_stats = {}
        province_stats = {}
        
        for item in self.all_results:
            city = item.get('scraped_city', 'unknown')
            province = item.get('scraped_province', 'unknown')
            
            # City stats
            if city not in city_stats:
                city_stats[city] = {'count': 0, 'total_value': 0}
            city_stats[city]['count'] += 1
            city_stats[city]['total_value'] += item.get('deal_price', 0)
            
            # Province stats
            if province not in province_stats:
                province_stats[province] = {'count': 0, 'cities': set()}
            province_stats[province]['count'] += 1
            province_stats[province]['cities'].add(city)
        
        # Print summary
        print('\n📈 SCRAPING SUMMARY REPORT')
        print('=' * 50)
        
        print('🏙️  By City:')
        for city, stats in sorted(city_stats.items(), key=lambda x: x[1]['count'], reverse=True):
            city_name = self.cities.get(city, {}).get('name', city)
            avg_price = stats['total_value'] / stats['count'] if stats['count'] > 0 else 0
            print(f'   {city_name}: {stats["count"]} properties (avg: ¥{avg_price:,.0f})')
        
        print('\n🗺️  By Province:')
        for province, stats in sorted(province_stats.items(), key=lambda x: x[1]['count'], reverse=True):
            cities_list = ', '.join([self.cities.get(c, {}).get('name', c) for c in stats['cities']])
            print(f'   {province}: {stats["count"]} properties from {len(stats["cities"])} cities')
            print(f'      Cities: {cities_list}')
        
        # Save summary to file
        summary_file = os.path.join(self.output_dir, f'summary_{self.date_str}.json')
        summary_data = {
            'date': self.date_str,
            'total_properties': len(self.all_results),
            'cities_scraped': len(city_stats),
            'provinces_covered': len(province_stats),
            'city_breakdown': city_stats,
            'province_breakdown': {k: {'count': v['count'], 'cities': list(v['cities'])} for k, v in province_stats.items()}
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        print(f'\n📋 Summary saved to: {summary_file}')

def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-City Property Scraper')
    parser.add_argument('--max-items', type=int, default=20, help='Max items per city (default: 20)')
    parser.add_argument('--max-workers', type=int, default=2, help='Max concurrent workers (default: 2)')
    parser.add_argument('--cities', nargs='+', help='Specific cities to scrape (default: all)')
    
    args = parser.parse_args()
    
    scraper = MultiCityPropertyScraper()
    
    if args.cities:
        # Scrape specific cities only
        print(f'🎯 Scraping specific cities: {args.cities}')
        scraper.scrape_city_batch(args.cities, args.max_items, args.max_workers)
        scraper.save_results()
        scraper.generate_summary_report()
    else:
        # Scrape all cities
        scraper.run_comprehensive_scrape(args.max_items, args.max_workers)

if __name__ == "__main__":
    main()
