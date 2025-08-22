import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import random
import json
from fake_useragent import UserAgent
from urllib.parse import urljoin, urlparse
import asyncio
import aiohttp
from datetime import datetime

class AdvancedPropertyScraper:
    """
    Advanced property scraper with multiple evasion techniques
    Uses stealth mode, proxy rotation, and smart request patterns
    """
    
    def __init__(self, use_stealth=True):
        self.use_stealth = use_stealth
        self.session = requests.Session()
        self.ua = UserAgent()
        self.proxies = []
        self.setup_session()
        
    def setup_session(self):
        """Configure session with rotating headers and proxies"""
        # Base headers that mimic real browsers
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
    
    def get_stealth_driver(self):
        """Create undetected Chrome driver with stealth configuration"""
        options = uc.ChromeOptions()
        
        # Stealth options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Random window size
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        options.add_argument(f'--window-size={width},{height}')
        
        # Random user agent
        options.add_argument(f'--user-agent={self.ua.random}')
        
        driver = uc.Chrome(options=options)
        
        # Execute stealth script
        stealth(driver,
                languages=["zh-CN", "zh", "en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
        
        return driver
    
    def get_random_headers(self):
        """Generate random headers for each request"""
        headers = self.base_headers.copy()
        headers['User-Agent'] = self.ua.random
        
        # Add random additional headers sometimes
        if random.random() > 0.5:
            headers['Sec-Fetch-Dest'] = random.choice(['document', 'empty'])
            headers['Sec-Fetch-Mode'] = random.choice(['navigate', 'cors'])
            headers['Sec-Fetch-Site'] = random.choice(['none', 'same-origin'])
        
        return headers
    
    def smart_delay(self, min_delay=2, max_delay=8):
        """Human-like random delays"""
        delay = random.uniform(min_delay, max_delay)
        # Add occasional longer pauses (simulating reading)
        if random.random() > 0.9:
            delay += random.uniform(5, 15)
        
        print(f"⏱️  Waiting {delay:.1f} seconds...")
        time.sleep(delay)
    
    def scrape_regional_sites(self, city='guangzhou'):
        """Scrape regional property sites for specific city"""
        print(f"🏙️  SCRAPING REGIONAL SITES FOR {city.upper()}")
        print("=" * 50)
        
        # Regional site configurations
        regional_configs = {
            'guangzhou': {
                'sites': [
                    {
                        'name': 'NetEase Guangzhou',
                        'url': 'http://gz.house.163.com/search/',
                        'selectors': {
                            'listings': '.search-item',
                            'title': '.item-title a',
                            'price': '.item-price',
                            'area': '.item-area',
                            'location': '.item-location'
                        }
                    },
                    {
                        'name': 'Guangzhou Focus',
                        'url': 'http://gz.jiaodian.com/newhouse/',
                        'selectors': {
                            'listings': '.house-item',
                            'title': '.house-title',
                            'price': '.house-price',
                            'area': '.house-area',
                            'location': '.house-location'
                        }
                    }
                ]
            },
            'beijing': {
                'sites': [
                    {
                        'name': 'Beijing Focus',
                        'url': 'http://bj.jiaodian.com/newhouse/',
                        'selectors': {
                            'listings': '.house-item',
                            'title': '.house-title',
                            'price': '.house-price',
                            'area': '.house-area',
                            'location': '.house-location'
                        }
                    }
                ]
            }
        }
        
        if city not in regional_configs:
            print(f"❌ No regional sites configured for {city}")
            return []
        
        all_properties = []
        
        for site_config in regional_configs[city]['sites']:
            print(f"\n🔍 Scraping: {site_config['name']}")
            print(f"🔗 URL: {site_config['url']}")
            
            try:
                properties = self.scrape_single_site(site_config)
                all_properties.extend(properties)
                print(f"✅ Found {len(properties)} properties")
                
                # Smart delay between sites
                self.smart_delay(5, 12)
                
            except Exception as e:
                print(f"❌ Error scraping {site_config['name']}: {e}")
                continue
        
        return all_properties
    
    def scrape_single_site(self, site_config):
        """Scrape a single property site"""
        properties = []
        
        try:
            # Method 1: Try simple requests first (faster)
            properties = self.scrape_with_requests(site_config)
            
            if len(properties) == 0:
                print("🤖 Requests failed, trying stealth browser...")
                # Method 2: Use stealth browser if requests fail
                properties = self.scrape_with_stealth_browser(site_config)
                
        except Exception as e:
            print(f"⚠️ Scraping error: {e}")
        
        return properties
    
    def scrape_with_requests(self, site_config):
        """Fast scraping with requests library"""
        properties = []
        
        headers = self.get_random_headers()
        response = self.session.get(site_config['url'], headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check for anti-bot indicators
            page_text = soup.get_text().lower()
            if any(indicator in page_text for indicator in ['验证码', 'captcha', 'blocked', '访问被拒绝']):
                raise Exception("Anti-bot protection detected")
            
            # Extract property listings
            listings = soup.select(site_config['selectors']['listings'])
            
            for listing in listings:
                property_data = self.extract_property_from_element(listing, site_config)
                if property_data:
                    properties.append(property_data)
        
        return properties
    
    def scrape_with_stealth_browser(self, site_config):
        """Advanced scraping with undetected Chrome"""
        properties = []
        driver = None
        
        try:
            driver = self.get_stealth_driver()
            
            # Navigate to site with human-like behavior
            driver.get(site_config['url'])
            
            # Wait for page load and add random mouse movements
            self.simulate_human_behavior(driver)
            
            # Wait for content to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Random scroll to trigger any lazy loading
            self.random_scroll(driver)
            
            # Extract properties
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            listings = soup.select(site_config['selectors']['listings'])
            
            for listing in listings:
                property_data = self.extract_property_from_element(listing, site_config)
                if property_data:
                    properties.append(property_data)
            
        finally:
            if driver:
                driver.quit()
        
        return properties
    
    def simulate_human_behavior(self, driver):
        """Simulate human browsing patterns"""
        # Random wait time
        time.sleep(random.uniform(2, 5))
        
        # Simulate scrolling behavior
        for _ in range(random.randint(1, 3)):
            scroll_height = random.randint(200, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_height});")
            time.sleep(random.uniform(0.5, 2))
        
        # Return to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(random.uniform(1, 3))
    
    def random_scroll(self, driver):
        """Random scrolling to trigger lazy loading"""
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        current_position = 0
        while current_position < total_height:
            # Random scroll distance
            scroll_distance = random.randint(viewport_height // 3, viewport_height)
            current_position += scroll_distance
            
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 2))
    
    def extract_property_from_element(self, element, site_config):
        """Extract property data from HTML element"""
        try:
            selectors = site_config['selectors']
            
            # Extract basic fields
            title_elem = element.select_one(selectors['title'])
            price_elem = element.select_one(selectors['price'])
            area_elem = element.select_one(selectors['area'])
            location_elem = element.select_one(selectors['location'])
            
            if not title_elem:
                return None
            
            title = title_elem.get_text().strip()
            price_text = price_elem.get_text().strip() if price_elem else ''
            area_text = area_elem.get_text().strip() if area_elem else ''
            location = location_elem.get_text().strip() if location_elem else ''
            
            # Parse price and area
            deal_price = self.parse_price(price_text)
            area = self.parse_area(area_text)
            
            return {
                'building_name_zh': title,
                'deal_price': deal_price,
                'area': area,
                'location': location,
                'zone': 'China',
                'city': self.extract_city_from_location(location),
                'province': '广东省',  # Adjust based on site
                'type_raw': '住宅',
                'type': '住宅',
                'deal_date': datetime.now().strftime('%Y-%m-%d'),
                'source_url': site_config['url'],
                'data_source': site_config['name'],
                'scraped_city': 'guangzhou',
                'start_url': site_config['url']
            }
            
        except Exception as e:
            print(f"⚠️ Error extracting property: {e}")
            return None
    
    def parse_price(self, price_text):
        """Parse price from Chinese text"""
        if not price_text:
            return 0
        
        try:
            # Handle different price formats
            import re
            
            # Remove all non-numeric characters except 万, 元, and decimal points
            clean_price = re.sub(r'[^\d万元.]', '', price_text)
            
            if '万' in clean_price:
                # Convert 万 to actual number
                price_match = re.search(r'(\d+\.?\d*)', clean_price)
                if price_match:
                    price_num = float(price_match.group(1))
                    return int(price_num * 10000)
            
            # Try to extract any number
            price_match = re.search(r'(\d+)', clean_price)
            if price_match:
                return int(price_match.group(1))
                
        except:
            pass
        
        return 0
    
    def parse_area(self, area_text):
        """Parse area from text"""
        if not area_text:
            return 0
        
        try:
            import re
            area_match = re.search(r'(\d+\.?\d*)', area_text)
            if area_match:
                return float(area_match.group(1))
        except:
            pass
        
        return 0
    
    def extract_city_from_location(self, location):
        """Extract city name from location string"""
        city_mapping = {
            '广州': '广州',
            '深圳': '深圳',
            '佛山': '佛山',
            '东莞': '东莞',
            '北京': '北京',
            '上海': '上海'
        }
        
        for key, value in city_mapping.items():
            if key in location:
                return value
        
        return '未知城市'
    
    async def async_scrape_multiple_sites(self, cities):
        """Asynchronously scrape multiple cities"""
        tasks = []
        
        for city in cities:
            task = asyncio.create_task(self.async_scrape_city(city))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def async_scrape_city(self, city):
        """Async scraping for a single city"""
        # Implementation for async scraping
        pass

def main():
    """Test the advanced scraper"""
    print("🕷️  ADVANCED PROPERTY SCRAPER TEST")
    print("=" * 50)
    
    scraper = AdvancedPropertyScraper(use_stealth=True)
    
    # Test cities
    test_cities = ['guangzhou', 'beijing']
    
    all_results = []
    
    for city in test_cities:
        print(f"\n🏙️ Testing {city.upper()}...")
        try:
            properties = scraper.scrape_regional_sites(city)
            all_results.extend(properties)
            print(f"✅ {city}: Found {len(properties)} properties")
        except Exception as e:
            print(f"❌ {city}: Error - {e}")
    
    # Save results
    if all_results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'advanced_scraping_results_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 SCRAPING COMPLETE")
        print(f"📊 Total properties: {len(all_results)}")
        print(f"💾 Results saved to: {filename}")
    else:
        print(f"\n⚠️ No properties found - try different sites or methods")

if __name__ == "__main__":
    main()
