#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "---- crawl started at $(date) ----" >> /var/log/scraper.log
source venv/bin/activate

scrapy crawl store_spider -a config_paths=config/hk_store.yaml,config/cn_store.yaml

scrapy crawl house_spider -a config_paths=config/hk_house.yaml,config/cn_house.yaml
