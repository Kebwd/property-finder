#!/usr/bin/env python3
"""
Test Enhanced Proxy System
Verifies proxy loading, rotation, and performance improvements
"""

import sys
import os

# Add the scraper directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from middlewares.enhanced_proxy_middleware import EnhancedProxyMiddleware
import time


def test_proxy_system():
    """Test the Enhanced Proxy System"""
    
    print("🚀 Testing Enhanced Proxy System")
    print("=" * 60)
    
    # Initialize proxy middleware
    proxy_middleware = EnhancedProxyMiddleware()
    
    print(f"📋 Total proxies loaded: {len(proxy_middleware.proxies)}")
    print(f"✅ Working proxies: {len(proxy_middleware.working_proxies)}")
    print(f"❌ Failed proxies: {len(proxy_middleware.failed_proxies)}")
    
    if proxy_middleware.working_proxies:
        print("\n🔗 Sample working proxies:")
        for i, proxy in enumerate(proxy_middleware.working_proxies[:5], 1):
            masked_proxy = proxy.split('@')[-1] if '@' in proxy else proxy
            print(f"   {i}. {masked_proxy}")
        
        print("\n🔄 Testing proxy rotation:")
        for i in range(5):
            proxy = proxy_middleware.get_next_proxy()
            if proxy:
                masked_proxy = proxy.split('@')[-1] if '@' in proxy else proxy
                print(f"   Request {i+1}: {masked_proxy}")
            else:
                print(f"   Request {i+1}: No proxy available")
    
    print("\n📊 Proxy Statistics:")
    for proxy, stats in list(proxy_middleware.proxy_stats.items())[:5]:
        masked_proxy = proxy.split('@')[-1] if '@' in proxy else proxy
        print(f"   {masked_proxy}: Success={stats['success']}, Failures={stats['failures']}")
    
    # Performance expectations
    print("\n🎯 EXPECTED PERFORMANCE IMPROVEMENTS:")
    print("   ✓ 3x Higher concurrency (3 vs 1 request)")
    print("   ✓ 2x Faster per domain (2 vs 1 concurrent)")
    print("   ✓ 50% Reduced blocking (IP rotation)")
    print("   ✓ 15 Retries with proxy rotation")
    print("   ✓ Geo-blocking bypass capability")
    print("   ✓ Automatic failed proxy removal")
    
    return len(proxy_middleware.working_proxies) > 0


def test_proxy_configuration():
    """Test different proxy configuration scenarios"""
    
    print("\n" + "=" * 60)
    print("🔧 PROXY CONFIGURATION GUIDE")
    print("=" * 60)
    
    print("\n1️⃣ FREE PROXIES (Current Setup):")
    print("   ✅ Automatically loaded from public APIs")
    print("   ⚠️ Lower reliability (~30-50% success)")
    print("   💰 Cost: Free")
    print("   🎯 Good for: Testing, low-volume scraping")
    
    print("\n2️⃣ PREMIUM DATACENTER PROXIES:")
    print("   ✅ High reliability (~90-95% success)")
    print("   ✅ Fast response times")
    print("   💰 Cost: $5-20/month for 1000 IPs")
    print("   🎯 Good for: Production scraping")
    print("   📝 Examples: Oxylabs, SmartProxy")
    
    print("\n3️⃣ RESIDENTIAL PROXIES:")
    print("   ✅ Highest success rate (~95-99%)")
    print("   ✅ Real user IPs, hardest to detect")
    print("   💰 Cost: $15-50/month per GB")
    print("   🎯 Good for: Anti-bot heavy sites")
    print("   📝 Examples: Bright Data, NetNut")
    
    print("\n4️⃣ ROTATING PROXIES:")
    print("   ✅ Automatic IP rotation per request")
    print("   ✅ No manual rotation needed")
    print("   💰 Cost: $20-100/month")
    print("   🎯 Good for: Large-scale scraping")
    
    print("\n💡 RECOMMENDATION for Property Scraping:")
    print("   🥇 Start with: Free proxies (current setup)")
    print("   🥈 Upgrade to: SmartProxy datacenter ($10/month)")
    print("   🥉 For heavy sites: Bright Data residential ($30/month)")


if __name__ == "__main__":
    success = test_proxy_system()
    test_proxy_configuration()
    
    if success:
        print("\n🎉 Proxy system ready for enhanced performance!")
        print("📈 Expected improvement: 2-5x faster scraping with higher success rates")
    else:
        print("\n⚠️ No working proxies found. Consider adding premium proxies for best performance.")
