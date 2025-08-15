# store_scraper/spiders/store_spider.py
import os
import scrapy
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


def extract_first(response, xpaths, default=None):
    for xp in xpaths:
        val = response.xpath(xp).get()
        if val:
            return val.strip()
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
                fields[std_field] = extract_first(response, xpath_map[std_field])
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Load all config blocks (list of dicts)
        self.configs = []
        self.configs += load_config("scraper/config/hk_house.yaml")
        self.configs += load_config("scraper/config/cn_house.yaml")

        # 2. Load your type mappings from YAML
        tm_path = Path(__file__).parents[2] / "config" / "type_mapping.yaml"
        with tm_path.open(encoding="utf-8") as f:
            mappings = yaml.safe_load(f)

        # 3. Extract the two dicts you need
        self.house_types = mappings.get("house_types", {})

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
        cfg      = response.meta["config"]
        raw_type = response.xpath(cfg["xpaths"]["type"]).get(default="").strip()

        # Choose the right mapping
        normalized_type = self.house_types.get(raw_type, raw_type)

        item = {
            "zone":        cfg["zone"],
            "type_raw":    raw_type,
            "type":        normalized_type,
        }

        # Extract all other fields
        for field, key in cfg["fields"].items():
            if key == "type":
                # Already extracted above
                item[field] = normalized_type
                continue

            xpath_expr = cfg["xpaths"].get(key)
            if not xpath_expr:
                item[field] = ""
                continue

            # If it’s a relative path off the whole page, apply it directly
            value = response.xpath(xpath_expr).get(default="").strip()
            item[field] = value

        yield 

    def spider_closed(self, spider):
        # 1. Build timestamped summary
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        summary = f"[{timestamp}] {self.name}: {self.item_count} items, {self.error_count} errors\n"

        # 2. Ensure the logs/ folder exists
        log_dir = "logs"
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)

        # 3. Append to summary.txt
        log_path = os.path.join(log_dir, "summary.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(summary)