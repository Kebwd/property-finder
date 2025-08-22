import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin

class GovernmentPropertyScraper:
    """
    Scraper for official government property transaction records
    These are often more accessible than commercial sites
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Government property data sources
        self.sources = {
            'beijing': {
                'name': '北京市住房和城乡建设委员会',
                'url': 'http://zjw.beijing.gov.cn/',
                'data_url': 'http://zjw.beijing.gov.cn/bjjs/fwgl/fdcjy/',
                'type': 'government'
            },
            'shanghai': {
                'name': '上海房地产市场网',
                'url': 'http://www.fangdi.com.cn/',
                'data_url': 'http://www.fangdi.com.cn/new_house/new_house.php',
                'type': 'government'
            },
            'shenzhen': {
                'name': '深圳市规划和国土资源委员会',
                'url': 'http://www.szpl.gov.cn/',
                'data_url': 'http://www.szpl.gov.cn/xxgk/zyfw/fdcjy/',
                'type': 'government'
            },
            'guangzhou': {
                'name': '广州市住房和城乡建设局',
                'url': 'http://zfcj.gz.gov.cn/',
                'data_url': 'http://zfcj.gz.gov.cn/gkmlpt/content/5/',
                'type': 'government'
            }
        }
    
    def test_government_sources(self):
        """Test accessibility of government property data sources"""
        print("🏛️  TESTING GOVERNMENT PROPERTY DATA SOURCES")
        print("=" * 50)
        
        results = {}
        
        for city, source_info in self.sources.items():
            print(f"\n🏙️  Testing {city.upper()}: {source_info['name']}")
            print(f"🔗 URL: {source_info['url']}")
            
            try:
                # Test main site accessibility
                response = requests.get(source_info['url'], headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    title = soup.title.string if soup.title else "No title"
                    
                    print(f"✅ Site accessible - Status: {response.status_code}")
                    print(f"📄 Title: {title[:100]}...")
                    
                    # Check for property-related content
                    content = soup.get_text()
                    property_keywords = ['房屋', '交易', '买卖', '住房', '房地产', '物业']
                    found_keywords = [kw for kw in property_keywords if kw in content]
                    
                    if found_keywords:
                        print(f"🏠 Property content found: {found_keywords}")
                        
                        # Look for data tables or links
                        tables = soup.find_all('table')
                        data_links = soup.find_all('a', href=True)
                        
                        if tables:
                            print(f"📊 Found {len(tables)} data tables")
                        if data_links:
                            relevant_links = [link for link in data_links 
                                            if any(kw in link.get_text() for kw in property_keywords)]
                            print(f"🔗 Found {len(relevant_links)} relevant data links")
                        
                        results[city] = {
                            'status': 'accessible',
                            'has_property_content': True,
                            'tables_count': len(tables),
                            'relevant_links': len(relevant_links) if 'relevant_links' in locals() else 0
                        }
                    else:
                        print("⚠️  No property-related content detected")
                        results[city] = {
                            'status': 'accessible',
                            'has_property_content': False
                        }
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    results[city] = {
                        'status': 'http_error',
                        'status_code': response.status_code
                    }
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Request failed: {e}")
                results[city] = {
                    'status': 'request_error',
                    'error': str(e)
                }
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                results[city] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Respectful delay
            time.sleep(random.uniform(2, 4))
        
        return results
    
    def generate_scraping_recommendations(self, results):
        """Generate recommendations based on test results"""
        print(f"\n📋 GOVERNMENT DATA SCRAPING RECOMMENDATIONS")
        print("=" * 50)
        
        accessible_sources = []
        blocked_sources = []
        
        for city, result in results.items():
            if result['status'] == 'accessible' and result.get('has_property_content', False):
                accessible_sources.append(city)
                print(f"✅ {city.upper()}: Ready for data extraction")
                if result.get('tables_count', 0) > 0:
                    print(f"   📊 {result['tables_count']} data tables available")
                if result.get('relevant_links', 0) > 0:
                    print(f"   🔗 {result['relevant_links']} relevant links found")
            else:
                blocked_sources.append(city)
                status = result['status']
                print(f"❌ {city.upper()}: {status}")
        
        print(f"\n🎯 IMPLEMENTATION STRATEGY:")
        
        if accessible_sources:
            print(f"✅ Priority Cities ({len(accessible_sources)}): {', '.join(accessible_sources)}")
            print("   → Focus scraping efforts on these government sources")
            print("   → Government data is typically more reliable and legal")
            print("   → Less likely to have anti-bot measures")
        
        if blocked_sources:
            print(f"⚠️  Alternative Needed ({len(blocked_sources)}): {', '.join(blocked_sources)}")
            print("   → Use demo data or API services for these cities")
            print("   → Consider regional property portals")
        
        print(f"\n💡 NEXT STEPS:")
        if accessible_sources:
            print("1. Create targeted scrapers for accessible government sources")
            print("2. Parse structured data tables from government sites")
            print("3. Supplement with demo data for blocked cities")
        else:
            print("1. All government sources blocked - use demo data approach")
            print("2. Consider paid API services for production data")
            print("3. Focus on alternative regional property sites")
        
        return accessible_sources, blocked_sources

def main():
    """Test government property data sources"""
    scraper = GovernmentPropertyScraper()
    
    print("🔍 Testing Chinese Government Property Data Sources...")
    print("Government sources are often more accessible and legal to scrape.\n")
    
    # Test all sources
    results = scraper.test_government_sources()
    
    # Generate recommendations
    accessible, blocked = scraper.generate_scraping_recommendations(results)
    
    # Save results
    with open('government_source_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Test results saved to: government_source_test_results.json")
    
    if accessible:
        print(f"🚀 SUCCESS: {len(accessible)} government sources ready for implementation!")
    else:
        print(f"⚠️  No accessible sources found - recommend using demo data approach")

if __name__ == "__main__":
    main()
