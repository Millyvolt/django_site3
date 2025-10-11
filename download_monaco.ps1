# Monaco Editor Download Script
# Downloads pre-built Monaco Editor files from jsDelivr CDN
# Version: 0.54.0

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Monaco Editor Download Script" -ForegroundColor Cyan
Write-Host "Version: 0.54.0" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$MonacoVersion = "0.54.0"
$BaseUrl = "https://cdn.jsdelivr.net/npm/monaco-editor@$MonacoVersion/min/vs"
$DestinationPath = "collab\static\collab\monaco\vs"

# Check if directory already exists
if (Test-Path $DestinationPath) {
    Write-Host "⚠️  Monaco files already exist at: $DestinationPath" -ForegroundColor Yellow
    $response = Read-Host "Do you want to re-download? (y/n)"
    if ($response -ne 'y') {
        Write-Host "Aborted. Using existing files." -ForegroundColor Yellow
        exit 0
    }
    Write-Host "Removing existing files..." -ForegroundColor Yellow
    Remove-Item -Path $DestinationPath -Recurse -Force
}

# Create directory structure
Write-Host "📁 Creating directory structure..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $DestinationPath | Out-Null

# Function to download a file
function Download-File {
    param(
        [string]$Url,
        [string]$Destination
    )
    
    $DestDir = Split-Path -Parent $Destination
    if (-not (Test-Path $DestDir)) {
        New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
    }
    
    try {
        Write-Host "  Downloading: $Url" -ForegroundColor Gray
        Invoke-WebRequest -Uri $Url -OutFile $Destination -ErrorAction Stop
        return $true
    }
    catch {
        Write-Host "  ✗ Failed: $_" -ForegroundColor Red
        return $false
    }
}

# Critical files to download
Write-Host ""
Write-Host "📥 Downloading Monaco Editor files..." -ForegroundColor Green
Write-Host "This may take 2-5 minutes depending on your connection..." -ForegroundColor Yellow
Write-Host ""

$FilesToDownload = @(
    # Core loader (critical!)
    "loader.js",
    
    # Editor main files
    "editor/editor.main.js",
    "editor/editor.main.css",
    "editor/editor.main.nls.js",
    
    # Workers
    "base/worker/workerMain.js",
    
    # Language files (our 12 languages)
    "basic-languages/javascript/javascript.js",
    "basic-languages/typescript/typescript.js",
    "basic-languages/python/python.js",
    "basic-languages/java/java.js",
    "basic-languages/cpp/cpp.js",
    "basic-languages/csharp/csharp.js",
    "basic-languages/go/go.js",
    "basic-languages/rust/rust.js",
    "basic-languages/html/html.js",
    "basic-languages/css/css.js",
    "basic-languages/sql/sql.js",
    "language/json/jsonMode.js",
    "language/json/jsonWorker.js",
    
    # Advanced language services
    "language/typescript/tsMode.js",
    "language/typescript/tsWorker.js",
    "language/css/cssMode.js",
    "language/css/cssWorker.js",
    "language/html/htmlMode.js",
    "language/html/htmlWorker.js"
)

$SuccessCount = 0
$FailCount = 0

foreach ($File in $FilesToDownload) {
    $Url = "$BaseUrl/$File"
    $Destination = Join-Path $DestinationPath $File
    
    if (Download-File -Url $Url -Destination $Destination) {
        $SuccessCount++
    }
    else {
        $FailCount++
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Download Summary:" -ForegroundColor Cyan
Write-Host "  ✓ Successful: $SuccessCount files" -ForegroundColor Green
if ($FailCount -gt 0) {
    Write-Host "  ✗ Failed: $FailCount files" -ForegroundColor Red
}
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if ($SuccessCount -gt 0) {
    # Check total size
    $TotalSize = (Get-ChildItem -Path $DestinationPath -Recurse | Measure-Object -Property Length -Sum).Sum
    $SizeMB = [math]::Round($TotalSize / 1MB, 2)
    
    Write-Host "✅ Monaco Editor downloaded successfully!" -ForegroundColor Green
    Write-Host "   Location: $DestinationPath" -ForegroundColor Green
    Write-Host "   Total size: $SizeMB MB" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  Note: This is a minimal download with only the core files." -ForegroundColor Yellow
    Write-Host "   Monaco will load additional modules on-demand from CDN if needed." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Run: python manage.py collectstatic --noinput" -ForegroundColor White
    Write-Host "  2. The fallback logic is already in room_monaco.html" -ForegroundColor White
    Write-Host "  3. Test by blocking CDN in browser DevTools" -ForegroundColor White
}
else {
    Write-Host "❌ Download failed!" -ForegroundColor Red
    Write-Host "Please check your internet connection and try again." -ForegroundColor Red
    exit 1
}

