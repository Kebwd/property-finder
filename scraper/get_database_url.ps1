# Get Database URL from Vercel Environment
# This script helps you retrieve the DATABASE_URL from your working Vercel deployment

Write-Host "🔗 EXTRACTING DATABASE_URL FROM VERCEL" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Blue

Write-Host "`n📋 Your API endpoints are working, which means Vercel has the correct DATABASE_URL" -ForegroundColor Yellow
Write-Host "To get the DATABASE_URL for your scraper:" -ForegroundColor White

Write-Host "`n🔧 Method 1: Vercel Dashboard" -ForegroundColor Cyan
Write-Host "1. Go to https://vercel.com/dashboard" -ForegroundColor White
Write-Host "2. Select your property-finder project" -ForegroundColor White
Write-Host "3. Go to Settings > Environment Variables" -ForegroundColor White
Write-Host "4. Find DATABASE_URL and copy its value" -ForegroundColor White

Write-Host "`n🔧 Method 2: Vercel CLI" -ForegroundColor Cyan
Write-Host "1. Run: vercel env ls" -ForegroundColor White
Write-Host "2. Find the DATABASE_URL value" -ForegroundColor White

Write-Host "`n🔧 Method 3: Direct from Supabase" -ForegroundColor Cyan
Write-Host "1. Go to https://supabase.com/dashboard" -ForegroundColor White
Write-Host "2. Select your project" -ForegroundColor White
Write-Host "3. Settings > Database > Connection string" -ForegroundColor White
Write-Host "4. Copy the 'URI' connection string" -ForegroundColor White

Write-Host "`n📝 Once you have the DATABASE_URL:" -ForegroundColor Yellow
Write-Host "1. Edit the scraper/.env file" -ForegroundColor White
Write-Host "2. Replace the DATABASE_URL line with your actual connection string" -ForegroundColor White
Write-Host "3. Test with: python test_db_connection.py" -ForegroundColor White

Write-Host "`n💡 Example DATABASE_URL format:" -ForegroundColor Green
Write-Host "postgresql://postgres:yourpassword@db.xxxxxxxxxxxx.supabase.co:5432/postgres" -ForegroundColor Gray

# Check if vercel CLI is available
$VercelCheck = Get-Command vercel -ErrorAction SilentlyContinue
if ($VercelCheck) {
    Write-Host "`n🚀 Attempting to get environment variables from Vercel..." -ForegroundColor Cyan
    try {
        $EnvList = vercel env ls 2>&1
        Write-Host $EnvList -ForegroundColor Gray
    } catch {
        Write-Host "❌ Could not retrieve Vercel environment variables" -ForegroundColor Red
    }
} else {
    Write-Host "`n⚠️  Vercel CLI not found. You'll need to get the DATABASE_URL manually." -ForegroundColor Yellow
}
