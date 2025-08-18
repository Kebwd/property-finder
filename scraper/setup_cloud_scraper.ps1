# Setup GitHub Actions for 24/7 Cloud Scraping
# This script helps you set up free cloud automation

Write-Host "🌐 GITHUB ACTIONS CLOUD SCRAPER SETUP" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Blue

Write-Host "`n🎯 This will set up 24/7 cloud scraping that runs even when your PC is off!" -ForegroundColor Yellow

Write-Host "`n📋 STEPS TO COMPLETE:" -ForegroundColor Cyan

Write-Host "`n1. 📁 GitHub Repository Setup" -ForegroundColor Yellow
Write-Host "   - Push your code to GitHub (if not already done)" -ForegroundColor White
Write-Host "   - The workflow file is already created at:" -ForegroundColor White
Write-Host "     .github/workflows/daily-scraper.yml" -ForegroundColor Gray

Write-Host "`n2. 🔐 Add Secrets to GitHub" -ForegroundColor Yellow
Write-Host "   - Go to your GitHub repository" -ForegroundColor White
Write-Host "   - Settings > Secrets and variables > Actions" -ForegroundColor White
Write-Host "   - Add these secrets:" -ForegroundColor White
Write-Host "     - DATABASE_URL: $DATABASE_URL" -ForegroundColor Gray
Write-Host "       (Use the same one from your .env file)" -ForegroundColor Gray

Write-Host "`n3. 🚀 Enable GitHub Actions" -ForegroundColor Yellow
Write-Host "   - Go to Actions tab in your repository" -ForegroundColor White
Write-Host "   - Enable workflows if prompted" -ForegroundColor White
Write-Host "   - The scraper will run daily at 2:00 AM UTC automatically" -ForegroundColor White

Write-Host "`n4. ✅ Test the Setup" -ForegroundColor Yellow
Write-Host "   - Go to Actions tab" -ForegroundColor White
Write-Host "   - Click on 'Daily Property Scraper'" -ForegroundColor White
Write-Host "   - Click 'Run workflow' to test immediately" -ForegroundColor White

Write-Host "`n🎉 BENEFITS OF GITHUB ACTIONS:" -ForegroundColor Green
Write-Host "   ✅ Completely FREE (2000 minutes/month)" -ForegroundColor White
Write-Host "   ✅ Runs 24/7 in the cloud" -ForegroundColor White
Write-Host "   ✅ No PC required - works when your computer is off" -ForegroundColor White
Write-Host "   ✅ Automatic logging and error notifications" -ForegroundColor White
Write-Host "   ✅ Easy to monitor and debug" -ForegroundColor White

Write-Host "`n📅 SCHEDULE:" -ForegroundColor Cyan
Write-Host "   - Runs daily at 2:00 AM UTC (10:00 AM Hong Kong time)" -ForegroundColor White
Write-Host "   - You can change the schedule in the workflow file" -ForegroundColor White

Write-Host "`n🔧 CURRENT LOCAL SETUP:" -ForegroundColor Yellow
if (Get-ScheduledTask -TaskName 'PropertyScraperDaily' -ErrorAction SilentlyContinue) {
    Write-Host "   ✅ Windows Task Scheduler: Active (requires PC on)" -ForegroundColor Green
    Write-Host "   💡 You can keep both or disable the local one" -ForegroundColor Yellow
} else {
    Write-Host "   ❌ Windows Task Scheduler: Not found" -ForegroundColor Red
}

Write-Host "`n📋 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Push your code to GitHub" -ForegroundColor White
Write-Host "2. Add DATABASE_URL secret" -ForegroundColor White
Write-Host "3. Enable Actions and test" -ForegroundColor White

# Get current DATABASE_URL for reference
$EnvFile = ".env"
if (Test-Path $EnvFile) {
    $DatabaseUrl = (Get-Content $EnvFile | Where-Object { $_ -match "^DATABASE_URL=" }) -replace "DATABASE_URL=", ""
    if ($DatabaseUrl) {
        Write-Host "`n🔗 Your DATABASE_URL (add this as GitHub secret):" -ForegroundColor Green
        Write-Host $DatabaseUrl -ForegroundColor Gray
    }
}
