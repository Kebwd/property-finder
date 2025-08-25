#!/usr/bin/env python3
"""
Simple but Effective Anti-Bot Protection
Focuses on proven techniques without relying on free proxies
"""

import random
import time
import requests
import logging
from datetime import datetime, timedelta
import json


class SimpleAntiBot:
    """
    Simple but highly effective anti-bot protection
    Uses proven techniques without complex proxy management
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.request_count = 0
        self.success_count = 0
        self.block_count = 0
        self.last_request_time = 0
        
        # Adaptive settings
        self.base_delay = 8  # Start with 8 seconds
        self.current_delay = self.base_delay
        self.max_delay = 60
        self.consecutive_failures = 0
        
        # Realistic browser session
        self.setup_browser_session()
        
        # Track session duration
        self.session_start = datetime.now()
        self.session_duration = random.randint(30, 60)  # Refresh session every 30-60 requests
    
    def setup_browser_session(self):
        """Setup realistic browser session"""
        
        # Realistic user agents (frequently updated)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # Set persistent headers
        self.session.headers.update({
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
        })
        
        # Set initial user agent
        self.rotate_user_agent()
    
    def rotate_user_agent(self):
        """Rotate user agent"""
        self.session.headers['User-Agent'] = random.choice(self.user_agents)
    
    def refresh_session(self):
        """Refresh session to avoid detection"""
        self.logger.info("🔄 Refreshing session - clearing cookies and rotating user agent")
        
        # Close old session
        self.session.close()
        
        # Create new session
        self.session = requests.Session()
        self.setup_browser_session()
        
        # Reset counters
        self.session_start = datetime.now()
        self.session_duration = random.randint(30, 60)
        self.request_count = 0
    
    def smart_delay(self):
        """Implement smart, human-like delays"""
        
        # Calculate time since last request
        now = time.time()
        time_since_last = now - self.last_request_time
        
        # Base delay with random variation
        delay = random.uniform(self.current_delay * 0.8, self.current_delay * 1.2)
        
        # Add extra randomness
        if random.random() < 0.1:  # 10% chance of longer delay
            delay += random.uniform(5, 15)
        
        # Ensure minimum time between requests
        min_delay = 3
        if time_since_last < min_delay:
            delay += (min_delay - time_since_last)
        
        # Apply delay
        self.logger.debug(f"⏱️ Waiting {delay:.1f} seconds")
        time.sleep(delay)
        
        self.last_request_time = time.time()
    
    def make_request(self, url, **kwargs):
        """Make a request with smart anti-bot protection"""
        
        self.request_count += 1
        
        # Refresh session if needed
        if self.request_count >= self.session_duration:
            self.refresh_session()
        
        # Rotate user agent periodically
        if self.request_count % random.randint(20, 40) == 0:
            self.rotate_user_agent()
        
        # Smart delay
        self.smart_delay()
        
        # Make request with timeout
        kwargs.setdefault('timeout', 20)
        
        try:
            response = self.session.get(url, **kwargs)
            
            # Check for blocking
            if self.is_blocked(response):
                self.handle_blocked_response(url)
                return None
            
            # Success
            if response.status_code == 200:
                self.success_count += 1
                self.consecutive_failures = 0
                self.adjust_delay_on_success()
                return response
            else:
                self.logger.warning(f"HTTP {response.status_code} for {url}")
                self.consecutive_failures += 1
                self.adjust_delay_on_failure()
                return None
                
        except Exception as e:
            self.logger.warning(f"Request failed for {url}: {e}")
            self.consecutive_failures += 1
            self.adjust_delay_on_failure()
            return None
    
    def is_blocked(self, response):
        """Check if response indicates blocking"""
        
        # Check status codes
        if response.status_code in [403, 429, 503]:
            return True
        
        # For successful status codes, check content
        if response.status_code != 200:
            return False
        
        # Check for blocking keywords in content
        content = response.text.lower()
        blocking_keywords = [
            'access denied', 'forbidden', 'captcha', '验证码', 
            '人机验证', 'robot', 'blocked', 'temporarily unavailable',
            'service unavailable', 'too many requests', 'verification required'
        ]
        
        # Only consider it blocked if we find blocking keywords
        # Don't use content length as it varies greatly between sites
        return any(keyword in content for keyword in blocking_keywords)
    
    def handle_blocked_response(self, url):
        """Handle blocked response"""
        self.block_count += 1
        self.consecutive_failures += 1
        
        self.logger.warning(f"🚫 Blocked response detected for {url}")
        
        # Aggressive measures
        self.current_delay = min(self.max_delay, self.current_delay * 2)
        
        # Force session refresh
        self.refresh_session()
        
        # Extended delay
        extended_delay = random.uniform(60, 180)  # 1-3 minutes
        self.logger.info(f"😴 Sleeping for {extended_delay:.0f} seconds due to blocking")
        time.sleep(extended_delay)
    
    def adjust_delay_on_success(self):
        """Reduce delay gradually on success"""
        if self.consecutive_failures == 0 and self.current_delay > self.base_delay:
            self.current_delay = max(self.base_delay, self.current_delay * 0.95)
    
    def adjust_delay_on_failure(self):
        """Increase delay on failure"""
        self.current_delay = min(self.max_delay, self.current_delay * 1.3)
    
    def get_stats(self):
        """Get performance statistics"""
        total_requests = self.success_count + self.consecutive_failures + self.block_count
        
        return {
            'total_requests': total_requests,
            'successful_requests': self.success_count,
            'blocked_requests': self.block_count,
            'success_rate': self.success_count / max(total_requests, 1),
            'current_delay': self.current_delay,
            'session_age': (datetime.now() - self.session_start).total_seconds() / 60,
            'consecutive_failures': self.consecutive_failures
        }


# Global instance
simple_antibot = SimpleAntiBot()


def test_simple_antibot():
    """Test the simple anti-bot system"""
    print("🚀 Testing Simple Anti-Bot System")
    print("=" * 50)
    
    # Test URLs
    test_urls = [
        'https://httpbin.org/ip',  # Should work
        'https://sh.lianjia.com/',  # Might be blocked
        'https://bj.lianjia.com/',  # Might be blocked
    ]
    
    for url in test_urls:
        print(f"\\n🔗 Testing: {url}")
        
        response = simple_antibot.make_request(url)
        
        if response:
            print(f"   ✅ Success: {len(response.text):,} chars")
            if 'lianjia.com' in url and '验证码' in response.text:
                print("   ⚠️  CAPTCHA detected but content received")
        else:
            print("   ❌ Failed or blocked")
    
    # Show stats
    stats = simple_antibot.get_stats()
    print(f"\\n📊 Performance Stats:")
    print(f"   Success rate: {stats['success_rate']:.2%}")
    print(f"   Current delay: {stats['current_delay']:.1f}s")
    print(f"   Blocked requests: {stats['blocked_requests']}")
    print(f"   Session age: {stats['session_age']:.1f} minutes")
    
    return stats['success_rate'] > 0.3  # 30% success rate is good


if __name__ == "__main__":
    success = test_simple_antibot()
    print(f"\\n{'✅ SUCCESS' if success else '❌ NEEDS IMPROVEMENT'}")
