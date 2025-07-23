@echo off
echo ============================================================
echo 🚀 AI GOLD SCALPER - DASHBOARD DEPLOYMENT
echo ============================================================
echo.

echo 🔍 Starting AI Gold Scalper Performance Dashboard...
echo.
echo 📊 Dashboard URL: http://localhost:5555
echo 🔄 Auto-refresh: Every 30 seconds  
echo 📈 Features: Real-time monitoring, Interactive charts
echo 🛑 Stop dashboard: Press Ctrl+C
echo.
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.7+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if dashboard file exists
if not exist "scripts\monitoring\performance_dashboard.py" (
    echo ❌ Dashboard file not found!
    echo Please ensure you're running this from the AI_Gold_Scalper directory.
    pause
    exit /b 1
)

echo 🚀 Starting dashboard...
echo.

REM Start the dashboard
python scripts\monitoring\performance_dashboard.py

echo.
echo ============================================================
echo 🛑 DASHBOARD STOPPED
echo ============================================================
echo Thank you for using AI Gold Scalper Dashboard!
pause
