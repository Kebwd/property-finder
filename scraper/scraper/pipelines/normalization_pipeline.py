import re
from config.key_library import config_map
from utils.config_loader import load_mapping_config
from scrapy.exceptions import DropItem
from datetime import datetime, date

def normalize_date(raw):
    # Handle multiple date formats
    if not raw:
        return None
        
    try:
        # Handle "2025-08-11 00:00:00" format (from JSON)
        if ' ' in str(raw) and ':' in str(raw):
            date_part = str(raw).split(' ')[0]  # Get just the date part
            return date_part  # Already in YYYY-MM-DD format
            
        # Handle "15/7/2025" format (DD/MM/YYYY from Hong Kong sites)
        if '/' in str(raw):
            parts = str(raw).split('/')
            if len(parts) == 3:
                # Check if it's YYYY/MM/DD format (from Chinese sites)
                if len(parts[0]) == 4:  # Year first
                    y, m, d = parts
                    result = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
                    return result
                # Otherwise DD/MM/YYYY format (Hong Kong sites)
                else:
                    d, m, y = parts
                    result = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
                    return result
            
        # If already in YYYY-MM-DD format
        if '-' in str(raw) and len(str(raw)) == 10:
            return str(raw)
            
        return None
        
    except Exception as e:
        return None

def normalize_area(raw):
    # Handle area strings like "約2,110呎" -> extract numeric value
    if not raw:
        return None
    
    # Clean the input - remove "約", "呎", commas
    s = str(raw).replace('約', '').replace('呎', '').replace(',', '').strip()
    
    # Extract numeric value
    match = re.match(r"(\d+(?:\.\d+)?)", s)
    if not match:
        return None
        
    return float(match.group(1))

def normalize_price(raw):
    # strip commas, handle 萬/億, remove prefixes like "售$"
    if not raw:
        return None
    
    # Clean the input - remove commas, "售", "$", "@" prefixes
    s = str(raw).replace(',', '').replace('售', '').replace('$', '').replace('@', '').strip()
    
    # Match number followed by optional unit
    match = re.match(r"(\d+(?:\.\d+)?)(萬|億|万|K)?", s)
    if not match:
        return None
        
    num, unit = match.groups()
    base = float(num)
    
    if unit == '萬': 
        return base * 10000
    if unit == '億': 
        return base * 100000000
    if unit == '万':
        return base * 10000
    if unit == 'K':
        return base * 1000
        
    return base

def normalize_type(raw_type, config):
    # Skip complex type mapping for now - this is handled in the spider
    return raw_type

class NormalizationPipeline:
    def process_item(self, item, spider):
        if 'deal_date' in item:
            item['deal_date'] = normalize_date(item['deal_date'])
            if not item['deal_date']:
                raise DropItem(f"Invalid deal_date: {item['deal_date']}")

        # Note: Date filtering is now handled by the spider's change detection system
        # today = date.today().strftime("%Y-%m-%d") #Only get today's transactions    
        # if item['deal_date'] == today:
        #     pass
        # else:
        #     raise DropItem(f"Item is not from today: {item['deal_date']}")

        # Normalize area field
        if 'area' in item:
            item['area'] = normalize_area(item.get('area', ''))
            # Don't drop items with invalid area - just set to None
            if item['area'] is None:
                item['area'] = None
        
        if 'deal_price' in item:
            item['deal_price'] = normalize_price(item.get('deal_price', ''))
            if item['deal_price'] is None:
                raise DropItem(f"Invalid deal_price: {item.get('deal_price', '')}")
            
        # Legacy support for 'price' field
        if 'price' in item:
            item['deal_price'] = normalize_price(item.get('price', 0))
            if item['deal_price'] is None:
                raise DropItem(f"Invalid deal_price: {item['price']}")
            
        if 'type' in item:
            item['type'] = normalize_type(item['type'], config_map)
            if not item['type']:
                raise DropItem(f"Invalid type: {item['type']}")
            
        # Trim whitespace from strings
        for key, value in item.items():
            if isinstance(value, str):
                item[key] = value.strip()

        # Convert empty strings to None
        for key, value in item.items():
            if value == '':
                item[key] = None

        return item
