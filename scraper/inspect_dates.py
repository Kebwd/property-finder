#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

print('🗓️ Inspecting Chinese property website date elements...')

# Set up headless browser
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

try:
    # Visit the website
    url = 'https://sz.centanet.com/chengjiao/'
    print(f'📡 Loading: {url}')
    driver.get(url)
    time.sleep(3)  # Wait for page to load
    
    # Get the first few property listings
    print('')
    print('🔍 Analyzing date elements in property listings...')
    
    property_items = driver.find_elements(By.CSS_SELECTOR, 'div.estate-item')
    print(f'Found {len(property_items)} property items')
    
    for i, item in enumerate(property_items[:3]):
        print(f'\n--- Property {i+1} ---')
        # Get all text content and look for dates
        text_content = item.text
        print(f'Full text: {text_content[:200]}...')
        
        # Look for elements that might contain dates
        date_elements = [
            item.find_elements(By.CSS_SELECTOR, '*[class*="date"]'),
            item.find_elements(By.CSS_SELECTOR, '*[class*="time"]'),
            item.find_elements(By.CSS_SELECTOR, 'span'),
            item.find_elements(By.CSS_SELECTOR, 'div')
        ]
        
        for element_list in date_elements:
            for elem in element_list:
                elem_text = elem.text.strip()
                if elem_text and any(char in elem_text for char in ['202', '/', '-', '月', '日']):
                    elem_class = elem.get_attribute('class')
                    print(f'  Potential date element: class="{elem_class}" text="{elem_text}"')
                    
finally:
    driver.quit()
    print('')
    print('✅ Date element analysis complete!')
