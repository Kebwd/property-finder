#!/usr/bin/env python3
"""
ScraperAPI Enhanced Test - Advanced Anti-Detection Features
Tests ScraperAPI's premium features for tough websites
"""

import requests
import urllib3
import json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Your ScraperAPI credentials
API_KEY = "b462bc754d65dad46e73652975fd308c"

def test_scraperapi_modes():
    """Test different ScraperAPI configurations"""
    
    test_url = "https://sz.centanet.com/chengjiao/"
    
    # Mode 1: Basic ScraperAPI
    print("🧪 Testing Mode 1: Basic ScraperAPI")
    try:
        proxy = {
            'http': f'http://scraperapi:{API_KEY}@proxy-server.scraperapi.com:8001',
            'https': f'http://scraperapi:{API_KEY}@proxy-server.scraperapi.com:8001'
        }
        response = requests.get(test_url, proxies=proxy, timeout=30, verify=False)
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)}")
        
        if '验证' in response.text or 'captcha' in response.text.lower():
            print("   ❌ CAPTCHA/Verification detected")
        elif '成交' in response.text:
            print("   ✅ Property data detected!")
        else:
            print("   ⚠️ Unknown response content")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Mode 2: ScraperAPI with render parameter
    print("🧪 Testing Mode 2: ScraperAPI Direct API with render=true")
    try:
        api_url = f"https://api.scraperapi.com/?api_key={API_KEY}&url={test_url}&render=true&country_code=cn"
        response = requests.get(api_url, timeout=60, verify=False)
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)}")
        
        if '验证' in response.text or 'captcha' in response.text.lower():
            print("   ❌ CAPTCHA/Verification still detected")
        elif '成交' in response.text:
            print("   ✅ Property data detected with JS rendering!")
        else:
            print("   ⚠️ Checking response content...")
            if response.status_code == 200 and len(response.text) > 1000:
                print("   📄 Large response received - likely successful")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Mode 3: ScraperAPI with premium residential
    print("🧪 Testing Mode 3: ScraperAPI with premium residential")
    try:
        api_url = f"https://api.scraperapi.com/?api_key={API_KEY}&url={test_url}&render=true&premium=true&country_code=cn"
        response = requests.get(api_url, timeout=60, verify=False)
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)}")
        
        if '验证' in response.text or 'captcha' in response.text.lower():
            print("   ❌ Still getting verification")
        elif '成交' in response.text:
            print("   ✅ SUCCESS with premium residential!")
        else:
            print("   📄 Response analysis...")
            # Check for common property-related terms
            if any(term in response.text for term in ['房', '价格', '面积', 'property']):
                print("   ✅ Property-related content detected")
            else:
                print("   ⚠️ Content unclear")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 ScraperAPI Enhanced Anti-Detection Test")
    print("=" * 50)
    test_scraperapi_modes()
    print("=" * 50)
    print("💡 Based on results, we can optimize your scraper configuration")
