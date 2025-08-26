#!/usr/bin/env python3
"""
Dependency checker for the scraper project
Verifies all required dependencies are installed and importable
"""

import sys
import importlib
import subprocess

def check_dependency(module_name, import_path=None, version_cmd=None):
    """Check if a dependency is available and importable"""
    try:
        if import_path:
            module = importlib.import_module(import_path)
        else:
            module = importlib.import_module(module_name)
        
        version = "unknown"
        if hasattr(module, '__version__'):
            version = module.__version__
        elif version_cmd:
            try:
                result = subprocess.run(version_cmd, capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    version = result.stdout.strip()
            except:
                pass
        
        print(f"✅ {module_name}: {version}")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: NOT FOUND - {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name}: ERROR - {e}")
        return False

def main():
    """Check all required dependencies"""
    print("🔍 Checking scraper dependencies...")
    print("=" * 50)
    
    dependencies = [
        ("scrapy", "scrapy"),
        ("scrapy-selenium", "scrapy_selenium"),
        ("beautifulsoup4", "bs4"),
        ("lxml", "lxml"),
        ("requests", "requests"),
        ("psycopg2-binary", "psycopg2"),
        ("selenium", "selenium"),
        ("PyYAML", "yaml"),
        ("python-dotenv", "dotenv"),
        ("aiohttp", "aiohttp"),
    ]
    
    all_good = True
    for package, import_name in dependencies:
        if not check_dependency(package, import_name):
            all_good = False
    
    print("=" * 50)
    
    if all_good:
        print("✅ All dependencies are available!")
        
        # Test scrapy spider loading
        print("\n🕷️  Testing scrapy spider loading...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "scrapy", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                spiders = result.stdout.strip().split('\n')
                print(f"✅ Found {len(spiders)} spiders:")
                for spider in spiders:
                    if spider.strip():
                        print(f"   - {spider.strip()}")
            else:
                print(f"❌ Scrapy spider loading failed: {result.stderr}")
                all_good = False
        except Exception as e:
            print(f"❌ Error testing scrapy: {e}")
            all_good = False
    
    if all_good:
        print("\n🎉 All checks passed! Scraper is ready to run.")
        return 0
    else:
        print("\n💥 Some dependencies are missing. Please install them:")
        print("   pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
