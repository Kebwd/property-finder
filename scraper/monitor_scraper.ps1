# Property Scraper Status Monitor
# Quick script to check scraper status and recent activity

Write-Host "🕷️  PROPERTY SCRAPER STATUS MONITOR" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Blue

# Check scheduled task status
Write-Host "`n📋 SCHEDULED TASK STATUS" -ForegroundColor Yellow
try {
    $Task = Get-ScheduledTask -TaskName 'PropertyScraperDaily' -ErrorAction Stop
    Write-Host "✅ Task Name: $($Task.TaskName)" -ForegroundColor Green
    Write-Host "✅ State: $($Task.State)" -ForegroundColor Green
    
    $TaskInfo = Get-ScheduledTaskInfo -TaskName 'PropertyScraperDaily'
    Write-Host "📅 Last Run: $($TaskInfo.LastRunTime)" -ForegroundColor White
    Write-Host "🔄 Next Run: $($TaskInfo.NextRunTime)" -ForegroundColor White
    Write-Host "📊 Last Result: $($TaskInfo.LastTaskResult)" -ForegroundColor White
} catch {
    Write-Host "❌ Scheduled task not found" -ForegroundColor Red
}

# Check recent scraping activity
Write-Host "`n📁 RECENT SCRAPING ACTIVITY" -ForegroundColor Yellow
$OutputDir = "daily_output"
if (Test-Path $OutputDir) {
    $RecentFiles = Get-ChildItem $OutputDir -Recurse -Include "*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 5
    
    if ($RecentFiles) {
        Write-Host "✅ Recent output files:" -ForegroundColor Green
        foreach ($File in $RecentFiles) {
            $SizeKB = [math]::Round($File.Length / 1KB, 1)
            Write-Host "   📄 $($File.Name) - $($File.LastWriteTime) ($SizeKB KB)" -ForegroundColor White
        }
    } else {
        Write-Host "⚠️  No output files found" -ForegroundColor Yellow
    }
    
    # Check latest.json for deal count
    $LatestFile = Join-Path $OutputDir "latest.json"
    if (Test-Path $LatestFile) {
        try {
            $LatestData = Get-Content $LatestFile | ConvertFrom-Json
            Write-Host "📊 Latest scrape: $($LatestData.Count) deals found" -ForegroundColor Cyan
        } catch {
            Write-Host "⚠️  Could not read latest.json" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "❌ Output directory not found" -ForegroundColor Red
}

# Check database connection (simplified)
Write-Host "`n🗄️  DATABASE STATUS" -ForegroundColor Yellow
if ($env:DATABASE_URL) {
    Write-Host "✅ Database URL configured" -ForegroundColor Green
} else {
    Write-Host "⚠️  DATABASE_URL environment variable not set" -ForegroundColor Yellow
}

# Check logs for errors
Write-Host "`n📋 RECENT LOG STATUS" -ForegroundColor Yellow
$LogFiles = Get-ChildItem $OutputDir -Recurse -Include "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 3

if ($LogFiles) {
    foreach ($LogFile in $LogFiles) {
        $LastLines = Get-Content $LogFile.FullName -Tail 5 | Where-Object { $_ -match "ERROR|CRITICAL|scraped" }
        if ($LastLines) {
            Write-Host "📄 $($LogFile.Name):" -ForegroundColor White
            foreach ($Line in $LastLines) {
                if ($Line -match "ERROR|CRITICAL") {
                    Write-Host "   ❌ $Line" -ForegroundColor Red
                } else {
                    Write-Host "   ✅ $Line" -ForegroundColor Green
                }
            }
        }
    }
}

Write-Host "`n🎯 QUICK COMMANDS" -ForegroundColor Yellow
Write-Host "Run now: Start-ScheduledTask -TaskName 'PropertyScraperDaily'" -ForegroundColor White
Write-Host "View task: Get-ScheduledTask -TaskName 'PropertyScraperDaily'" -ForegroundColor White
Write-Host "Manual run: python daily_scraper.py" -ForegroundColor White
Write-Host "Health check: python health_check.py" -ForegroundColor White
