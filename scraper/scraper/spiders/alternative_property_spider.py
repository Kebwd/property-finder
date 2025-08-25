import scrapy
try:
    from scrapy_selenium import SeleniumRequest
    SELENIUM_AVAILABLE = True
except ImportError:
    print("⚠️ scrapy-selenium not available. Install with: pip install scrapy-selenium")
    SELENIUM_AVAILABLE = False
    SeleniumRequest = None

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import yaml
import os
import re
from urllib.parse import urljoin
import time
import random

class AlternativePropertySpider(scrapy.Spider):
    name = "alternative_property_spider"
    
    def __init__(self, site='58', city='beijing', *args, **kwargs):
        super(AlternativePropertySpider, self).__init__(*args, **kwargs)
        self.site = site  # '58', 'anjuke', or 'fang'
        self.city = city
        
        # Load alternative sites configuration
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'alternative_sites.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Set up site configuration
        site_key = f'site_{site}' if site == '58' else site
        if site_key not in self.config['alternative_property_sites']:
            raise ValueError(f"Site {site} not supported")
        
        self.site_config = self.config['alternative_property_sites'][site_key]
        
        if city not in self.site_config['cities']:
            raise ValueError(f"City {city} not supported for site {site}")
        
        self.city_config = self.site_config['cities'][city]
        self.selectors = self.city_config['selectors']
        
        # Set start URLs
        self.start_urls = [self.city_config['url']]
    
    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse,
                wait_time=8,
                wait_until=EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
    
    def parse(self, response):
        """Parse property listing pages"""
        self.logger.info(f"🕷️  Parsing {self.site_config['name']} - {response.url}")
        
        # Extract property listings using configured selectors
        properties = response.xpath(self.selectors['property_list'])
        self.logger.info(f"📊 Found {len(properties)} properties on page")
        
        for property_element in properties:
            property_data = self.extract_property_data(property_element, response)
            if property_data:
                yield property_data
        
        # Handle pagination (basic implementation)
        next_page = response.xpath("//a[contains(@class, 'next') or contains(text(), '下一页')]/@href").get()
        if next_page:
            next_url = urljoin(response.url, next_page)
            self.logger.info(f"➡️  Following pagination: {next_url}")
            yield SeleniumRequest(
                url=next_url,
                callback=self.parse,
                wait_time=8
            )
    
    def extract_property_data(self, property_element, response):
        """Extract property data from listing element"""
        try:
            # Extract fields using configured selectors
            title = property_element.xpath(self.selectors['title']).get()
            price_text = property_element.xpath(self.selectors['price']).get()
            area_text = property_element.xpath(self.selectors['area']).get()
            location = property_element.xpath(self.selectors['location']).get()
            
            if not title:
                return None
            
            # Parse price and area
            deal_price = self.parse_price(price_text)
            area = self.parse_area(area_text)
            
            # Create property data
            property_data = {
                'building_name_zh': title.strip() if title else '',
                'deal_price': deal_price,
                'area': area,
                'location': location.strip() if location else '',
                'zone': 'China',
                'city': self.get_city_name(),
                'province': self.get_province_name(),
                'type_raw': '住宅',
                'type': ['住宅'],
                'deal_date': self.get_current_date(),
                'source_url': response.url,
                'data_source': self.site_config['name'],
                'scraped_city': self.city,
                'start_url': response.url,
            }
            
            return property_data
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting property data: {e}")
            return None
    
    def parse_price(self, price_text):
        """Parse price from text"""
        if not price_text:
            return 0
        
        try:
            # Remove non-numeric characters except 万
            price_clean = re.sub(r'[^\d万.]', '', price_text)
            
            if '万' in price_clean:
                # Convert 万 to actual number  
                price_num = float(price_clean.replace('万', ''))
                return int(price_num * 10000)
            else:
                # Try to extract any number
                numbers = re.findall(r'\d+', price_clean)
                if numbers:
                    return int(numbers[0])
        except:
            pass
        return 0
    
    def parse_area(self, area_text):
        """Parse area from text"""
        if not area_text:
            return 0
        
        try:
            # Extract numeric part
            area_match = re.search(r'(\d+\.?\d*)', area_text)
            if area_match:
                return float(area_match.group(1))
        except:
            pass
        return 0
    
    def get_city_name(self):
        """Get Chinese city name"""
        city_names = {
            'beijing': '北京',
            'shanghai': '上海',
            'shenzhen': '深圳',
            'guangzhou': '广州',
            'foshan': '佛山',
            'dongguan': '东莞'
        }
        return city_names.get(self.city, self.city)
    
    def get_province_name(self):
        """Get province name"""
        province_mapping = {
            'beijing': '北京市',
            'shanghai': '上海市',
            'shenzhen': '广东省',
            'guangzhou': '广东省',
            'foshan': '广东省',
            'dongguan': '广东省'
        }
        return province_mapping.get(self.city, '未知省份')
    
    def get_current_date(self):
        """Get current date"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')
