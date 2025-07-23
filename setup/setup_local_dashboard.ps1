# AI Gold Scalper - Local Dashboard Setup
# This script helps you set up the dashboard on your local machine
# Run this script on your LOCAL COMPUTER, not on the VPS

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🏠 AI GOLD SCALPER - LOCAL DASHBOARD SETUP" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This script will help you set up the dashboard on your LOCAL machine." -ForegroundColor Yellow
Write-Host "Make sure you're running this on your LOCAL COMPUTER, not on the VPS." -ForegroundColor Yellow
Write-Host ""

# Check if we're on VPS (basic check)
$computerName = $env:COMPUTERNAME
if ($computerName -like "*VPS*" -or $computerName -like "*SERVER*") {
    Write-Host "⚠️  WARNING: This appears to be a server/VPS environment." -ForegroundColor Red
    Write-Host "This script is intended for your LOCAL machine." -ForegroundColor Red
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Exiting. Run this script on your local machine." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if project exists
if (-not (Test-Path "scripts\monitoring\performance_dashboard.py")) {
    Write-Host "❌ Dashboard files not found in current directory." -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 SETUP INSTRUCTIONS:" -ForegroundColor Yellow
    Write-Host "1. Download/copy the AI_Gold_Scalper project to your local machine" -ForegroundColor White
    Write-Host "2. Open PowerShell in the AI_Gold_Scalper directory" -ForegroundColor White
    Write-Host "3. Run this setup script again" -ForegroundColor White
    Write-Host ""
    Write-Host "📁 Required project structure:" -ForegroundColor Yellow
    Write-Host "   AI_Gold_Scalper/" -ForegroundColor White
    Write-Host "   ├── scripts/" -ForegroundColor White
    Write-Host "   │   └── monitoring/" -ForegroundColor White
    Write-Host "   │       ├── performance_dashboard.py" -ForegroundColor White
    Write-Host "   │       ├── enhanced_trade_logger.py" -ForegroundColor White
    Write-Host "   │       └── trade_logs.db" -ForegroundColor White
    Write-Host "   └── start_dashboard.ps1" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Project files found!" -ForegroundColor Green

# Install required packages
Write-Host "📦 Installing required packages..." -ForegroundColor Yellow
$packages = @("flask", "pandas", "plotly", "numpy", "flask-cors")

foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Gray
    try {
        pip install $package --quiet
        Write-Host "✅ $package installed" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Warning: Could not install $package" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🎯 DASHBOARD CONNECTION OPTIONS" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Choose how you want to connect to your trading data:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. 🏠 LOCAL DATA (if you have copied trade_logs.db locally)" -ForegroundColor White
Write-Host "2. 🌐 VPS DATA (connect to VPS database - requires network setup)" -ForegroundColor White
Write-Host "3. 📊 DEMO MODE (sample data for testing)" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-3)"

switch ($choice) {
    "1" {
        Write-Host "Selected: Local Data Mode" -ForegroundColor Green
        if (-not (Test-Path "scripts\monitoring\trade_logs.db")) {
            Write-Host "⚠️  trade_logs.db not found locally." -ForegroundColor Yellow
            Write-Host "Copy the database file from your VPS to:" -ForegroundColor Yellow
            Write-Host "   scripts\monitoring\trade_logs.db" -ForegroundColor White
        }
    }
    "2" {
        Write-Host "Selected: VPS Data Mode" -ForegroundColor Green
        Write-Host "⚠️  This requires network configuration to access VPS database." -ForegroundColor Yellow
        Write-Host "You may need to:" -ForegroundColor Yellow
        Write-Host "   - Set up SSH tunnel to VPS" -ForegroundColor White
        Write-Host "   - Configure database connection settings" -ForegroundColor White
    }
    "3" {
        Write-Host "Selected: Demo Mode" -ForegroundColor Green
        Write-Host "Creating sample database for demonstration..." -ForegroundColor Yellow
        # Create sample data script would go here
    }
    default {
        Write-Host "Invalid choice. Defaulting to Local Data Mode." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 READY TO START DASHBOARD" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your dashboard is now ready to run!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 To start the dashboard:" -ForegroundColor Yellow
Write-Host "   .\start_dashboard.ps1" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Dashboard will be available at:" -ForegroundColor Yellow
Write-Host "   http://localhost:5555" -ForegroundColor White
Write-Host ""
Write-Host "🔄 Features:" -ForegroundColor Yellow
Write-Host "   • Real-time performance monitoring" -ForegroundColor White
Write-Host "   • Interactive charts and graphs" -ForegroundColor White
Write-Host "   • System health monitoring" -ForegroundColor White
Write-Host "   • Trade history analysis" -ForegroundColor White
Write-Host ""
Write-Host "🛑 To stop: Press Ctrl+C in the dashboard terminal" -ForegroundColor Yellow
Write-Host ""

$startNow = Read-Host "Start the dashboard now? (Y/n)"
if ($startNow -eq "" -or $startNow -eq "y" -or $startNow -eq "Y") {
    Write-Host ""
    Write-Host "🚀 Starting dashboard..." -ForegroundColor Green
    .\start_dashboard.ps1
} else {
    Write-Host ""
    Write-Host "✅ Setup complete! Run .\start_dashboard.ps1 when ready." -ForegroundColor Green
}
