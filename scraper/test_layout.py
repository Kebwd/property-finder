#!/usr/bin/env python3

import requests
from scrapy import Selector

url = 'https://oir.centanet.com/transaction/search/?posttype=S&usagenames=Office,Industrial,Retail&daterang=06%2F08%2F2025-20%2F08%2F2025'
headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'}

response = requests.get(url, headers=headers)
selector = Selector(text=response.text)

# Test different row selectors
tbody_rows = selector.xpath('//tbody/tr').getall()
mobile_rows = selector.xpath('//div[@class="m-transaction-list-item"]').getall()

print('Table rows found:', len(tbody_rows))
print('Mobile rows found:', len(mobile_rows))

# Check for building names
if tbody_rows:
    building_names = selector.xpath('//tbody/tr[1]//td[4]//a//text()').get()
    print('Building name (table):', building_names)
    # Try all table building name possibilities
    alt_building = selector.xpath('//tbody/tr[1]//td[4]//text()').get()
    print('Building name alt (table):', alt_building)

if mobile_rows:
    mobile_building = selector.xpath('//div[@class="m-transaction-list-item"][1]//div[@class="property-name"]//text()').get()
    print('Building name (mobile):', mobile_building)

# Let's also check the actual table structure for building names
if tbody_rows:
    first_row = selector.xpath('//tbody/tr[1]').get()
    print('\nFirst row HTML:', first_row[:200] + '...')
    
    # Check all td elements in first row
    tds = selector.xpath('//tbody/tr[1]/td')
    for i, td in enumerate(tds):
        text = td.xpath('.//text()').get()
        print(f'TD {i+1}: {text}')
    
    # Check second and third rows too
    print('\n--- Second row ---')
    tds2 = selector.xpath('//tbody/tr[2]/td')
    for i, td in enumerate(tds2):
        text = td.xpath('.//text()').get()
        print(f'TD {i+1}: {text}')
    
    print('\n--- Third row ---')
    tds3 = selector.xpath('//tbody/tr[3]/td')
    for i, td in enumerate(tds3):
        text = td.xpath('.//text()').get()
        print(f'TD {i+1}: {text}')
