"""
Mobile Lianjia Spider - Based on CaoZ/Fast-LianJia-Crawler approach
Uses official Lianjia mobile API instead of web scraping to avoid blocking
"""

import scrapy
import json
import time
import hashlib
import base64
from urllib.parse import urlencode
import logging


class MobileLianjiaSpider(scrapy.Spider):
    name = 'mobile_lianjia'
    allowed_domains = ['app.api.lianjia.com', 'm.lianjia.com']
    
    # Mobile app credentials (from CaoZ project)
    APP_CONFIG = {
        'ua': 'HomeLink7.7.6; Android 7.0',
        'app_id': '20161001_android', 
        'app_secret': '7df91ff794c67caee14c3dacd5549b35'
    }
    
    # City mappings
    CITY_MAPPINGS = {
        'beijing': {'id': 110000, 'abbr': 'bj'},
        'shanghai': {'id': 310000, 'abbr': 'sh'},
        'guangzhou': {'id': 440100, 'abbr': 'gz'},
        'shenzhen': {'id': 440300, 'abbr': 'sz'},
        'chengdu': {'id': 510100, 'abbr': 'cd'},
        'hangzhou': {'id': 330100, 'abbr': 'hz'},
        'wuhan': {'id': 420100, 'abbr': 'wh'},
        'chongqing': {'id': 500000, 'abbr': 'cq'}
    }
    
    def __init__(self, city='beijing', mode='communities', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.city = city
        self.mode = mode  # 'communities', 'details', 'houses'
        
        if city not in self.CITY_MAPPINGS:
            raise ValueError(f"Unsupported city: {city}. Available: {list(self.CITY_MAPPINGS.keys())}")
            
        self.city_info = self.CITY_MAPPINGS[city]
        self.logger.info(f"🏙️ Initialized Mobile Lianjia Spider for {city} (ID: {self.city_info['id']})")
    
    def start_requests(self):
        """Start with city info initialization"""
        yield self.create_api_request(
            url='http://app.api.lianjia.com/config/config/initData',
            callback=self.parse_city_info,
            method='POST',
            payload={
                'params': f'{{"city_id": {self.city_info["id"]}, "mobile_type": "android", "version": "8.0.1"}}',
                'fields': '{"city_info": "", "city_config_all": ""}'
            }
        )
    
    def create_api_request(self, url, callback, method='GET', payload=None):
        """Create authenticated API request with proper mobile headers"""
        if payload is None:
            payload = {}
            
        # Add timestamp
        payload['request_ts'] = str(int(time.time()))
        
        # Ensure all values are strings for FormRequest
        payload = {k: str(v) for k, v in payload.items()}
        
        # Generate authentication token
        auth_token = self.get_auth_token(payload)
        
        headers = {
            'User-Agent': self.APP_CONFIG['ua'],
            'Authorization': auth_token,
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded' if method == 'POST' else None
        }
        
        if method == 'POST':
            return scrapy.FormRequest(
                url=url,
                formdata=payload,
                headers=headers,
                callback=callback,
                dont_filter=True
            )
        else:
            return scrapy.Request(
                url=f"{url}?{urlencode(payload)}",
                headers=headers,
                callback=callback,
                dont_filter=True
            )
    
    def get_auth_token(self, payload):
        """Generate authentication token using app secret"""
        # Sort parameters
        data = list(payload.items())
        data.sort()
        
        # Build token string
        token = self.APP_CONFIG['app_secret']
        for key, value in data:
            token += f'{key}={value}'
        
        # Generate hash
        token_hash = hashlib.sha1(token.encode()).hexdigest()
        token_string = f"{self.APP_CONFIG['app_id']}:{token_hash}"
        
        # Base64 encode
        return base64.b64encode(token_string.encode()).decode()
    
    def parse_api_response(self, response):
        """Parse API response and handle errors"""
        try:
            data = response.json()
            
            if data.get('errno'):
                error_msg = data.get('error', 'Unknown API error')
                self.logger.error(f"❌ API Error: {error_msg}")
                return None
                
            return data.get('data')
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ JSON decode error: {e}")
            return None
    
    def parse_city_info(self, response):
        """Parse city information and start district/community crawling"""
        data = self.parse_api_response(response)
        if not data:
            return
            
        city_info = data['city_info']['info'][0]
        
        # Find city abbreviation
        for city_config in data['city_config_all']['list']:
            if city_config['city_id'] == self.city_info['id']:
                city_info['city_abbr'] = city_config['abbr']
                break
        
        self.logger.info(f"🏙️ City: {city_info['city_name']}, Districts: {len(city_info['district'])}")
        
        # Yield city data
        yield {
            'type': 'city',
            'city_id': city_info['city_id'],
            'city_name': city_info['city_name'],
            'city_abbr': city_info.get('city_abbr', self.city_info['abbr']),
            'districts_count': len(city_info['district']),
            'data_source': 'mobile_api'
        }
        
        # Process districts and business circles
        for district in city_info['district']:
            yield {
                'type': 'district',
                'city_id': city_info['city_id'],
                'district_id': district['district_id'],
                'district_name': district['district_name'],
                'district_quanpin': district['district_quanpin'],
                'biz_circles_count': len(district['bizcircle']),
                'data_source': 'mobile_api'
            }
            
            # Process business circles
            for biz_circle in district['bizcircle']:
                yield {
                    'type': 'biz_circle',
                    'city_id': city_info['city_id'],
                    'district_id': district['district_id'],
                    'biz_circle_id': biz_circle['bizcircle_id'],
                    'biz_circle_name': biz_circle['bizcircle_name'],
                    'biz_circle_quanpin': biz_circle['bizcircle_quanpin'],
                    'data_source': 'mobile_api'
                }
                
                # Start community crawling for this business circle
                if self.mode in ['communities', 'details']:
                    yield self.create_api_request(
                        url='http://app.api.lianjia.com/house/community/search',
                        callback=self.parse_communities,
                        payload={
                            'bizcircle_id': biz_circle['bizcircle_id'],
                            'group_type': 'community',
                            'limit_offset': 0,
                            'city_id': city_info['city_id'],
                            'limit_count': 30
                        },
                        meta={
                            'biz_circle_id': biz_circle['bizcircle_id'],
                            'biz_circle_name': biz_circle['bizcircle_name'],
                            'city_id': city_info['city_id'],
                            'district_id': district['district_id']
                        }
                    )
    
    def parse_communities(self, response):
        """Parse communities in a business circle"""
        data = self.parse_api_response(response)
        if not data:
            return
            
        meta = response.meta
        communities = data.get('list', [])
        total_count = data.get('total_count', 0)
        has_more = data.get('has_more_data', False)
        
        self.logger.info(f"🏘️ Business Circle: {meta['biz_circle_name']}, Communities: {len(communities)}/{total_count}")
        
        # Process communities
        for community in communities:
            community_data = {
                'type': 'community',
                'city_id': meta['city_id'],
                'district_id': meta['district_id'],
                'biz_circle_id': meta['biz_circle_id'],
                'community_id': community['community_id'],
                'community_name': community['community_name'],
                'building_finish_year': community.get('building_finish_year'),
                'building_type': community.get('building_type'),
                'second_hand_quantity': community.get('ershoufang_source_count', 0),
                'second_hand_unit_price': community.get('ershoufang_avg_unit_price'),
                'data_source': 'mobile_api'
            }
            
            yield community_data
            
            # If detailed mode, crawl community details page
            if self.mode == 'details':
                detail_url = f"https://m.lianjia.com/{self.city_info['abbr']}/xiaoqu/{community['community_id']}/pinzhi"
                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_community_details,
                    headers={'User-Agent': self.APP_CONFIG['ua']},
                    meta={'community_data': community_data}
                )
        
        # Handle pagination
        if has_more:
            current_offset = response.meta.get('offset', 0)
            new_offset = current_offset + len(communities)
            
            yield self.create_api_request(
                url='http://app.api.lianjia.com/house/community/search',
                callback=self.parse_communities,
                payload={
                    'bizcircle_id': meta['biz_circle_id'],
                    'group_type': 'community',
                    'limit_offset': new_offset,
                    'city_id': meta['city_id'],
                    'limit_count': 30
                },
                meta={**meta, 'offset': new_offset}
            )
    
    def parse_community_details(self, response):
        """Parse community detail page (HTML)"""
        community_data = response.meta['community_data']
        
        # Extract details using CSS selectors (similar to CaoZ approach)
        detail_keys = response.css('span.hdic_key::text').getall()
        detail_values = response.css('span.hdic_value::text').getall()
        
        details = {}
        for key, value in zip(detail_keys, detail_values):
            clean_key = key.rstrip('：')
            details[clean_key] = value
        
        if details:
            community_data['details'] = details
            community_data['type'] = 'community_detail'
            self.logger.info(f"📋 Community details: {community_data['community_name']} - {len(details)} fields")
        else:
            self.logger.warning(f"⚠️ No details found for community: {community_data['community_name']}")
        
        yield community_data
