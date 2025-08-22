# Windows Task Scheduler Script for Property Scraping
# This batch file can be scheduled in Windows Task Scheduler

@echo off
echo Starting Automated Property Scraping System
echo ==========================================

cd /d "C:\Users\User\property-finder\scraper"

REM Activate Python environment if needed
REM call venv\Scripts\activate.bat

echo Running morning scraping routine...
python automated_scraping_scheduler.py --mode test

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Scraping failed with code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Scraping completed successfully!
echo Log files created in current directory
echo.
echo Check these files for results:
echo - morning_scrape_*.json
echo - afternoon_scrape_*.json  
echo - daily_report_*.json
echo - automated_scraping.log

pause
