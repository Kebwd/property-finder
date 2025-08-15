#!/usr/bin/env python3
"""
Test script for the scraper API endpoints
Run this to verify the scraping API is working correctly
"""

import requests
import time
import json
import sys
import os

# Configuration
API_BASE = os.getenv('API_BASE_URL', 'http://localhost:5000')
API_KEY = os.getenv('SCRAPER_API_KEY', 'scraper-secret-key')

def test_scraper_api():
    print("🕷️  Testing Scraper API")
    print("=" * 50)
    
    headers = {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Test 1: Check status endpoint
    print("1️⃣  Testing status endpoint...")
    try:
        response = requests.get(f"{API_BASE}/api/scraper/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Status endpoint working")
            print(f"   Is Running: {status.get('isRunning', False)}")
            print(f"   Last Run: {status.get('lastRun', 'Never')}")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
        return False
    
    # Test 2: Check if scraping is already running
    if status.get('isRunning'):
        print("⏳ Scraping already running, waiting...")
        return True
    
    # Test 3: Trigger scraping
    print("\n2️⃣  Testing scraper trigger...")
    try:
        response = requests.post(f"{API_BASE}/api/scraper/start", headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Scraping triggered successfully")
            print(f"   Message: {result.get('message')}")
            print(f"   Start Time: {result.get('startTime')}")
        elif response.status_code == 429:
            print(f"⏰ Rate limited (too recent): {response.json()}")
            return True  # This is expected behavior
        elif response.status_code == 401:
            print(f"🔒 Authentication failed - check API key")
            return False
        else:
            print(f"❌ Trigger failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Trigger error: {e}")
        return False
    
    # Test 4: Monitor status for a bit
    print("\n3️⃣  Monitoring status...")
    for i in range(3):
        time.sleep(10)
        try:
            response = requests.get(f"{API_BASE}/api/scraper/status")
            if response.status_code == 200:
                status = response.json()
                print(f"   Check {i+1}: Running={status.get('isRunning')}")
                if not status.get('isRunning') and status.get('lastResult'):
                    result = status['lastResult']
                    if result.get('success'):
                        print(f"✅ Scraping completed successfully!")
                    else:
                        print(f"❌ Scraping failed: {result.get('error', 'Unknown error')}")
                    break
        except Exception as e:
            print(f"   Error checking status: {e}")
    
    # Test 5: Get logs
    print("\n4️⃣  Testing logs endpoint...")
    try:
        response = requests.get(f"{API_BASE}/api/scraper/logs?limit=5")
        if response.status_code == 200:
            logs_data = response.json()
            logs = logs_data.get('logs', [])
            print(f"✅ Logs endpoint working ({len(logs)} entries)")
            for log in logs[-3:]:  # Show last 3 logs
                print(f"   {log.get('timestamp', 'No time')} [{log.get('type', 'info')}]: {log.get('message', 'No message')}")
        else:
            print(f"❌ Logs endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Logs error: {e}")
    
    print("\n🎉 API Test Complete!")
    return True

if __name__ == "__main__":
    print(f"Using API Base: {API_BASE}")
    print(f"Using API Key: {API_KEY[:10]}...")
    
    success = test_scraper_api()
    sys.exit(0 if success else 1)
