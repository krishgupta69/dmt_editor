$ErrorActionPreference = "Stop"

Write-Host "Setting up DMT Video Editor Environment..." -ForegroundColor Cyan

# Check for Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found! Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
$VenvActivate = "$PSScriptRoot\..\venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    . $VenvActivate
} else {
    Write-Host "Failed to find venv activation script." -ForegroundColor Red
    exit 1
}

Write-Host "Installing requirements..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r "$PSScriptRoot\..\requirements.txt"

Write-Host "Note: openshot-qt bindings require specialized installation on Windows." -ForegroundColor Yellow
Write-Host "Depending on your setup, you might need to install OpenShot daily builds and copy libopenshot.pyd into venv/Lib/site-packages/" -ForegroundColor Yellow

Write-Host "Dependencies installed successfully." -ForegroundColor Green
