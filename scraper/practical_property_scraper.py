import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

class PracticalPropertyScraper:
    """
    Practical property scraper targeting sites that actually work
    Focus on news sites, regional portals, and academic sources
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
    
    def test_accessible_sites(self):
        """Test which property-related sites are actually accessible"""
        print("🧪 TESTING ACCESSIBLE PROPERTY DATA SOURCES")
        print("=" * 60)
        
        # Sites to test (likely to work)
        test_sites = {
            'news_sites': [
                {
                    'name': '新华网房产',
                    'url': 'http://www.news.cn/house/',
                    'keywords': ['房价', '房产', '楼市']
                },
                {
                    'name': '人民网房产',
                    'url': 'http://house.people.com.cn/',
                    'keywords': ['房地产', '住房', '楼盘']
                },
                {
                    'name': '中新网房产',
                    'url': 'http://www.chinanews.com/house/',
                    'keywords': ['房屋', '房价', '地产']
                }
            ],
            
            'regional_sites': [
                {
                    'name': '网易房产广州',
                    'url': 'http://gz.house.163.com/',
                    'keywords': ['广州', '房价', '楼盘']
                },
                {
                    'name': '网易房产北京',
                    'url': 'http://bj.house.163.com/',
                    'keywords': ['北京', '房价', '新房']
                },
                {
                    'name': '搜狐焦点',
                    'url': 'https://house.focus.cn/',
                    'keywords': ['房产', '楼盘', '房价']
                }
            ],
            
            'government_related': [
                {
                    'name': '中国房地产业协会',
                    'url': 'http://www.realestate.org.cn/',
                    'keywords': ['房地产', '市场', '统计']
                },
                {
                    'name': '住建部门户网站',
                    'url': 'http://www.mohurd.gov.cn/',
                    'keywords': ['住房', '建设', '政策']
                }
            ]
        }
        
        accessible_sites = {}
        
        for category, sites in test_sites.items():
            print(f"\n📂 Testing {category.upper().replace('_', ' ')}")
            accessible_sites[category] = []
            
            for site in sites:
                result = self.test_single_site(site)
                if result['accessible']:
                    accessible_sites[category].append(result)
                    print(f"✅ {site['name']}: Accessible")
                    if result['has_property_data']:
                        print(f"   🏠 Contains property data")
                    if result['has_data_tables']:
                        print(f"   📊 Has data tables")
                else:
                    print(f"❌ {site['name']}: {result['error']}")
                
                # Respectful delay
                time.sleep(random.uniform(2, 4))
        
        return accessible_sites
    
    def test_single_site(self, site_config):
        """Test if a single site is accessible and has property data"""
        try:
            response = self.session.get(site_config['url'], timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                page_text = soup.get_text().lower()
                
                # Check for property-related content
                has_property_data = any(keyword in page_text for keyword in site_config['keywords'])
                
                # Check for data structures
                tables = soup.find_all('table')
                lists = soup.find_all(['ul', 'ol'])
                
                return {
                    'accessible': True,
                    'name': site_config['name'],
                    'url': site_config['url'],
                    'has_property_data': has_property_data,
                    'has_data_tables': len(tables) > 0,
                    'tables_count': len(tables),
                    'lists_count': len(lists),
                    'title': soup.title.string if soup.title else 'No title'
                }
            else:
                return {
                    'accessible': False,
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'accessible': False,
                'error': str(e)
            }
    
    def scrape_property_news_data(self, accessible_sites):
        """Extract property data from news and accessible sites"""
        print(f"\n🔍 EXTRACTING PROPERTY DATA FROM ACCESSIBLE SITES")
        print("=" * 60)
        
        all_properties = []
        
        # Focus on sites that showed property data
        for category, sites in accessible_sites.items():
            for site in sites:
                if site['has_property_data']:
                    print(f"\n📊 Extracting from: {site['name']}")
                    
                    try:
                        properties = self.extract_property_data_from_site(site)
                        all_properties.extend(properties)
                        print(f"✅ Extracted {len(properties)} property records")
                        
                    except Exception as e:
                        print(f"❌ Error extracting from {site['name']}: {e}")
                    
                    # Respectful delay
                    time.sleep(random.uniform(3, 6))
        
        return all_properties
    
    def extract_property_data_from_site(self, site):
        """Extract property data from a specific site"""
        properties = []
        
        try:
            response = self.session.get(site['url'], timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Strategy 1: Look for property price patterns in text
            properties.extend(self.extract_from_text_patterns(soup, site))
            
            # Strategy 2: Look for structured data in tables
            properties.extend(self.extract_from_tables(soup, site))
            
            # Strategy 3: Look for article content with property info
            properties.extend(self.extract_from_articles(soup, site))
            
        except Exception as e:
            print(f"⚠️ Extraction error: {e}")
        
        return properties
    
    def extract_from_text_patterns(self, soup, site):
        """Extract property data using text pattern matching"""
        properties = []
        
        # Common Chinese property patterns
        patterns = [
            # Pattern: 地区 + 价格 + 面积
            r'([^，。\s]{2,8}(?:区|市|县))[^，。]*?(\d+\.?\d*)[^，。]*?万[^，。]*?(\d+\.?\d*)[^，。]*?平',
            
            # Pattern: 楼盘名 + 价格
            r'([^，。\s]*?(?:花园|小区|公寓|大厦|广场|城|苑|庭|府))[^，。]*?(\d+\.?\d*)[^，。]*?万',
            
            # Pattern: 价格万元/平米
            r'(\d+\.?\d*)[^，。]*?万元[^，。]*?平[^，。]*?米[^，。]*?([^，。\s]{2,8}(?:区|市|县))',
        ]
        
        page_text = soup.get_text()
        
        for pattern in patterns:
            matches = re.finditer(pattern, page_text)
            
            for match in matches:
                try:
                    if len(match.groups()) >= 2:
                        if '区' in match.group(1) or '市' in match.group(1):
                            # Location + Price pattern
                            location = match.group(1)
                            price_wan = float(match.group(2))
                            area = float(match.group(3)) if len(match.groups()) >= 3 else 100
                        else:
                            # Building + Price pattern  
                            building_name = match.group(1)
                            price_wan = float(match.group(2))
                            location = self.extract_city_from_url(site['url'])
                            area = 100  # Default area
                        
                        property_data = {
                            'building_name_zh': building_name if 'building_name' in locals() else f"{location}住宅",
                            'deal_price': int(price_wan * 10000),
                            'area': area,
                            'location': location if 'location' in locals() else self.extract_city_from_url(site['url']),
                            'zone': 'China',
                            'city': self.extract_city_from_url(site['url']),
                            'province': self.get_province_from_city(self.extract_city_from_url(site['url'])),
                            'type_raw': '住宅',
                            'type': '住宅',
                            'deal_date': datetime.now().strftime('%Y-%m-%d'),
                            'source_url': site['url'],
                            'data_source': site['name'],
                            'scraped_city': self.extract_city_from_url(site['url']),
                            'start_url': site['url']
                        }
                        
                        properties.append(property_data)
                        
                except (ValueError, IndexError) as e:
                    continue
        
        return properties[:10]  # Limit to avoid duplicates
    
    def extract_from_tables(self, soup, site):
        """Extract property data from HTML tables"""
        properties = []
        
        tables = soup.find_all('table')
        
        for table in tables:
            try:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                # Look for property-related headers
                header_row = rows[0]
                headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
                
                # Check if table contains property data
                property_indicators = ['房价', '价格', '楼盘', '小区', '面积', '地区']
                if not any(indicator in ' '.join(headers) for indicator in property_indicators):
                    continue
                
                # Extract data from rows
                for row in rows[1:6]:  # Limit to first 5 rows
                    cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                    if len(cells) >= 2:
                        property_data = self.create_property_from_table_row(cells, headers, site)
                        if property_data:
                            properties.append(property_data)
                            
            except Exception as e:
                continue
        
        return properties
    
    def extract_from_articles(self, soup, site):
        """Extract property data from article content"""
        properties = []
        
        # Look for article-like content
        articles = soup.find_all(['article', 'div'], class_=lambda x: x and any(
            keyword in x.lower() for keyword in ['content', 'article', 'news', 'text']
        ))
        
        for article in articles[:3]:  # Limit to first 3 articles
            try:
                text = article.get_text()
                if any(keyword in text for keyword in ['房价', '楼盘', '万元', '平米']):
                    article_properties = self.extract_from_text_patterns(article, site)
                    properties.extend(article_properties)
            except:
                continue
        
        return properties[:5]  # Limit results
    
    def create_property_from_table_row(self, cells, headers, site):
        """Create property record from table row data"""
        try:
            property_data = {
                'building_name_zh': '',
                'deal_price': 0,
                'area': 100,
                'location': self.extract_city_from_url(site['url']),
                'zone': 'China',
                'city': self.extract_city_from_url(site['url']),
                'province': self.get_province_from_city(self.extract_city_from_url(site['url'])),
                'type_raw': '住宅',
                'type': '住宅',
                'deal_date': datetime.now().strftime('%Y-%m-%d'),
                'source_url': site['url'],
                'data_source': site['name'],
                'scraped_city': self.extract_city_from_url(site['url']),
                'start_url': site['url']
            }
            
            # Try to extract meaningful data from cells
            for i, cell in enumerate(cells):
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
            
            # Set default building name if not found
            if not property_data['building_name_zh']:
                property_data['building_name_zh'] = f"{property_data['city']}住宅项目"
            
            # Validate minimum requirements
            if property_data['deal_price'] > 0:
                return property_data
                
        except Exception as e:
            pass
        
        return None
    
    def extract_city_from_url(self, url):
        """Extract city name from URL"""
        city_patterns = {
            'bj.': '北京',
            'sh.': '上海',
            'gz.': '广州',
            'sz.': '深圳',
            'tj.': '天津',
            'cq.': '重庆'
        }
        
        for pattern, city in city_patterns.items():
            if pattern in url:
                return city
        
        return '未知城市'
    
    def get_province_from_city(self, city):
        """Get province from city name"""
        province_mapping = {
            '北京': '北京市',
            '上海': '上海市',
            '广州': '广东省',
            '深圳': '广东省',
            '天津': '天津市',
            '重庆': '重庆市'
        }
        
        return province_mapping.get(city, '未知省份')
    
    def run_complete_scraping(self):
        """Run complete practical scraping process"""
        print("🕷️  PRACTICAL PROPERTY DATA SCRAPING")
        print("=" * 60)
        print("Testing accessible sites and extracting real property data...\n")
        
        # Step 1: Test site accessibility
        accessible_sites = self.test_accessible_sites()
        
        # Step 2: Extract property data
        properties = self.scrape_property_news_data(accessible_sites)
        
        # Step 3: Save results
        if properties:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'practical_scraping_results_{timestamp}.json'
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(properties, f, ensure_ascii=False, indent=2)
            
            print(f"\n🎉 SCRAPING COMPLETE")
            print(f"📊 Total properties extracted: {len(properties)}")
            print(f"💾 Results saved to: {filename}")
            
            # Show sample data
            if len(properties) > 0:
                print(f"\n📋 SAMPLE PROPERTY DATA:")
                sample = properties[0]
                print(f"   楼盘: {sample['building_name_zh']}")
                print(f"   价格: ¥{sample['deal_price']:,}")
                print(f"   面积: {sample['area']}平米")
                print(f"   位置: {sample['location']}")
                print(f"   数据源: {sample['data_source']}")
        else:
            print(f"\n⚠️ No property data extracted")
            print("💡 Consider trying different sites or adjusting extraction patterns")
        
        return properties

def main():
    """Run practical property scraping"""
    scraper = PracticalPropertyScraper()
    
    print("🌐 Starting practical property data scraping...")
    print("Targeting news sites, regional portals, and accessible sources\n")
    
    try:
        properties = scraper.run_complete_scraping()
        
        if properties:
            print(f"\n✅ SUCCESS: Extracted {len(properties)} property records")
            print("🔧 Next steps:")
            print("1. Review the extracted data for quality")
            print("2. Adjust extraction patterns if needed")
            print("3. Scale up successful sites")
            print("4. Integrate with your database")
        else:
            print(f"\n🔍 ALTERNATIVE SUGGESTIONS:")
            print("1. Try the API approach (RapidAPI, Fang.com APIs)")
            print("2. Use government open data sources")
            print("3. Focus on academic research datasets")
            
    except Exception as e:
        print(f"❌ Scraping failed: {e}")

if __name__ == "__main__":
    main()
