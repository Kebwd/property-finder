# PowerShell script to download GeoJSON files from Google Drive (requires public direct links)
$geojsonDir = "scraper/config/districts"
if (-not (Test-Path $geojsonDir)) { New-Item -ItemType Directory -Path $geojsonDir }

# Example: Download a GeoJSON file from Google Drive using its file ID
# Repeat the Invoke-WebRequest line for each GeoJSON file you want to download

# Example for one file (replace the OutFile name as needed):
Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=1UHp3DLRwhVsd2hoN-Qn3yxRlP_pv2c_Y" -OutFile "$geojsonDir/hk_island.geojson"

Write-Host "GeoJSON files downloaded."
