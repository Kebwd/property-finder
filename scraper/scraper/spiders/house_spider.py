# house_spider.py - Enhanced with store spider improvements
import os
import scrapy
import logging
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy import signals
from scrapy.signalmanager import dispatcher
from datetime import datetime
import yaml
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parents[2]))
from utils.config_loader import load_config


def extract_first(response, xpaths, default=None, debug_field=None):
    if debug_field == "deal_date":
        logging.info(f"🔍 DEBUG - Extracting {debug_field} with XPaths: {xpaths}")
    
    for i, xp in enumerate(xpaths):
        val = response.xpath(xp).get()
        if debug_field == "deal_date":
            logging.info(f"🔍 DEBUG - XPath {i}: '{xp}' -> '{val}'")
        if val:
            return val.strip()
    
    if debug_field == "deal_date":
        logging.info(f"🔍 DEBUG - No value found for {debug_field}, returning default: {default}")
    return default

def generate_fields(record, config_fields, response=None, xpath_map=None):
    fields = {}
    for std_field, source_key in config_fields.items():
        # Try JSON first
        value = record.get(source_key)
        if value:
            fields[std_field] = value
        else:
            # Fallback to XPath
            if response and xpath_map and std_field in xpath_map:
                fields[std_field] = extract_first(response, xpath_map[std_field], debug_field=std_field if std_field == "deal_date" else None)
            else:
                fields[std_field] = None
    return fields

def load_type_mapping(path="type_mapping.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def classify_type(record, item_type, mapping):
    raw_type = record.get("property_type")
    if item_type == "store":
        return mapping["store_types"].get(raw_type)
    elif item_type == "house":
        return mapping["house_types"].get(raw_type)
    return None


class HouseSpider(CrawlSpider):
    name = "house_spider"

    def __init__(self, mode="daily", *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Mode can be 'daily' or 'weekly'
        self.mode = mode
        self.logger.info(f"🏠 House spider initialized in {mode} mode")

        # 1. Load all config blocks (list of dicts)
        self.configs = []
        self.configs += load_config("config/hk_house.yaml")
        self.configs += load_config("config/cn_house.yaml")

        # 2. Load your type mappings from YAML
        tm_path = Path(__file__).parents[2] / "config" / "type_mapping.yaml"
        with tm_path.open(encoding="utf-8") as f:
            mappings = yaml.safe_load(f)

        # 3. Extract the two dicts you need
        self.house_types = mappings.get("house_types", {})
        
        # Initialize counters
        self.item_count = 0
        self.error_count = 0
        
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
        # Loop over each config block
        for cfg in self.configs:
            for url in cfg["start_urls"]:
                yield scrapy.Request(
                    url,
                    callback=self.parse_item,
                    meta={"config": cfg}
                )

    def parse_item(self, response):
        cfg = response.meta["config"]
        
        # Check for rows using XPath
        row_xpath = cfg["xpaths"].get("rows", ["//tr"])[0]
        rows = response.xpath(row_xpath)
        
        self.logger.info(f"📊 Found {len(rows)} rows using xpath: {row_xpath}")
        
        if len(rows) == 0:
            self.logger.warning(f"⚠️ zero rows in {response.url}")
            return
        
        for row in rows:
            # Extract data from each row
            item = {
                "zone": cfg["zone"],
            }
            
            # Extract all fields using XPaths
            for field, xpath_list in cfg["xpaths"].items():
                if field == "rows":
                    continue
                    
                # Ensure xpath_list is a list
                if isinstance(xpath_list, str):
                    xpath_list = [xpath_list]
                    
                # Check if this is a static value (doesn't start with . or /)
                value = None
                for xpath in xpath_list:
                    try:
                        # Handle static values (non-XPath)
                        if not xpath.startswith('.') and not xpath.startswith('/') and not xpath.startswith('@'):
                            value = xpath  # Use the value directly
                            break
                        else:
                            # Handle XPath extraction
                            value = row.xpath(xpath).get()
                            if value and value.strip():
                                value = value.strip()
                                break
                    except Exception as e:
                        self.logger.debug(f"XPath failed for {field}: {e}")
                        continue
                
                # Map field to item
                mapped_field = cfg["fields"].get(field, field)
                item[mapped_field] = value
            
            # Handle URL completion - convert relative URLs to absolute URLs
            if "source_url" in item and item["source_url"]:
                if item["source_url"].startswith('/'):
                    # Convert relative URL to absolute URL
                    base_url = response.url.split('/')[0] + '//' + response.url.split('/')[2]
                    item["source_url"] = base_url + item["source_url"]
                elif not item["source_url"].startswith('http'):
                    # If it's not a relative path and not absolute, make it absolute
                    base_url = response.url.split('/')[0] + '//' + response.url.split('/')[2]
                    item["source_url"] = base_url + '/' + item["source_url"]
            
            # Apply type mapping
            raw_type = item.get("type_raw", "")
            normalized_type = self.house_types.get(raw_type, raw_type)
            # Handle case where normalized_type might already be a list
            if isinstance(normalized_type, list):
                item["type"] = normalized_type
            else:
                item["type"] = [normalized_type] if normalized_type else []
            
            # Data quality validation
            if self.has_too_many_null_columns(item):
                self.logger.warning(f"🚫 REJECTED: Too many null columns in house deal: {item.get('building_name_zh', 'Unknown')} - {item.get('type_raw', 'Unknown')}")
                continue
            
            self.logger.info(f"🆕 NEW HOUSE DEAL: {item.get('building_name_zh', 'Unknown')} - {item.get('type_raw', 'Unknown')} - 售${item.get('deal_price', 'Unknown')}")
            self.item_count += 1
            yield item

    def spider_closed(self, spider):
        # Enhanced summary with statistics
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        self.logger.info("🏠 HOUSE SPIDER SUMMARY:")
        self.logger.info(f"   🆕 New deals found: {self.item_count}")
        self.logger.info(f"   📊 Total deals processed: {self.item_count}")
        self.logger.info(f"   🔄 Monitoring mode: {self.mode}")
        
        summary = f"[{timestamp}] {self.name}: {self.item_count} items, {self.error_count} errors\n"

        # Ensure the logs/ folder exists
        log_dir = "logs"
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)

        # Append to summary.txt
        log_path = os.path.join(log_dir, "summary.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(summary)
