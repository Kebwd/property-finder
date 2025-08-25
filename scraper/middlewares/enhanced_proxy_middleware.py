#!/usr/bin/env python3
"""
Enhanced Proxy Middleware for Scrapy
Integrates with Simple AntiBot for maximum success
"""

import random
import logging
import requests
import time
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
from scrapy import signals
import os


class EnhancedProxyMiddleware:
    """
    Enhanced proxy middleware with intelligent rotation and health checking
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.proxies = []
        self.working_proxies = []
        self.failed_proxies = set()
        self.proxy_stats = {}
        self.current_proxy_index = 0
        
        # Performance settings
        self.health_check_interval = 50  # Check proxy health every 50 requests
        self.request_count = 0
        self.max_failures_per_proxy = 3
        
        # Load proxies
        self.load_proxies()
        
        # Test proxies on startup
        if self.proxies:
            self.test_proxy_health()
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    def spider_opened(self, spider):
        self.logger.info(f"🔗 Enhanced Proxy Middleware activated for {spider.name}")
        self.logger.info(f"📊 Loaded {len(self.working_proxies)} working proxies")
    
    def load_proxies(self):
        """Load proxies ONLY from proxy_list.txt - NO free proxies for ScraperAPI-only mode"""
        
        # Load from proxy_list.txt ONLY
        proxy_file = os.path.join(os.path.dirname(__file__), '..', 'proxy_list.txt')
        if os.path.exists(proxy_file):
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('https://'):
                        self.proxies.append(line)
        
        # DISABLED: No free proxy loading in ScraperAPI-only mode
        # This ensures only premium ScraperAPI proxies are used
        if not self.proxies:
            self.logger.warning("⚠️ No premium proxies found in proxy_list.txt")
            self.logger.info("🔧 ScraperAPI-only mode: Add your ScraperAPI credentials to proxy_list.txt")
        else:
            self.logger.info(f"🎯 ScraperAPI-only mode: Using {len(self.proxies)} premium proxies")
        
        self.logger.info(f"📋 Loaded {len(self.proxies)} proxies from configuration")
    
    def load_free_proxies(self):
        """Load free proxies from public APIs"""
        
        # Try multiple free proxy sources
        free_proxy_sources = [
            {
                'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                'format': 'plain'
            },
            {
                'url': 'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt', 
                'format': 'plain'
            },
            {
                'url': 'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
                'format': 'plain'
            }
        ]
        
        for source in free_proxy_sources:
            try:
                self.logger.info(f"🔍 Loading free proxies from {source['url']}")
                response = requests.get(source['url'], timeout=15)
                
                if response.status_code == 200:
                    content = response.text.strip()
                    if content and not content.startswith('<!DOCTYPE') and not content.startswith('{'):
                        proxy_list = content.split('\n')
                        valid_proxies = []
                        
                        for proxy in proxy_list:
                            proxy = proxy.strip()
                            # Validate proxy format (IP:PORT)
                            if proxy and ':' in proxy and len(proxy.split(':')) == 2:
                                ip, port = proxy.split(':')
                                if ip.replace('.', '').isdigit() and port.isdigit():
                                    valid_proxies.append(proxy)
                        
                        if valid_proxies:
                            self.proxies.extend(valid_proxies[:20])  # Take first 20
                            self.logger.info(f"✅ Loaded {len(valid_proxies[:20])} valid free proxies")
                            break  # Use first successful source
                        else:
                            self.logger.warning(f"⚠️ No valid proxies found in response")
                    else:
                        self.logger.warning(f"⚠️ Invalid response format from {source['url']}")
                else:
                    self.logger.warning(f"⚠️ Failed to fetch from {source['url']}: {response.status_code}")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Error loading from {source['url']}: {e}")
        
        # Add some reliable free proxies as fallback
        fallback_proxies = [
            '8.8.8.8:8080',      # Google DNS (might work)
            '1.1.1.1:8080',      # Cloudflare DNS (might work)  
            '208.67.222.222:8080', # OpenDNS (might work)
        ]
        
        if not self.proxies:
            self.logger.info("📋 Using fallback proxy list")
            self.proxies.extend(fallback_proxies)
        
        # Remove duplicates
        self.proxies = list(set(self.proxies))
    
    def test_proxy_health(self):
        """Test proxy health on startup"""
        
        self.logger.info("🔍 Testing proxy health...")
        test_url = "http://httpbin.org/ip"
        
        for proxy in self.proxies[:20]:  # Test first 20 proxies
            if self.test_single_proxy(proxy, test_url):
                self.working_proxies.append(proxy)
                self.proxy_stats[proxy] = {'success': 1, 'failures': 0}
            else:
                self.failed_proxies.add(proxy)
        
        self.logger.info(f"✅ {len(self.working_proxies)} proxies are working")
        
        # If no working proxies, add some proxies to working list anyway
        if not self.working_proxies and self.proxies:
            self.working_proxies = self.proxies[:10]  # Try first 10
            self.logger.warning("⚠️ No proxies passed health check, using first 10 anyway")
    
    def test_single_proxy(self, proxy, test_url):
        """Test a single proxy"""
        
        try:
            proxy_dict = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
            response = requests.get(test_url, proxies=proxy_dict, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def get_next_proxy(self):
        """Get next working proxy with rotation"""
        
        if not self.working_proxies:
            return None
        
        # Round-robin with random start
        proxy = self.working_proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.working_proxies)
        
        return proxy
    
    def process_request(self, request, spider):
        """Process request with proxy"""
        
        self.request_count += 1
        
        # Skip proxy for local/test URLs
        if any(domain in request.url for domain in ['localhost', '127.0.0.1', 'httpbin.org']):
            return None
        
        # Get proxy
        proxy = self.get_next_proxy()
        if not proxy:
            self.logger.warning("⚠️ No working proxies available")
            return None
        
        # Set proxy
        request.meta['proxy'] = f'http://{proxy}'
        request.meta['proxy_address'] = proxy
        
        # Add proxy info to headers for debugging
        request.headers['X-Proxy-Used'] = proxy.split('@')[-1] if '@' in proxy else proxy
        
        self.logger.debug(f"🔗 Using proxy: {proxy} for {request.url}")
        
        # Periodic health check
        if self.request_count % self.health_check_interval == 0:
            self.refresh_proxy_health()
        
        return None
    
    def process_response(self, request, response, spider):
        """Process response and update proxy stats"""
        
        proxy = request.meta.get('proxy_address')
        if proxy:
            if response.status in [200, 201, 202]:
                # Success
                if proxy in self.proxy_stats:
                    self.proxy_stats[proxy]['success'] += 1
                    # Reset failures on success
                    self.proxy_stats[proxy]['failures'] = 0
            else:
                # Failure
                self.handle_proxy_failure(proxy, response.status)
        
        return response
    
    def process_exception(self, request, exception, spider):
        """Handle request exceptions"""
        
        proxy = request.meta.get('proxy_address')
        if proxy:
            self.handle_proxy_failure(proxy, f"Exception: {exception}")
        
        return None
    
    def handle_proxy_failure(self, proxy, reason):
        """Handle proxy failure"""
        
        if proxy not in self.proxy_stats:
            self.proxy_stats[proxy] = {'success': 0, 'failures': 0}
        
        self.proxy_stats[proxy]['failures'] += 1
        
        self.logger.warning(f"⚠️ Proxy failure: {proxy} - {reason}")
        
        # Remove proxy if too many failures
        if self.proxy_stats[proxy]['failures'] >= self.max_failures_per_proxy:
            self.remove_failed_proxy(proxy)
    
    def remove_failed_proxy(self, proxy):
        """Remove failed proxy from working list"""
        
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
            self.failed_proxies.add(proxy)
            self.logger.warning(f"🚫 Removed failed proxy: {proxy}")
            
            # Adjust current index if needed
            if self.current_proxy_index >= len(self.working_proxies) and self.working_proxies:
                self.current_proxy_index = 0
    
    def refresh_proxy_health(self):
        """Refresh proxy health periodically"""
        
        self.logger.info("🔄 Refreshing proxy health...")
        
        # Test a few failed proxies to see if they're working again
        failed_to_test = list(self.failed_proxies)[:5]
        for proxy in failed_to_test:
            if self.test_single_proxy(proxy, "http://httpbin.org/ip"):
                self.failed_proxies.remove(proxy)
                self.working_proxies.append(proxy)
                self.proxy_stats[proxy] = {'success': 1, 'failures': 0}
                self.logger.info(f"✅ Restored proxy: {proxy}")
        
        self.logger.info(f"📊 Working proxies: {len(self.working_proxies)}")


class ProxyRetryMiddleware(RetryMiddleware):
    """
    Enhanced retry middleware that works with proxy rotation
    """
    
    def __init__(self, settings):
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)
        # Define exceptions to retry
        self.EXCEPTIONS_TO_RETRY = (
            ConnectionRefusedError,
            ConnectionResetError,
            TimeoutError,
            OSError,
            Exception  # Catch-all for proxy-related errors
        )
    
    def process_response(self, request, response, spider):
        """Process response with proxy-aware retry logic"""
        
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            
            # For proxy-related errors, try different proxy
            if response.status in [407, 502, 503, 504]:
                self.logger.info(f"🔄 Proxy error {response.status}, will retry with different proxy")
                # Force proxy rotation on next request
                request.meta.pop('proxy_address', None)
            
            return self._retry(request, reason, spider) or response
        
        return response
    
    def process_exception(self, request, exception, spider):
        """Process exception with proxy-aware retry logic"""
        
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY):
            # For connection errors, try different proxy
            self.logger.info(f"🔄 Connection error, will retry with different proxy: {exception}")
            request.meta.pop('proxy_address', None)
            
            return self._retry(request, str(exception), spider)
