#!/usr/bin/env python3
"""
Anti-Bot Protection Test Script
Tests the effectiveness of our anti-bot middlewares against Lianjia
"""

import sys
import os
import time
import requests
from datetime import datetime

# Add the scraper directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from middlewares.anti_bot_middleware import AntiBot, ShadowUserAgentMiddleware
from middlewares.proxy_middleware import SmartProxyMiddleware

def test_user_agent_rotation():
    """Test user agent rotation functionality"""
    print("🔄 Testing User-Agent Rotation...")
    
    # Test fake-useragent (more reliable)
    try:
        from fake_useragent import UserAgent
        ua_gen = UserAgent()
        
        print("✅ Fake-UserAgent library loaded successfully")
        
        # Test generating different user agents
        user_agents = set()
        for i in range(5):
            ua = ua_gen.random
            user_agents.add(ua)
            print(f"   UA {i+1}: {ua[:70]}...")
        
        print(f"✅ Generated {len(user_agents)} unique user agents with fake-useragent")
        return True
        
    except ImportError:
        print("❌ Fake-UserAgent library not available")
    except Exception as e:
        print(f"⚠️  Fake-UserAgent error: {e}")
    
    # Fallback to shadow-useragent
    try:
        from shadow_useragent import ShadowUserAgent
        sua = ShadowUserAgent()
        
        print("✅ Shadow-UserAgent library loaded as fallback")
        
        # Test generating different user agents
        user_agents = set()
        for i in range(3):
            ua = sua.get_useragent()
            if not ua:
                ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            
            user_agents.add(ua)
            print(f"   UA {i+1}: {ua[:70]}...")
        
        print(f"✅ Generated {len(user_agents)} unique user agents with shadow-useragent")
        return True
        
    except ImportError:
        print("❌ Shadow-UserAgent library not available")
        return False
    except Exception as e:
        print(f"⚠️  Shadow-UserAgent error: {e}")
        print("   Using fallback user agent rotation")
        return False

def test_anti_bot_detection():
    """Test anti-bot detection patterns"""
    print("\n🛡️ Testing Anti-Bot Detection...")
    
    # Mock responses to test detection
    test_cases = [
        (b"Access Denied", "Access Denied"),
        (b"captcha required", "CAPTCHA"),
        ("验证码".encode('utf-8'), "Chinese verification code"),
        (b"robot detected", "Robot detection"),
        (b"<html><head><title>403 Forbidden</title></head><body>Forbidden</body></html>", "Short response (possible block page)")
    ]
    
    from unittest.mock import Mock
    
    # Create a mock AntiBot instance
    class MockCrawler:
        def __init__(self):
            self.settings = Mock()
            self.signals = Mock()
    
    anti_bot = AntiBot(MockCrawler())
    
    for response_body, description in test_cases:
        mock_response = Mock()
        mock_response.body = response_body
        mock_response.status = 200
        
        is_blocked = anti_bot._is_blocked_response(mock_response)
        status = "✅ DETECTED" if is_blocked else "❌ MISSED"
        print(f"   {status}: {description}")
    
    print("✅ Anti-bot detection patterns tested")

def test_lianjia_access():
    """Test actual access to Lianjia with anti-bot headers"""
    print("\n🌐 Testing Lianjia Access...")
    
    # Realistic headers that mimic browser behavior
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
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
    
    test_urls = [
        'https://sh.lianjia.com/',  # Shanghai main page
        'https://bj.lianjia.com/',  # Beijing main page
        'https://gz.lianjia.com/',  # Guangzhou main page
    ]
    
    session = requests.Session()
    
    for url in test_urls:
        try:
            print(f"   Testing: {url}")
            
            # Add delay between requests
            time.sleep(2)
            
            response = session.get(url, headers=headers, timeout=10)
            
            # Analyze response
            if response.status_code == 200:
                if len(response.text) > 10000:  # Substantial content
                    if '验证码' in response.text or 'captcha' in response.text.lower():
                        print(f"   ⚠️  CAPTCHA detected - {url}")
                    else:
                        print(f"   ✅ SUCCESS - {url} (Content: {len(response.text)} chars)")
                else:
                    print(f"   ⚠️  Short response - possible blocking - {url}")
            else:
                print(f"   ❌ HTTP {response.status_code} - {url}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed - {url}: {e}")

def test_scrapy_command():
    """Test running Scrapy with anti-bot middlewares"""
    print("\n🕷️ Testing Scrapy Integration...")
    
    # Check if house spider exists
    spider_path = os.path.join(os.path.dirname(__file__), 'scraper', 'spiders', 'house_spider.py')
    if os.path.exists(spider_path):
        print("✅ House spider found")
        
        # Show command to run with anti-bot protection
        print("\n📋 To test with Scrapy, run:")
        print("   cd scraper")
        print("   scrapy crawl house_spider -s DOWNLOAD_DELAY=5 -s CONCURRENT_REQUESTS=1")
        print("   (Anti-bot middlewares will be automatically enabled)")
        
    else:
        print("❌ House spider not found")

def main():
    """Run all anti-bot tests"""
    print("🤖 Anti-Bot Protection Test Suite")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    test_user_agent_rotation()
    test_anti_bot_detection()
    test_lianjia_access()
    test_scrapy_command()
    
    print("\n" + "=" * 50)
    print("✅ Anti-Bot Test Suite Complete!")
    print("\n💡 Tips for bypassing Lianjia anti-bot:")
    print("   1. Use random delays (2-8 seconds between requests)")
    print("   2. Rotate user agents every 30-60 requests")
    print("   3. Clear cookies/session every 30-60 requests")
    print("   4. Monitor for CAPTCHA/blocking indicators")
    print("   5. Use proxy rotation if direct access fails")
    print("   6. Keep concurrent requests to 1")
    print("   7. Enable AutoThrottle for intelligent delays")

if __name__ == "__main__":
    main()
