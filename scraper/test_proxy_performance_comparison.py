#!/usr/bin/env python3
"""
Performance Comparison: With and Without Proxies
Demonstrates the performance improvements from using proxies
"""

import time
import subprocess
import json
import os


def run_performance_test():
    """Compare performance with and without proxies"""
    
    print("🚀 PROXY PERFORMANCE COMPARISON TEST")
    print("=" * 70)
    
    # Test results storage
    results = {
        'without_proxy': {'time': 0, 'success': False, 'error': None},
        'with_proxy': {'time': 0, 'success': False, 'error': None}
    }
    
    print("\n1️⃣ TESTING WITHOUT PROXIES")
    print("-" * 40)
    
    # Test without proxies (disable proxy middleware)
    start_time = time.time()
    try:
        result = subprocess.run([
            'python', '-m', 'scrapy', 'crawl', 'house_spider',
            '-a', 'mode=daily',
            '-L', 'ERROR',  # Reduce log noise
            '-s', 'CLOSESPIDER_ITEMCOUNT=1',
            '-s', 'CONCURRENT_REQUESTS=1',
            # Disable proxy middleware
            '-s', 'DOWNLOADER_MIDDLEWARES={"middlewares.scrapy_simple_antibot.ScrapySimpleAntiBot": 200}'
        ], capture_output=True, text=True, timeout=60)
        
        end_time = time.time()
        results['without_proxy']['time'] = end_time - start_time
        results['without_proxy']['success'] = result.returncode == 0
        
        if result.returncode == 0:
            print(f"✅ Success - Time: {results['without_proxy']['time']:.2f}s")
        else:
            print(f"❌ Failed - Time: {results['without_proxy']['time']:.2f}s")
            results['without_proxy']['error'] = result.stderr[:200]
            
    except subprocess.TimeoutExpired:
        results['without_proxy']['time'] = 60
        results['without_proxy']['error'] = "Timeout after 60s"
        print("⏰ Timeout after 60s")
    except Exception as e:
        results['without_proxy']['error'] = str(e)
        print(f"❌ Error: {e}")
    
    print("\n2️⃣ TESTING WITH PROXIES")
    print("-" * 40)
    
    # Test with proxies (full configuration)
    start_time = time.time()
    try:
        result = subprocess.run([
            'python', '-m', 'scrapy', 'crawl', 'house_spider',
            '-a', 'mode=daily',
            '-L', 'ERROR',  # Reduce log noise
            '-s', 'CLOSESPIDER_ITEMCOUNT=1',
            # Use default settings with proxy middleware
        ], capture_output=True, text=True, timeout=60)
        
        end_time = time.time()
        results['with_proxy']['time'] = end_time - start_time
        results['with_proxy']['success'] = result.returncode == 0
        
        if result.returncode == 0:
            print(f"✅ Success - Time: {results['with_proxy']['time']:.2f}s")
        else:
            print(f"❌ Failed - Time: {results['with_proxy']['time']:.2f}s")
            results['with_proxy']['error'] = result.stderr[:200]
            
    except subprocess.TimeoutExpired:
        results['with_proxy']['time'] = 60
        results['with_proxy']['error'] = "Timeout after 60s"
        print("⏰ Timeout after 60s")
    except Exception as e:
        results['with_proxy']['error'] = str(e)
        print(f"❌ Error: {e}")
    
    # Analysis
    print("\n" + "=" * 70)
    print("📊 PERFORMANCE ANALYSIS")
    print("=" * 70)
    
    print(f"\n⏱️  TIME COMPARISON:")
    print(f"   Without Proxies: {results['without_proxy']['time']:.2f}s")
    print(f"   With Proxies:    {results['with_proxy']['time']:.2f}s")
    
    if results['without_proxy']['time'] > 0 and results['with_proxy']['time'] > 0:
        if results['with_proxy']['time'] < results['without_proxy']['time']:
            improvement = ((results['without_proxy']['time'] - results['with_proxy']['time']) / results['without_proxy']['time']) * 100
            print(f"   🚀 Improvement: {improvement:.1f}% faster with proxies")
        else:
            slowdown = ((results['with_proxy']['time'] - results['without_proxy']['time']) / results['without_proxy']['time']) * 100
            print(f"   ⚠️ Slowdown: {slowdown:.1f}% slower with proxies")
    
    print(f"\n✅ SUCCESS RATE:")
    print(f"   Without Proxies: {'✅ Success' if results['without_proxy']['success'] else '❌ Failed'}")
    print(f"   With Proxies:    {'✅ Success' if results['with_proxy']['success'] else '❌ Failed'}")
    
    if results['without_proxy']['error'] or results['with_proxy']['error']:
        print(f"\n❌ ERRORS:")
        if results['without_proxy']['error']:
            print(f"   Without Proxies: {results['without_proxy']['error']}")
        if results['with_proxy']['error']:
            print(f"   With Proxies: {results['with_proxy']['error']}")
    
    print(f"\n🎯 EXPECTED BENEFITS WITH PREMIUM PROXIES:")
    print(f"   🔄 IP Rotation: Avoid rate limiting")
    print(f"   🌍 Geo-bypass: Access region-locked content")
    print(f"   ⚡ Higher Concurrency: 3x more parallel requests")
    print(f"   🛡️ Reduced Blocking: Different IPs per request")
    print(f"   📈 Scalability: Handle larger scraping volumes")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if not results['with_proxy']['success'] and results['without_proxy']['success']:
        print(f"   🔧 Current free proxies failing - consider premium proxies")
        print(f"   💰 Investment: $10-30/month for reliable proxy service")
        print(f"   📈 Expected ROI: 2-5x performance improvement")
    elif results['with_proxy']['success']:
        print(f"   ✅ Proxy system working - ready for scaling")
        print(f"   📊 Monitor performance and upgrade to premium if needed")
    
    return results


if __name__ == "__main__":
    results = run_performance_test()
    
    # Save results
    with open('proxy_performance_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: proxy_performance_results.json")
