# Monaco Editor Full Download Script
# Downloads complete Monaco Editor package from npm
# Version: 0.54.0

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Monaco Editor Full Download Script" -ForegroundColor Cyan
Write-Host "Version: 0.54.0" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$MonacoVersion = "0.54.0"
$TempDir = "temp_monaco_download"
$DestinationPath = "collab\static\collab\monaco"
$ZipUrl = "https://registry.npmjs.org/monaco-editor/-/monaco-editor-$MonacoVersion.tgz"

# Check if destination already exists
if (Test-Path "$DestinationPath\vs") {
    Write-Host "WARNING: Monaco files already exist at: $DestinationPath\vs" -ForegroundColor Yellow
    $response = Read-Host "Do you want to re-download? (y/n)"
    if ($response -ne 'y') {
        Write-Host "Aborted. Using existing files." -ForegroundColor Yellow
        exit 0
    }
    Write-Host "Removing existing files..." -ForegroundColor Yellow
    Remove-Item -Path "$DestinationPath\vs" -Recurse -Force -ErrorAction SilentlyContinue
}

# Create temp directory
Write-Host "Creating temporary directory..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

try {
    # Download the package
    Write-Host "Downloading Monaco Editor package..." -ForegroundColor Green
    Write-Host "   URL: $ZipUrl" -ForegroundColor Gray
    Write-Host "   This may take 1-3 minutes..." -ForegroundColor Yellow
    Write-Host ""
    
    $TgzFile = Join-Path $TempDir "monaco.tgz"
    Invoke-WebRequest -Uri $ZipUrl -OutFile $TgzFile -ErrorAction Stop
    
    Write-Host "[SUCCESS] Download complete!" -ForegroundColor Green
    
    # Check file size
    $FileSize = (Get-Item $TgzFile).Length / 1MB
    Write-Host "   Downloaded: $([math]::Round($FileSize, 2)) MB" -ForegroundColor Gray
    Write-Host ""
    
    # Extract using tar (built into Windows 10+)
    Write-Host "Extracting package..." -ForegroundColor Green
    
    Push-Location $TempDir
    tar -xzf "monaco.tgz" 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: tar extraction failed, trying alternative method..." -ForegroundColor Yellow
        
        # Fallback: Try using 7-Zip if available
        $7zipPath = "C:\Program Files\7-Zip\7z.exe"
        if (Test-Path $7zipPath) {
            & $7zipPath x "monaco.tgz" -so | & $7zipPath x -si -ttar
        }
        else {
            throw "Could not extract .tgz file. Please install 7-Zip or use Windows 10+ with built-in tar support."
        }
    }
    
    Pop-Location
    
    Write-Host "[SUCCESS] Extraction complete!" -ForegroundColor Green
    Write-Host ""
    
    # Copy the vs folder
    Write-Host "Copying Monaco files..." -ForegroundColor Green
    
    $SourceVs = Join-Path $TempDir "package\min\vs"
    
    if (-not (Test-Path $SourceVs)) {
        throw "Could not find vs folder in extracted package"
    }
    
    # Create destination directory
    New-Item -ItemType Directory -Force -Path $DestinationPath | Out-Null
    
    # Copy vs folder
    Copy-Item -Path $SourceVs -Destination $DestinationPath -Recurse -Force
    
    Write-Host "[SUCCESS] Files copied successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Calculate final size
    $TotalSize = (Get-ChildItem -Path "$DestinationPath\vs" -Recurse | Measure-Object -Property Length -Sum).Sum
    $SizeMB = [math]::Round($TotalSize / 1MB, 2)
    
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "Monaco Editor downloaded and installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Location: $DestinationPath\vs" -ForegroundColor White
    Write-Host "Size: $SizeMB MB" -ForegroundColor White
    Write-Host "Files: $(( Get-ChildItem -Path "$DestinationPath\vs" -Recurse -File | Measure-Object).Count)" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. [DONE] Local Monaco files are ready" -ForegroundColor Green
    Write-Host "  2. [DONE] Fallback logic already in room_monaco.html" -ForegroundColor Green  
    Write-Host "  3. Start server and test!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Testing:" -ForegroundColor Cyan
    Write-Host "  - Normal: CDN will load (fast)" -ForegroundColor White
    Write-Host "  - Block CDN: Local files will load automatically" -ForegroundColor White
    Write-Host "  - Offline: Local files will work" -ForegroundColor White
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Red
    Write-Host "ERROR" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Red
    Write-Host "Failed to download Monaco Editor: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check internet connection" -ForegroundColor White
    Write-Host "  2. Try running as Administrator" -ForegroundColor White
    Write-Host "  3. Check if Windows 10+ (tar built-in)" -ForegroundColor White
    Write-Host "  4. Install 7-Zip as fallback" -ForegroundColor White
    Write-Host ""
    exit 1
}
finally {
    # Cleanup temp directory
    if (Test-Path $TempDir) {
        Write-Host "Cleaning up temporary files..." -ForegroundColor Gray
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Done!" -ForegroundColor Green

