# PowerShell Script for Automated Property Scraping
# Can be scheduled with Windows Task Scheduler or run manually

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("test", "schedule")]
    [string]$Mode = "test",
    
    [Parameter(Mandatory=$false)]
    [string]$LogPath = ".\automated_scraping.log"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write timestamped log messages
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogPath -Value $logMessage
}

try {
    Write-Log "🤖 Starting Automated Property Scraping System"
    Write-Log "Mode: $Mode"
    
    # Change to scraper directory
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $ScriptDir
    Write-Log "Working directory: $(Get-Location)"
    
    # Check Python availability
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        throw "Python not found in PATH"
    }
    Write-Log "Python found: $($pythonCmd.Source)"
    
    # Install required packages if needed
    Write-Log "Installing required Python packages..."
    & python -m pip install schedule requests beautifulsoup4 lxml selenium fake-useragent undetected-chromedriver --quiet
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Warning: Some packages may not have installed correctly" "WARN"
    }
    
    # Run the automated scraping system
    Write-Log "🚀 Launching automated scraping system..."
    & python automated_scraping_scheduler.py --mode $Mode
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ Scraping system completed successfully"
        
        # List generated files
        Write-Log "📁 Generated files:"
        Get-ChildItem -Name "*scrape_*.json", "*report_*.json" | ForEach-Object {
            Write-Log "   - $_"
        }
        
    } else {
        throw "Scraping system failed with exit code: $LASTEXITCODE"
    }
    
} catch {
    Write-Log "❌ Error: $($_.Exception.Message)" "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    exit 1
}

Write-Log "🎉 Automated Property Scraping System completed"

# If running in test mode, show results summary
if ($Mode -eq "test") {
    Write-Host "`n📊 RESULTS SUMMARY" -ForegroundColor Green
    Write-Host "==================" -ForegroundColor Green
    
    # Check for today's files
    $today = Get-Date -Format "yyyyMMdd"
    $morningFile = "morning_scrape_$today.json"
    $afternoonFile = "afternoon_scrape_$today.json"
    $reportFile = "daily_report_$today.json"
    
    if (Test-Path $morningFile) {
        $morningData = Get-Content $morningFile | ConvertFrom-Json
        $morningCount = $morningData.properties.Count
        Write-Host "🌅 Morning scrape: $morningCount properties" -ForegroundColor Cyan
    }
    
    if (Test-Path $afternoonFile) {
        $afternoonData = Get-Content $afternoonFile | ConvertFrom-Json
        $afternoonCount = $afternoonData.summary.totals.total_properties
        Write-Host "🌞 Afternoon scrape: $afternoonCount properties" -ForegroundColor Cyan
    }
    
    if (Test-Path $reportFile) {
        $reportData = Get-Content $reportFile | ConvertFrom-Json
        $totalCount = $reportData.daily_summary.total
        Write-Host "📈 Total daily properties: $totalCount" -ForegroundColor Yellow
    }
    
    Write-Host "`n🔍 Check automated_scraping.log for detailed logs" -ForegroundColor Gray
}
