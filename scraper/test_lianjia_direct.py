#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Direct Lianjia Test - Based on waugustus/lianjia-spider approach
Test basic connectivity and data extraction without Scrapy overhead
"""

import requests
import json
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings()

def test_lianjia_direct():
    """Test Lianjia directly using waugustus approach"""
    
    print("🏠 Testing Lianjia Direct Access (waugustus style)")
    print("=" * 60)
    
    # ScraperAPI configuration
    api_key = 'b462bc754d65dad46e73652975fd308c'
    proxy = {
        'http': f'http://scraperapi:{api_key}@proxy-server.scraperapi.com:8001',
        'https': f'http://scraperapi:{api_key}@proxy-server.scraperapi.com:8001'
    }
    
    # Headers (based on waugustus approach)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-us",
        "Connection": "keep-alive",
        "Accept-Charset": "GB2312,utf-8;q=0.7,*;q=0.7"
    }
    
    # Test URLs (waugustus patterns)
    test_urls = [
        'https://bj.lianjia.com/ershoufang/',
        'https://bj.lianjia.com/ershoufang/pg1/',
        'https://bj.lianjia.com/ershoufang/pg1l2l3l4/',
        'https://sh.lianjia.com/ershoufang/',
        'https://gz.lianjia.com/ershoufang/'
    ]
    
    for url in test_urls:
        print(f"\n🔍 Testing: {url}")
        print("-" * 50)
        
        try:
            # Make request with ScraperAPI
            response = requests.get(
                url, 
                proxies=proxy, 
                headers=headers, 
                timeout=60,  # Longer timeout
                verify=False
            )
            
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Content Length: {len(response.content)} bytes")
            
            # Check for key indicators
            content = response.text
            
            # Success indicators
            has_sellListContent = 'sellListContent' in content
            has_properties = '二手房' in content or '房源' in content
            has_prices = '万' in content and ('总价' in content or '单价' in content)
            has_pagination = 'page-box' in content
            
            print(f"🏠 sellListContent found: {'✅' if has_sellListContent else '❌'}")
            print(f"📋 Property listings: {'✅' if has_properties else '❌'}")
            print(f"💰 Price information: {'✅' if has_prices else '❌'}")
            print(f"📄 Pagination: {'✅' if has_pagination else '❌'}")
            
            # Check for blocking indicators
            blocking_indicators = ['验证', 'captcha', 'verify', 'blocked', '人机验证']
            is_blocked = any(indicator in content.lower() for indicator in blocking_indicators)
            print(f"🚫 Blocked: {'❌ YES' if is_blocked else '✅ NO'}")
            
            # If successful, try to extract data using waugustus method
            if has_sellListContent and not is_blocked:
                print("🎉 SUCCESS! Attempting data extraction...")
                
                soup = BeautifulSoup(content, 'html.parser')
                properties = extract_properties_waugustus(soup, url)
                
                print(f"📊 Properties extracted: {len(properties)}")
                
                if properties:
                    print("\n📋 Sample Property:")
                    sample = properties[0]
                    for key, value in sample.items():
                        print(f"   {key}: {value}")
                
                return True, len(properties)
            
            elif is_blocked:
                print("❌ BLOCKED - Anti-bot detection active")
                # Print first 200 chars to see what we got
                print(f"Response preview: {content[:200]}...")
            
            else:
                print("⚠️ UNCLEAR - Page loaded but no property data found")
                # Print first 200 chars
                print(f"Response preview: {content[:200]}...")
                
        except Exception as e:
            print(f"💥 ERROR: {e}")
    
    return False, 0

def extract_properties_waugustus(soup, url):
    """Extract properties using exact waugustus method"""
    properties = []
    
    # Find house list (waugustus selector)
    house_list = soup.find('ul', {'class': 'sellListContent'})
    if not house_list:
        return properties
    
    print(f"🔍 Found sellListContent container")
    
    # Extract each house (waugustus approach)
    houses = house_list.find_all('li')
    print(f"🏠 Found {len(houses)} house items")
    
    for house in houses[:3]:  # Test first 3 only
        try:
            # waugustus extraction logic
            info = house.find("div", {'class': 'info'})
            if not info:
                continue
            
            # Title and ID (waugustus method)
            house_title = info.find("div", {'class': 'title'})
            if not house_title or not house_title.a:
                continue
            
            title_link = house_title.a
            house_id = extract_house_id_waugustus(title_link.get('href', ''))
            title = title_link.get_text(strip=True)
            
            # Location (waugustus method)
            house_location = ''
            flood_div = info.find("div", {'class': 'flood'})
            if flood_div and flood_div.div and flood_div.div.a:
                house_location = flood_div.div.a.get_text(strip=True)
            
            # Address (waugustus method)
            address = info.find("div", {'class': 'address'})
            address_info = parse_address_waugustus(address)
            
            # Price (waugustus method)
            price_info = info.find("div", {'class': 'priceInfo'})
            prices = parse_price_waugustus(price_info)
            
            # Build property data (waugustus format)
            property_data = {
                'house_id': house_id,
                'house_location': house_location,
                'house_type': address_info.get('house_type', ''),
                'house_size': address_info.get('house_size', ''),
                'house_towards': address_info.get('house_towards', ''),
                'house_flood': address_info.get('house_flood', ''),
                'house_year': address_info.get('house_year', ''),
                'house_building': address_info.get('house_building', ''),
                'house_total_price': prices.get('total_price', ''),
                'house_unit_price': prices.get('unit_price', ''),
                'title': title,
                'url': url
            }
            
            if house_id > 0:
                properties.append(property_data)
                
        except Exception as e:
            print(f"   ❌ Error extracting property: {e}")
            continue
    
    return properties

def extract_house_id_waugustus(href):
    """Extract house ID - waugustus method"""
    if not href:
        return 0
    try:
        match = re.search(r'/(\d+)\.html', href)
        if match:
            return int(match.group(1))
    except:
        pass
    return 0

def parse_address_waugustus(address_div):
    """Parse address - waugustus method"""
    info = {
        'house_type': '',
        'house_size': '',
        'house_towards': '',
        'house_flood': '',
        'house_year': '',
        'house_building': ''
    }
    
    if not address_div:
        return info
    
    try:
        address_text = address_div.get_text(strip=True)
        address_parts = [part.strip() for part in address_text.split('|')]
        
        # waugustus logic
        if len(address_parts) >= 1:
            info['house_type'] = address_parts[0]
        if len(address_parts) >= 2:
            info['house_size'] = address_parts[1]
        if len(address_parts) >= 3:
            info['house_towards'] = address_parts[2]
        if len(address_parts) >= 4:
            info['house_flood'] = address_parts[3]
        if len(address_parts) < 7:
            if len(address_parts) >= 6:
                info['house_building'] = address_parts[5]
        else:
            if len(address_parts) >= 6:
                info['house_year'] = address_parts[5]
            if len(address_parts) >= 7:
                info['house_building'] = address_parts[6]
                
    except Exception as e:
        print(f"   Address parsing error: {e}")
    
    return info

def parse_price_waugustus(price_info):
    """Parse price - waugustus method"""
    prices = {
        'total_price': '',
        'unit_price': ''
    }
    
    if not price_info:
        return prices
    
    try:
        # Total price (waugustus method)
        total_price_div = price_info.find("div", {'class': 'totalPrice'})
        if total_price_div and total_price_div.span:
            prices['total_price'] = total_price_div.span.get_text(strip=True) + "万"
        
        # Unit price (waugustus method)
        unit_price_div = price_info.find("div", {'class': 'unitPrice'})
        if unit_price_div and unit_price_div.span:
            unit_price_text = unit_price_div.span.get_text(strip=True)
            # Extract from format like "单价33000元/平米"
            prices['unit_price'] = unit_price_text[2:-4] if len(unit_price_text) > 6 else unit_price_text
            
    except Exception as e:
        print(f"   Price parsing error: {e}")
    
    return prices

if __name__ == '__main__':
    try:
        success, count = test_lianjia_direct()
        
        print("\n" + "=" * 60)
        print("📊 FINAL RESULT")
        print("=" * 60)
        
        if success:
            print(f"🎉 SUCCESS! Extracted {count} properties using waugustus method")
            print("✅ The waugustus/lianjia-spider approach works with ScraperAPI!")
            print("✅ Ready for integration into your property-finder system")
        else:
            print("❌ FAILED - Lianjia blocking detection too strong")
            print("💡 Consider alternative approaches:")
            print("   - Different property sites (Fang.com, 58.com)")
            print("   - Browser automation with Selenium")
            print("   - Official APIs or data partnerships")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
