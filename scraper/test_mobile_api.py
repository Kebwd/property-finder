"""
Test Mobile Lianjia API - Verify CaoZ approach works
"""

import asyncio
import sys
from pathlib import Path

# Add scraper directory to path
sys.path.append(str(Path(__file__).parent))

from utils.mobile_api_helpers import test_mobile_api_connection, test_community_page_access


async def test_mobile_api():
    """Test mobile API authentication and data access"""
    print("🚀 Testing Mobile Lianjia API (CaoZ approach)...")
    print("=" * 60)
    
    # Mobile app configuration
    app_config = {
        'user_agent': 'HomeLink7.7.6; Android 7.0',
        'app_id': '20161001_android',
        'app_secret': '7df91ff794c67caee14c3dacd5549b35'
    }
    
    # Test cities
    test_cities = [
        {'id': 110000, 'abbr': 'bj', 'name': 'Beijing'},
        {'id': 310000, 'abbr': 'sh', 'name': 'Shanghai'},
        {'id': 440100, 'abbr': 'gz', 'name': 'Guangzhou'}
    ]
    
    print("📱 Testing Mobile API Authentication...")
    
    for city in test_cities:
        print(f"\n🏙️ Testing {city['name']} (ID: {city['id']})...")
        
        result = await test_mobile_api_connection(
            endpoint='http://app.api.lianjia.com/config/config/initData',
            city_id=city['id'],
            app_config=app_config
        )
        
        if result['success']:
            print(f"  ✅ API Success: {result['message']}")
            if 'city_count' in result:
                print(f"  📊 Data received: {result['city_count']} city records")
        else:
            print(f"  ❌ API Failed: {result['error']}")
    
    print("\n📄 Testing Community Detail Pages...")
    
    # Test community page access (sample community IDs)
    test_communities = [
        {'city': 'bj', 'id': '1111027377528', 'name': 'Beijing Sample'},
        {'city': 'sh', 'id': '1111027374645', 'name': 'Shanghai Sample'},
        {'city': 'gz', 'id': '1111027378493', 'name': 'Guangzhou Sample'}
    ]
    
    for community in test_communities:
        print(f"\n🏘️ Testing {community['name']} community page...")
        
        result = await test_community_page_access(
            city_abbr=community['city'],
            community_id=community['id'],
            user_agent=app_config['user_agent']
        )
        
        if result['success']:
            print(f"  ✅ Page Access Success")
            print(f"  📄 Content length: {result.get('content_length', 0)} chars")
            print(f"  📊 Has data: {result.get('has_data', False)}")
        else:
            print(f"  ❌ Page Access Failed: {result.get('error', 'Unknown error')}")
            print(f"  🚫 Blocked: {result.get('is_blocked', False)}")
    
    print("\n" + "=" * 60)
    print("🎯 Mobile API Test Summary:")
    print("📱 API Approach: Uses official Lianjia mobile app endpoints")
    print("🔐 Authentication: App credentials + signed requests")
    print("⚡ Speed: Much faster than web scraping")
    print("🛡️ Anti-Bot: Lower risk due to mobile API usage")
    
    print("\n🚀 Ready to run mobile spider:")
    print("python -m scrapy crawl mobile_lianjia -a city=beijing -a mode=communities")


if __name__ == '__main__':
    asyncio.run(test_mobile_api())
