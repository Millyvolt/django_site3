# Download Y.js Libraries for Monaco Editor CRDT Integration
# This script downloads Y.js, y-monaco, y-websocket, and y-protocols from npm CDN

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Y.js Libraries Download Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$targetDir = "collab\static\collab\js\yjs"
$tempDir = "temp_yjs_download"

# Library versions (latest stable versions)
$yjsVersion = "13.6.18"
$yMonacoVersion = "0.1.6"
$yWebsocketVersion = "2.0.4"
$yProtocolsVersion = "1.0.6"

# CDN URLs (using jsDelivr for npm packages)
$libraries = @(
    @{
        Name = "yjs"
        Version = $yjsVersion
        Files = @(
            "dist/yjs.mjs",
            "dist/yjs.cjs"
        )
        Url = "https://cdn.jsdelivr.net/npm/yjs@$yjsVersion"
    },
    @{
        Name = "y-monaco"
        Version = $yMonacoVersion
        Files = @(
            "dist/y-monaco.cjs"
        )
        Url = "https://cdn.jsdelivr.net/npm/y-monaco@$yMonacoVersion"
    },
    @{
        Name = "y-websocket"
        Version = $yWebsocketVersion
        Files = @(
            "dist/y-websocket.cjs"
        )
        Url = "https://cdn.jsdelivr.net/npm/y-websocket@$yWebsocketVersion"
    },
    @{
        Name = "y-protocols"
        Version = $yProtocolsVersion
        Files = @(
            "dist/awareness.cjs",
            "dist/sync.cjs"
        )
        Url = "https://cdn.jsdelivr.net/npm/y-protocols@$yProtocolsVersion"
    }
)

# Create directories
Write-Host "Creating directories..." -ForegroundColor Yellow
if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Write-Host "✓ Created $targetDir" -ForegroundColor Green
} else {
    Write-Host "✓ Directory $targetDir already exists" -ForegroundColor Green
}

if (-not (Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
}

Write-Host ""

# Download each library
foreach ($lib in $libraries) {
    Write-Host "Downloading $($lib.Name) v$($lib.Version)..." -ForegroundColor Cyan
    
    foreach ($file in $lib.Files) {
        $url = "$($lib.Url)/$file"
        $fileName = Split-Path $file -Leaf
        $destPath = Join-Path $targetDir $fileName
        
        try {
            Write-Host "  -> Downloading $fileName..." -NoNewline
            Invoke-WebRequest -Uri $url -OutFile $destPath -UseBasicParsing
            $fileSize = (Get-Item $destPath).Length
            $fileSizeKB = [math]::Round($fileSize / 1KB, 2)
            Write-Host " OK ($fileSizeKB KB)" -ForegroundColor Green
        } catch {
            Write-Host " FAILED" -ForegroundColor Red
            Write-Host "    Error: $_" -ForegroundColor Red
        }
    }
    
    Write-Host ""
}

# Download bundled version for browser usage (UMD/ESM)
Write-Host "Downloading browser-compatible bundles..." -ForegroundColor Cyan

# Y.js browser bundle
try {
    Write-Host "  -> Downloading yjs.mjs (ES Module)..." -NoNewline
    $url = "https://cdn.jsdelivr.net/npm/yjs@$yjsVersion/dist/yjs.mjs"
    Invoke-WebRequest -Uri $url -OutFile "$targetDir\yjs.mjs" -UseBasicParsing
    $size = [math]::Round((Get-Item "$targetDir\yjs.mjs").Length / 1KB, 2)
    Write-Host " OK ($size KB)" -ForegroundColor Green
} catch {
    Write-Host " FAILED" -ForegroundColor Red
}

# lib0 (Y.js dependency)
try {
    Write-Host "  -> Downloading lib0 (Y.js dependency)..." -NoNewline
    $url = "https://cdn.jsdelivr.net/npm/lib0@0.2.97/dist/index.cjs"
    Invoke-WebRequest -Uri $url -OutFile "$targetDir\lib0.cjs" -UseBasicParsing
    $size = [math]::Round((Get-Item "$targetDir\lib0.cjs").Length / 1KB, 2)
    Write-Host " OK ($size KB)" -ForegroundColor Green
} catch {
    Write-Host " FAILED" -ForegroundColor Red
}

Write-Host ""

# Clean up temp directory
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Download Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Files saved to: $targetDir" -ForegroundColor Yellow
Write-Host ""

# List downloaded files
Write-Host "Downloaded files:" -ForegroundColor Cyan
Get-ChildItem $targetDir | ForEach-Object {
    $sizeKB = [math]::Round($_.Length / 1KB, 2)
    Write-Host "  * $($_.Name) - $sizeKB KB" -ForegroundColor White
}

Write-Host ""
Write-Host "Total size: $([math]::Round((Get-ChildItem $targetDir | Measure-Object -Property Length -Sum).Sum / 1KB, 2)) KB" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. The files are ready to use as local fallback" -ForegroundColor White
Write-Host "2. CDN will be tried first, then these local files" -ForegroundColor White
Write-Host "3. Test the Monaco Y.js room at /collab/monaco-yjs/<room_name>/" -ForegroundColor White
Write-Host ""

