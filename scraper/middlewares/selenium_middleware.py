"""
Selenium middleware for handling JavaScript-rendered pages
"""
from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

class SeleniumMiddleware:
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger(__name__)
        
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware
    
    def spider_opened(self, spider):
        """Initialize Chrome driver when spider opens"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.logger.info("🚗 Chrome driver initialized for JavaScript sites")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Chrome driver: {e}")
            self.driver = None
    
    def spider_closed(self, spider):
        """Close driver when spider closes"""
        if self.driver:
            self.driver.quit()
            self.logger.info("🚗 Chrome driver closed")
    
    def process_request(self, request, spider):
        """Process requests for JavaScript sites"""
        # Only use Selenium for Midland ICI
        if 'midlandici.com' not in request.url:
            return None
            
        if not self.driver:
            self.logger.warning("⚠️ Chrome driver not available, skipping Selenium request")
            return None
            
        try:
            self.logger.info(f"🔍 Loading JavaScript page: {request.url}")
            self.driver.get(request.url)
            
            # Wait for the transaction table to load
            wait = WebDriverWait(self.driver, 10)
            
            try:
                # Wait for transaction data to appear
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".transaction-row, tbody tr, table tr")))
                self.logger.info("✅ Transaction data loaded")
            except Exception:
                self.logger.warning("⚠️ No transaction data found, continuing anyway")
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            # Get page source after JavaScript execution
            body = self.driver.page_source.encode('utf-8')
            
            # Create new response with rendered content
            return HtmlResponse(
                url=request.url,
                body=body,
                encoding='utf-8',
                request=request
            )
            
        except Exception as e:
            self.logger.error(f"❌ Selenium request failed: {e}")
            return None
