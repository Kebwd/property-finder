import scrapy
import re
import time
import random
from urllib.parse import urljoin


class LianjiaSimpleSpider(scrapy.Spider):
    """
    Production Lianjia spider with conservative approach
    Designed for manual CAPTCHA solving and long-term stability
    """
    name = 'lianjia_simple'
    
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
        'DOWNLOAD_DELAY': 30,  # Very conservative delay
        'RANDOMIZE_DOWNLOAD_DELAY': 0.9,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 20,
        'AUTOTHROTTLE_MAX_DELAY': 180,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.05,
        'RETRY_TIMES': 1,
        'DOWNLOAD_TIMEOUT': 180,
        'ROBOTSTXT_OBEY': False,
        'COOKIES_ENABLED': True,
        'DUPEFILTER_DEBUG': True,
    }
    
    def __init__(self, city='guangzhou', max_pages=2, *args, **kwargs):
        super(LianjiaSimpleSpider, self).__init__(*args, **kwargs)
        self.city = city.lower()
        self.domain = self.CITY_DOMAINS.get(self.city, 'gz.lianjia.com')
        self.max_pages = int(max_pages)
        self.captcha_count = 0
        self.success_count = 0
        self.logger.info(f"Starting Lianjia spider for {self.city} (max {self.max_pages} pages)")
    
    def start_requests(self):
        """Start with a single page to test connectivity"""
        base_url = f"https://{self.domain}/ershoufang/"
        
        yield scrapy.Request(
            url=base_url,
            callback=self.parse_listings_page,
            meta={'page': 1, 'dont_retry': True},
            headers=self.get_headers(),
            dont_filter=True
        )
    
    def get_headers(self):
        """Get realistic browser headers"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }
    
    def is_captcha_page(self, response):
        """Check if response is a CAPTCHA page"""
        captcha_indicators = [
            '人机验证',
            'CAPTCHA',
            'captcha',
            'verification',
            'captcha-anti-spider',
            'blocked'
        ]
        
        content = response.text.lower()
        return any(indicator in content for indicator in captcha_indicators)
    
    def parse_listings_page(self, response):
        """Parse property listings from search results"""
        page = response.meta.get('page', 1)
        
        self.logger.info(f"Processing page {page}: {response.url}")
        self.logger.info(f"Response status: {response.status}, length: {len(response.body)}")
        
        # Check for CAPTCHA
        if self.is_captcha_page(response):
            self.captcha_count += 1
            self.logger.error(f"🚫 CAPTCHA detected on page {page}")
            self.logger.error("⚠️  Manual intervention required:")
            self.logger.error(f"    1. Open browser and visit: {response.url}")
            self.logger.error("    2. Solve CAPTCHA manually")
            self.logger.error("    3. Wait for session to be established")
            self.logger.error("    4. Re-run spider after 10-15 minutes")
            return
        
        # Success - log and continue
        self.success_count += 1
        self.logger.info(f"✅ Successfully accessed page {page}")
        
        # Extract property links with multiple selector strategies
        property_links = self.extract_property_links(response)
        
        if not property_links:
            self.logger.warning(f"No property links found on page {page}")
            # Log page structure for debugging
            self.log_page_structure(response)
            return
        
        self.logger.info(f"Found {len(property_links)} properties on page {page}")
        
        # Process properties (limit to first 3 for testing)
        for i, link in enumerate(property_links[:3]):
            if link.startswith('/'):
                full_url = f"https://{self.domain}{link}"
            else:
                full_url = link
            
            # Add delay between property requests
            delay = random.uniform(10, 20)
            
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_property,
                meta={'page': page, 'property_index': i, 'delay': delay},
                headers=self.get_headers(),
                dont_filter=True
            )
        
        # Continue to next page if within limit
        if page < self.max_pages and len(property_links) > 0:
            next_page = page + 1
            next_url = f"https://{self.domain}/ershoufang/pg{next_page}/"
            
            # Add significant delay before next page
            time.sleep(random.uniform(30, 45))
            
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_listings_page,
                meta={'page': next_page},
                headers=self.get_headers(),
                dont_filter=True
            )
    
    def extract_property_links(self, response):
        """Extract property links using multiple strategies"""
        selectors = [
            'li.clear.LOGVIEWDATA a::attr(href)',
            '.sellListContent li .title a::attr(href)',
            '.resblock-list li a::attr(href)',
            'ul.sellListContent li a[data-log_index]::attr(href)',
            '.info.clear .title a::attr(href)',
            '.LOGCLICKDATA::attr(href)',
            'a[href*="/ershoufang/"]::attr(href)'
        ]
        
        for selector in selectors:
            links = response.css(selector).getall()
            if links:
                # Filter for valid property links
                valid_links = [
                    link for link in links 
                    if '/ershoufang/' in link and link.count('/') >= 3
                ]
                if valid_links:
                    self.logger.info(f"Extracted {len(valid_links)} links using: {selector}")
                    return valid_links
        
        return []
    
    def log_page_structure(self, response):
        """Log page structure for debugging"""
        # Log available CSS classes
        all_classes = response.css('*::attr(class)').getall()
        unique_classes = list(set([cls for cls in all_classes if cls]))[:20]
        self.logger.info(f"Available CSS classes: {unique_classes}")
        
        # Log all links
        all_links = response.css('a::attr(href)').getall()
        property_related = [link for link in all_links if 'ershoufang' in link][:10]
        self.logger.info(f"Property-related links: {property_related}")
    
    def parse_property(self, response):
        """Parse individual property details"""
        page = response.meta.get('page', 1)
        prop_index = response.meta.get('property_index', 0)
        
        self.logger.info(f"Parsing property {prop_index+1} from page {page}: {response.url}")
        
        # Check for CAPTCHA on property page
        if self.is_captcha_page(response):
            self.captcha_count += 1
            self.logger.error(f"🚫 CAPTCHA on property page {prop_index+1}")
            return
        
        try:
            # Extract property data with multiple fallbacks
            property_data = self.extract_property_data(response)
            
            if property_data and property_data.get('name'):
                self.logger.info(f"✅ Extracted: {property_data['name']} - ¥{property_data.get('deal_price', 'N/A')}")
                yield property_data
            else:
                self.logger.warning(f"⚠️  Failed to extract data from: {response.url}")
                
        except Exception as e:
            self.logger.error(f"Error parsing property {response.url}: {e}")
    
    def extract_property_data(self, response):
        """Extract property data with multiple fallback strategies"""
        # Title extraction
        title_selectors = [
            'h1.main::text',
            '.title h1::text',
            '.property-content .title::text',
            'h1::text',
            '.sellDetailHeader h1::text',
            '.house-title h1::text'
        ]
        
        title = None
        for selector in title_selectors:
            title = response.css(selector).get()
            if title:
                title = title.strip()
                break
        
        # Price extraction
        price_selectors = [
            '.price .total::text',
            '.unitPrice .total::text',
            '.overview .price .total::text',
            '.price-container .total::text',
            '.house-price .total::text'
        ]
        
        price_text = None
        for selector in price_selectors:
            price_text = response.css(selector).get()
            if price_text:
                break
        
        deal_price = None
        if price_text:
            price_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
            if price_match:
                deal_price = float(price_match.group(1)) * 10000  # Convert 万 to yuan
        
        # Area extraction
        area_selectors = [
            '.area .mainInfo::text',
            '.overview .area::text',
            '.house-area::text'
        ]
        
        area_text = None
        for selector in area_selectors:
            area_text = response.css(selector).get()
            if area_text:
                break
        
        area = None
        if area_text:
            area_match = re.search(r'(\d+(?:\.\d+)?)', area_text)
            area = float(area_match.group(1)) if area_match else None
        
        # Room layout
        room_selectors = [
            '.room .mainInfo::text',
            '.overview .room::text',
            '.house-room::text'
        ]
        
        room_layout = None
        for selector in room_selectors:
            room_layout = response.css(selector).get()
            if room_layout:
                room_layout = room_layout.strip()
                break
        
        # Location info
        location_selectors = [
            '.communityName .info a::text',
            '.community .info a::text',
            '.house-community a::text'
        ]
        
        location_info = []
        for selector in location_selectors:
            location_info = response.css(selector).getall()
            if location_info:
                break
        
        district = location_info[0] if len(location_info) > 0 else None
        subdistrict = location_info[1] if len(location_info) > 1 else None
        
        # Community name
        community_selectors = [
            '.communityName a.info::text',
            '.community a::text',
            '.house-community a::text'
        ]
        
        community_name = None
        for selector in community_selectors:
            community_name = response.css(selector).get()
            if community_name:
                community_name = community_name.strip()
                break
        
        if not title:
            return None
        
        return {
            'type': 'house',
            'source': 'lianjia',
            'city': self.city,
            'name': title,
            'building_name_zh': community_name or title,
            'deal_price': deal_price or 0,
            'area': area,
            'room_layout': room_layout,
            'district': district,
            'subdistrict': subdistrict,
            'url': response.url,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def closed(self, reason):
        """Log spider completion stats"""
        self.logger.info(f"Spider completed: {reason}")
        self.logger.info(f"📊 Final Stats:")
        self.logger.info(f"   ✅ Successful pages: {self.success_count}")
        self.logger.info(f"   🚫 CAPTCHA pages: {self.captcha_count}")
        
        if self.captcha_count > 0:
            self.logger.info("🔧 CAPTCHA Resolution Tips:")
            self.logger.info("   1. Use residential proxy services")
            self.logger.info("   2. Implement longer delays (60+ seconds)")
            self.logger.info("   3. Run during off-peak hours")
            self.logger.info("   4. Consider alternative data sources")
