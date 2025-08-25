# Windows PowerShell version of combined daily scraper
# Usage: .\run_daily_combined.ps1

Write-Host "🚀 Starting Daily Combined Property Scraper" -ForegroundColor Green
Write-Host "📅 Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan

Set-Location -Path "C:\Users\User\property-finder\scraper"

# Run house spider first (takes longer, more comprehensive)
Write-Host "🏠 Starting house spider..." -ForegroundColor Yellow
& python daily_scraper.py --houses daily
$houseResult = $LASTEXITCODE

# Wait 5 minutes to avoid rate limiting
Write-Host "⏳ Waiting 5 minutes before store spider..." -ForegroundColor Blue
Start-Sleep -Seconds 300

# Run store spider second
Write-Host "🏪 Starting store spider..." -ForegroundColor Yellow
& python daily_scraper.py --stores daily
$storeResult = $LASTEXITCODE

# Report results
Write-Host ""
Write-Host "📊 SCRAPING RESULTS:" -ForegroundColor Magenta
if ($houseResult -eq 0) {
    Write-Host "🏠 House spider: ✅ SUCCESS" -ForegroundColor Green
} else {
    Write-Host "🏠 House spider: ❌ FAILED" -ForegroundColor Red
}

if ($storeResult -eq 0) {
    Write-Host "🏪 Store spider: ✅ SUCCESS" -ForegroundColor Green
} else {
    Write-Host "🏪 Store spider: ❌ FAILED" -ForegroundColor Red
}

# Exit with error if either failed
if ($houseResult -ne 0 -or $storeResult -ne 0) {
    Write-Host "⚠️  Some spiders failed - check logs" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "🎉 All spiders completed successfully!" -ForegroundColor Green
    exit 0
}
