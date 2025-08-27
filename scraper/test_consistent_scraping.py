#!/usr/bin/env python3
"""
Consistent Scraping Test Suite
Tests the enhanced anti-bot system for maximum success rate
"""

import sys
import os
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path

# Add the scraper directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_proxy_pool():
    """Test the proxy pool functionality"""
    print("🌐 Testing Proxy Pool...")
    
    try:
        from middlewares.consistent_scraping import ProxyPool
        
        pool = ProxyPool()
        stats = pool.get_proxy_stats()
        
        print(f"   📊 Total proxies loaded: {stats['total_proxies']}")
        print(f"   ✅ Healthy proxies: {stats['healthy_proxies']}")
        print(f"   ❌ Failed proxies: {stats['failed_proxies']}")
        print(f"   📈 Success rate: {stats['success_rate']:.2%}")
        
        if stats['total_proxies'] > 0:
            best_proxy = pool.get_best_proxy()
            if best_proxy:
                print(f"   🏆 Best proxy: {best_proxy}")
                return True
            else:
                print("   ⚠️  No working proxies available")
                return False
        else:
            print("   ℹ️  No proxies configured (will use direct connection)")
            return True
            
    except Exception as e:
        print(f"   ❌ Proxy pool test failed: {e}")
        return False

def test_consistent_manager():
    """Test the consistent scraping manager"""
    print("\\n🤖 Testing Consistent Scraping Manager...")
    
    try:
        from middlewares.consistent_scraping import consistent_manager
        
        # Test with a simple request
        test_url = "https://httpbin.org/ip"
        print(f"   🔗 Testing request to: {test_url}")
        
        start_time = time.time()
        response = consistent_manager.make_request(test_url)
        duration = time.time() - start_time
        
        if response and response.status_code == 200:
            print(f"   ✅ Request successful in {duration:.2f}s")
            
            # Show stats
            stats = consistent_manager.get_stats()
            print(f"   📊 Success rate: {stats['success_rate']:.2%}")
            print(f"   ⏱️  Current delay: {stats['current_delay']:.1f}s")
            
            return True
        else:
            print("   ❌ Request failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Consistent manager test failed: {e}")
        return False

def test_lianjia_access():
    """Test actual Lianjia access with consistent protection"""
    print("\\n🏠 Testing Lianjia Access with Consistent Protection...")
    
    try:
        from middlewares.consistent_scraping import consistent_manager
        
        test_urls = [
            'https://sh.lianjia.com/',
            'https://bj.lianjia.com/',
        ]
        
        success_count = 0
        
        for url in test_urls:
            print(f"   📍 Testing: {url}")
            
            response = consistent_manager.make_request(url)
            
            if response and response.status_code == 200:
                content_length = len(response.text)
                
                if content_length > 10000:  # Substantial content
                    if '验证码' in response.text or 'captcha' in response.text.lower():
                        print(f"   ⚠️  CAPTCHA detected but response received - {url}")
                    else:
                        print(f"   ✅ SUCCESS - {url} (Content: {content_length:,} chars)")
                        success_count += 1
                else:
                    print(f"   ⚠️  Short response - possible blocking - {url}")
            else:
                print(f"   ❌ Failed - {url}")
        
        success_rate = success_count / len(test_urls)
        print(f"   📊 Overall success rate: {success_rate:.2%}")
        
        return success_rate > 0.5  # Consider 50%+ success as good
        
    except Exception as e:
        print(f"   ❌ Lianjia test failed: {e}")
        return False

def test_spider_with_consistent_protection():
    """Test spider with consistent anti-bot protection"""
    print("\\n🕷️ Testing Spider with Consistent Protection...")
    
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "house_spider",
        "-a", "mode=test",
        "-a", "max_pages=1",
        "-L", "INFO",
        "-s", "CLOSESPIDER_ITEMCOUNT=3",  # Stop after 3 items
        "-o", "consistent_test_output.json",
        "--logfile", "consistent_test.log"
    ]
    
    print(f"   🚀 Running: {' '.join(cmd[-6:])}")  # Show last 6 args
    
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        duration = time.time() - start_time
        
        print(f"   ⏱️  Completed in {duration:.1f} seconds")
        print(f"   📊 Return code: {result.returncode}")
        
        if result.returncode == 0:
            # Check output
            output_file = Path("consistent_test_output.json")
            if output_file.exists():
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        item_count = len(data) if data else 0
                        
                    print(f"   📊 Items scraped: {item_count}")
                    
                    if item_count > 0:
                        sample = data[0]
                        print(f"   🏠 Sample: {sample.get('estate_name_zh', 'N/A')}")
                        print(f"   ✅ Consistent protection working!")
                        
                        # Cleanup
                        output_file.unlink()
                        Path("consistent_test.log").unlink(missing_ok=True)
                        
                        return True
                    else:
                        print("   ⚠️  No items scraped - checking logs...")
                        
                        # Show log excerpt
                        log_file = Path("consistent_test.log")
                        if log_file.exists():
                            with open(log_file, 'r', encoding='utf-8') as f:
                                log_content = f.read()
                                if 'Blocking detected' in log_content:
                                    print("   🚫 Blocking detected but system is working")
                                elif 'SUCCESS' in log_content:
                                    print("   ✅ Requests successful but no items extracted")
                                else:
                                    print("   ❓ Check full log for details")
                        
                        return False
                        
                except json.JSONDecodeError:
                    print("   ❌ Invalid JSON output")
                    return False
            else:
                print("   ❌ No output file created")
                return False
        else:
            print(f"   ❌ Spider failed with return code: {result.returncode}")
            if result.stderr:
                print(f"   📋 Error: {result.stderr[-200:]}")  # Last 200 chars
            return False
            
    except subprocess.TimeoutExpired:
        print("   ⏰ Test timed out (5+ minutes)")
        return False
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def main():
    """Run comprehensive consistent scraping tests"""
    print("🚀 CONSISTENT SCRAPING TEST SUITE")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Proxy Pool", test_proxy_pool),
        ("Consistent Manager", test_consistent_manager),
        ("Lianjia Access", test_lianjia_access),
        ("Spider Integration", test_spider_with_consistent_protection),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   💥 {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\\n📈 Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests:.1%})")
    
    if passed_tests == total_tests:
        print("\\n🎉 ALL TESTS PASSED - Consistent scraping is ready!")
        print("\\n💡 Next steps:")
        print("   1. Add premium proxies to proxy_list.txt for best results")
        print("   2. Run: python daily_scraper.py --houses daily")
        print("   3. Monitor success rates and adjust delays if needed")
    elif passed_tests >= total_tests * 0.75:
        print("\\n✅ MOSTLY WORKING - Minor issues detected")
        print("\\n💡 Recommendations:")
        print("   1. Add more proxies for better success rates")
        print("   2. Consider premium proxy services")
        print("   3. Test during off-peak hours")
    else:
        print("\\n⚠️  SIGNIFICANT ISSUES - Need troubleshooting")
        print("\\n🔧 Troubleshooting steps:")
        print("   1. Check internet connection")
        print("   2. Verify proxy configurations")
        print("   3. Try during different time periods")
        print("   4. Consider using premium proxy services")
    
    return passed_tests >= total_tests * 0.5

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
