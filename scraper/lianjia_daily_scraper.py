#!/usr/bin/env python3
"""
Lianjia Daily Scraper - Integrate with existing daily scraper system
"""
import subprocess
import sys
import os
from datetime import datetime
import json

class LianjiaDaily:
    def __init__(self):
        self.cities = ['beijing', 'shanghai', 'shenzhen', 'guangzhou']
        self.output_dir = 'daily_output'
        self.date_str = datetime.now().strftime('%Y-%m-%d')
        
    def run_daily_scrape(self, max_items_per_city=50):
        """Run daily scrape for all cities"""
        print('🕷️  LIANJIA DAILY SCRAPER')
        print(f'📅 Date: {self.date_str}')
        print('=' * 50)
        
        all_results = []
        
        for city in self.cities:
            print(f'🏙️  Scraping {city}...')
            results = self.scrape_city(city, max_items_per_city)
            if results:
                all_results.extend(results)
                print(f'✅ {city}: {len(results)} properties found')
            else:
                print(f'⚠️  {city}: No properties found')
        
        # Save combined results
        if all_results:
            output_file = os.path.join(self.output_dir, f'lianjia_{self.date_str}.json')
            os.makedirs(self.output_dir, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            
            print(f'📊 Total properties scraped: {len(all_results)}')
            print(f'💾 Results saved to: {output_file}')
        else:
            print('❌ No properties found in any city')
    
    def scrape_city(self, city, max_items=50):
        """Scrape properties for a specific city"""
        try:
            output_file = f'temp_{city}_output.json'
            
            cmd = [
                sys.executable, '-m', 'scrapy', 'crawl', 'lianjia_spider',
                '-a', f'city={city}',
                '-a', 'property_type=ershoufang',
                '-s', f'CLOSESPIDER_ITEMCOUNT={max_items}',
                '-o', output_file,
                '-L', 'ERROR'  # Only show errors to reduce noise
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0 and os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Clean up temp file
                os.remove(output_file)
                
                return data if isinstance(data, list) else []
            else:
                if os.path.exists(output_file):
                    os.remove(output_file)
                return []
                
        except Exception as e:
            print(f'❌ Error scraping {city}: {e}')
            return []

def main():
    scraper = LianjiaDaily()
    scraper.run_daily_scrape(max_items_per_city=20)  # Limit for testing

if __name__ == "__main__":
    main()
