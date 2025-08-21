#!/usr/bin/env python3
"""
Debug URL extraction from the website
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html

def debug_url_extraction():
    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        url = "https://sz.centanet.com/chengjiao/"
        print(f"Loading {url}...")
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "estate-item"))
        )
        
        # Get page source and parse with lxml
        page_source = driver.page_source
        tree = html.fromstring(page_source)
        
        # Get property items
        items = tree.xpath("//div[contains(@class,'estate-item')]")
        
        print(f"Found {len(items)} property items")
        print("="*80)
        
        # Test URL extraction on first 3 items
        url_xpaths = [
            ".//div[contains(@class,'item-info')]//h3//a/@href",
            ".//h3//a/@href", 
            ".//a[contains(@href,'/ershoufang/')]/@href",
            ".//a/@href"  # General link search
        ]
        
        for i, item in enumerate(items[:3]):
            print(f"Item {i+1}:")
            
            # Get building name for reference
            building_name = None
            building_xpaths = [".//div[contains(@class,'item-info')]//h3//text()", ".//h3//text()"]
            for xpath in building_xpaths:
                try:
                    result = item.xpath(xpath)
                    if result:
                        building_name = result[0].strip()
                        break
                except:
                    continue
            
            print(f"  Building: {building_name}")
            
            # Test each URL XPath
            for j, url_xpath in enumerate(url_xpaths):
                try:
                    url_results = item.xpath(url_xpath)
                    print(f"  URL XPath {j+1}: {url_xpath}")
                    print(f"  Results: {url_results}")
                    if url_results:
                        print(f"  ✅ URL found: {url_results[0]}")
                    else:
                        print(f"  ❌ No URL data")
                except Exception as e:
                    print(f"  ❌ XPath error: {e}")
            
            # Check all links in this item
            all_links = item.xpath(".//a")
            print(f"  All links in this item:")
            for link in all_links:
                href = link.get('href', '')
                text = ''.join(link.itertext()).strip()
                print(f"    href='{href}', text='{text}'")
            
            print("-" * 50)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_url_extraction()
