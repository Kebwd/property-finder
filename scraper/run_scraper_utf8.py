#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UTF-8 Safe Scraper Runner
This script sets the proper encoding environment before running the scraper
"""
import os
import sys
import locale

def setup_utf8_environment():
    """Set up UTF-8 environment for Windows"""
    # Set environment variables for UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # Set console code page to UTF-8 (Windows)
    if sys.platform.startswith('win'):
        try:
            import subprocess
            subprocess.run(['chcp', '65001'], shell=True, check=False, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    
    # Set locale
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except:
            pass

def main():
    """Run the daily scraper with UTF-8 setup"""
    setup_utf8_environment()
    
    # Import and run daily scraper
    from daily_scraper import main as run_daily_scraper
    return run_daily_scraper()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
