#!/bin/bash
# Quick fix for scrapy-selenium dependency in deployment environment
echo "🔧 Installing missing dependencies for property scraper..."

# Install scrapy-selenium if not available
python -c "import scrapy_selenium" 2>/dev/null || {
    echo "📦 Installing scrapy-selenium..."
    pip install scrapy-selenium>=0.0.7
}

# Verify installation
python -c "from scrapy_selenium import SeleniumRequest; print('✅ scrapy-selenium ready')" || {
    echo "❌ Failed to install scrapy-selenium"
    exit 1
}

# Test spider loading
echo "🕷️ Testing spider loading..."
python -m scrapy list >/dev/null 2>&1 || {
    echo "❌ Spider loading failed"
    exit 1
}

echo "✅ All dependencies ready for scraping!"
