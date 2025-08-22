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
    # Anti-bot protection middlewares
    "middlewares.anti_bot_middleware.AntiBot": 100,
    "middlewares.anti_bot_middleware.ShadowUserAgentMiddleware": 200,
    "middlewares.proxy_middleware.SmartProxyMiddleware": 300,
    "middlewares.anti_bot_middleware.EnhancedRetryMiddleware": 400,
    
    # Existing middlewares
    "middlewares.selenium_middleware.SeleniumMiddleware": 543,
    "scrapy_selenium.SeleniumMiddleware": 800,
}

# Anti-bot configuration
CONCURRENT_REQUESTS = 1  # Reduced to be more conservative
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 3  # Base delay, anti-bot middleware will add more randomization
RANDOMIZE_DOWNLOAD_DELAY = 0.5  # 50% randomization

# Enable AutoThrottle for intelligent request throttling
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5  # Very conservative
AUTOTHROTTLE_DEBUG = True  # Enable to see throttling stats

# Retry configuration for anti-bot scenarios
RETRY_TIMES = 5  # Increased retries for blocked requests
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]

# Proxy configuration (optional - add your proxy list here)
# PROXY_LIST = [
#     'http://proxy1:port',
#     'http://proxy2:port',
# ]
# PROXY_FILE = 'proxies.txt'  # Path to proxy file
# USE_FREE_PROXIES = False  # Set to True to use free proxies (not recommended for production)

# Cookies configuration
COOKIES_ENABLED = True  # Enable cookies for session management

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
