import re
import yaml

def parse_price(price_str):
    # Converts "$12K" or "¥1.2万" to integer
    price_str = price_str.replace(',', '').replace('¥', '').replace('$', '')
    match = re.search(r'(\d+(\.\d+)?)(万|K)?', price_str)
    if match:
        value = float(match.group(1))
        unit = match.group(3)
        if unit == '万':
            return int(value * 10000)
        elif unit == 'K':
            return int(value * 1000)
        else:
            return int(value)
    return None

def load_type_mapping(path="config/type_mapping.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
    
def normalize_region(region_str):
    region_map = {
        'HK': 'Hong Kong',
        '香港': 'Hong Kong',
        'CN': 'China',
        '中国': 'China'
    }
    return region_map.get(region_str.strip(), region_str.strip())

def format_date(date_str):
    # Converts "2025年7月28日" or "28/07/2025" to "2025-07-28"
    date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
    match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
    if match:
        year, month, day = match.groups()
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    return date_str
