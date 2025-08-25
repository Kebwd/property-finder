#!/bin/bash

# Daily Combined Scraper - Runs both house and store spiders
# Usage: ./run_daily_combined.sh

echo "🚀 Starting Daily Combined Property Scraper"
echo "📅 Date: $(date '+%Y-%m-%d %H:%M:%S')"

cd /scraper

# Run house spider first (takes longer, more comprehensive)
echo "🏠 Starting house spider..."
python daily_scraper.py --houses daily
HOUSE_RESULT=$?

# Wait 5 minutes to avoid rate limiting
echo "⏳ Waiting 5 minutes before store spider..."
sleep 300

# Run store spider second
echo "🏪 Starting store spider..."
python daily_scraper.py --stores daily
STORE_RESULT=$?

# Report results
echo ""
echo "📊 SCRAPING RESULTS:"
echo "🏠 House spider: $([ $HOUSE_RESULT -eq 0 ] && echo "✅ SUCCESS" || echo "❌ FAILED")"
echo "🏪 Store spider: $([ $STORE_RESULT -eq 0 ] && echo "✅ SUCCESS" || echo "❌ FAILED")"

# Exit with error if either failed
if [ $HOUSE_RESULT -ne 0 ] || [ $STORE_RESULT -ne 0 ]; then
    echo "⚠️  Some spiders failed - check logs"
    exit 1
else
    echo "🎉 All spiders completed successfully!"
    exit 0
fi
