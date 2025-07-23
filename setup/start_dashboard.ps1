# AI Gold Scalper - Dashboard Deployment Script
# This script starts the Performance Dashboard
# 
# Usage: .\start_dashboard.ps1
# Dashboard will be available at: http://localhost:5555

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 AI GOLD SCALPER - DASHBOARD DEPLOYMENT" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.7+ first." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check if required packages are installed
Write-Host "🔍 Checking required packages..." -ForegroundColor Yellow
$requiredPackages = @("flask", "pandas", "plotly", "numpy")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    try {
        $result = pip show $package 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $package is installed" -ForegroundColor Green
        } else {
            $missingPackages += $package
        }
    } catch {
        $missingPackages += $package
    }
}

# Install missing packages
if ($missingPackages.Count -gt 0) {
    Write-Host "📦 Installing missing packages: $($missingPackages -join ', ')" -ForegroundColor Yellow
    try {
        pip install $missingPackages
        Write-Host "✅ Packages installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install packages. Please run as Administrator." -ForegroundColor Red
        exit 1
    }
}

# Check if dashboard file exists
$dashboardFile = "scripts\monitoring\performance_dashboard.py"
if (-not (Test-Path $dashboardFile)) {
    Write-Host "❌ Dashboard file not found: $dashboardFile" -ForegroundColor Red
    Write-Host "Please ensure you're running this script from the AI_Gold_Scalper directory." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ All prerequisites met!" -ForegroundColor Green
Write-Host ""

# Display startup information
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🎯 DASHBOARD STARTUP INFORMATION" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📊 Dashboard URL: http://localhost:5555" -ForegroundColor White
Write-Host "🔄 Auto-refresh: Every 30 seconds" -ForegroundColor White
Write-Host "📈 Features: Real-time monitoring, Interactive charts" -ForegroundColor White
Write-Host "🛑 Stop dashboard: Press Ctrl+C" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start the dashboard
Write-Host "🚀 Starting AI Gold Scalper Dashboard..." -ForegroundColor Green
Write-Host "Please wait while the dashboard initializes..." -ForegroundColor Yellow
Write-Host ""

try {
    # Start the dashboard
    python $dashboardFile
} catch {
    Write-Host ""
    Write-Host "❌ Error starting dashboard: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "1. Ensure you're running from the AI_Gold_Scalper directory" -ForegroundColor White
    Write-Host "2. Check if port 5555 is available" -ForegroundColor White
    Write-Host "3. Run PowerShell as Administrator" -ForegroundColor White
    Write-Host "4. Check firewall settings" -ForegroundColor White
} finally {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "🛑 DASHBOARD STOPPED" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Thank you for using AI Gold Scalper Dashboard!" -ForegroundColor Green
}
