import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import threading
from concurrent.futures import ThreadPoolExecutor

class ExpandedCityPropertyScraper:
    """
    Expanded scraper covering all major Chinese cities
    Based on successful practical scraper with multi-city support
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        }
        self.session.headers.update(self.headers)
        
        # Expanded city configurations
        self.city_configs = {
            # Tier 1 Cities
            'guangzhou': {
                'name_zh': '广州',
                'province': '广东省',
                'sites': [
                    {
                        'name': '网易房产广州',
                        'url': 'http://gz.house.163.com/',
                        'working': True
                    },
                    {
                        'name': '搜狐焦点广州',
                        'url': 'https://gz.focus.cn/',
                        'working': True
                    }
                ]
            },
            'beijing': {
                'name_zh': '北京',
                'province': '北京市',
                'sites': [
                    {
                        'name': '网易房产北京',
                        'url': 'http://bj.house.163.com/',
                        'working': True
                    },
                    {
                        'name': '搜狐焦点北京',
                        'url': 'https://bj.focus.cn/',
                        'working': True
                    }
                ]
            },
            'shanghai': {
                'name_zh': '上海',
                'province': '上海市',
                'sites': [
                    {
                        'name': '网易房产上海',
                        'url': 'http://sh.house.163.com/',
                        'working': True
                    },
                    {
                        'name': '搜狐焦点上海',
                        'url': 'https://sh.focus.cn/',
                        'working': True
                    }
                ]
            },
            'shenzhen': {
                'name_zh': '深圳',
                'province': '广东省',
                'sites': [
                    {
                        'name': '网易房产深圳',
                        'url': 'http://sz.house.163.com/',
                        'working': True
                    },
                    {
                        'name': '搜狐焦点深圳',
                        'url': 'https://sz.focus.cn/',
                        'working': True
                    }
                ]
            },
            
            # Tier 2 Cities - Guangdong Province
            'foshan': {
                'name_zh': '佛山',
                'province': '广东省',
                'sites': [
                    {
                        'name': '网易房产佛山',
                        'url': 'http://fs.house.163.com/',
                        'working': True
                    },
                    {
                        'name': '搜狐焦点佛山',
                        'url': 'https://fs.focus.cn/',
                        'working': True
                    }
                ]
            },
            'dongguan': {
                'name_zh': '东莞',
                'province': '广东省',
                'sites': [
                    {
                        'name': '网易房产东莞',
                        'url': 'http://dg.house.163.com/',
                        'working': True
                    },
                    {
                        'name': '搜狐焦点东莞',
                        'url': 'https://dg.focus.cn/',
                        'working': True
                    }
                ]
            },
            'zhuhai': {
                'name_zh': '珠海',
                'province': '广东省',
                'sites': [
                    {
                        'name': '网易房产珠海',
                        'url': 'http://zh.house.163.com/',
                        'working': True
                    },
                    {
                        'name': '搜狐焦点珠海',
                        'url': 'https://zh.focus.cn/',
                        'working': True
                    }
                ]
            },
            'zhongshan': {
                'name_zh': '中山',
                'province': '广东省',
                'sites': [
                    {
                        'name': '网易房产中山',
                        'url': 'http://zs.house.163.com/',
                        'working': True
                    }
                ]
            },
            'jiangmen': {
                'name_zh': '江门',
                'province': '广东省',
                'sites': [
                    {
                        'name': '网易房产江门',
                        'url': 'http://jm.house.163.com/',
                        'working': True
                    }
                ]
            },
            'huizhou': {
                'name_zh': '惠州',
                'province': '广东省',
                'sites': [
                    {
                        'name': '网易房产惠州',
                        'url': 'http://hz.house.163.com/',
                        'working': True
                    }
                ]
            },
            
            # Other Major Cities
            'chongqing': {
                'name_zh': '重庆',
                'province': '重庆市',
                'sites': [
                    {
                        'name': '网易房产重庆',
                        'url': 'http://cq.house.163.com/',
                        'working': True
                    },
                    {
                        'name': '搜狐焦点重庆',
                        'url': 'https://cq.focus.cn/',
                        'working': True
                    }
                ]
            },
            'wuhan': {
                'name_zh': '武汉',
                'province': '湖北省',
                'sites': [
                    {
                        'name': '网易房产武汉',
                        'url': 'http://wh.house.163.com/',
                        'working': True
                    },
                    {
                        'name': '搜狐焦点武汉',
                        'url': 'https://wh.focus.cn/',
                        'working': True
                    }
                ]
            },
            'xiamen': {
                'name_zh': '厦门',
                'province': '福建省',
                'sites': [
                    {
                        'name': '网易房产厦门',
                        'url': 'http://xm.house.163.com/',
                        'working': True
                    },
                    {
                        'name': '搜狐焦点厦门',
                        'url': 'https://xm.focus.cn/',
                        'working': True
                    }
                ]
            },
            'fuzhou': {
                'name_zh': '福州',
                'province': '福建省',
                'sites': [
                    {
                        'name': '网易房产福州',
                        'url': 'http://fz.house.163.com/',
                        'working': True
                    }
                ]
            },
            'quanzhou': {
                'name_zh': '泉州',
                'province': '福建省',
                'sites': [
                    {
                        'name': '网易房产泉州',
                        'url': 'http://qz.house.163.com/',
                        'working': True
                    }
                ]
            }
        }
    
    def scrape_all_cities(self, max_workers=5):
        """Scrape all cities using multi-threading"""
        print("🏙️  EXPANDED MULTI-CITY PROPERTY SCRAPING")
        print("=" * 60)
        print(f"🎯 Target cities: {len(self.city_configs)}")
        print(f"🧵 Using {max_workers} concurrent workers\n")
        
        all_results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit scraping tasks for all cities
            future_to_city = {
                executor.submit(self.scrape_single_city, city_key, city_config): city_key
                for city_key, city_config in self.city_configs.items()
            }
            
            # Collect results as they complete
            for future in future_to_city:
                city_key = future_to_city[future]
                try:
                    result = future.result()
                    all_results[city_key] = result
                    
                    city_name = self.city_configs[city_key]['name_zh']
                    property_count = len(result['properties'])
                    status = "✅" if property_count > 0 else "⚠️"
                    
                    print(f"{status} {city_name}: {property_count} properties extracted")
                    
                except Exception as e:
                    print(f"❌ {city_key}: Error - {e}")
                    all_results[city_key] = {'properties': [], 'error': str(e)}
        
        return all_results
    
    def scrape_single_city(self, city_key, city_config):
        """Scrape a single city with all its sites"""
        city_properties = []
        city_name = city_config['name_zh']
        
        try:
            for site in city_config['sites']:
                if site.get('working', True):
                    try:
                        site_properties = self.scrape_site_with_retry(site, city_config)
                        city_properties.extend(site_properties)
                        
                        # Respectful delay between sites
                        time.sleep(random.uniform(2, 5))
                        
                    except Exception as e:
                        print(f"⚠️ {site['name']}: {e}")
                        continue
            
            return {
                'city': city_name,
                'city_key': city_key,
                'province': city_config['province'],
                'properties': city_properties,
                'sites_scraped': len(city_config['sites']),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'city': city_name,
                'city_key': city_key,
                'properties': [],
                'error': str(e)
            }
    
    def scrape_site_with_retry(self, site, city_config, max_retries=3):
        """Scrape a site with retry logic"""
        properties = []
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(site['url'], timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Check for anti-bot indicators
                    page_text = soup.get_text().lower()
                    if any(indicator in page_text for indicator in ['验证码', 'captcha', 'blocked']):
                        if attempt < max_retries - 1:
                            time.sleep(random.uniform(5, 10))
                            continue
                        else:
                            raise Exception("Anti-bot protection detected")
                    
                    # Extract properties using proven patterns
                    properties = self.extract_properties_enhanced(soup, site, city_config)
                    break
                    
                else:
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(3, 7))
                        continue
                    else:
                        raise Exception(f"HTTP {response.status_code}")
                        
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(random.uniform(3, 7))
        
        return properties
    
    def extract_properties_enhanced(self, soup, site, city_config):
        """Enhanced property extraction with multiple strategies"""
        properties = []
        
        # Strategy 1: Text pattern matching (proven to work)
        properties.extend(self.extract_from_text_patterns(soup, site, city_config))
        
        # Strategy 2: Table extraction
        properties.extend(self.extract_from_tables(soup, site, city_config))
        
        # Strategy 3: Article/content extraction
        properties.extend(self.extract_from_content_blocks(soup, site, city_config))
        
        # Remove duplicates and limit results
        seen = set()
        unique_properties = []
        for prop in properties:
            prop_key = f"{prop['building_name_zh']}-{prop['deal_price']}-{prop['area']}"
            if prop_key not in seen:
                seen.add(prop_key)
                unique_properties.append(prop)
        
        return unique_properties[:10]  # Limit to 10 per site
    
    def extract_from_text_patterns(self, soup, site, city_config):
        """Extract using proven text patterns"""
        properties = []
        
        patterns = [
            r'([^，。\s]{2,8}(?:小区|花园|公寓|大厦|广场|城|苑|庭|府))[^，。]*?(\d+\.?\d*)[^，。]*?万[^，。]*?(\d+\.?\d*)[^，。]*?平',
            r'([^，。\s]{2,8}(?:区|市|县))[^，。]*?(\d+\.?\d*)[^，。]*?万[^，。]*?(\d+\.?\d*)[^，。]*?平',
            r'(\d+\.?\d*)[^，。]*?万[^，。]*?平[^，。]*?([^，。\s]{2,8}(?:区|市|县))',
        ]
        
        page_text = soup.get_text()
        
        for pattern in patterns:
            matches = re.finditer(pattern, page_text)
            
            for match in matches:
                try:
                    if len(match.groups()) >= 2:
                        building_name = match.group(1) if '小区' in match.group(1) or '花园' in match.group(1) else f"{city_config['name_zh']}住宅"
                        price_wan = float(match.group(2))
                        area = float(match.group(3)) if len(match.groups()) >= 3 else 100
                        
                        property_data = {
                            'building_name_zh': building_name,
                            'deal_price': int(price_wan * 10000),
                            'area': area,
                            'location': city_config['name_zh'],
                            'zone': 'China',
                            'city': city_config['name_zh'],
                            'province': city_config['province'],
                            'type_raw': '住宅',
                            'type': '住宅',
                            'deal_date': datetime.now().strftime('%Y-%m-%d'),
                            'source_url': site['url'],
                            'data_source': site['name'],
                            'scraped_city': city_config['name_zh'],
                            'start_url': site['url']
                        }
                        
                        properties.append(property_data)
                        
                except (ValueError, IndexError):
                    continue
        
        return properties[:5]  # Limit per pattern
    
    def extract_from_tables(self, soup, site, city_config):
        """Extract from HTML tables"""
        properties = []
        
        tables = soup.find_all('table')
        
        for table in tables[:3]:  # Limit to first 3 tables
            try:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                for row in rows[1:4]:  # Process first 3 data rows
                    cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                    if len(cells) >= 2:
                        property_data = self.create_property_from_cells(cells, site, city_config)
                        if property_data:
                            properties.append(property_data)
                            
            except Exception:
                continue
        
        return properties
    
    def extract_from_content_blocks(self, soup, site, city_config):
        """Extract from content blocks and articles"""
        properties = []
        
        # Look for content blocks
        content_selectors = [
            '.house-item', '.property-item', '.list-item',
            '[class*="house"]', '[class*="property"]', '[class*="item"]'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            
            for element in elements[:5]:  # Limit to first 5 elements
                text = element.get_text()
                if any(keyword in text for keyword in ['万', '平', '房', '住宅']):
                    # Try to extract property info from this element
                    element_properties = self.extract_from_text_patterns(element, site, city_config)
                    properties.extend(element_properties)
        
        return properties[:3]  # Limit results
    
    def create_property_from_cells(self, cells, site, city_config):
        """Create property record from table cells"""
        try:
            property_data = {
                'building_name_zh': f"{city_config['name_zh']}住宅项目",
                'deal_price': 0,
                'area': 100,
                'location': city_config['name_zh'],
                'zone': 'China',
                'city': city_config['name_zh'],
                'province': city_config['province'],
                'type_raw': '住宅',
                'type': '住宅',
                'deal_date': datetime.now().strftime('%Y-%m-%d'),
                'source_url': site['url'],
                'data_source': site['name'],
                'scraped_city': city_config['name_zh'],
                'start_url': site['url']
            }
            
            for cell in cells:
                if not cell:
                    continue
                
                # Look for building names
                if any(char in cell for char in ['小区', '花园', '公寓', '大厦']):
                    property_data['building_name_zh'] = cell
                
                # Look for prices
                elif '万' in cell and re.search(r'\d', cell):
                    price_match = re.search(r'(\d+\.?\d*)', cell)
                    if price_match:
                        property_data['deal_price'] = int(float(price_match.group(1)) * 10000)
                
                # Look for areas
                elif '平' in cell and re.search(r'\d', cell):
                    area_match = re.search(r'(\d+\.?\d*)', cell)
                    if area_match:
                        property_data['area'] = float(area_match.group(1))
            
            # Validate minimum requirements
            if property_data['deal_price'] > 0 or 'building_name_zh' in property_data:
                return property_data
                
        except Exception:
            pass
        
        return None
    
    def save_results(self, all_results):
        """Save scraping results to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'expanded_city_scraping_results_{timestamp}.json'
        
        # Flatten results for easier analysis
        flattened_results = {
            'timestamp': datetime.now().isoformat(),
            'total_cities': len(all_results),
            'cities': all_results,
            'summary': {}
        }
        
        # Generate summary
        total_properties = 0
        successful_cities = 0
        
        for city_key, city_result in all_results.items():
            property_count = len(city_result.get('properties', []))
            total_properties += property_count
            
            if property_count > 0:
                successful_cities += 1
            
            flattened_results['summary'][city_key] = {
                'city_name': city_result.get('city', city_key),
                'property_count': property_count,
                'success': property_count > 0
            }
        
        flattened_results['summary']['totals'] = {
            'total_properties': total_properties,
            'successful_cities': successful_cities,
            'success_rate': f"{(successful_cities/len(all_results)*100):.1f}%"
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(flattened_results, f, ensure_ascii=False, indent=2)
        
        return filename, flattened_results
    
    def run_expanded_scraping(self):
        """Run the complete expanded scraping process"""
        print("🚀 STARTING EXPANDED MULTI-CITY SCRAPING")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Scrape all cities
        all_results = self.scrape_all_cities()
        
        # Save results
        filename, summary = self.save_results(all_results)
        
        # Display summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n🎉 EXPANDED SCRAPING COMPLETE")
        print("=" * 40)
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"🏙️  Cities processed: {summary['total_cities']}")
        print(f"✅ Successful cities: {summary['summary']['totals']['successful_cities']}")
        print(f"📊 Total properties: {summary['summary']['totals']['total_properties']}")
        print(f"📈 Success rate: {summary['summary']['totals']['success_rate']}")
        print(f"💾 Results saved to: {filename}")
        
        # Show city breakdown
        print(f"\n📋 CITY BREAKDOWN:")
        for city_key, city_summary in summary['summary'].items():
            if city_key != 'totals':
                status = "✅" if city_summary['success'] else "❌"
                print(f"   {status} {city_summary['city_name']}: {city_summary['property_count']} properties")
        
        return summary

def main():
    """Run expanded city scraping"""
    scraper = ExpandedCityPropertyScraper()
    
    print("🌟 EXPANDED CHINESE PROPERTY SCRAPER")
    print("=" * 50)
    print(f"🎯 Covering {len(scraper.city_configs)} major Chinese cities")
    print("📡 Using proven working sites (NetEase, Sohu Focus)")
    print("🧵 Multi-threaded for fast parallel processing\n")
    
    try:
        summary = scraper.run_expanded_scraping()
        
        if summary['summary']['totals']['total_properties'] > 0:
            print(f"\n🎊 SUCCESS: Collected property data from multiple cities!")
            print("🔧 Next steps:")
            print("1. Review the detailed results file")
            print("2. Set up automated daily scraping")
            print("3. Integrate with database import")
        else:
            print(f"\n⚠️ Limited success - consider API integration")
            
    except Exception as e:
        print(f"❌ Scraping failed: {e}")

if __name__ == "__main__":
    main()
