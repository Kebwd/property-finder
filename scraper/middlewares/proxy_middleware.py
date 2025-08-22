import random
import requests
import logging
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message


class ProxyRotationMiddleware:
    """
    Proxy rotation middleware for IP rotation to bypass anti-bot detection
    Supports both free and premium proxy providers
    """
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        self.proxy_list = []
        self.current_proxy_index = 0
        self.failed_proxies = set()
        self.logger = logging.getLogger(__name__)
        
        # Load proxies from settings or external source
        self.load_proxies()
        
        # Proxy rotation settings
        self.rotate_after_requests = random.randint(30, 60)  # Rotate IP every 30-60 requests
        self.request_count = 0
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def load_proxies(self):
        """Load proxy list from various sources"""
        
        # Method 1: Load from settings
        proxy_list_setting = self.settings.get('PROXY_LIST', [])
        if proxy_list_setting:
            self.proxy_list.extend(proxy_list_setting)
            self.logger.info(f"Loaded {len(proxy_list_setting)} proxies from settings")
        
        # Method 2: Load from file
        proxy_file = self.settings.get('PROXY_FILE')
        if proxy_file:
            try:
                with open(proxy_file, 'r') as f:
                    file_proxies = [line.strip() for line in f if line.strip()]
                    self.proxy_list.extend(file_proxies)
                    self.logger.info(f"Loaded {len(file_proxies)} proxies from file: {proxy_file}")
            except FileNotFoundError:
                self.logger.warning(f"Proxy file not found: {proxy_file}")
        
        # Method 3: Load from free proxy API (example)
        if self.settings.getbool('USE_FREE_PROXIES', False):
            self.load_free_proxies()
        
        if not self.proxy_list:
            self.logger.warning("No proxies loaded. Proxy rotation disabled.")
        else:
            self.logger.info(f"Total proxies available: {len(self.proxy_list)}")
    
    def load_free_proxies(self):
        """Load free proxies from public APIs (use with caution)"""
        try:
            # Example: Free proxy API
            response = requests.get('https://api.proxyscrape.com/v2/?request=get&format=json&protocol=http&country=all')
            if response.status_code == 200:
                data = response.json()
                for proxy_info in data:
                    proxy = f"http://{proxy_info['ip']}:{proxy_info['port']}"
                    self.proxy_list.append(proxy)
                
                self.logger.info(f"Loaded {len(data)} free proxies")
        except Exception as e:
            self.logger.error(f"Failed to load free proxies: {e}")
    
    def get_random_proxy(self):
        """Get a random proxy that hasn't failed"""
        available_proxies = [p for p in self.proxy_list if p not in self.failed_proxies]
        
        if not available_proxies:
            # Reset failed proxies if all have failed
            self.failed_proxies.clear()
            available_proxies = self.proxy_list
            self.logger.warning("All proxies failed, resetting failed proxy list")
        
        if available_proxies:
            return random.choice(available_proxies)
        return None
    
    def process_request(self, request, spider):
        """Apply proxy rotation to requests"""
        if not self.proxy_list:
            return None
        
        self.request_count += 1
        
        # Rotate proxy every N requests or if no proxy is set
        if (self.request_count % self.rotate_after_requests == 0 or 
            'proxy' not in request.meta):
            
            proxy = self.get_random_proxy()
            if proxy:
                request.meta['proxy'] = proxy
                self.logger.debug(f"Using proxy: {proxy}")
        
        return None
    
    def process_response(self, request, response, spider):
        """Handle response and mark failed proxies"""
        
        # Check if proxy failed
        if response.status in [403, 407, 429, 503]:
            proxy = request.meta.get('proxy')
            if proxy:
                self.failed_proxies.add(proxy)
                self.logger.warning(f"Proxy failed: {proxy} (Status: {response.status})")
                
                # Retry with different proxy
                return self.retry_with_new_proxy(request, spider)
        
        return response
    
    def retry_with_new_proxy(self, request, spider):
        """Retry request with a new proxy"""
        retries = request.meta.get('retry_times', 0) + 1
        
        if retries <= self.crawler.settings.getint('RETRY_TIMES', 2):
            new_proxy = self.get_random_proxy()
            if new_proxy:
                retry_req = request.copy()
                retry_req.meta['proxy'] = new_proxy
                retry_req.meta['retry_times'] = retries
                retry_req.dont_filter = True
                
                self.logger.info(f"Retrying with new proxy: {new_proxy}")
                return retry_req
        
        return None


class SmartProxyMiddleware:
    """
    Smart proxy middleware that automatically detects and switches between
    direct connection and proxy based on success rates
    """
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        self.proxy_middleware = ProxyRotationMiddleware(crawler)
        self.use_proxy = True
        self.direct_success_rate = 0.0
        self.proxy_success_rate = 0.0
        self.request_count = 0
        self.direct_success_count = 0
        self.proxy_success_count = 0
        self.evaluation_interval = 50  # Evaluate every 50 requests
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def process_request(self, request, spider):
        """Decide whether to use proxy or direct connection"""
        self.request_count += 1
        
        # Evaluate success rates periodically
        if self.request_count % self.evaluation_interval == 0:
            self.evaluate_success_rates()
        
        # Apply proxy if enabled
        if self.use_proxy and self.proxy_middleware.proxy_list:
            return self.proxy_middleware.process_request(request, spider)
        
        return None
    
    def process_response(self, request, response, spider):
        """Track success rates and handle responses"""
        is_success = response.status == 200 and len(response.body) > 1000
        
        # Track success rates
        if 'proxy' in request.meta:
            if is_success:
                self.proxy_success_count += 1
        else:
            if is_success:
                self.direct_success_count += 1
        
        # Handle proxy responses
        if 'proxy' in request.meta:
            return self.proxy_middleware.process_response(request, response, spider)
        
        return response
    
    def evaluate_success_rates(self):
        """Evaluate which method (direct/proxy) is more successful"""
        if self.request_count < self.evaluation_interval:
            return
        
        # Calculate success rates
        total_requests = self.evaluation_interval
        proxy_requests = min(total_requests // 2, len(self.proxy_middleware.proxy_list))
        direct_requests = total_requests - proxy_requests
        
        if proxy_requests > 0:
            self.proxy_success_rate = self.proxy_success_count / proxy_requests
        if direct_requests > 0:
            self.direct_success_rate = self.direct_success_count / direct_requests
        
        # Decide which method to use
        if self.direct_success_rate > self.proxy_success_rate + 0.1:  # 10% threshold
            self.use_proxy = False
            self.logger.info(f"Switching to direct connection (success rate: {self.direct_success_rate:.2%})")
        else:
            self.use_proxy = True
            self.logger.info(f"Using proxy rotation (success rate: {self.proxy_success_rate:.2%})")
        
        # Reset counters
        self.proxy_success_count = 0
        self.direct_success_count = 0