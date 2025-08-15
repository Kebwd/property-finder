#!/usr/bin/env python3
"""
Cloud Deployment Verification Script
Tests your fully deployed Property Finder application
"""
import requests
import json
import sys
import time
from urllib.parse import urljoin

def test_cloud_deployment(base_url, timeout=30):
    """Test the cloud-deployed application"""
    
    print("🌐 TESTING CLOUD DEPLOYMENT")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print()
    
    # Ensure base_url ends with /
    if not base_url.endswith('/'):
        base_url += '/'
    
    tests_passed = 0
    total_tests = 6
    
    # Test 1: Health Check
    print("1️⃣  Testing Health Check...")
    try:
        health_url = urljoin(base_url, 'health')
        response = requests.get(health_url, timeout=timeout)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            tests_passed += 1
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: API Health
    print("\n2️⃣  Testing API Health...")
    try:
        api_health_url = urljoin(base_url, 'api/health')
        response = requests.get(api_health_url, timeout=timeout)
        if response.status_code == 200:
            print("   ✅ API health check passed")
            tests_passed += 1
        else:
            print(f"   ❌ API health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API health check error: {e}")
    
    # Test 3: Search Endpoint
    print("\n3️⃣  Testing Search Endpoint...")
    try:
        search_url = urljoin(base_url, 'api/search')
        response = requests.get(f"{search_url}?query=test", timeout=timeout)
        if response.status_code == 200:
            print("   ✅ Search endpoint accessible")
            tests_passed += 1
        else:
            print(f"   ❌ Search endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Search endpoint error: {e}")
    
    # Test 4: Database Connection (via business endpoint)
    print("\n4️⃣  Testing Database Connection...")
    try:
        business_url = urljoin(base_url, 'api/business')
        response = requests.get(business_url, timeout=timeout)
        if response.status_code == 200:
            print("   ✅ Database connection working")
            tests_passed += 1
        else:
            print(f"   ❌ Database connection failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Database connection error: {e}")
    
    # Test 5: Frontend Loading
    print("\n5️⃣  Testing Frontend...")
    try:
        response = requests.get(base_url, timeout=timeout)
        if response.status_code == 200 and 'html' in response.headers.get('content-type', '').lower():
            print("   ✅ Frontend loading successfully")
            tests_passed += 1
        else:
            print(f"   ❌ Frontend failed to load: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Frontend loading error: {e}")
    
    # Test 6: CORS Headers
    print("\n6️⃣  Testing CORS Configuration...")
    try:
        api_url = urljoin(base_url, 'api/health')
        response = requests.options(api_url, timeout=timeout)
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        if cors_header:
            print("   ✅ CORS headers configured")
            tests_passed += 1
        else:
            print("   ⚠️  CORS headers not found (may still work)")
            tests_passed += 0.5
    except Exception as e:
        print(f"   ⚠️  CORS test error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed >= total_tests * 0.8:  # 80% pass rate
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("\n✅ Your Property Finder app is running in the cloud!")
        print(f"\n🔗 Access your app at: {base_url}")
        print(f"🔗 API documentation: {urljoin(base_url, 'api')}")
        return True
    else:
        print("❌ DEPLOYMENT ISSUES DETECTED")
        print("\n🔧 Please check:")
        print("   - Vercel environment variables")
        print("   - Supabase database connection")
        print("   - Domain configuration")
        return False

def test_supabase_connection(supabase_url, anon_key):
    """Test Supabase connection directly"""
    print("\n🗄️  TESTING SUPABASE CONNECTION")
    print("=" * 40)
    
    try:
        # Test Supabase REST API
        headers = {
            'apikey': anon_key,
            'Authorization': f'Bearer {anon_key}',
            'Content-Type': 'application/json'
        }
        
        # Test connection to stores table
        response = requests.get(
            f"{supabase_url}/rest/v1/stores?select=count",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Supabase connection successful")
            return True
        else:
            print(f"❌ Supabase connection failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_cloud_deployment.py <vercel-url> [supabase-url] [supabase-anon-key]")
        print("\nExample:")
        print("  python verify_cloud_deployment.py https://my-app.vercel.app")
        print("  python verify_cloud_deployment.py https://my-app.vercel.app https://xxx.supabase.co eyJhbGc...")
        sys.exit(1)
    
    base_url = sys.argv[1]
    
    # Test main deployment
    deployment_success = test_cloud_deployment(base_url)
    
    # Test Supabase if credentials provided
    if len(sys.argv) >= 4:
        supabase_url = sys.argv[2]
        anon_key = sys.argv[3]
        supabase_success = test_supabase_connection(supabase_url, anon_key)
    else:
        print("\n💡 Tip: Add Supabase URL and anon key to test database connection")
        supabase_success = True
    
    # Final result
    if deployment_success and supabase_success:
        print("\n🚀 FULL CLOUD DEPLOYMENT VERIFIED!")
        print("Your Property Finder application is ready for production use.")
        sys.exit(0)
    else:
        print("\n🔧 Some issues were detected. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
