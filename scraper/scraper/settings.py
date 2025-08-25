# Scrapy settings for store_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "store_scraper (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings
CONCURRENT_REQUESTS = 1  # Will be overridden by anti-bot middleware
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 3  # Will be enhanced by anti-bot middleware
AUTOTHROTTLE_ENABLED = True  # Will be configured below
# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "store_scraper.middlewares.StoreScraperSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # Enhanced proxy middleware (highest priority)
    "middlewares.enhanced_proxy_middleware.EnhancedProxyMiddleware": 100,
    
    # Simple but highly effective anti-bot protection
    "middlewares.scrapy_simple_antibot.ScrapySimpleAntiBot": 200,
    
    # Enhanced retry with proxy-aware logic
    "middlewares.enhanced_proxy_middleware.ProxyRetryMiddleware": 300,
    
    # Disable default retry middleware (replaced by our enhanced version)
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
    
    # Existing middlewares
    "middlewares.selenium_middleware.SeleniumMiddleware": 543,
    "scrapy_selenium.SeleniumMiddleware": 800,
}

# ScraperAPI Optimized settings for maximum success
CONCURRENT_REQUESTS = 1          # Conservative with premium proxy
CONCURRENT_REQUESTS_PER_DOMAIN = 1  # Single request per domain (ScraperAPI handles rotation)
DOWNLOAD_DELAY = 0               # Let ScraperAPI handle timing
RANDOMIZE_DOWNLOAD_DELAY = 0     # ScraperAPI manages request timing

# AutoThrottle optimized for ScraperAPI
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1     # Fast start with ScraperAPI
AUTOTHROTTLE_MAX_DELAY = 10      # Lower max delay for premium proxy
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.8  # Higher concurrency with reliable proxy
AUTOTHROTTLE_DEBUG = True        # Show throttling stats

# Fast and efficient retry settings for ScraperAPI
RETRY_TIMES = 3                  # Reduced from 8 - fail fast with premium proxy
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403, 407, 401]  # Include common errors

# Session management
COOKIES_ENABLED = True
COOKIES_DEBUG = False

# Reduced timeouts for faster response
DOWNLOAD_TIMEOUT = 15            # Reduced from 30 - fail fast approach
DOWNLOAD_DELAY_EXPOSURE_RANDOMIZE = False  # Consistent timing with ScraperAPI

# ScraperAPI-specific settings
PROXY_POOL_SIZE = 1             # Only one ScraperAPI proxy needed
PROXY_HEALTH_CHECK_INTERVAL = 100  # Less frequent health checks for reliable proxy
PROXY_MAX_FAILURES = 5         # More tolerance for ScraperAPI temporary issues

# Selenium configuration for Lianjia spider with anti-detection
from selenium import webdriver
SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = None  # Use default Chrome driver
SELENIUM_DRIVER_ARGUMENTS = [
    '--headless',
    '--no-sandbox', 
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--window-size=1920,1080',
    '--disable-blink-features=AutomationControlled',  # Hide automation
    '--disable-extensions',
    '--disable-plugins',
    '--disable-images',  # Speed up loading
    '--disable-javascript',  # May help avoid detection
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "scraper.pipelines.normalization_pipeline.NormalizationPipeline": 100,
   "scraper.pipelines.house_pipeline.HousePipeline":300,
   "scraper.pipelines.store_pipeline.StorePipeline": 400
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False
# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
