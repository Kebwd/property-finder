import requests
from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Create driver
driver = webdriver.Chrome(options=chrome_options)
driver.get('https://sz.centanet.com/chengjiao/')
time.sleep(3)

# Get the page source
html = driver.page_source
selector = Selector(text=html)

# Find all estate items
estate_items = selector.xpath('//div[contains(@class,"estate-item")]')
print(f'Found {len(estate_items)} estate items')

if estate_items:
    # Get first item for analysis
    first_item = estate_items[0]
    print('\n--- First Item HTML ---')
    print(first_item.get())
    
    # Look for date elements
    print('\n--- Date element search ---')
    date_spans = first_item.xpath('.//span[contains(@class, "time")]')
    print(f'Found {len(date_spans)} time spans')
    
    for i, span in enumerate(date_spans):
        print(f'Time span {i}: {span.get()}')
        print(f'Text: {span.xpath(".//text()").getall()}')
    
    # Search for all spans with text
    all_spans = first_item.xpath('.//span')
    print(f'\nFound {len(all_spans)} total spans')
    
    for i, span in enumerate(all_spans[:10]):  # First 10 spans
        text = span.xpath('.//text()').getall()
        classes = span.xpath('@class').get()
        print(f'Span {i}: class="{classes}" text={text}')

driver.quit()
