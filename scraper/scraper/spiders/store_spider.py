# store_scraper/spiders/store_spider.py
import os
import scrapy
from scrapy.spiders import CrawlSpider
from scrapy import signals
from scrapy.signalmanager import dispatcher
from datetime import datetime, timedelta
import yaml
from pathlib import Path
import sys
import re
import urllib.parse
import json
sys.path.append(str(Path(__file__).parents[2]))
from utils.config_loader import load_config



def split_address_info(text):
    """
    Split combined address info like '大鴻輝(荃灣)中心 商場' or '昌明大廈 地舖'
    Returns (building_name, floor, unit)
    """
    if not text:
        return "", "", ""
    
    text = text.strip()
    
    # Common Hong Kong floor patterns
    floor_patterns = [
        r'(地下|地舖|閣樓|天台|頂層)',  # Special floors
        r'(低層|中層|高層|上層)',      # General floor ranges  
        r'(商場|商舖|寫字樓|工商)',    # Property types that act as floor info
        r'(\d+樓|\d+層)',            # Specific floors like 15樓, 3層
        r'([A-Z]/F|G/F|U[A-Z]/F)',   # Floor abbreviations like LG/F, G/F, UG/F
    ]
    
    # Common unit patterns
    unit_patterns = [
        r'(\d+室)',                  # 1室, 2室
        r'(\d+號)',                  # 1號, 2號  
        r'(\d+[A-Z]室?)',           # 1A室, 2B
        r'([A-Z]\d*室?)',           # A室, B1室
        r'(\d+[A-Z]-\d+[A-Z])',     # 1A-2B (unit ranges)
    ]
    
    floor = ""
    unit = ""
    building_name = text
    
    # Extract floor information
    for pattern in floor_patterns:
        match = re.search(pattern, text)
        if match:
            floor = match.group(1)
            building_name = building_name.replace(floor, "")
            break
    
    # Extract unit information  
    for pattern in unit_patterns:
        match = re.search(pattern, text)
        if match:
            unit = match.group(1)
            building_name = building_name.replace(unit, "")
            break
    
    # Clean building name (remove extra whitespace)
    building_name = re.sub(r'\s+', ' ', building_name).strip()
    
    return building_name, floor, unit


def extract_first(response, xpaths, default=None):
    """
    Try each xp in the list (or single string), skip invalid or empty expressions,
    and return the first non-empty result.
    """
    # normalize to list
    if isinstance(xpaths, str):
        xps = [xpaths]
    else:
        xps = xpaths or []

    for xp in xps:
        if not xp or not isinstance(xp, str):
            # completely empty or non-string—skip
            continue
        xp = xp.strip()
        # quick sanity check: valid XPaths usually start with '/' or '.'
        if not (xp.startswith("/") or xp.startswith(".")):
            # you can log or print here to see what's wrong
            print(f"⚠️  skipping invalid xpath fragment: {xp!r}")
            continue
        try:
            val = response.xpath(xp).get()
        except Exception as e:
            # malformed XPath—skip it, but let me know
            print(f"⚠️  malformed xpath {xp!r}, skipping: {e}")
            continue
        if val:
            return val.strip()
    return default


def generate_fields(record, config_fields, response=None, xpath_map=None):
    fields = {}
    for std_field, source in config_fields.items():
        # allow either a single key or a list of keys
        keys = source if isinstance(source, list) else [source]

        # 1) Try JSON keys in order
        value = None
        for key in keys:
            if key and record.get(key) not in (None, "", []):
                value = record.get(key)
                break

        # 2) Fallback to HTML if JSON lookup failed
        if value not in (None, ""):
            fields[std_field] = value
        elif response and xpath_map and std_field in xpath_map:
            fields[std_field] = extract_first(response, xpath_map[std_field])
        else:
            fields[std_field] = None

    return fields


def classify_type(record, item_type, mapping):
    raw_type = record.get("tx_type") or record.get("property_type")
    if item_type == "store":
        return mapping["store_types"].get(raw_type, raw_type)
    elif item_type == "house":
        return mapping["house_types"].get(raw_type, raw_type)
    return raw_type


class StoreSpider(CrawlSpider):
    name = "store_spider"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize tracking for newly posted deals
        self.today_date = datetime.now().strftime("%d/%m/%Y")  # DD/MM/YYYY format
        self.monitoring_mode = kwargs.get('mode', 'daily')  # 'daily' or 'weekly'
        
        if self.monitoring_mode == 'daily':
            self.logger.info(f"🗓️  Daily mode: Checking for newly posted deals")
        elif self.monitoring_mode == 'weekly':
            self.logger.info(f"📅 Weekly mode: Checking last 14 days for new additions")
        
        # Load previous results for change detection
        self.previous_deals = self.load_previous_deals()
        self.current_deals = set()

        # load your site configs using absolute paths
        config_dir = Path(__file__).parents[2] / "config"
        self.configs  = load_config(str(config_dir / "hk_store.yaml"))
        self.configs += load_config(str(config_dir / "cn_store.yaml"))

        # load type mappings
        tm_path = config_dir / "type_mapping.yaml"
        with open(tm_path, encoding="utf-8") as f:
            self.type_mapping = yaml.safe_load(f)

        # connect summary writer
        dispatcher.connect(self.spider_closed, signals.spider_closed)

        # counters
        self.item_count  = 0
        self.error_count = 0
        self.new_deals_count = 0

    def load_previous_deals(self):
        """Load previously seen deals for change detection"""
        try:
            tracking_file = Path("deal_tracking.json")
            if tracking_file.exists():
                with open(tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert to set of deal IDs
                    previous_ids = set()
                    for period_data in data.values():
                        for deal_id, _ in period_data:
                            previous_ids.add(deal_id)
                    self.logger.info(f"📋 Loaded {len(previous_ids)} previously seen deals")
                    return previous_ids
        except Exception as e:
            self.logger.warning(f"⚠️  Could not load previous deals: {e}")
        return set()

    def save_current_deals(self):
        """Save current deals for next run comparison"""
        try:
            tracking_file = Path("deal_tracking.json")
            current_data = {
                'last_run': datetime.now().isoformat(),
                'current_deals': list(self.current_deals)
            }
            with open(tracking_file, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"💾 Saved {len(self.current_deals)} current deals for next comparison")
        except Exception as e:
            self.logger.warning(f"⚠️  Could not save current deals: {e}")

    def create_deal_id(self, item):
        """Create unique identifier for a deal"""
        building = item.get('building_name_zh') or ''
        building = building.strip() if building else ''
        
        floor = item.get('floor') or ''
        floor = floor.strip() if floor else ''
        
        unit = item.get('unit') or ''
        unit = unit.strip() if unit else ''
        
        price = item.get('deal_price') or ''
        price = price.strip() if price else ''
        
        date = item.get('deal_date') or ''
        date = date.strip() if date else ''
        
        # Create unique ID combining key fields
        return f"{building}_{floor}_{unit}_{price}_{date}"

    def is_new_deal(self, deal_id):
        """Check if this is a newly posted deal"""
        return deal_id not in self.previous_deals

    def generate_today_url(self, base_url):
        """Generate URL with today's date filter"""
        today = datetime.now()
        date_str = today.strftime("%d%%2F%m%%2F%Y")  # URL encoded DD/MM/YYYY
        
        if "centanet.com" in base_url:
            # For Centanet: update daterang parameter
            if "daterang=" in base_url:
                # Replace existing date range with today-today
                pattern = r'daterang=[^&]*'
                new_date_param = f"daterang={date_str}-{date_str}"
                updated_url = re.sub(pattern, new_date_param, base_url)
                return updated_url
            else:
                # Add date parameter if not present
                separator = "&" if "?" in base_url else "?"
                return f"{base_url}{separator}daterang={date_str}-{date_str}"
        
        # For other sites, try to add date filter
        elif "midlandici.com" in base_url:
            # Add date parameter for Midland
            separator = "&" if "?" in base_url else "?"
            return f"{base_url}{separator}date={date_str}"
        
        return base_url

    def is_today_deal(self, deal_date_text):
        """Check if the deal date matches today"""
        if not deal_date_text:
            return False
            
        # Clean the date text
        deal_date_text = deal_date_text.strip()
        
        # Handle JSON format: "2025-08-11 00:00:00"
        if ' ' in deal_date_text and ':' in deal_date_text:
            date_part = deal_date_text.split(' ')[0]  # Get "2025-08-11"
            # Convert to DD/MM/YYYY format for comparison
            try:
                y, m, d = date_part.split('-')
                formatted_date = f"{int(d):02d}/{int(m):02d}/{y}"
                return formatted_date == self.today_date
            except:
                return False
        
        # Handle HTML format: "DD/MM/YYYY" - direct comparison
        return deal_date_text == self.today_date

    def has_too_many_null_columns(self, item):
        """
        Check if item has more than 1 null/empty columns in critical fields.
        Returns True if item should be filtered out.
        Note: floor and unit are allowed to be empty.
        """
        # Define critical fields to check (floor and unit are allowed to be empty)
        important_fields = [
            'building_name_zh', 'area', 'deal_date', 'deal_price'
        ]
        
        null_count = 0
        for field in important_fields:
            value = item.get(field)
            # Consider None, empty string, '--', or whitespace-only as null
            if not value or str(value).strip() in ['', '--', 'None', 'null']:
                null_count += 1
        
        self.logger.debug(f"📊 Data quality check: {null_count}/{len(important_fields)} null columns in {item.get('building_name_zh', 'N/A')}")
        
        # Return True if more than 1 column is null (item should be filtered out)
        return null_count > 1

    def start_requests(self):
        for cfg in self.configs:
            json_tmpl = cfg.get("json_url_template")
            if json_tmpl:
                url = json_tmpl.format(cursor=0)
                yield scrapy.Request(
                    url,
                    callback=self.parse_json,
                    headers={"Accept": "application/json"},
                    meta={"config": cfg, "cursor": 0}
                )
            else:
                for base_url in cfg["start_urls"]:
                    # Generate URL based on monitoring mode
                    if self.monitoring_mode == 'weekly':
                        # Check last 14 days for newly posted deals
                        monitoring_url = self.generate_weekly_url(base_url)
                        self.logger.info(f"� Weekly check: {monitoring_url}")
                    else:
                        # Daily mode: check broader range but filter new deals
                        monitoring_url = self.generate_monitoring_url(base_url)
                        self.logger.info(f"📍 Daily monitoring: {monitoring_url}")
                    
                    yield scrapy.Request(
                        monitoring_url,
                        callback=self.parse_listing_page,
                        meta={"config": cfg},
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                    )

    def generate_weekly_url(self, base_url):
        """Generate URL to check last 14 days for new additions"""
        today = datetime.now()
        start_date = today - timedelta(days=14)
        
        start_str = start_date.strftime("%d%%2F%m%%2F%Y")
        end_str = today.strftime("%d%%2F%m%%2F%Y")
        
        if "centanet.com" in base_url:
            if "daterang=" in base_url:
                pattern = r'daterang=[^&]*'
                new_date_param = f"daterang={start_str}-{end_str}"
                return re.sub(pattern, new_date_param, base_url)
            else:
                separator = "&" if "?" in base_url else "?"
                return f"{base_url}{separator}daterang={start_str}-{end_str}"
        
        return base_url

    def generate_monitoring_url(self, base_url):
        """Generate URL for daily monitoring (last 7 days to catch recent additions)"""
        today = datetime.now()
        start_date = today - timedelta(days=7)  # Check last week for new additions
        
        start_str = start_date.strftime("%d%%2F%m%%2F%Y")
        end_str = today.strftime("%d%%2F%m%%2F%Y")
        
        if "centanet.com" in base_url:
            if "daterang=" in base_url:
                pattern = r'daterang=[^&]*'
                new_date_param = f"daterang={start_str}-{end_str}"
                return re.sub(pattern, new_date_param, base_url)
            else:
                separator = "&" if "?" in base_url else "?"
                return f"{base_url}{separator}daterang={start_str}-{end_str}"
        
        return base_url

    def parse_listing_page(self, response):
        cfg      = response.meta["config"]
        # log out the raw xpaths you’ll try
        self.logger.debug(f"Trying xpaths for 'type': {cfg['xpaths'].get('type')}")
        raw_type = extract_first(response, cfg["xpaths"]["type"], default="").strip()

        rows = response.xpath(cfg["xpaths"].get("rows", ["//tbody/tr"])[0])
        if not rows:
            self.logger.warning("⚠️ zero rows in %s", response.url)
            return

        self.logger.info(f"📊 Found {len(rows)} rows using xpath: {cfg['xpaths'].get('rows', ['//tbody/tr'])[0]}")

        for row_index, row in enumerate(rows):
            # Extract type from each row individually
            raw_type = extract_first(row, cfg["xpaths"].get("type", []), default="").strip()
            normalized = classify_type({"tx_type": raw_type}, cfg["type"], self.type_mapping)
            
            item = {"zone": cfg["zone"], "type_raw": raw_type, "type": normalized}

            for field, key in cfg["fields"].items():
                if key == "type":
                    # For carpark type, use static assignment
                    if cfg.get("type") == "carpark":
                        item[field] = "carpark"
                    else:
                        item[field] = normalized
                    continue

                xp = cfg["xpaths"].get(key)
                if not xp:
                    item[field] = None
                else:
                    extracted_value = extract_first(row, xp)
                    item[field] = extracted_value

            # Handle combined address fields (building name + floor + unit in one field)
            # Check if we have a combined address situation
            building_name_raw = item.get('building_name_zh', '')
            if building_name_raw and any(keyword in building_name_raw for keyword in ['地舖', '商場', '中層', '低層', '高層', '樓', '層']):
                # Split the combined address
                building_name, floor_info, unit_info = split_address_info(building_name_raw)
                
                # Update the item with split information
                item['building_name_zh'] = building_name if building_name else building_name_raw
                
                # Only override floor/unit if they're currently empty and we found something
                if not item.get('floor') and floor_info:
                    item['floor'] = floor_info
                if not item.get('unit') and unit_info:
                    item['unit'] = unit_info
                    
                self.logger.debug(f"🔀 Split address: '{building_name_raw}' → Building: '{building_name}', Floor: '{floor_info}', Unit: '{unit_info}'")

            # Handle carpark-specific data processing
            if cfg.get("type") == "carpark":
                # Process combined floor/unit (e.g., "2/P16" → floor="2", unit="P16")
                floor_unit_combined = item.get('floor_unit_combined', '')
                if floor_unit_combined and '/' in floor_unit_combined:
                    parts = floor_unit_combined.split('/', 1)
                    item['floor'] = parts[0].strip()
                    item['unit'] = parts[1].strip()
                    self.logger.debug(f"🚗 Split carpark floor/unit: '{floor_unit_combined}' → Floor: '{parts[0].strip()}', Unit: '{parts[1].strip()}'")
                
                # Convert price from millions to actual amount (e.g., "0.970" → "970000")
                price_millions = item.get('deal_price_millions', '')
                if price_millions:
                    try:
                        price_float = float(price_millions)
                        actual_price = int(price_float * 1000000)  # Convert millions to actual amount
                        item['deal_price'] = str(actual_price)
                        self.logger.debug(f"💰 Converted carpark price: '{price_millions}' million → {actual_price}")
                    except (ValueError, TypeError):
                        self.logger.warning(f"⚠️ Failed to convert carpark price: '{price_millions}'")
                        item['deal_price'] = price_millions  # Keep original if conversion fails

            # Create unique deal ID for change detection
            deal_id = self.create_deal_id(item)
            self.current_deals.add(deal_id)
            
            # Check if this deal is from today (only in daily mode)
            if self.monitoring_mode == 'daily':
                deal_date = item.get('deal_date', '')
                if not self.is_today_deal(deal_date):
                    self.logger.info(f"🛑 STOPPING: Found deal from {deal_date} (not today), stopping crawl")
                    return  # Stop processing when we hit a non-today deal
            
            # Check if this is a newly posted deal
            if self.is_new_deal(deal_id):
                # Validate data quality - filter out items with more than 2 null columns
                if self.has_too_many_null_columns(item):
                    self.logger.warning(f"🚫 REJECTED: Too many null columns in deal: {item.get('building_name_zh', 'N/A')} - {raw_type}")
                    continue
                
                self.logger.info(f"🆕 NEW DEAL: {item.get('building_name_zh', 'N/A')} - {raw_type} - {item.get('deal_price', 'N/A')}")
                self.new_deals_count += 1
                self.item_count += 1
                yield item
            else:
                self.logger.debug(f"⏭️  Known deal: {item.get('building_name_zh', 'N/A')} - {raw_type}")

    def parse_json(self, response):
        cfg    = response.meta["config"]
        cursor = response.meta["cursor"]
        data   = response.json()
        txs    = data.get("transactions", [])

        for rec in txs:
            # Check if deal is from today
            deal_date = rec.get("tx_date", "")  # Use tx_date field from JSON
            if not self.is_today_deal(deal_date):
                self.logger.debug(f"⏭️  Skipping JSON deal from {deal_date} (not today)")
                continue
                
            item = generate_fields(rec, cfg["fields"])
            item["zone"]     = cfg["zone"]
            item["type_raw"] = rec.get("tx_type")
            item["type"]     = classify_type(rec, cfg["type"], self.type_mapping)
            
            # Validate data quality - filter out items with more than 2 null columns
            if self.has_too_many_null_columns(item):
                self.logger.warning(f"🚫 REJECTED JSON: Too many null columns in deal: {item.get('building_name_zh', 'N/A')}")
                continue
            
            self.logger.info(f"✅ Found today's JSON deal: {item.get('building_name_zh', 'N/A')}")
            self.item_count += 1
            yield item

        total = data.get("count", 0)
        next_cursor = cursor + len(txs)
        if next_cursor < total:
            next_url = cfg["json_url_template"].format(cursor=next_cursor)
            yield scrapy.Request(
                next_url,
                callback=self.parse_json,
                headers=response.request.headers,
                meta={"config": cfg, "cursor": next_cursor}
            )

    def spider_closed(self, spider):
        # Save current deals for next comparison
        self.save_current_deals()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        mode_info = f"Mode: {self.monitoring_mode}"
        summary = f"[{timestamp}] {self.name}: {self.new_deals_count} new deals, {self.item_count} total items, {self.error_count} errors ({mode_info})\n"
        
        os.makedirs("logs", exist_ok=True)
        with open("logs/summary.txt", "a", encoding="utf-8") as f:
            f.write(summary)
        
        # Log summary
        self.logger.info(f"🎯 SPIDER SUMMARY:")
        self.logger.info(f"   🆕 New deals found: {self.new_deals_count}")
        self.logger.info(f"   📊 Total deals checked: {len(self.current_deals)}")
        self.logger.info(f"   📋 Previously known deals: {len(self.previous_deals)}")
        self.logger.info(f"   🔄 Monitoring mode: {self.monitoring_mode}")
