# Supabase Database Configuration Script
# This script helps you connect the scraper to your Supabase database

Write-Host "🗄️  SUPABASE DATABASE CONFIGURATION" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Blue

Write-Host "`n📋 To connect your scraper to Supabase, you need:" -ForegroundColor Yellow
Write-Host "1. Your Supabase project URL" -ForegroundColor White
Write-Host "2. Your database password" -ForegroundColor White
Write-Host "3. Your project reference ID" -ForegroundColor White

Write-Host "`n🔧 Steps to get your Supabase credentials:" -ForegroundColor Cyan
Write-Host "1. Go to https://supabase.com/dashboard" -ForegroundColor White
Write-Host "2. Select your project" -ForegroundColor White
Write-Host "3. Go to Settings > Database" -ForegroundColor White
Write-Host "4. Copy the connection string" -ForegroundColor White

Write-Host "`n📝 Your connection string should look like:" -ForegroundColor Yellow
Write-Host "postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" -ForegroundColor Green

# Check if .env file exists
$EnvFile = ".env"
if (Test-Path $EnvFile) {
    Write-Host "`n✅ Found existing .env file" -ForegroundColor Green
    $Content = Get-Content $EnvFile
    if ($Content -match "DATABASE_URL") {
        Write-Host "✅ DATABASE_URL already configured" -ForegroundColor Green
    } else {
        Write-Host "⚠️  DATABASE_URL not found in .env file" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n❌ No .env file found" -ForegroundColor Red
    Write-Host "📝 Creating .env file template..." -ForegroundColor Yellow
    
    # Create .env file with template
    $EnvTemplate = @"
# Supabase Database Configuration
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# Alternative individual settings
DB_HOST=db.[YOUR-PROJECT-REF].supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=[YOUR-SUPABASE-PASSWORD]

# Scraper Settings
SCRAPER_MODE=daily
LOG_LEVEL=INFO
"@
    
    $EnvTemplate | Out-File -FilePath $EnvFile -Encoding UTF8
    Write-Host "✅ Created .env template file" -ForegroundColor Green
}

Write-Host "`n🔧 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Edit the .env file with your actual Supabase credentials" -ForegroundColor White
Write-Host "2. Replace [YOUR-PASSWORD] with your database password" -ForegroundColor White
Write-Host "3. Replace [YOUR-PROJECT-REF] with your project reference" -ForegroundColor White
Write-Host "4. Test the connection with: python test_db_connection.py" -ForegroundColor White

Write-Host "`n💡 Need help? Check the working API configuration:" -ForegroundColor Yellow
Write-Host "The same DATABASE_URL used in your Vercel deployment should work here." -ForegroundColor White
