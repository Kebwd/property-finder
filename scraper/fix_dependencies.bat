@echo off
REM Quick fix for scrapy-selenium dependency in Windows environment
echo 🔧 Installing missing dependencies for property scraper...

REM Install scrapy-selenium if not available
python -c "import scrapy_selenium" >nul 2>&1 || (
    echo 📦 Installing scrapy-selenium...
    pip install scrapy-selenium>=0.0.7
)

REM Verify installation
python -c "from scrapy_selenium import SeleniumRequest; print('✅ scrapy-selenium ready')" || (
    echo ❌ Failed to install scrapy-selenium
    exit /b 1
)

REM Test spider loading
echo 🕷️ Testing spider loading...
python -m scrapy list >nul 2>&1 || (
    echo ❌ Spider loading failed
    exit /b 1
)

echo ✅ All dependencies ready for scraping!
