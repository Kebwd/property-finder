import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

class BeijingGovernmentScraper:
    """
    Scraper for Beijing Housing Commission official data
    Source: http://zjw.beijing.gov.cn/
    """
    
    def __init__(self):
        self.base_url = "http://zjw.beijing.gov.cn"
        self.property_section = "/bjjs/fwgl/fdcjy/"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def discover_data_sources(self):
        """Find all property-related data pages on Beijing Housing Commission site"""
        print("🔍 DISCOVERING BEIJING GOVERNMENT PROPERTY DATA SOURCES")
        print("=" * 60)
        
        try:
            # Start from main property section
            url = self.base_url + self.property_section
            print(f"📋 Checking: {url}")
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to access property section: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links that might contain property data
            property_keywords = [
                '交易', '成交', '房屋', '住宅', '商品房', 
                '二手房', '新房', '备案', '网签', '数据'
            ]
            
            data_links = []
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                link_text = link.get_text().strip()
                link_url = link['href']
                
                # Check if link contains property-related keywords
                if any(keyword in link_text for keyword in property_keywords):
                    full_url = urljoin(url, link_url)
                    data_links.append({
                        'text': link_text,
                        'url': full_url,
                        'type': 'property_data'
                    })
                    print(f"🏠 Found: {link_text} → {full_url}")
            
            # Also look for direct data files or tables
            tables = soup.find_all('table')
            if tables:
                print(f"📊 Found {len(tables)} data tables on main page")
                for i, table in enumerate(tables):
                    data_links.append({
                        'text': f'Main Page Data Table {i+1}',
                        'url': url,
                        'type': 'data_table',
                        'table_index': i
                    })
            
            print(f"\n✅ Discovery complete: {len(data_links)} potential data sources found")
            return data_links
            
        except Exception as e:
            print(f"❌ Error during discovery: {e}")
            return []
    
    def extract_property_data_from_page(self, url, page_type='general'):
        """Extract property data from a specific page"""
        print(f"\n📊 Extracting data from: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            properties = []
            
            # Strategy 1: Look for data tables
            tables = soup.find_all('table')
            for table in tables:
                table_data = self.parse_data_table(table, url)
                properties.extend(table_data)
            
            # Strategy 2: Look for structured lists
            lists = soup.find_all(['ul', 'ol'])
            for list_elem in lists:
                list_data = self.parse_data_list(list_elem, url)
                properties.extend(list_data)
            
            # Strategy 3: Look for article content with property info
            articles = soup.find_all(['article', 'div'], class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['content', 'article', 'info', 'data']
            ))
            for article in articles:
                article_data = self.parse_article_content(article, url)
                properties.extend(article_data)
            
            print(f"📈 Extracted {len(properties)} property records")
            return properties
            
        except Exception as e:
            print(f"❌ Error extracting from {url}: {e}")
            return []
    
    def parse_data_table(self, table, source_url):
        """Parse property data from HTML table"""
        properties = []
        
        try:
            rows = table.find_all('tr')
            if len(rows) < 2:  # Need header + data
                return properties
            
            # Try to identify table structure
            headers = [th.get_text().strip() for th in rows[0].find_all(['th', 'td'])]
            
            # Look for property-related columns
            property_indicators = ['房屋', '小区', '地址', '价格', '面积', '成交']
            has_property_data = any(any(indicator in header for indicator in property_indicators) 
                                  for header in headers)
            
            if not has_property_data:
                return properties
            
            print(f"📋 Processing table with columns: {headers}")
            
            for row in rows[1:]:  # Skip header
                cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                if len(cells) >= 3:  # Minimum viable data
                    
                    # Extract property information
                    property_data = self.create_property_record(cells, headers, source_url)
                    if property_data:
                        properties.append(property_data)
            
        except Exception as e:
            print(f"⚠️ Table parsing error: {e}")
        
        return properties
    
    def parse_data_list(self, list_elem, source_url):
        """Parse property data from HTML list"""
        properties = []
        
        try:
            items = list_elem.find_all('li')
            
            for item in items:
                text = item.get_text().strip()
                
                # Look for property-like patterns
                if any(keyword in text for keyword in ['房', '住宅', '小区', '万元', '平米']):
                    property_data = self.extract_property_from_text(text, source_url)
                    if property_data:
                        properties.append(property_data)
        
        except Exception as e:
            print(f"⚠️ List parsing error: {e}")
        
        return properties
    
    def parse_article_content(self, article, source_url):
        """Parse property data from article content"""
        properties = []
        
        try:
            text = article.get_text()
            
            # Look for structured property information
            property_patterns = [
                r'(\S+小区|\S+花园|\S+公寓).*?(\d+\.?\d*)\s*万.*?(\d+\.?\d*)\s*平',
                r'([^，。]+区[^，。]*?).*?(\d+\.?\d*)\s*万.*?(\d+\.?\d*)\s*平米?',
            ]
            
            for pattern in property_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    try:
                        name = match.group(1).strip()
                        price_wan = float(match.group(2))
                        area = float(match.group(3))
                        
                        property_data = {
                            'building_name_zh': name,
                            'deal_price': int(price_wan * 10000),
                            'area': area,
                            'location': '北京市',
                            'zone': 'China',
                            'city': '北京',
                            'province': '北京市',
                            'type_raw': '住宅',
                            'type': '住宅',
                            'deal_date': datetime.now().strftime('%Y-%m-%d'),
                            'source_url': source_url,
                            'data_source': '北京市住建委',
                            'scraped_city': 'beijing',
                            'start_url': source_url
                        }
                        properties.append(property_data)
                        
                    except (ValueError, IndexError):
                        continue
        
        except Exception as e:
            print(f"⚠️ Article parsing error: {e}")
        
        return properties
    
    def create_property_record(self, cells, headers, source_url):
        """Create standardized property record from table cells"""
        try:
            # Basic property record template
            property_data = {
                'building_name_zh': '',
                'deal_price': 0,
                'area': 0,
                'location': '北京市',
                'zone': 'China',
                'city': '北京',
                'province': '北京市',
                'type_raw': '住宅',
                'type': '住宅',
                'deal_date': datetime.now().strftime('%Y-%m-%d'),
                'source_url': source_url,
                'data_source': '北京市住建委',
                'scraped_city': 'beijing',
                'start_url': source_url
            }
            
            # Try to map cells to fields based on content
            for i, cell in enumerate(cells):
                if not cell:
                    continue
                
                # Look for building names (contains certain characters)
                if any(char in cell for char in ['小区', '花园', '公寓', '大厦', '广场']):
                    property_data['building_name_zh'] = cell
                
                # Look for prices (contains 万 or large numbers)
                elif '万' in cell or re.search(r'\d{3,}', cell):
                    try:
                        price_match = re.search(r'(\d+\.?\d*)', cell)
                        if price_match:
                            price_val = float(price_match.group(1))
                            if '万' in cell:
                                property_data['deal_price'] = int(price_val * 10000)
                            else:
                                property_data['deal_price'] = int(price_val)
                    except ValueError:
                        pass
                
                # Look for area (contains 平 or decimal numbers)
                elif '平' in cell or re.search(r'\d+\.\d+', cell):
                    try:
                        area_match = re.search(r'(\d+\.?\d*)', cell)
                        if area_match:
                            property_data['area'] = float(area_match.group(1))
                    except ValueError:
                        pass
            
            # Validate minimum required fields
            if (property_data['building_name_zh'] and 
                property_data['deal_price'] > 0 and 
                property_data['area'] > 0):
                return property_data
            
        except Exception as e:
            print(f"⚠️ Record creation error: {e}")
        
        return None
    
    def extract_property_from_text(self, text, source_url):
        """Extract property data from free text"""
        # Implementation for text-based extraction
        pass
    
    def run_full_scrape(self, max_pages=10):
        """Run complete scraping process"""
        print("🚀 STARTING BEIJING GOVERNMENT PROPERTY SCRAPE")
        print("=" * 60)
        
        # Step 1: Discover data sources
        data_sources = self.discover_data_sources()
        
        if not data_sources:
            print("❌ No data sources found")
            return []
        
        # Step 2: Extract from each source
        all_properties = []
        
        for i, source in enumerate(data_sources[:max_pages]):
            print(f"\n📖 Processing source {i+1}/{min(len(data_sources), max_pages)}")
            print(f"📋 {source['text']}")
            
            properties = self.extract_property_data_from_page(source['url'])
            all_properties.extend(properties)
            
            # Respectful delay
            time.sleep(random.uniform(3, 6))
        
        # Step 3: Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'beijing_government_data_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_properties, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 SCRAPING COMPLETE")
        print(f"📊 Total properties extracted: {len(all_properties)}")
        print(f"💾 Data saved to: {filename}")
        
        return all_properties

def main():
    """Run Beijing government scraper"""
    scraper = BeijingGovernmentScraper()
    
    print("🏛️ Beijing Government Property Data Scraper")
    print("Source: Beijing Housing and Urban-Rural Development Commission")
    print("=" * 60)
    
    # Run scraping
    properties = scraper.run_full_scrape(max_pages=5)
    
    if properties:
        print(f"\n✅ SUCCESS: Collected {len(properties)} property records")
        print("💡 Next: Import this data to your database")
    else:
        print(f"\n⚠️ No properties extracted - site structure may have changed")
        print("💡 Fallback: Use demo data for development")

if __name__ == "__main__":
    main()
