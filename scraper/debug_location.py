from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)
driver.get('https://sz.centanet.com/chengjiao/')
time.sleep(3)

html = driver.page_source
selector = Selector(text=html)

# Find all estate items
estate_items = selector.xpath('//div[contains(@class,"estate-item")]')
print(f'Found {len(estate_items)} estate items')

if estate_items:
    first_item = estate_items[0]
    print('\n--- Location information ---')
    
    # Try to find location links with dashes
    location_links = first_item.xpath('.//p[contains(@class,"house-txt")]//a//text()')
    print(f'Location links: {location_links}')
    
    # Look for all text containing dashes
    dash_texts = first_item.xpath('.//text()[contains(.,"-")]')
    print(f'Texts with dashes: {dash_texts}')
    
    # Look at the house-txt section specifically
    house_txt = first_item.xpath('.//p[contains(@class,"house-txt")]')
    if house_txt:
        print(f'House txt section: {house_txt[0].get()}')
        
    # Look for all links in the item
    all_links = first_item.xpath('.//a')
    for i, link in enumerate(all_links):
        href = link.xpath('@href').get()
        text = link.xpath('.//text()').getall()
        print(f'Link {i}: href={href}, text={text}')

driver.quit()
