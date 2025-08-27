#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Enhanced Lianjia Spider
Based on waugustus/lianjia-spider approach with ScraperAPI integration
"""

import subprocess
import sys
import os
from datetime import datetime
import json

def test_enhanced_lianjia_spider():
    """Test the enhanced Lianjia spider with different configurations"""
    
    print("🕷️  Testing Enhanced Lianjia Spider")
    print("=" * 60)
    print(f"📅 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test configurations based on waugustus project approach
    test_configs = [
        {
            'name': 'Beijing Basic Test',
            'description': 'Test Beijing with default settings (1 item)',
            'command': [
                'python', '-m', 'scrapy', 'crawl', 'enhanced_lianjia',
                '-a', 'city=beijing',
                '-s', 'CLOSESPIDER_ITEMCOUNT=1',
                '-L', 'INFO'
            ]
        },
        {
            'name': 'Shanghai District Test', 
            'description': 'Test Shanghai with specific district (1 item)',
            'command': [
                'python', '-m', 'scrapy', 'crawl', 'enhanced_lianjia',
                '-a', 'city=shanghai',
                '-a', 'district=浦东',
                '-s', 'CLOSESPIDER_ITEMCOUNT=1',
                '-L', 'INFO'
            ]
        },
        {
            'name': 'Guangzhou Price Filter Test',
            'description': 'Test Guangzhou with price filtering (1 item)',
            'command': [
                'python', '-m', 'scrapy', 'crawl', 'enhanced_lianjia',
                '-a', 'city=guangzhou',
                '-a', 'min_price=200',
                '-a', 'max_price=500',
                '-s', 'CLOSESPIDER_ITEMCOUNT=1',
                '-L', 'INFO'
            ]
        },
        {
            'name': 'Shenzhen House Type Test',
            'description': 'Test Shenzhen with house type filtering (1 item)',
            'command': [
                'python', '-m', 'scrapy', 'crawl', 'enhanced_lianjia',
                '-a', 'city=shenzhen',
                '-a', 'house_type=l2l3',
                '-s', 'CLOSESPIDER_ITEMCOUNT=1',
                '-L', 'INFO'
            ]
        }
    ]
    
    # Change to scraper directory
    scraper_dir = r'C:\Users\User\property-finder\scraper'
    if os.path.exists(scraper_dir):
        os.chdir(scraper_dir)
        print(f"📁 Changed to directory: {scraper_dir}")
    else:
        print(f"❌ Directory not found: {scraper_dir}")
        return
    
    results = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n🧪 Test {i}/{len(test_configs)}: {config['name']}")
        print(f"📝 {config['description']}")
        print(f"⚡ Command: {' '.join(config['command'])}")
        print("-" * 50)
        
        try:
            # Run the spider
            result = subprocess.run(
                config['command'],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                cwd=scraper_dir
            )
            
            # Analyze results
            success = result.returncode == 0
            output_lines = result.stdout.split('\n') if result.stdout else []
            error_lines = result.stderr.split('\n') if result.stderr else []
            
            # Extract key information
            items_scraped = 0
            for line in output_lines:
                if 'item_scraped_count' in line:
                    try:
                        items_scraped = int(line.split('item_scraped_count')[1].split()[0])
                    except:
                        pass
            
            # Check for ScraperAPI usage
            scraperapi_used = any('scraperapi' in line.lower() for line in output_lines)
            
            # Check for blocking
            blocked = any(
                indicator in ' '.join(output_lines).lower() 
                for indicator in ['blocked', 'captcha', '验证', '人机验证']
            )
            
            # Store results
            test_result = {
                'name': config['name'],
                'success': success,
                'items_scraped': items_scraped,
                'scraperapi_used': scraperapi_used,
                'blocked': blocked,
                'return_code': result.returncode,
                'duration': 'N/A'  # Would need timing logic
            }
            
            results.append(test_result)
            
            # Print immediate results
            if success:
                print(f"✅ {config['name']}: SUCCESS")
                print(f"📊 Items scraped: {items_scraped}")
                print(f"🔗 ScraperAPI used: {'Yes' if scraperapi_used else 'No'}")
                print(f"🚫 Blocked: {'Yes' if blocked else 'No'}")
            else:
                print(f"❌ {config['name']}: FAILED")
                print(f"💥 Return code: {result.returncode}")
                if error_lines:
                    print(f"🔥 Error: {error_lines[0][:100]}...")
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {config['name']}: TIMEOUT (5 minutes)")
            results.append({
                'name': config['name'],
                'success': False,
                'error': 'Timeout',
                'duration': '300+ seconds'
            })
        except Exception as e:
            print(f"💥 {config['name']}: ERROR - {e}")
            results.append({
                'name': config['name'],
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    print(f"❌ Failed tests: {total_tests - successful_tests}/{total_tests}")
    
    total_items = sum(r.get('items_scraped', 0) for r in results)
    print(f"📊 Total items scraped: {total_items}")
    
    scraperapi_tests = sum(1 for r in results if r.get('scraperapi_used', False))
    print(f"🔗 Tests using ScraperAPI: {scraperapi_tests}/{total_tests}")
    
    blocked_tests = sum(1 for r in results if r.get('blocked', False))
    print(f"🚫 Tests encountering blocks: {blocked_tests}/{total_tests}")
    
    print(f"\n📅 Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Detailed results
    print("\n📋 DETAILED RESULTS:")
    print("-" * 60)
    for result in results:
        status = "✅ PASS" if result.get('success') else "❌ FAIL"
        print(f"{status} {result['name']}")
        if result.get('items_scraped', 0) > 0:
            print(f"    📊 Items: {result['items_scraped']}")
        if result.get('error'):
            print(f"    💥 Error: {result['error']}")
    
    # Save results to file
    results_file = f"enhanced_lianjia_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'total_items_scraped': total_items,
                    'scraperapi_usage': scraperapi_tests,
                    'blocked_tests': blocked_tests
                },
                'detailed_results': results
            }, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {results_file}")
    except Exception as e:
        print(f"\n❌ Failed to save results: {e}")
    
    return successful_tests == total_tests

if __name__ == '__main__':
    try:
        success = test_enhanced_lianjia_spider()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
