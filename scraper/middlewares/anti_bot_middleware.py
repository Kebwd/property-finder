import random
import time
import json
import requests
from scrapy.http import HtmlResponse
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy import signals
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

# Import our consistent scraping manager
try:
    from .consistent_scraping import consistent_manager
    CONSISTENT_SCRAPING_AVAILABLE = True
except ImportError:
    CONSISTENT_SCRAPING_AVAILABLE = False
    logging.warning("Consistent scraping manager not available")


class ConsistentAntiBot:
    """
    Enhanced Anti-Bot middleware using consistent scraping manager
    Provides maximum success rate with adaptive strategies
    """
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        self.logger = logging.getLogger(__name__)
        
        # Use consistent manager if available
        if CONSISTENT_SCRAPING_AVAILABLE:
            self.manager = consistent_manager
            self.use_consistent_manager = True
            self.logger.info("✅ Consistent scraping manager loaded - maximum anti-bot protection enabled")
        else:
            self.use_consistent_manager = False
            self.logger.warning("⚠️  Consistent scraping manager not available - using fallback anti-bot")
            
            # Fallback configuration
            self.request_count = 0
            self.session = requests.Session()
            self.base_delay = 8
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware
    
    def spider_opened(self, spider):
        if self.use_consistent_manager:
            self.logger.info(f"🚀 ConsistentAntiBot activated for {spider.name} with proxy pool and adaptive delays")
        else:
            self.logger.info(f"🛡️  FallbackAntiBot activated for {spider.name}")
    
    def spider_closed(self, spider):
        if self.use_consistent_manager:
            stats = self.manager.get_stats()
            self.logger.info(f"📊 Final scraping stats:")
            self.logger.info(f"   Success rate: {stats['success_rate']:.2%}")
            self.logger.info(f"   Requests made: {stats['requests_made']}")
            self.logger.info(f"   Proxy success rate: {stats['proxy_stats']['success_rate']:.2%}")
    
    def process_request(self, request, spider):
        """Apply consistent anti-bot protection"""
        
        if self.use_consistent_manager:
            # Use consistent manager for optimal protection
            
            # Add random jitter to delay
            base_delay = self.manager.current_delay
            jitter = random.uniform(-0.2, 0.2) * base_delay
            delay = base_delay + jitter
            
            time.sleep(max(1, delay))
            
            # Set optimal headers (manager will handle user-agent)
            enhanced_headers = {
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
            
            for key, value in enhanced_headers.items():
                request.headers[key] = value
            
            # Get best proxy from pool
            proxy = self.manager.proxy_pool.get_best_proxy()
            if proxy:
                request.meta['proxy'] = proxy
                self.logger.debug(f"Using proxy: {proxy}")
            
        else:
            # Fallback anti-bot protection
            self.request_count += 1
            
            # Basic delay
            delay = random.uniform(self.base_delay * 0.8, self.base_delay * 1.2)
            time.sleep(delay)
            
            # Basic headers
            request.headers['User-Agent'] = random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ])
        
        return None
    
    def process_response(self, request, response, spider):
        """Handle response with consistent anti-bot logic"""
        
        if self.use_consistent_manager:
            # Use consistent manager's blocking detection
            if self.manager.is_blocked_response(response):
                self.logger.warning(f"🚫 Blocking detected: {request.url}")
                
                # Mark proxy as failed if used
                proxy = request.meta.get('proxy')
                if proxy:
                    self.manager.proxy_pool.mark_proxy_failed(proxy)
                
                # Handle blocking
                self.manager.handle_blocking()
                
                # Create retry request
                return self._create_retry_request(request, "Consistent manager detected blocking")
            
            # Update success stats
            self.manager.success_count += 1
            
        else:
            # Fallback blocking detection
            if self._is_blocked_response_fallback(response):
                self.logger.warning(f"🚫 Fallback blocking detected: {request.url}")
                return self._create_retry_request(request, "Fallback detected blocking")
        
        return response
    
    def _create_retry_request(self, request, reason):
        """Create a retry request with updated settings"""
        retries = request.meta.get('retry_times', 0) + 1
        max_retries = self.crawler.settings.getint('RETRY_TIMES', 5)
        
        if retries <= max_retries:
            retry_req = request.copy()
            retry_req.meta['retry_times'] = retries
            retry_req.dont_filter = True
            
            # Remove failed proxy
            if 'proxy' in retry_req.meta:
                del retry_req.meta['proxy']
            
            self.logger.info(f"🔄 Retrying {request.url} (attempt {retries}/{max_retries}) - {reason}")
            return retry_req
        else:
            self.logger.error(f"❌ Max retries exceeded for {request.url}")
            return None
    
    def _is_blocked_response_fallback(self, response):
        """Fallback blocking detection"""
        if response.status in [403, 429, 503]:
            return True
        
        if len(response.body) < 1000:
            return True
        
        content_lower = response.body.lower()
        blocking_indicators = [
            b'access denied', b'forbidden', b'captcha',
            '验证码'.encode('utf-8'), '人机验证'.encode('utf-8'),
            b'robot', b'blocked'
        ]
        
        return any(indicator in content_lower for indicator in blocking_indicators)
    """
    Advanced Anti-Bot Middleware implementing multiple evasion techniques:
    1. Random delays between requests (30-60 requests intervals)
    2. Session management with cookie persistence
    3. User-agent rotation with real browser signatures
    4. IP rotation support (requires proxy provider)
    5. Enhanced browser fingerprint randomization
    """
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        self.request_count = 0
        self.session_request_count = 0
        self.current_session = requests.Session()
        self.last_user_agent_change = 0
        self.current_proxy = None
        
        # Session management settings
        self.session_duration = random.randint(30, 60)  # Keep session for 30-60 requests
        self.user_agent_change_interval = random.randint(30, 60)  # Change UA every 30-60 requests
        
        # Real browser user agents - frequently updated ones
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # Common accept headers for different browsers
        self.accept_headers = [
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        ]
        
        # Accept-Language variations
        self.accept_languages = [
            'zh-CN,zh;q=0.9,en;q=0.8',
            'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'zh-CN,zh;q=0.9',
            'zh,en-US;q=0.9,en;q=0.8',
        ]
        
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware
    
    def spider_opened(self, spider):
        self.logger.info(f"AntiBot middleware activated for spider: {spider.name}")
        
    def spider_closed(self, spider):
        if hasattr(self, 'current_session'):
            self.current_session.close()
    
    def process_request(self, request, spider):
        """Apply anti-bot techniques to each request"""
        self.request_count += 1
        self.session_request_count += 1
        
        # 1. Random delays between requests
        delay = random.uniform(2, 8)  # 2-8 seconds delay
        if self.request_count % random.randint(5, 10) == 0:
            # Occasionally longer delays to appear more human
            delay = random.uniform(10, 20)
        
        time.sleep(delay)
        
        # 2. Session management - refresh session every 30-60 requests
        if self.session_request_count >= self.session_duration:
            self._refresh_session()
        
        # 3. User-agent rotation
        if (self.request_count - self.last_user_agent_change) >= self.user_agent_change_interval:
            self._rotate_user_agent(request)
        
        # 4. Enhanced headers with browser fingerprinting
        self._set_realistic_headers(request)
        
        # 5. Apply proxy rotation if available
        self._apply_proxy_rotation(request)
        
        self.logger.debug(f"Request #{self.request_count} processed with anti-bot protection")
        return None
    
    def _refresh_session(self):
        """Refresh the session and reset counters"""
        if hasattr(self, 'current_session'):
            self.current_session.close()
        
        self.current_session = requests.Session()
        self.session_request_count = 0
        self.session_duration = random.randint(30, 60)
        
        self.logger.info("Session refreshed - cleared cookies and reset connection")
    
    def _rotate_user_agent(self, request):
        """Rotate user agent and update change tracking"""
        new_ua = random.choice(self.user_agents)
        request.headers['User-Agent'] = new_ua
        self.last_user_agent_change = self.request_count
        self.user_agent_change_interval = random.randint(30, 60)
        
        self.logger.debug(f"User-Agent rotated to: {new_ua[:50]}...")
    
    def _set_realistic_headers(self, request):
        """Set realistic browser headers to avoid detection"""
        headers = {
            'Accept': random.choice(self.accept_headers),
            'Accept-Language': random.choice(self.accept_languages),
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
        
        # Apply headers to request
        for key, value in headers.items():
            request.headers[key] = value
    
    def _apply_proxy_rotation(self, request):
        """Apply proxy rotation if proxy list is available"""
        # TODO: Implement proxy rotation when proxy provider is available
        # For now, this is a placeholder for future proxy integration
        
        # Example implementation (uncomment when you have proxies):
        # if hasattr(self, 'proxy_list') and self.proxy_list:
        #     if self.request_count % random.randint(30, 60) == 0:
        #         self.current_proxy = random.choice(self.proxy_list)
        #         request.meta['proxy'] = self.current_proxy
        #         self.logger.debug(f"Proxy rotated to: {self.current_proxy}")
        
        pass
    
    def process_response(self, request, response, spider):
        """Handle response and detect if we've been blocked"""
        
        # Check for common anti-bot responses
        if self._is_blocked_response(response):
            self.logger.warning(f"Potential blocking detected for URL: {request.url}")
            
            # Trigger more aggressive anti-bot measures
            self._handle_blocking_detected()
            
            # Return a retry request instead of None
            retries = request.meta.get('retry_times', 0) + 1
            
            if retries <= self.crawler.settings.getint('RETRY_TIMES', 2):
                retry_req = request.copy()
                retry_req.meta['retry_times'] = retries
                retry_req.dont_filter = True
                
                self.logger.info(f"Retrying blocked request: {request.url} (attempt {retries})")
                return retry_req
            else:
                self.logger.error(f"Max retries exceeded for blocked URL: {request.url}")
                return response
        
        return response
    
    def _is_blocked_response(self, response):
        """Detect if the response indicates we've been blocked"""
        # Common indicators of being blocked
        blocking_indicators = [
            b'Access Denied',
            b'Forbidden',
            b'captcha',
            '验证码'.encode('utf-8'),  # Chinese for verification code
            '人机验证'.encode('utf-8'),  # Chinese for human verification
            b'robot',
            b'blocked',
            b'429',  # Too Many Requests
            b'503',  # Service Unavailable
        ]
        
        response_body = response.body.lower()
        
        # Check status code
        if response.status in [403, 429, 503]:
            return True
        
        # Check response content
        for indicator in blocking_indicators:
            if indicator in response_body:
                return True
        
        # Check if response is unusually small (might be a block page)
        if len(response.body) < 1000 and response.status == 200:
            return True
        
        return False
    
    def _handle_blocking_detected(self):
        """Handle detection of blocking - implement more aggressive measures"""
        self.logger.warning("Blocking detected! Implementing aggressive anti-bot measures...")
        
        # Force session refresh
        self._refresh_session()
        
        # Increase delays significantly
        extended_delay = random.uniform(60, 120)  # 1-2 minute delay
        self.logger.info(f"Sleeping for {extended_delay:.1f} seconds due to blocking detection")
        time.sleep(extended_delay)
        
        # Reset request counters to restart patterns
        self.request_count = 0
        self.session_request_count = 0


class ShadowUserAgentMiddleware:
    """
    Advanced User-Agent rotation using multiple libraries
    Priority: fake-useragent > shadow-useragent > fallback list
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.use_fake_ua = False
        self.use_shadow = False
        
        # Try fake-useragent first (more reliable)
        try:
            from fake_useragent import UserAgent
            self.fake_ua = UserAgent()
            self.use_fake_ua = True
            self.logger.info("Fake-UserAgent library loaded for UA rotation")
        except ImportError:
            self.logger.warning("Fake-UserAgent library not available")
        
        # Try shadow-useragent as backup
        if not self.use_fake_ua:
            try:
                from shadow_useragent import ShadowUserAgent
                self.sua = ShadowUserAgent()
                self.use_shadow = True
                self.logger.info("Shadow-UserAgent library loaded for UA rotation")
            except ImportError:
                self.logger.warning("Shadow-UserAgent library not available")
        
        # Fallback user agents if both libraries fail
        self.fallback_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        ]
        
        if not self.use_fake_ua and not self.use_shadow:
            self.logger.info("Using fallback user agent rotation")
    
    def process_request(self, request, spider):
        ua = None
        
        # Try fake-useragent first
        if self.use_fake_ua:
            try:
                ua = self.fake_ua.random
            except Exception as e:
                self.logger.warning(f"Fake-UserAgent error: {e}")
                self.use_fake_ua = False
        
        # Try shadow-useragent as backup
        if not ua and self.use_shadow:
            try:
                ua = self.sua.get_useragent()
            except Exception as e:
                self.logger.warning(f"Shadow-UserAgent error: {e}")
                self.use_shadow = False
        
        # Use fallback if both fail
        if not ua:
            ua = random.choice(self.fallback_agents)
        
        request.headers['User-Agent'] = ua
        return None


class EnhancedRetryMiddleware(RetryMiddleware):
    """
    Enhanced retry middleware with intelligent backoff for anti-bot scenarios
    """
    
    def __init__(self, settings):
        super().__init__(settings)
        self.backoff_factor = 2
        self.max_backoff = 300  # 5 minutes max backoff
    
    def process_response(self, request, response, spider):
        if response.status in [403, 429, 503]:
            # Calculate backoff delay
            retries = request.meta.get('retry_times', 0)
            delay = min(self.backoff_factor ** retries, self.max_backoff)
            
            spider.logger.info(f"Anti-bot response detected, backing off for {delay} seconds")
            time.sleep(delay)
        
        return super().process_response(request, response, spider)
