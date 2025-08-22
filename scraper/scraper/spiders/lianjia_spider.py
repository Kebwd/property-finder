import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import yaml
import os
import re
from urllib.parse import urljoin, urlparse
import time
import random

class LianjiaSpider(scrapy.Spider):
    name = "lianjia_spider"
    
    def __init__(self, city='beijing', property_type='ershoufang', *args, **kwargs):
        super(LianjiaSpider, self).__init__(*args, **kwargs)
        self.city = city
        self.property_type = property_type  # 'ershoufang' or 'zufang'
        
        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'lianjia.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Set up city configuration
        if city not in self.config['cities']:
            raise ValueError(f"City {city} not supported. Available cities: {list(self.config['cities'].keys())}")
        
        self.city_config = self.config['cities'][city]
        self.selectors = self.config['selectors']
        self.field_mappings = self.config['field_mappings']
        self.type_mappings = self.config['type_mappings']
        
        # Set start URLs
        if property_type == 'ershoufang':
            self.start_urls = [self.city_config['ershoufang_url']]
        else:
            self.start_urls = [self.city_config['zufang_url']]
    
    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse,
                wait_time=10,
                wait_until=EC.presence_of_element_located((By.CSS_SELECTOR, "ul.sellListContent"))
            )
    
    def parse(self, response):
        """Parse property listing pages"""
        self.logger.info(f"🕷️  Parsing Lianjia page: {response.url}")
        
        # Extract property listings
        properties = response.xpath(self.selectors['property_list'])
        self.logger.info(f"📊 Found {len(properties)} properties on page")
        
        for property_element in properties:
            # Extract basic property data
            property_data = self.extract_property_data(property_element, response)
            
            if property_data:
                # Get detailed property information
                property_url = property_data.get('property_url')
                if property_url:
                    yield SeleniumRequest(
                        url=urljoin(response.url, property_url),
                        callback=self.parse_property_detail,
                        meta={'property_data': property_data},
                        wait_time=5
                    )
        
        # Handle pagination
        next_page = response.xpath(self.selectors['next_page']).get()
        if next_page:
            next_url = urljoin(response.url, next_page)
            self.logger.info(f"➡️  Following pagination: {next_url}")
            yield SeleniumRequest(
                url=next_url,
                callback=self.parse,
                wait_time=10,
                wait_until=EC.presence_of_element_located((By.CSS_SELECTOR, "ul.sellListContent"))
            )
    
    def extract_property_data(self, property_element, response):
        """Extract property data from listing element"""
        try:
            # Extract basic fields
            title = property_element.xpath(self.selectors['title']).get()
            price_text = property_element.xpath(self.selectors['price']).get()
            area_text = property_element.xpath(self.selectors['area']).get()
            location = property_element.xpath(self.selectors['location']).get()
            district = property_element.xpath(self.selectors['district']).get()
            property_url = property_element.xpath(self.selectors['property_url']).get()
            
            if not title or not price_text:
                return None
            
            # Parse price (convert 万 to actual number)
            deal_price = self.parse_price(price_text)
            
            # Parse area
            area = self.parse_area(area_text)
            
            # Basic property data
            property_data = {
                'title': title.strip() if title else '',
                'deal_price': deal_price,
                'area': area,
                'location': location.strip() if location else '',
                'district': district.strip() if district else '',
                'property_url': property_url,
                'zone': 'China',
                'city': self.city_config['name'],
                'province': self.get_province_by_city(self.city),
                'source_url': property_url,
            }
            
            return property_data
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting property data: {e}")
            return None
    
    def parse_property_detail(self, response):
        """Parse detailed property information"""
        property_data = response.meta['property_data']
        
        try:
            # Extract detailed information
            building_name = response.xpath(self.selectors['building_name']).get()
            floor_info = response.xpath(self.selectors['floor']).get()
            property_type = response.xpath(self.selectors['detail_type']).get()
            year_built = response.xpath(self.selectors['year_built']).get()
            
            # Update property data with detailed info
            property_data.update({
                'building_name_zh': building_name.strip() if building_name else property_data.get('title', ''),
                'floor': self.parse_floor(floor_info),
                'type_raw': property_type.strip() if property_type else '住宅',
                'type': self.map_property_type(property_type),
                'deal_date': self.get_current_date(),
                'developer': '',
                'start_url': response.url,
            })
            
            # Normalize and validate data
            normalized_data = self.normalize_property_data(property_data)
            
            if self.validate_property_data(normalized_data):
                self.logger.info(f"✅ Extracted property: {normalized_data.get('building_name_zh', 'Unknown')}")
                yield normalized_data
            else:
                self.logger.warning(f"⚠️  Invalid property data, skipping")
                
        except Exception as e:
            self.logger.error(f"❌ Error parsing property detail: {e}")
    
    def parse_price(self, price_text):
        """Parse price from text (e.g., '300万' -> 3000000)"""
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
                return int(float(price_clean))
        except:
            return 0
    
    def parse_area(self, area_text):
        """Parse area from text (e.g., '89.5平米' -> 89.5)"""
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
    
    def parse_floor(self, floor_info):
        """Parse floor information"""
        if not floor_info:
            return ''
        
        # Extract floor number and level (e.g., "中楼层(共32层)" -> "中层")
        floor_match = re.search(r'(高|中|低).*?层', floor_info)
        if floor_match:
            return floor_match.group(1) + '层'
        
        return floor_info.strip()
    
    def map_property_type(self, property_type):
        """Map property type using type_mappings"""
        if not property_type:
            return ['住宅']
        
        property_type = property_type.strip()
        
        for mapped_type, variations in self.type_mappings.items():
            if property_type in variations or property_type == mapped_type:
                return [mapped_type]
        
        return [property_type]
    
    def get_province_by_city(self, city):
        """Get province name by city"""
        province_mapping = {
            'beijing': '北京市',
            'shanghai': '上海市', 
            'shenzhen': '广东省',
            'guangzhou': '广东省',
        }
        return province_mapping.get(city, '未知省份')
    
    def get_current_date(self):
        """Get current date in YYYY-MM-DD format"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')
    
    def normalize_property_data(self, property_data):
        """Normalize property data to match database schema"""
        normalized = {}
        
        for db_field, source_field in self.field_mappings.items():
            if source_field in property_data:
                normalized[db_field] = property_data[source_field]
        
        # Add any additional fields
        for key, value in property_data.items():
            if key not in normalized:
                normalized[key] = value
        
        return normalized
    
    def validate_property_data(self, property_data):
        """Validate property data before yielding"""
        required_fields = ['building_name_zh', 'deal_price', 'deal_date']
        
        for field in required_fields:
            if not property_data.get(field):
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        if property_data.get('deal_price', 0) <= 0:
            self.logger.warning("Invalid price")
            return False
        
        return True
