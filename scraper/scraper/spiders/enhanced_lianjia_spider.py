#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced Lianjia Spider - Based on waugustus/lianjia-spider
Integrated with ScraperAPI and existing property-finder infrastructure
"""

import scrapy
import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import time
import random
from urllib.parse import urljoin, urlparse
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parents[2]))

class EnhancedLianjiaSpider(scrapy.Spider):
    name = "enhanced_lianjia"
    allowed_domains = ["lianjia.com"]
    
    def __init__(self, city='beijing', district='', property_type='ershoufang', 
                 min_price=0, max_price=0, house_type='', *args, **kwargs):
        super(EnhancedLianjiaSpider, self).__init__(*args, **kwargs)
        
        # Configuration based on waugustus/lianjia-spider approach
        self.city = city
        self.district = district or '马连洼'  # Default district
        self.property_type = property_type
        self.min_price = min_price
        self.max_price = max_price
        self.house_type = house_type or 'l2l3l4'  # ln表示n居室
        
        # City configuration
        self.city_config = {
            'beijing': {
                'host': 'https://bj.lianjia.com',
                'name': '北京',
                'province': '北京市'
            },
            'shanghai': {
                'host': 'https://sh.lianjia.com', 
                'name': '上海',
                'province': '上海市'
            },
            'guangzhou': {
                'host': 'https://gz.lianjia.com',
                'name': '广州', 
                'province': '广东省'
            },
            'shenzhen': {
                'host': 'https://sz.lianjia.com',
                'name': '深圳',
                'province': '广东省'
            },
            'chongqing': {
                'host': 'https://cq.lianjia.com',
                'name': '重庆',
                'province': '重庆市'
            }
        }
        
        if city not in self.city_config:
            raise ValueError(f"Unsupported city: {city}. Available: {list(self.city_config.keys())}")
        
        self.base_url = self.city_config[city]['host']
        self.ershoufang_url = f"{self.base_url}/ershoufang"
        
        # Build price filter string
        self.price_filter = self._build_price_filter()
        
        # Statistics
        self.total_scraped = 0
        self.current_page = 1
        self.max_pages = 100  # Limit for testing
        
        # Build start URLs
        self.start_urls = self._build_start_urls()
        
        self.logger.info(f"🏠 Enhanced Lianjia Spider initialized")
        self.logger.info(f"🌆 City: {self.city_config[city]['name']}")
        self.logger.info(f"🏢 District: {self.district}")
        self.logger.info(f"💰 Price range: {self.price_filter}")
        self.logger.info(f"🔗 Start URLs: {self.start_urls}")

    def _build_price_filter(self):
        """Build price filter string like 'bp100ep500' """
        if self.max_price > 0:
            return f"bp{self.min_price}ep{self.max_price}"
        return ""

    def _build_start_urls(self):
        """Build start URLs based on configuration"""
        urls = []
        
        # Base URL with filters
        url_parts = [self.ershoufang_url]
        
        # Add pagination, house type, price, and district filters
        filter_parts = []
        if self.house_type:
            filter_parts.append(self.house_type)
        if self.price_filter:
            filter_parts.append(self.price_filter)
        if self.district:
            filter_parts.append(f"rs{self.district}")
        
        # Build URL: /ershoufang/pg1l2l3l4bp0ep500rs马连洼/
        url = f"{self.ershoufang_url}/pg{self.current_page}{''.join(filter_parts)}/"
        urls.append(url)
        
        return urls

    def start_requests(self):
        """Generate initial requests"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    'page': self.current_page,
                    'retry_count': 0
                },
                errback=self.handle_error
            )

    def parse(self, response):
        """Parse listing pages - based on waugustus approach"""
        current_page = response.meta.get('page', 1)
        self.logger.info(f"📄 Parsing page {current_page}: {response.url}")
        
        # Check if we're blocked
        if self._is_blocked(response):
            self.logger.warning(f"🚫 Blocked detected on page {current_page}")
            return
        
        # Extract property listings using BeautifulSoup (like waugustus approach)
        soup = BeautifulSoup(response.body, 'html.parser')
        
        # Get total pages on first page
        if current_page == 1:
            total_pages = self._extract_total_pages(soup)
            if total_pages:
                self.max_pages = min(total_pages, self.max_pages)
                self.logger.info(f"📊 Total pages available: {total_pages}, will scrape: {self.max_pages}")
        
        # Extract property listings
        properties = self._extract_property_listings(soup, response)
        
        properties_count = len(properties)
        self.logger.info(f"🏠 Found {properties_count} properties on page {current_page}")
        
        # Yield properties
        for property_data in properties:
            if property_data:
                self.total_scraped += 1
                yield property_data

        # Handle pagination
        if current_page < self.max_pages and properties_count > 0:
            next_page = current_page + 1
            next_url = self._build_page_url(next_page)
            
            self.logger.info(f"➡️  Following to page {next_page}")
            
            # Add delay between pages
            time.sleep(random.uniform(1, 3))
            
            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={
                    'page': next_page,
                    'retry_count': 0
                },
                errback=self.handle_error
            )
        else:
            self.logger.info(f"✅ Scraping completed. Total properties: {self.total_scraped}")

    def _build_page_url(self, page):
        """Build URL for specific page"""
        # Build URL: /ershoufang/pg2l2l3l4bp0ep500rs马连洼/
        filter_parts = []
        if self.house_type:
            filter_parts.append(self.house_type)
        if self.price_filter:
            filter_parts.append(self.price_filter)
        if self.district:
            filter_parts.append(f"rs{self.district}")
        
        return f"{self.ershoufang_url}/pg{page}{''.join(filter_parts)}/"

    def _is_blocked(self, response):
        """Check if we're being blocked"""
        # Check for common blocking indicators
        if response.status != 200:
            return True
        
        text = response.text.lower()
        blocking_indicators = [
            '验证', 'captcha', 'verify', 'blocked', 
            '人机验证', '安全验证', '访问受限'
        ]
        
        return any(indicator in text for indicator in blocking_indicators)

    def _extract_total_pages(self, soup):
        """Extract total pages from pagination"""
        try:
            # Look for pagination info
            page_box = soup.find('div', {'class': 'page-box'})
            if page_box and page_box.div:
                page_data = page_box.div.get('page-data')
                if page_data:
                    page_info = json.loads(page_data)
                    return page_info.get('totalPage', 1)
        except:
            pass
        return None

    def _extract_property_listings(self, soup, response):
        """Extract property listings from page - based on waugustus approach"""
        properties = []
        
        # Find property list container
        house_list = soup.find('ul', {'class': 'sellListContent'})
        if not house_list:
            self.logger.warning("❌ No property list found")
            return properties
        
        # Extract each property (based on waugustus logic)
        for house in house_list.find_all('li'):
            try:
                property_data = self._extract_single_property(house, response)
                if property_data:
                    properties.append(property_data)
            except Exception as e:
                self.logger.error(f"❌ Error extracting property: {e}")
                continue
        
        return properties

    def _extract_single_property(self, house_element, response):
        """Extract single property data - based on waugustus/lianjia-spider logic"""
        try:
            # Find info div
            info = house_element.find("div", {'class': 'info'})
            if not info:
                return None
            
            # Extract title and ID (based on waugustus approach)
            house_title = info.find("div", {'class': 'title'})
            if not house_title or not house_title.a:
                return None
            
            title_link = house_title.a
            house_id = self._extract_house_id(title_link.get('href', ''))
            title = title_link.get_text(strip=True)
            
            # Extract location (community name)
            flood_div = info.find("div", {'class': 'flood'})
            location = ''
            if flood_div and flood_div.div and flood_div.div.a:
                location = flood_div.div.a.get_text(strip=True)
            
            # Extract address details (based on waugustus logic)
            address_div = info.find("div", {'class': 'address'})
            address_info = self._parse_address_info(address_div)
            
            # Extract price info (based on waugustus approach)
            price_info = info.find("div", {'class': 'priceInfo'})
            price_data = self._parse_price_info(price_info)
            
            # Build property data (matching your database schema)
            property_data = {
                # Core identification
                'house_id': house_id,
                'building_name_zh': location or title,
                'title': title,
                
                # Location information
                'zone': 'China',
                'city': self.city_config[self.city]['name'],
                'province': self.city_config[self.city]['province'],
                'district': self.district,
                'location': location,
                'area': address_info.get('area', ''),
                
                # Property details
                'type': address_info.get('house_type', ['住宅']),
                'type_raw': address_info.get('house_type_raw', '住宅'),
                'size': address_info.get('size', ''),
                'floor': address_info.get('floor', ''),
                'orientation': address_info.get('orientation', ''),
                'year_built': address_info.get('year_built', ''),
                'building_type': address_info.get('building_type', ''),
                
                # Price information
                'deal_price': price_data.get('total_price', 0),
                'price_per_sqm': price_data.get('unit_price', 0),
                'deal_date': datetime.now().strftime('%Y-%m-%d'),
                
                # Source information
                'source_url': urljoin(response.url, title_link.get('href', '')),
                'start_url': response.url,
                'developer': '',
                
                # Status
                'status': 'active'
            }
            
            # Validate data
            if self._validate_property_data(property_data):
                return property_data
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error extracting single property: {e}")
            return None

    def _extract_house_id(self, href):
        """Extract house ID from href like '/ershoufang/123456789.html'"""
        if not href:
            return 0
        try:
            # Extract number from URL
            match = re.search(r'/(\d+)\.html', href)
            if match:
                return int(match.group(1))
        except:
            pass
        return 0

    def _parse_address_info(self, address_div):
        """Parse address information - based on waugustus approach"""
        info = {
            'house_type': '住宅',
            'house_type_raw': '住宅',
            'size': '',
            'orientation': '',
            'floor': '',
            'year_built': '',
            'building_type': '',
            'area': ''
        }
        
        if not address_div:
            return info
        
        try:
            # Parse address text (format: "户型 | 面积 | 朝向 | 楼层 | 年份 | 建筑类型")
            address_text = address_div.get_text(strip=True)
            address_parts = [part.strip() for part in address_text.split('|')]
            
            if len(address_parts) >= 1:
                info['house_type_raw'] = address_parts[0]
                info['house_type'] = [self._normalize_house_type(address_parts[0])]
            
            if len(address_parts) >= 2:
                info['size'] = address_parts[1]
                info['area'] = self._extract_numeric_size(address_parts[1])
            
            if len(address_parts) >= 3:
                info['orientation'] = address_parts[2]
            
            if len(address_parts) >= 4:
                info['floor'] = address_parts[3]
            
            if len(address_parts) >= 5:
                info['year_built'] = address_parts[4]
            
            if len(address_parts) >= 6:
                info['building_type'] = address_parts[5]
                
        except Exception as e:
            self.logger.debug(f"Address parsing error: {e}")
        
        return info

    def _normalize_house_type(self, house_type):
        """Normalize house type"""
        type_mapping = {
            '住宅': '住宅',
            '公寓': '公寓',
            '别墅': '别墅',
            '写字楼': '写字楼',
            '商铺': '商铺'
        }
        
        for key in type_mapping:
            if key in house_type:
                return type_mapping[key]
        
        return '住宅'

    def _extract_numeric_size(self, size_text):
        """Extract numeric size from text like '89.5平米'"""
        if not size_text:
            return 0
        
        try:
            match = re.search(r'(\d+\.?\d*)', size_text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0

    def _parse_price_info(self, price_info):
        """Parse price information - based on waugustus approach"""
        price_data = {
            'total_price': 0,
            'unit_price': 0
        }
        
        if not price_info:
            return price_data
        
        try:
            # Extract total price (万元)
            total_price_div = price_info.find("div", {'class': 'totalPrice'})
            if total_price_div and total_price_div.span:
                total_price_text = total_price_div.span.get_text(strip=True)
                price_data['total_price'] = self._parse_total_price(total_price_text)
            
            # Extract unit price (元/平米)
            unit_price_div = price_info.find("div", {'class': 'unitPrice'})
            if unit_price_div and unit_price_div.span:
                unit_price_text = unit_price_div.span.get_text(strip=True)
                price_data['unit_price'] = self._parse_unit_price(unit_price_text)
                
        except Exception as e:
            self.logger.debug(f"Price parsing error: {e}")
        
        return price_data

    def _parse_total_price(self, price_text):
        """Parse total price from text like '300万' -> 3000000"""
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

    def _parse_unit_price(self, price_text):
        """Parse unit price from text like '单价33000元/平米' -> 33000"""
        if not price_text:
            return 0
        
        try:
            # Extract numeric part
            match = re.search(r'(\d+)', price_text)
            if match:
                return int(match.group(1))
        except:
            pass
        return 0

    def _validate_property_data(self, property_data):
        """Validate property data before yielding"""
        # Check required fields
        required_fields = ['house_id', 'building_name_zh', 'deal_price']
        
        for field in required_fields:
            if not property_data.get(field):
                self.logger.debug(f"Missing required field: {field}")
                return False
        
        # Check valid house ID
        if property_data.get('house_id', 0) <= 0:
            self.logger.debug("Invalid house ID")
            return False
        
        # Check reasonable price
        if property_data.get('deal_price', 0) <= 0:
            self.logger.debug("Invalid price")
            return False
        
        return True

    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"❌ Request failed: {failure.value}")
        
        # Extract retry count
        retry_count = failure.request.meta.get('retry_count', 0)
        max_retries = 3
        
        if retry_count < max_retries:
            self.logger.info(f"🔄 Retrying request (attempt {retry_count + 1}/{max_retries})")
            
            # Wait before retry
            time.sleep(random.uniform(2, 5))
            
            # Retry request
            new_request = failure.request.copy()
            new_request.meta['retry_count'] = retry_count + 1
            
            yield new_request
        else:
            self.logger.error(f"❌ Max retries reached for {failure.request.url}")

    def closed(self, reason):
        """Spider closed callback"""
        self.logger.info(f"🕷️  Enhanced Lianjia Spider closed: {reason}")
        self.logger.info(f"📊 Total properties scraped: {self.total_scraped}")
