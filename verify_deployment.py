#!/usr/bin/env python3
"""
Post-deployment verification script
Run this after deploying to Railway to verify everything works
"""

import requests
import json
import sys

def test_deployment(base_url, api_key):
    print(f"🔍 Testing deployment at: {base_url}")
    print("=" * 50)
    
    tests = []
    
    # Test 1: Health endpoint
    print("1️⃣  Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {health.get('status')}")
            print(f"   Database: {health.get('database')}")
            tests.append(True)
        else:
            print(f"❌ Health check failed: {response.status_code}")
            tests.append(False)
    except Exception as e:
        print(f"❌ Health check error: {e}")
        tests.append(False)
    
    # Test 2: Scraper status
    print("\n2️⃣  Testing scraper status...")
    try:
        response = requests.get(f"{base_url}/api/scraper/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Scraper status accessible")
            print(f"   Is Running: {status.get('isRunning')}")
            print(f"   Last Run: {status.get('lastRun') or 'Never'}")
            tests.append(True)
        else:
            print(f"❌ Scraper status failed: {response.status_code}")
            tests.append(False)
    except Exception as e:
        print(f"❌ Scraper status error: {e}")
        tests.append(False)
    
    # Test 3: API endpoints
    print("\n3️⃣  Testing other API endpoints...")
    endpoints = [
        "/api/house",
        "/api/business", 
        "/api/search"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code in [200, 404, 405]:  # 404/405 are ok for GET on POST endpoints
                print(f"✅ {endpoint} - accessible")
            else:
                print(f"⚠️  {endpoint} - unexpected status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - error: {e}")
    
    # Test 4: Database connectivity (if health passed)
    if tests[0]:  # Only if health check passed
        print("\n4️⃣  Testing database operations...")
        try:
            # Try a simple search (should work even with empty DB)
            response = requests.get(f"{base_url}/api/search?type=house&limit=1", timeout=10)
            if response.status_code == 200:
                print("✅ Database search queries working")
                tests.append(True)
            else:
                print(f"⚠️  Database search returned: {response.status_code}")
                tests.append(False)
        except Exception as e:
            print(f"❌ Database test error: {e}")
            tests.append(False)
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"   Passed: {sum(tests)}/{len(tests)}")
    
    if all(tests):
        print("\n🎉 All tests passed! Your deployment is working correctly.")
        print(f"\n🌐 Your app is live at: {base_url}")
        print("\n📝 Next steps:")
        print("   - Upload CSV data via the interface")
        print("   - Test manual scraping from GitHub Actions")
        print("   - Monitor daily automation")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the Railway logs for details.")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python verify_deployment.py <base_url> <api_key>")
        print("Example: python verify_deployment.py https://your-app.railway.app <YOUR_SCRAPER_API_KEY>")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    api_key = sys.argv[2]
    
    success = test_deployment(base_url, api_key)
    sys.exit(0 if success else 1)
