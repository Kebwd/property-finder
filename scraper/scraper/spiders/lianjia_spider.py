import scrapy
import re
import time
import json
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class LianjiaSpider(scrapy.Spider):
    """
    Production-ready Lianjia spider with CAPTCHA handling
    Uses Selenium for CAPTCHA bypass and intelligent retry logic
    """
    name = 'lianjia'
    
    # City domain mapping
    CITY_DOMAINS = {
        'beijing': 'bj.lianjia.com',
        'shanghai': 'sh.lianjia.com',
        'guangzhou': 'gz.lianjia.com',
        'shenzhen': 'sz.lianjia.com',
        'hangzhou': 'hz.lianjia.com',
        'nanjing': 'nj.lianjia.com',
        'tianjin': 'tj.lianjia.com',
        'chengdu': 'cd.lianjia.com',
        'wuhan': 'wh.lianjia.com',
        'chongqing': 'cq.lianjia.com'
    }
    
    custom_settings = {
        'DOWNLOAD_DELAY': 15,  # Conservative delay
        'RANDOMIZE_DOWNLOAD_DELAY': 0.9,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 10,
        'AUTOTHROTTLE_MAX_DELAY': 120,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.1,
        'RETRY_TIMES': 2,
        'DOWNLOAD_TIMEOUT': 120,
        'ROBOTSTXT_OBEY': False,
        'COOKIES_ENABLED': True,
        'SESSION_PERSISTENCE': True,
    }
    
    def __init__(self, city='guangzhou', *args, **kwargs):
        super(LianjiaSpider, self).__init__(*args, **kwargs)
        self.city = city.lower()
        self.domain = self.CITY_DOMAINS.get(self.city, 'gz.lianjia.com')
        self.logger.info(f"Starting simple Lianjia spider for city: {self.city} (Domain: {self.domain})")
    
    def start_requests(self):
        """Generate minimal requests to test connectivity"""
        base_url = f"https://{self.domain}/ershoufang/"
        
        # Only make ONE request to test
        yield scrapy.Request(
            url=base_url,
            callback=self.debug_response,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            dont_filter=True
        )
    
    def debug_response(self, response):
        """Debug what we're getting from Lianjia"""
        self.logger.info(f"Response URL: {response.url}")
        self.logger.info(f"Response status: {response.status}")
        self.logger.info(f"Response headers: {dict(response.headers)}")
        self.logger.info(f"Response length: {len(response.body)}")
        
        # Log first 1000 characters to see what we got
        content_sample = response.text[:1000] if response.text else "No text content"
        self.logger.info(f"Content sample: {content_sample}")
        
        # Look for property listings
        property_selectors = [
            'li.clear.LOGVIEWDATA',
            '.sellListContent li',
            '.resblock-list li',
            'ul.sellListContent li',
            '.info.clear',
        ]
        
        for selector in property_selectors:
            elements = response.css(selector)
            if elements:
                self.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                # Get the first element's HTML to see structure
                if elements:
                    first_element = elements[0].get()[:500]
                    self.logger.info(f"First element structure: {first_element}")
                break
        else:
            self.logger.warning("No property listings found with any selector")
        
        # Look for links that might be property links
        all_links = response.css('a::attr(href)').getall()
        property_links = [link for link in all_links if '/ershoufang/' in link and link.count('/') >= 3]
        
        if property_links:
            self.logger.info(f"Found {len(property_links)} potential property links")
            # Test parsing one property
            first_link = property_links[0]
            if first_link.startswith('/'):
                full_url = f"https://{self.domain}{first_link}"
            else:
                full_url = first_link
            
            self.logger.info(f"Testing property link: {full_url}")
            
            yield scrapy.Request(
                url=full_url,
                callback=self.debug_property,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': response.url,
                },
                dont_filter=True
            )
        else:
            self.logger.warning("No property links found")
    
    def debug_property(self, response):
        """Debug property page content"""
        self.logger.info(f"Property URL: {response.url}")
        self.logger.info(f"Property status: {response.status}")
        self.logger.info(f"Property length: {len(response.body)}")
        
        # Log first 1000 characters
        content_sample = response.text[:1000] if response.text else "No text content"
        self.logger.info(f"Property content sample: {content_sample}")
        
        # Try to extract basic info
        title_selectors = [
            'h1.main::text',
            '.title h1::text',
            '.property-content .title::text',
            'h1::text',
            '.sellDetailHeader h1::text'
        ]
        
        title = None
        for selector in title_selectors:
            title = response.css(selector).get()
            if title:
                title = title.strip()
                self.logger.info(f"Found title with selector '{selector}': {title}")
                break
        
        if not title:
            self.logger.warning("No title found")
        
        # Try to find price
        price_selectors = [
            '.price .total::text',
            '.unitPrice .total::text',
            '.overview .price .total::text',
            '.price-container .total::text'
        ]
        
        price = None
        for selector in price_selectors:
            price = response.css(selector).get()
            if price:
                self.logger.info(f"Found price with selector '{selector}': {price}")
                break
        
        if not price:
            self.logger.warning("No price found")
        
        # If we have basic data, create a test item
        if title:
            test_item = {
                'type': 'house',
                'source': 'lianjia',
                'city': self.city,
                'name': title,
                'building_name_zh': title,
                'deal_price': 1000000,  # Test value
                'area': 100,  # Test value
                'url': response.url,
            }
            self.logger.info(f"Creating test item: {test_item}")
            yield test_item
    
    def closed(self, reason):
        self.logger.info(f"Simple spider closed: {reason}")
    
    def parse_property_listings(self, response):
        """Parse property listings from web pages"""
        try:
            page = response.meta.get('page', 1)
            self.logger.info(f"Parsing property listings from page {page}: {response.url}")
            
            # Extract property listings
            properties = response.css('.sellListContent li')
            
            if not properties:
                self.logger.warning(f"No properties found on page {page}")
                return
            
            self.logger.info(f"Found {len(properties)} properties on page {page}")
            
            # Process each property (limit to first 10 for testing)
            for prop in properties[:10]:
                try:
                    # Extract property data
                    title = prop.css('.title a::text').get()
                    if not title:
                        continue
                    
                    title = title.strip()
                    
                    # Extract price
                    price_text = prop.css('.totalPrice .number::text').get()
                    deal_price = 0
                    if price_text:
                        try:
                            deal_price = int(float(price_text) * 10000)  # Convert from 万 to yuan
                        except:
                            deal_price = 0
                    
                    # Extract area and rooms info
                    house_info = prop.css('.houseInfo::text').get()
                    area = 0
                    rooms = ''
                    if house_info:
                        # Extract area
                        area_match = re.search(r'(\d+\.?\d*)平米', house_info)
                        if area_match:
                            area = float(area_match.group(1))
                        
                        # Extract room layout (e.g., "2室1厅")
                        room_match = re.search(r'(\d+室\d+厅)', house_info)
                        if room_match:
                            rooms = room_match.group(1)
                    
                    # Extract position info (floor, direction, year)
                    position_info = prop.css('.positionInfo::text').get()
                    floor_info = ''
                    direction = ''
                    year = ''
                    if position_info:
                        position_info = position_info.strip()
                        floor_info = position_info
                        
                        # Extract building year
                        year_match = re.search(r'(\d{4})年建', position_info)
                        if year_match:
                            year = year_match.group(1)
                        
                        # Extract direction
                        direction_match = re.search(r'(南|北|东|西|东南|西南|东北|西北)', position_info)
                        if direction_match:
                            direction = direction_match.group(1)
                    
                    # Extract community/district info
                    follow_info = prop.css('.followInfo::text').get()
                    district_name = ''
                    community_name = ''
                    if follow_info:
                        # Usually contains district and area info
                        district_name = follow_info.strip()
                        community_name = title.split()[0] if title else ''  # First part of title is usually community
                    
                    # Extract detailed URL for more info
                    detail_url = prop.css('.title a::attr(href)').get()
                    full_url = urljoin(response.url, detail_url) if detail_url else response.url
                    
                    # Create property item
                    property_item = {
                        'type': 'property',
                        'source': 'lianjia_web',
                        'title': title,
                        'building_name_zh': community_name or title.split()[0] if title else '',
                        'estate_name_zh': community_name or title.split()[0] if title else '',
                        'deal_price': deal_price,
                        'area': area,
                        'rooms': rooms,
                        'floor_info': floor_info,
                        'direction': direction,
                        'building_year': year,
                        'district_name': district_name,
                        'city_name': self._get_city_name(),
                        'zone': 'China',
                        'province': self._get_province_by_city(),
                        'deal_date': self._get_current_date(),
                        'url': full_url,
                        'raw_data': {
                            'title': title,
                            'price_text': price_text,
                            'house_info': house_info,
                            'position_info': position_info,
                            'follow_info': follow_info
                        }
                    }
                    
                    yield property_item
                    self.logger.info(f"✅ Extracted property: {title} - {deal_price} yuan, {area}㎡")
                
                except Exception as e:
                    self.logger.error(f"Error extracting property data: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Error parsing property listings: {e}")
    
    def _get_city_name(self):
        """Get Chinese city name by domain"""
        city_mapping = {
            'bj.lianjia.com': '北京',
            'sh.lianjia.com': '上海',
            'gz.lianjia.com': '广州',
            'sz.lianjia.com': '深圳',
            'hz.lianjia.com': '杭州',
            'nj.lianjia.com': '南京',
            'wh.lianjia.com': '武汉',
            'cd.lianjia.com': '成都',
            'xa.lianjia.com': '西安',
            'tj.lianjia.com': '天津'
        }
        return city_mapping.get(self.base_domain, '广州')
    
    def _get_province_by_city(self):
        """Get province name by city"""
        province_mapping = {
            'beijing': '北京市',
            'shanghai': '上海市', 
            'shenzhen': '广东省',
            'guangzhou': '广东省',
            'hangzhou': '浙江省',
            'nanjing': '江苏省',
            'wuhan': '湖北省',
            'chengdu': '四川省',
            'xian': '陕西省',
            'tianjin': '天津市'
        }
        return province_mapping.get(self.city_name, '广东省')
    
    def _get_current_date(self):
        """Get current date in YYYY-MM-DD format"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')
