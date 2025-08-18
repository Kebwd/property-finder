# Property Scraper Daily Task Setup
# Creates a Windows Task Scheduler task to run the scraper daily

param(
    [string]$Time = "02:00"  # Default to 2 AM
)

Write-Host "🕷️  Setting up daily property scraper task..." -ForegroundColor Green
Write-Host "📅 Schedule: Daily at $Time" -ForegroundColor Yellow

# Get current directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "daily_scraper.py"
$LogDir = Join-Path $ScriptDir "logs"

# Create logs directory if it doesn't exist
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force
    Write-Host "📁 Created logs directory: $LogDir" -ForegroundColor Green
}

# Get Python executable path
$PythonPath = (Get-Command python).Source
Write-Host "🐍 Python path: $PythonPath" -ForegroundColor Blue

# Create the task action
$TaskAction = New-ScheduledTaskAction -Execute $PythonPath -Argument $PythonScript -WorkingDirectory $ScriptDir

# Create the task trigger (daily at specified time)
$TaskTrigger = New-ScheduledTaskTrigger -Daily -At $Time

# Create task settings
$TaskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Create the task principal (run as current user)
$TaskPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType ServiceAccount

# Create the scheduled task
$TaskName = "PropertyScraperDaily"
$TaskDescription = "Daily property data scraping from Hong Kong real estate websites"

try {
    # Remove existing task if it exists
    $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($ExistingTask) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "🗑️  Removed existing task" -ForegroundColor Yellow
    }

    # Register the new task
    Register-ScheduledTask -TaskName $TaskName -Action $TaskAction -Trigger $TaskTrigger -Settings $TaskSettings -Principal $TaskPrincipal -Description $TaskDescription

    Write-Host "✅ Task '$TaskName' created successfully!" -ForegroundColor Green
    Write-Host "📋 Task details:" -ForegroundColor Blue
    Write-Host "   - Name: $TaskName" -ForegroundColor White
    Write-Host "   - Schedule: Daily at $Time" -ForegroundColor White
    Write-Host "   - Script: $PythonScript" -ForegroundColor White
    Write-Host "   - Working Directory: $ScriptDir" -ForegroundColor White
    
    # Show the task
    Get-ScheduledTask -TaskName $TaskName | Format-Table TaskName, State, NextRunTime
    
    Write-Host "🔧 To manage the task:" -ForegroundColor Yellow
    Write-Host "   - View: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "   - Run now: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "   - Disable: Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "   - Remove: Unregister-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White

} catch {
    Write-Host "❌ Failed to create task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Try running PowerShell as Administrator" -ForegroundColor Yellow
}
