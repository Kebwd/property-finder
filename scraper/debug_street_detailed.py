#!/usr/bin/env python3
"""
Debug script to check what street data is being extracted from individual items
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html

def debug_street_extraction():
    # Load configuration
    with open('config/cn_house.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    site_config = config['config'][0]
    
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
        rows_xpath = site_config['xpaths']['rows'][0]
        items = tree.xpath(rows_xpath)
        
        print(f"Found {len(items)} property items")
        print("="*60)
        
        # Test street extraction on first 3 items
        street_xpaths = site_config['xpaths']['street']
        
        for i, item in enumerate(items[:3]):
            print(f"Item {i+1}:")
            
            # Get building name for reference
            building_name_xpaths = site_config['xpaths']['building_name_zh']
            building_name = None
            for xpath in building_name_xpaths:
                try:
                    result = item.xpath(xpath)
                    if result:
                        building_name = result[0].strip()
                        break
                except:
                    continue
            
            print(f"  Building: {building_name}")
            
            # Test each street XPath
            for j, street_xpath in enumerate(street_xpaths):
                try:
                    street_results = item.xpath(street_xpath)
                    print(f"  Street XPath {j+1}: {street_xpath}")
                    print(f"  Results: {street_results}")
                    if street_results:
                        print(f"  ✅ Street found: {street_results[0].strip()}")
                    else:
                        print(f"  ❌ No street data")
                except Exception as e:
                    print(f"  ❌ XPath error: {e}")
            
            # Check all links in this item
            all_links = item.xpath(".//a[contains(@href,'/chengjiao/')]")
            print(f"  All chengjiao links in this item:")
            for link in all_links:
                href = link.get('href', '')
                text = ''.join(link.itertext()).strip()
                print(f"    href='{href}', text='{text}'")
            
            print("-" * 40)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_street_extraction()
