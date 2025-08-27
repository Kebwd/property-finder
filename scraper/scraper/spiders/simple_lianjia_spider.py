#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple Lianjia Spider - Based on waugustus/lianjia-spider
Optimized for ScraperAPI and simplified for reliability
"""

import scrapy
import re
import json
import time
import random
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging
from bs4 import BeautifulSoup

class SimpleLianjiaSpider(scrapy.Spider):
    name = "simple_lianjia"
    allowed_domains = ["lianjia.com"]
    
    def __init__(self, city='beijing', district='', house_type='l2l3l4', 
                 min_price=0, max_price=0, *args, **kwargs):
        super(SimpleLianjiaSpider, self).__init__(*args, **kwargs)
        
        # Configuration (based on waugustus approach but simplified)
        self.city = city
        self.district = district  
        self.house_type = house_type or 'l2l3l4'
        self.min_price = int(min_price) if min_price else 0
        self.max_price = int(max_price) if max_price else 0
        
        # City mapping (simplified from waugustus project)
        self.city_hosts = {
            'beijing': 'https://bj.lianjia.com',
            'shanghai': 'https://sh.lianjia.com',
            'guangzhou': 'https://gz.lianjia.com',
            'shenzhen': 'https://sz.lianjia.com',
            'chongqing': 'https://cq.lianjia.com'
        }
        
        self.city_names = {
            'beijing': '北京',
            'shanghai': '上海',
            'guangzhou': '广州',
            'shenzhen': '深圳',
            'chongqing': '重庆'
        }
        
        if city not in self.city_hosts:
            raise ValueError(f"Unsupported city: {city}")
        
        self.base_url = self.city_hosts[city]
        self.city_name = self.city_names[city]
        
        # Build start URLs (based on waugustus URL pattern)
        self.start_urls = self._build_urls()
        
        # Stats
        self.properties_found = 0
        self.current_page = 1
        self.max_pages = 5  # Limit for testing
        
        self.logger.info(f"🏠 Simple Lianjia Spider for {self.city_name}")
        self.logger.info(f"🔗 Start URLs: {self.start_urls}")

    def _build_urls(self):
        """Build URLs based on waugustus project pattern"""
        base = f"{self.base_url}/ershoufang"
        
        # Basic URL without filters first
        urls = [f"{base}/"]
        
        # Add filtered URLs if parameters provided
        if self.district or self.house_type or self.min_price or self.max_price:
            # Build filter string: /pg1l2l3l4bp100ep500rs朝阳/
            filter_parts = []
            
            # Add page
            filter_parts.append("pg1")
            
            # Add house type (l2l3l4)
            if self.house_type:
                filter_parts.append(self.house_type)
            
            # Add price range (bp100ep500)
            if self.min_price or self.max_price:
                price_filter = f"bp{self.min_price}"
                if self.max_price > 0:
                    price_filter += f"ep{self.max_price}"
                filter_parts.append(price_filter)
            
            # Add district (rs朝阳)
            if self.district:
                filter_parts.append(f"rs{self.district}")
            
            filtered_url = f"{base}/{''.join(filter_parts)}/"
            urls.append(filtered_url)
        
        return urls

    def start_requests(self):
        """Generate initial requests"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'page': 1},
                dont_filter=True,
                errback=self.handle_error
            )

    def parse(self, response):
        """Parse property listing page - simplified approach"""
        page = response.meta.get('page', 1)
        self.logger.info(f"📄 Parsing page {page}: {response.url}")
        
        # Check if blocked
        if self._is_blocked(response):
            self.logger.warning(f"🚫 Page appears to be blocked: {response.url}")
            return
        
        # Use BeautifulSoup for parsing (like waugustus approach)
        soup = BeautifulSoup(response.body, 'html.parser')
        
        # Extract properties using waugustus method
        properties = self._extract_properties_waugustus_style(soup, response)
        
        self.logger.info(f"🏠 Found {len(properties)} properties on page {page}")
        
        # Yield properties
        for prop in properties:
            if prop:
                self.properties_found += 1
                yield prop

        # Handle pagination (simplified)
        if len(properties) > 0 and page < self.max_pages:
            next_page = page + 1
            next_url = self._build_next_page_url(response.url, next_page)
            
            if next_url:
                self.logger.info(f"➡️  Going to page {next_page}")
                
                # Add delay
                time.sleep(random.uniform(2, 4))
                
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse,
                    meta={'page': next_page},
                    dont_filter=True,
                    errback=self.handle_error
                )

    def _is_blocked(self, response):
        """Check if response indicates blocking"""
        if response.status != 200:
            return True
        
        # Check content length (blocked pages are usually very small)
        if len(response.body) < 5000:
            return True
        
        # Check for blocking keywords
        text = response.text.lower()
        blocking_indicators = [
            '验证', 'captcha', 'verify', 'blocked',
            '人机验证', '安全验证', '访问受限'
        ]
        
        return any(indicator in text for indicator in blocking_indicators)

    def _extract_properties_waugustus_style(self, soup, response):
        """Extract properties using waugustus/lianjia-spider approach"""
        properties = []
        
        # Find the property list container (sellListContent is the key selector)
        house_list = soup.find('ul', {'class': 'sellListContent'})
        if not house_list:
            self.logger.warning("❌ No 'sellListContent' found - page may be blocked")
            return properties
        
        # Extract each property (following waugustus logic)
        house_items = house_list.find_all('li')
        self.logger.info(f"🔍 Found {len(house_items)} house items in sellListContent")
        
        for house in house_items:
            try:
                property_data = self._extract_single_property_waugustus(house, response)
                if property_data:
                    properties.append(property_data)
            except Exception as e:
                self.logger.debug(f"Error extracting property: {e}")
        
        return properties

    def _extract_single_property_waugustus(self, house_element, response):
        """Extract single property - exact waugustus approach"""
        try:
            # Find info div (waugustus approach)
            info = house_element.find("div", {'class': 'info'})
            if not info:
                return None
            
            # Extract title and house_id (waugustus method)
            house_title = info.find("div", {'class': 'title'})
            if not house_title or not house_title.a:
                return None
            
            title_link = house_title.a
            house_id = self._extract_house_id_waugustus(title_link.get('href', ''))
            title = title_link.get_text(strip=True)
            
            # Extract location (community name) - waugustus method
            house_location = ''
            flood_div = info.find("div", {'class': 'flood'})
            if flood_div and flood_div.div and flood_div.div.a:
                house_location = flood_div.div.a.get_text(strip=True)
            
            # Extract address details - waugustus method
            address = info.find("div", {'class': 'address'})
            address_info = self._parse_address_waugustus(address)
            
            # Extract price info - waugustus method
            price_info = info.find("div", {'class': 'priceInfo'})
            prices = self._parse_price_waugustus(price_info)
            
            # Build property data (compatible with your database)
            property_data = {
                # Core fields
                'house_id': house_id,
                'building_name_zh': house_location or title,
                'title': title,
                
                # Location
                'zone': 'China',
                'city': self.city_name,
                'district': self.district or '',
                'location': house_location,
                
                # Property details (from address parsing)
                'type': [address_info.get('house_type', '住宅')],
                'type_raw': address_info.get('house_type', '住宅'),
                'size': address_info.get('house_size', ''),
                'area': address_info.get('house_size_num', 0),
                'orientation': address_info.get('house_towards', ''),
                'floor': address_info.get('house_flood', ''),
                'year_built': address_info.get('house_year', ''),
                'building_type': address_info.get('house_building', ''),
                
                # Price (converted to proper format)
                'deal_price': prices.get('total_price', 0),
                'price_per_sqm': prices.get('unit_price', 0),
                'deal_date': datetime.now().strftime('%Y-%m-%d'),
                
                # Source
                'source_url': urljoin(response.url, title_link.get('href', '')),
                'start_url': response.url,
                'developer': '',
                'status': 'active'
            }
            
            # Validate (basic checks)
            if house_id > 0 and property_data['deal_price'] > 0:
                return property_data
            
        except Exception as e:
            self.logger.debug(f"Property extraction error: {e}")
        
        return None

    def _extract_house_id_waugustus(self, href):
        """Extract house ID from href - waugustus method"""
        if not href:
            return 0
        try:
            # Pattern from waugustus: '/ershoufang/123456789.html'
            match = re.search(r'/(\d+)\.html', href)
            if match:
                return int(match.group(1))
        except:
            pass
        return 0

    def _parse_address_waugustus(self, address_div):
        """Parse address info - waugustus approach"""
        info = {
            'house_type': '住宅',
            'house_size': '',
            'house_size_num': 0,
            'house_towards': '',
            'house_flood': '',
            'house_year': '',
            'house_building': ''
        }
        
        if not address_div:
            return info
        
        try:
            # waugustus approach: split by ' | '
            address_text = address_div.get_text(strip=True)
            address_parts = [part.strip() for part in address_text.split('|')]
            
            # waugustus logic for parsing address parts
            if len(address_parts) >= 1:
                info['house_type'] = address_parts[0]
            if len(address_parts) >= 2:
                info['house_size'] = address_parts[1]
                info['house_size_num'] = self._extract_size_number(address_parts[1])
            if len(address_parts) >= 3:
                info['house_towards'] = address_parts[2]
            if len(address_parts) >= 4:
                info['house_flood'] = address_parts[3]
            
            # Handle year and building type (waugustus conditional logic)
            if len(address_parts) < 7:
                if len(address_parts) >= 6:
                    info['house_building'] = address_parts[5]
            else:
                if len(address_parts) >= 6:
                    info['house_year'] = address_parts[5]
                if len(address_parts) >= 7:
                    info['house_building'] = address_parts[6]
                    
        except Exception as e:
            self.logger.debug(f"Address parsing error: {e}")
        
        return info

    def _extract_size_number(self, size_text):
        """Extract numeric size from text"""
        if not size_text:
            return 0
        try:
            match = re.search(r'(\d+\.?\d*)', size_text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0

    def _parse_price_waugustus(self, price_info):
        """Parse price info - waugustus approach"""
        prices = {
            'total_price': 0,
            'unit_price': 0
        }
        
        if not price_info:
            return prices
        
        try:
            # Total price - waugustus method
            total_price_div = price_info.find("div", {'class': 'totalPrice'})
            if total_price_div and total_price_div.span:
                total_price_text = total_price_div.span.get_text(strip=True)
                prices['total_price'] = self._parse_total_price_waugustus(total_price_text)
            
            # Unit price - waugustus method
            unit_price_div = price_info.find("div", {'class': 'unitPrice'})
            if unit_price_div and unit_price_div.span:
                unit_price_text = unit_price_div.span.get_text(strip=True)
                prices['unit_price'] = self._parse_unit_price_waugustus(unit_price_text)
                
        except Exception as e:
            self.logger.debug(f"Price parsing error: {e}")
        
        return prices

    def _parse_total_price_waugustus(self, price_text):
        """Parse total price - waugustus method: '300万' -> 3000000"""
        if not price_text:
            return 0
        try:
            # waugustus approach: convert 万 to actual number
            price_clean = re.sub(r'[^\d万.]', '', price_text)
            if '万' in price_clean:
                price_num = float(price_clean.replace('万', ''))
                return int(price_num * 10000)  # Convert 万 to actual price
            else:
                return int(float(price_clean))
        except:
            return 0

    def _parse_unit_price_waugustus(self, price_text):
        """Parse unit price - waugustus method"""
        if not price_text:
            return 0
        try:
            # Extract from text like '单价33000元/平米' or just numbers
            match = re.search(r'(\d+)', price_text)
            if match:
                return int(match.group(1))
        except:
            pass
        return 0

    def _build_next_page_url(self, current_url, next_page):
        """Build next page URL"""
        try:
            # Replace page number in URL
            if 'pg' in current_url:
                # Replace existing page number
                new_url = re.sub(r'pg\d+', f'pg{next_page}', current_url)
            else:
                # Add page number to base URL
                if current_url.endswith('/'):
                    new_url = f"{current_url[:-1]}/pg{next_page}/"
                else:
                    new_url = f"{current_url}/pg{next_page}/"
            
            return new_url
        except:
            return None

    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"❌ Request failed: {failure.value}")

    def closed(self, reason):
        """Spider closed callback"""
        self.logger.info(f"🕷️  Simple Lianjia Spider closed: {reason}")
        self.logger.info(f"📊 Total properties found: {self.properties_found}")
