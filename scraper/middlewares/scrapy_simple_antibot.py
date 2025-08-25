import random
import time
import logging
from scrapy import signals
from scrapy.downloadermiddlewares.retry import RetryMiddleware

try:
    from .simple_antibot import simple_antibot
    SIMPLE_ANTIBOT_AVAILABLE = True
except ImportError:
    SIMPLE_ANTIBOT_AVAILABLE = False
    logging.warning("Simple antibot not available")


class ScrapySimpleAntiBot:
    """
    Scrapy middleware using simple but effective anti-bot protection
    Focus on proven techniques without complex proxy management
    """
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        self.logger = logging.getLogger(__name__)
        
        if SIMPLE_ANTIBOT_AVAILABLE:
            self.antibot = simple_antibot
            self.use_antibot = True
            self.logger.info("✅ Simple AntiBot loaded - effective protection enabled")
        else:
            self.use_antibot = False
            self.logger.warning("⚠️ Simple AntiBot not available - using basic protection")
            
            # Fallback settings
            self.request_count = 0
            self.base_delay = 8
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            ]
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware
    
    def spider_opened(self, spider):
        if self.use_antibot:
            self.logger.info(f"🛡️ ScrapySimpleAntiBot activated for {spider.name}")
        else:
            self.logger.info(f"⚙️ Basic protection fallback for {spider.name}")
    
    def spider_closed(self, spider):
        if self.use_antibot:
            stats = self.antibot.get_stats()
            self.logger.info(f"📊 Final Anti-Bot Stats:")
            self.logger.info(f"   Total requests: {stats['total_requests']}")
            self.logger.info(f"   Success rate: {stats['success_rate']:.2%}")
            self.logger.info(f"   Blocked requests: {stats['blocked_requests']}")
            self.logger.info(f"   Final delay: {stats['current_delay']:.1f}s")
    
    def process_request(self, request, spider):
        """Apply anti-bot protection to request"""
        
        if self.use_antibot:
            # Use simple antibot system
            
            # Apply smart delay (done in antibot.smart_delay())
            self.antibot.smart_delay()
            
            # Set realistic headers
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            
            # Add user agent from antibot session
            if hasattr(self.antibot.session, 'headers'):
                ua = self.antibot.session.headers.get('User-Agent')
                if ua:
                    headers['User-Agent'] = ua
            
            # Apply headers to request
            for key, value in headers.items():
                request.headers[key] = value
            
            # Track request
            self.antibot.request_count += 1
            
            # Session refresh if needed
            if self.antibot.request_count >= self.antibot.session_duration:
                self.antibot.refresh_session()
            
            # User agent rotation
            if self.antibot.request_count % random.randint(20, 40) == 0:
                self.antibot.rotate_user_agent()
                request.headers['User-Agent'] = self.antibot.session.headers['User-Agent']
        
        else:
            # Fallback protection
            self.request_count += 1
            
            # Basic delay
            delay = random.uniform(self.base_delay * 0.8, self.base_delay * 1.2)
            time.sleep(delay)
            
            # Basic user agent rotation
            if self.request_count % 20 == 0:
                request.headers['User-Agent'] = random.choice(self.user_agents)
        
        return None
    
    def process_response(self, request, response, spider):
        """Handle response and detect blocking"""
        
        if self.use_antibot:
            # Use antibot's blocking detection
            if self.antibot.is_blocked(response):
                self.logger.warning(f"🚫 Blocking detected by SimpleAntiBot: {request.url}")
                
                # Handle blocking (this will apply delays and refresh session)
                self.antibot.handle_blocked_response(request.url)
                
                # Create retry request
                return self._create_retry_request(request, response, "SimpleAntiBot detected blocking")
            
            # Update success count
            self.antibot.success_count += 1
            self.antibot.consecutive_failures = 0
            self.antibot.adjust_delay_on_success()
        
        else:
            # Fallback blocking detection
            if self._is_blocked_fallback(response):
                self.logger.warning(f"🚫 Basic blocking detection: {request.url}")
                return self._create_retry_request(request, response, "Basic blocking detection")
        
        return response
    
    def _create_retry_request(self, request, response, reason):
        """Create retry request"""
        retries = request.meta.get('retry_times', 0) + 1
        max_retries = self.crawler.settings.getint('RETRY_TIMES', 8)
        
        if retries <= max_retries:
            retry_req = request.copy()
            retry_req.meta['retry_times'] = retries
            retry_req.dont_filter = True
            
            self.logger.info(f"🔄 Retrying {request.url} (attempt {retries}/{max_retries}) - {reason}")
            return retry_req
        else:
            self.logger.error(f"❌ Max retries exceeded for {request.url}")
            return response
    
    def _is_blocked_fallback(self, response):
        """Fallback blocking detection"""
        if response.status in [403, 429, 503]:
            return True
        
        if len(response.body) < 5000:
            return True
        
        content = response.body.lower()
        return any(keyword.encode() in content for keyword in [
            'access denied', 'forbidden', 'captcha', 'robot', 'blocked'
        ])


class EnhancedRetryMiddleware(RetryMiddleware):
    """
    Enhanced retry middleware with exponential backoff
    """
    
    def __init__(self, settings):
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
    
    def process_response(self, request, response, spider):
        if response.status in [403, 429, 503]:
            retries = request.meta.get('retry_times', 0)
            
            # Exponential backoff
            backoff_delay = min(2 ** retries, 60)  # Max 60 seconds
            jitter = random.uniform(0.5, 1.5)
            total_delay = backoff_delay * jitter
            
            self.logger.info(f"⏱️ Enhanced retry backoff: {total_delay:.1f}s for {request.url}")
            time.sleep(total_delay)
        
        return super().process_response(request, response, spider)
