#!/usr/bin/env python3
"""
Premium Proxy Integration for Consistent Scraping Success
Implements rotating proxy pools with health monitoring
"""

import random
import requests
import time
import logging
from typing import List, Dict, Optional
import threading
from datetime import datetime, timedelta


class ProxyPool:
    """
    Advanced proxy pool management with health monitoring and rotation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.proxies = []
        self.failed_proxies = set()
        self.proxy_stats = {}
        self.last_health_check = datetime.now() - timedelta(hours=1)
        self.health_check_interval = 300  # 5 minutes
        self.lock = threading.Lock()
        
        # Load proxies from multiple sources
        self.load_all_proxies()
    
    def load_all_proxies(self):
        """Load proxies from all available sources"""
        
        # Method 1: Free proxy services (for testing)
        free_proxies = self.get_free_proxies()
        
        # Method 2: Premium proxy services (recommended for production)
        premium_proxies = self.get_premium_proxies()
        
        # Method 3: Load from file
        file_proxies = self.load_proxy_file()
        
        # Combine all sources
        all_proxies = free_proxies + premium_proxies + file_proxies
        
        # Remove duplicates and initialize stats
        unique_proxies = list(set(all_proxies))
        
        with self.lock:
            self.proxies = unique_proxies
            for proxy in self.proxies:
                if proxy not in self.proxy_stats:
                    self.proxy_stats[proxy] = {
                        'success_count': 0,
                        'failure_count': 0,
                        'last_used': None,
                        'avg_response_time': 0,
                        'consecutive_failures': 0
                    }
        
        self.logger.info(f"Loaded {len(self.proxies)} proxies from all sources")
        
        # Initial health check
        if self.proxies:
            self.health_check_proxies()
    
    def get_free_proxies(self) -> List[str]:
        """Get free proxies from public APIs"""
        free_proxies = []
        
        try:
            # Free proxy API 1
            response = requests.get(
                'https://www.proxy-list.download/api/v1/get?type=http',
                timeout=10
            )
            if response.status_code == 200:
                for line in response.text.strip().split('\n'):
                    if ':' in line:
                        ip, port = line.strip().split(':')
                        free_proxies.append(f'http://{ip}:{port}')
        except Exception as e:
            self.logger.warning(f"Failed to load free proxies from API 1: {e}")
        
        try:
            # Free proxy API 2
            response = requests.get(
                'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                timeout=10
            )
            if response.status_code == 200:
                for line in response.text.strip().split('\n'):
                    if ':' in line:
                        ip, port = line.strip().split(':')
                        free_proxies.append(f'http://{ip}:{port}')
        except Exception as e:
            self.logger.warning(f"Failed to load free proxies from API 2: {e}")
        
        self.logger.info(f"Loaded {len(free_proxies)} free proxies")
        return free_proxies[:50]  # Limit to 50 free proxies
    
    def get_premium_proxies(self) -> List[str]:
        """Get premium proxy configurations"""
        # Example premium proxy configurations
        # Replace with your actual premium proxy credentials
        
        premium_proxies = []
        
        # Example: Bright Data (replace with your credentials)
        # premium_proxies.extend([
        #     'http://username:password@proxy1.brightdata.com:22225',
        #     'http://username:password@proxy2.brightdata.com:22225',
        # ])
        
        # Example: Oxylabs (replace with your credentials)
        # premium_proxies.extend([
        #     'http://username:password@proxy.oxylabs.io:10000',
        #     'http://username:password@proxy.oxylabs.io:10001',
        # ])
        
        # Example: ProxyMesh (replace with your credentials)
        # premium_proxies.extend([
        #     'http://username:password@us.proxymesh.com:31280',
        #     'http://username:password@jp.proxymesh.com:31280',
        # ])
        
        if premium_proxies:
            self.logger.info(f"Loaded {len(premium_proxies)} premium proxies")
        else:
            self.logger.info("No premium proxies configured - add your proxy service credentials")
        
        return premium_proxies
    
    def load_proxy_file(self) -> List[str]:
        """Load proxies from local file"""
        file_proxies = []
        
        try:
            with open('proxy_list.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if not line.startswith('http'):
                            line = f'http://{line}'
                        file_proxies.append(line)
            
            self.logger.info(f"Loaded {len(file_proxies)} proxies from file")
        except FileNotFoundError:
            self.logger.info("No proxy_list.txt file found")
        except Exception as e:
            self.logger.warning(f"Error loading proxy file: {e}")
        
        return file_proxies
    
    def health_check_proxies(self):
        """Check proxy health and remove failed ones"""
        if datetime.now() - self.last_health_check < timedelta(seconds=self.health_check_interval):
            return
        
        self.logger.info("Starting proxy health check...")
        
        test_url = 'https://httpbin.org/ip'
        healthy_proxies = []
        
        for proxy in self.proxies[:20]:  # Test first 20 proxies
            if self.test_proxy(proxy, test_url):
                healthy_proxies.append(proxy)
                with self.lock:
                    self.proxy_stats[proxy]['consecutive_failures'] = 0
            else:
                with self.lock:
                    self.proxy_stats[proxy]['consecutive_failures'] += 1
                    if self.proxy_stats[proxy]['consecutive_failures'] >= 3:
                        self.failed_proxies.add(proxy)
        
        self.logger.info(f"Health check complete: {len(healthy_proxies)} healthy proxies")
        self.last_health_check = datetime.now()
    
    def test_proxy(self, proxy: str, test_url: str, timeout: int = 10) -> bool:
        """Test if a proxy is working"""
        try:
            start_time = time.time()
            response = requests.get(
                test_url,
                proxies={'http': proxy, 'https': proxy},
                timeout=timeout
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                with self.lock:
                    stats = self.proxy_stats[proxy]
                    stats['success_count'] += 1
                    stats['avg_response_time'] = (
                        (stats['avg_response_time'] * (stats['success_count'] - 1) + response_time) /
                        stats['success_count']
                    )
                return True
            
        except Exception:
            pass
        
        with self.lock:
            self.proxy_stats[proxy]['failure_count'] += 1
        
        return False
    
    def get_best_proxy(self) -> Optional[str]:
        """Get the best performing proxy"""
        with self.lock:
            available_proxies = [
                p for p in self.proxies 
                if p not in self.failed_proxies
            ]
            
            if not available_proxies:
                # Reset failed proxies if all failed
                self.failed_proxies.clear()
                available_proxies = self.proxies
                self.logger.warning("All proxies failed, resetting failed proxy list")
            
            if not available_proxies:
                return None
            
            # Sort by success rate and response time
            def proxy_score(proxy):
                stats = self.proxy_stats[proxy]
                total_requests = stats['success_count'] + stats['failure_count']
                if total_requests == 0:
                    return 0.5  # Neutral score for untested proxies
                
                success_rate = stats['success_count'] / total_requests
                response_penalty = min(stats['avg_response_time'] / 10, 0.3)  # Max 30% penalty
                
                return success_rate - response_penalty
            
            # Get top 5 proxies and randomly select one
            top_proxies = sorted(available_proxies, key=proxy_score, reverse=True)[:5]
            selected_proxy = random.choice(top_proxies)
            
            self.proxy_stats[selected_proxy]['last_used'] = datetime.now()
            return selected_proxy
    
    def mark_proxy_failed(self, proxy: str):
        """Mark a proxy as failed"""
        with self.lock:
            self.failed_proxies.add(proxy)
            self.proxy_stats[proxy]['failure_count'] += 1
            self.proxy_stats[proxy]['consecutive_failures'] += 1
    
    def get_proxy_stats(self) -> Dict:
        """Get proxy pool statistics"""
        with self.lock:
            total_proxies = len(self.proxies)
            failed_proxies = len(self.failed_proxies)
            healthy_proxies = total_proxies - failed_proxies
            
            return {
                'total_proxies': total_proxies,
                'healthy_proxies': healthy_proxies,
                'failed_proxies': failed_proxies,
                'success_rate': healthy_proxies / total_proxies if total_proxies > 0 else 0
            }


class ConsistentScrapingManager:
    """
    Manager for consistent scraping with multiple fallback strategies
    """
    
    def __init__(self):
        self.proxy_pool = ProxyPool()
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.request_count = 0
        self.success_count = 0
        
        # Adaptive delay settings
        self.base_delay = 5
        self.max_delay = 30
        self.current_delay = self.base_delay
        self.consecutive_failures = 0
        
        # User agent rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
    
    def make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make a request with full anti-bot protection"""
        
        self.request_count += 1
        
        # Adaptive delay
        delay = random.uniform(self.current_delay * 0.8, self.current_delay * 1.2)
        time.sleep(delay)
        
        # Get best proxy
        proxy = self.proxy_pool.get_best_proxy()
        
        # Prepare headers
        headers = {
            'User-Agent': random.choice(self.user_agents),
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
        
        # Merge with provided headers
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        # Set proxy
        if proxy:
            kwargs['proxies'] = {'http': proxy, 'https': proxy}
        
        # Set timeout
        kwargs.setdefault('timeout', 15)
        
        # Make request with retries
        for attempt in range(3):
            try:
                response = self.session.get(url, **kwargs)
                
                # Check if blocked
                if self.is_blocked_response(response):
                    self.logger.warning(f"Blocked response detected for {url}")
                    if proxy:
                        self.proxy_pool.mark_proxy_failed(proxy)
                    self.handle_blocking()
                    continue
                
                # Success
                if response.status_code == 200:
                    self.success_count += 1
                    self.consecutive_failures = 0
                    self.adjust_delay_on_success()
                    return response
                
            except Exception as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if proxy:
                    self.proxy_pool.mark_proxy_failed(proxy)
                
                # Get new proxy for retry
                proxy = self.proxy_pool.get_best_proxy()
                if proxy:
                    kwargs['proxies'] = {'http': proxy, 'https': proxy}
        
        # All attempts failed
        self.consecutive_failures += 1
        self.adjust_delay_on_failure()
        return None
    
    def is_blocked_response(self, response: requests.Response) -> bool:
        """Check if response indicates blocking"""
        if response.status_code in [403, 429, 503]:
            return True
        
        content = response.text.lower()
        blocking_indicators = [
            'access denied', 'forbidden', 'captcha', '验证码', 
            '人机验证', 'robot', 'blocked', 'temporarily unavailable'
        ]
        
        return any(indicator in content for indicator in blocking_indicators)
    
    def handle_blocking(self):
        """Handle blocking detection"""
        self.consecutive_failures += 1
        
        # Increase delay aggressively
        self.current_delay = min(self.max_delay, self.current_delay * 1.5)
        
        # Extended sleep on blocking
        sleep_time = random.uniform(30, 90)
        self.logger.info(f"Blocking detected, sleeping for {sleep_time:.1f} seconds")
        time.sleep(sleep_time)
        
        # Refresh session
        self.session.close()
        self.session = requests.Session()
    
    def adjust_delay_on_success(self):
        """Adjust delay based on success"""
        if self.consecutive_failures == 0 and self.current_delay > self.base_delay:
            # Gradually reduce delay on consistent success
            self.current_delay = max(self.base_delay, self.current_delay * 0.95)
    
    def adjust_delay_on_failure(self):
        """Adjust delay based on failure"""
        self.current_delay = min(self.max_delay, self.current_delay * 1.2)
    
    def get_success_rate(self) -> float:
        """Get current success rate"""
        if self.request_count == 0:
            return 0.0
        return self.success_count / self.request_count
    
    def get_stats(self) -> Dict:
        """Get scraping statistics"""
        proxy_stats = self.proxy_pool.get_proxy_stats()
        
        return {
            'requests_made': self.request_count,
            'successful_requests': self.success_count,
            'success_rate': self.get_success_rate(),
            'current_delay': self.current_delay,
            'consecutive_failures': self.consecutive_failures,
            'proxy_stats': proxy_stats
        }


# Global instance for use in middlewares
consistent_manager = ConsistentScrapingManager()
