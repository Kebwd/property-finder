#!/usr/bin/env python3
"""
Scrapy Health Check
Comprehensive system check for spider functionality
"""
import sys
import os
import json
import yaml
import importlib.util
from pathlib import Path

def check_environment():
    """Check if the environment is set up correctly"""
    print("🔧 ENVIRONMENT CHECK")
    print("=" * 40)
    
    checks = {
        'python_version': False,
        'scrapy_installed': False,
        'working_directory': False,
        'config_files': False,
        'spider_files': False
    }
    
    # Python version
    if sys.version_info >= (3, 7):
        print("✅ Python version:", sys.version.split()[0])
        checks['python_version'] = True
    else:
        print("❌ Python version too old:", sys.version.split()[0])
    
    # Scrapy installation
    try:
        import scrapy
        print("✅ Scrapy installed:", scrapy.__version__)
        checks['scrapy_installed'] = True
    except ImportError:
        print("❌ Scrapy not installed")
    
    # Working directory
    if os.path.exists('scrapy.cfg'):
        print("✅ Scrapy project detected")
        checks['working_directory'] = True
    else:
        print("❌ Not in Scrapy project directory")
    
    # Config files
    config_dir = Path('config')
    if config_dir.exists():
        config_files = list(config_dir.glob('*.yaml'))
        if config_files:
            print(f"✅ Config files found: {len(config_files)}")
            checks['config_files'] = True
        else:
            print("❌ No YAML config files found")
    else:
        print("❌ Config directory not found")
    
    # Spider files
    spider_dir = Path('scraper/spiders')
    if spider_dir.exists():
        spider_files = list(spider_dir.glob('*.py'))
        spider_files = [f for f in spider_files if not f.name.startswith('__')]
        if spider_files:
            print(f"✅ Spider files found: {len(spider_files)}")
            checks['spider_files'] = True
        else:
            print("❌ No spider files found")
    else:
        print("❌ Spider directory not found")
    
    return checks


def check_spider_configuration():
    """Check spider configuration files"""
    print("\\n⚙️  SPIDER CONFIGURATION CHECK")
    print("=" * 40)
    
    checks = {
        'config_valid': False,
        'xpaths_defined': False,
        'type_mapping': False
    }
    
    config_files = ['config/hk_store_fixed.yaml', 'config/hk_store.yaml', 'config/cn_store.yaml']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                print(f"✅ {config_file} loaded successfully")
                
                # Check for required sections
                if 'start_urls' in config:
                    print(f"  📍 Start URLs: {len(config['start_urls'])}")
                
                if 'field_xpaths' in config:
                    print(f"  🎯 XPath fields: {len(config['field_xpaths'])}")
                    checks['xpaths_defined'] = True
                
                checks['config_valid'] = True
                
            except Exception as e:
                print(f"❌ {config_file} error: {e}")
        else:
            print(f"⚠️  {config_file} not found")
    
    # Check type mapping
    type_mapping_file = 'config/type_mapping.yaml'
    if os.path.exists(type_mapping_file):
        try:
            with open(type_mapping_file, 'r', encoding='utf-8') as f:
                type_mapping = yaml.safe_load(f)
                print(f"✅ Type mapping loaded: {len(type_mapping)} mappings")
                checks['type_mapping'] = True
        except Exception as e:
            print(f"❌ Type mapping error: {e}")
    else:
        print("❌ Type mapping file not found")
    
    return checks


def check_spider_imports():
    """Check if spider can import all dependencies"""
    print("\\n📦 IMPORT CHECK")
    print("=" * 40)
    
    checks = {
        'spider_imports': False,
        'utils_imports': False,
        'config_loader': False
    }
    
    # Test spider imports
    try:
        sys.path.append('.')
        from scraper.spiders.store_spider import StoreSpider
        print("✅ Store spider imports successfully")
        checks['spider_imports'] = True
    except Exception as e:
        print(f"❌ Store spider import error: {e}")
    
    # Test utils imports
    try:
        from utils.config_loader import load_config
        print("✅ Utils imports successfully")
        checks['utils_imports'] = True
        checks['config_loader'] = True
    except Exception as e:
        print(f"❌ Utils import error: {e}")
    
    return checks


def check_website_connectivity():
    """Check if target websites are accessible"""
    print("\\n🌐 WEBSITE CONNECTIVITY CHECK")
    print("=" * 40)
    
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    # Setup session with retries
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    test_urls = [
        'https://www.centanet.com/icms/template/transaction-list.jsp?type=1',
        'https://www.midlandici.com.hk/property-transactions'
    ]
    
    checks = {'connectivity': False}
    
    for url in test_urls:
        try:
            response = session.head(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                print(f"✅ {url} - Status: {response.status_code}")
                checks['connectivity'] = True
            else:
                print(f"⚠️  {url} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {url} - Error: {e}")
    
    return checks


def run_quick_spider_test():
    """Run a quick test of the spider"""
    print("\\n🕷️  QUICK SPIDER TEST")
    print("=" * 40)
    
    import subprocess
    
    try:
        # Run spider with just 3 items
        cmd = [
            sys.executable, "-m", "scrapy", "crawl", "store_spider",
            "-s", "ITEM_PIPELINES={}",
            "-s", "CLOSESPIDER_ITEMCOUNT=3",
            "-L", "ERROR",  # Only show errors
            "-o", "health_check_test.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Check if data was scraped
            if os.path.exists('health_check_test.json'):
                with open('health_check_test.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if data and len(data) > 0:
                    print(f"✅ Spider test successful: {len(data)} items scraped")
                    print(f"  Sample: {data[0].get('building_name_zh', 'N/A')} - {data[0].get('type_raw', 'N/A')}")
                    return True
                else:
                    print("❌ Spider ran but no data scraped")
            else:
                print("❌ Spider ran but no output file created")
        else:
            print(f"❌ Spider failed with return code: {result.returncode}")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}...")
    
    except subprocess.TimeoutExpired:
        print("❌ Spider test timed out (>60 seconds)")
    except Exception as e:
        print(f"❌ Spider test error: {e}")
    
    return False


def main():
    """Run comprehensive health check"""
    print("🏥 SCRAPY HEALTH CHECK")
    print("=" * 60)
    
    all_checks = {}
    
    # Run all checks
    all_checks.update(check_environment())
    all_checks.update(check_spider_configuration())
    all_checks.update(check_spider_imports())
    all_checks.update(check_website_connectivity())
    
    # Quick spider test only if basic checks pass
    basic_checks = ['python_version', 'scrapy_installed', 'working_directory', 'spider_imports']
    if all(all_checks.get(check, False) for check in basic_checks):
        spider_test_passed = run_quick_spider_test()
        all_checks['spider_test'] = spider_test_passed
    else:
        print("\\n⚠️  Skipping spider test due to failed basic checks")
        all_checks['spider_test'] = False
    
    # Summary
    print("\\n📋 HEALTH CHECK SUMMARY")
    print("=" * 40)
    
    passed = sum(1 for v in all_checks.values() if v)
    total = len(all_checks)
    
    for check, status in all_checks.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {check.replace('_', ' ').title()}")
    
    print(f"\\n🎯 Overall Health: {passed}/{total} checks passed ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 All systems operational! Scrapy is ready to use.")
    elif passed >= total * 0.8:
        print("✅ System mostly healthy with minor issues.")
    elif passed >= total * 0.6:
        print("⚠️  System has some issues that need attention.")
    else:
        print("❌ System has major issues that must be fixed.")
    
    # Cleanup
    if os.path.exists('health_check_test.json'):
        os.remove('health_check_test.json')


if __name__ == "__main__":
    main()
