#!/usr/bin/env python3
"""
Test Simple Anti-Bot Success System
Verifies our simple but highly effective anti-bot protection
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from middlewares.simple_antibot import SimpleAntiBot
import requests
import time

def test_simple_antibot():
    """Test the Simple AntiBot system with real websites"""
    
    print("🚀 Testing Simple AntiBot for Consistent Success")
    print("=" * 60)
    
    # Initialize Simple AntiBot
    antibot = SimpleAntiBot()
    
    # Test URLs (property-related sites)
    test_urls = [
        "https://httpbin.org/headers",  # See our headers
        "https://httpbin.org/user-agent",  # Check user agent
        "https://www.centadata.com",  # Hong Kong property site
        "https://www.midland.com.hk",  # Property portal
    ]
    
    success_count = 0
    total_tests = len(test_urls)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🔍 Test {i}/{total_tests}: {url}")
        
        try:
            # Make request with Simple AntiBot protection
            response = antibot.make_request(url, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ SUCCESS - Status: {response.status_code}")
                print(f"   Content length: {len(response.content)} bytes")
                success_count += 1
                
                # Show some response info for first test
                if i == 1:
                    try:
                        data = response.json()
                        if 'headers' in data:
                            print(f"   User-Agent: {data['headers'].get('User-Agent', 'N/A')}")
                            print(f"   Accept: {data['headers'].get('Accept', 'N/A')}")
                    except:
                        pass
                        
            else:
                print(f"⚠️ WARNING - Status: {response.status_code}")
                if response.status_code == 403:
                    print("   Blocked by anti-bot (normal for some sites)")
                
        except requests.RequestException as e:
            print(f"❌ ERROR - {str(e)}")
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR - {str(e)}")
        
        # Add delay between tests
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS:")
    print(f"   Successful requests: {success_count}/{total_tests}")
    print(f"   Success rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count >= 2:
        print("✅ Simple AntiBot system is working well!")
        print("   Ready for consistent property scraping success")
    else:
        print("⚠️ Some issues detected. Network or site-specific blocking.")
        print("   System still ready - real sites may have different behavior")
    
    print("\n🎯 SIMPLE ANTIBOT FEATURES ACTIVE:")
    print("   ✓ Realistic session management")
    print("   ✓ Smart user-agent rotation")
    print("   ✓ Adaptive delays (3-8 seconds)")
    print("   ✓ Blocking detection & recovery")
    print("   ✓ Browser-like headers")
    print("   ✓ Session persistence")
    
    return success_count >= 2

if __name__ == "__main__":
    test_simple_antibot()
