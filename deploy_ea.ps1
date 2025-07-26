# AI Gold Scalper EA Deployment Script
# This script copies the EA files to your MetaTrader 5 installation

param(
    [string]$MetaTraderPath = "",
    [switch]$AutoDetect = $false,
    [switch]$Help = $false
)

# Display help information
if ($Help) {
    Write-Host "AI Gold Scalper EA Deployment Script" -ForegroundColor Green
    Write-Host "Usage: .\deploy_ea.ps1 [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -MetaTraderPath <path>  Specify MetaTrader 5 Experts directory path"
    Write-Host "  -AutoDetect             Automatically detect MetaTrader 5 installation"
    Write-Host "  -Help                   Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Magenta
    Write-Host "  .\deploy_ea.ps1 -AutoDetect"
    Write-Host "  .\deploy_ea.ps1 -MetaTraderPath 'C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts'"
    exit 0
}

Write-Host "AI Gold Scalper EA Deployment Script" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Get current script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$EASourceDir = Join-Path $ScriptDir "EA"

# Check if EA source directory exists
if (-not (Test-Path $EASourceDir)) {
    Write-Host "ERROR: EA source directory not found at: $EASourceDir" -ForegroundColor Red
    Write-Host "Please ensure you're running this script from the AI_Gold_Scalper directory." -ForegroundColor Yellow
    exit 1
}

# Function to find MetaTrader 5 installations
function Find-MetaTraderInstallations {
    $installations = @()
    $metaQuotesPath = "$env:APPDATA\MetaQuotes\Terminal"
    
    if (Test-Path $metaQuotesPath) {
        $terminals = Get-ChildItem $metaQuotesPath -Directory
        foreach ($terminal in $terminals) {
            $expertsPath = Join-Path $terminal.FullName "MQL5\Experts"
            if (Test-Path $expertsPath) {
                $installations += @{
                    Path = $expertsPath
                    TerminalId = $terminal.Name
                }
            }
        }
    }
    
    return $installations
}

# Auto-detect MetaTrader installations if requested
if ($AutoDetect -or [string]::IsNullOrEmpty($MetaTraderPath)) {
    Write-Host "Searching for MetaTrader 5 installations..." -ForegroundColor Yellow
    $installations = Find-MetaTraderInstallations
    
    if ($installations.Count -eq 0) {
        Write-Host "ERROR: No MetaTrader 5 installations found." -ForegroundColor Red
        Write-Host "Please specify the path manually using -MetaTraderPath parameter." -ForegroundColor Yellow
        exit 1
    }
    
    if ($installations.Count -eq 1) {
        $MetaTraderPath = $installations[0].Path
        Write-Host "Found MetaTrader 5 installation: $MetaTraderPath" -ForegroundColor Green
    } else {
        Write-Host "Multiple MetaTrader 5 installations found:" -ForegroundColor Yellow
        for ($i = 0; $i -lt $installations.Count; $i++) {
            Write-Host "  [$($i + 1)] $($installations[$i].Path)" -ForegroundColor Cyan
            Write-Host "      Terminal ID: $($installations[$i].TerminalId)" -ForegroundColor Gray
        }
        
        do {
            $choice = Read-Host "Select installation (1-$($installations.Count))"
            $choiceNum = 0
            if ([int]::TryParse($choice, [ref]$choiceNum) -and $choiceNum -ge 1 -and $choiceNum -le $installations.Count) {
                $MetaTraderPath = $installations[$choiceNum - 1].Path
                break
            }
            Write-Host "Invalid selection. Please enter a number between 1 and $($installations.Count)." -ForegroundColor Red
        } while ($true)
    }
}

# Validate MetaTrader path
if ([string]::IsNullOrEmpty($MetaTraderPath) -or -not (Test-Path $MetaTraderPath)) {
    Write-Host "ERROR: Invalid MetaTrader 5 Experts directory path: $MetaTraderPath" -ForegroundColor Red
    Write-Host "Please check the path and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Deployment Configuration:" -ForegroundColor Cyan
Write-Host "  Source Directory: $EASourceDir" -ForegroundColor White
Write-Host "  Target Directory: $MetaTraderPath" -ForegroundColor White
Write-Host ""

# List files to be copied
$filesToCopy = @(
    "AI_Gold_Scalper.mq5",
    "AI_Gold_Scalper.ex5",
    "EA_Trade_Logger.mq5"
)

$serverFiles = @(
    "enhanced_logging.mq5",
    "ml_integration.mq5",
    "performance_analytics.mq5",
    "risk_management_enhanced.mq5",
    "telegram_alerts_addon.mq5",
    "trade_journal_addon.mq5"
)

Write-Host "Files to be deployed:" -ForegroundColor Yellow
foreach ($file in $filesToCopy) {
    if (Test-Path (Join-Path $EASourceDir $file)) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (missing)" -ForegroundColor Red
    }
}

$serverDir = Join-Path $EASourceDir "server"
if (Test-Path $serverDir) {
    Write-Host "  Server modules:" -ForegroundColor Cyan
    foreach ($file in $serverFiles) {
        if (Test-Path (Join-Path $serverDir $file)) {
            Write-Host "    ✓ $file" -ForegroundColor Green
        } else {
            Write-Host "    ✗ $file (missing)" -ForegroundColor Red
        }
    }
}

Write-Host ""
$confirm = Read-Host "Proceed with deployment? (Y/N)"
if ($confirm -notmatch '^[Yy]') {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}

# Create backup directory
$backupDir = Join-Path $MetaTraderPath "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$createBackup = $false

# Check if any files already exist and create backup if needed
foreach ($file in $filesToCopy) {
    $targetFile = Join-Path $MetaTraderPath $file
    if (Test-Path $targetFile) {
        if (-not $createBackup) {
            Write-Host "Existing files found. Creating backup..." -ForegroundColor Yellow
            New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
            $createBackup = $true
        }
        Copy-Item $targetFile $backupDir -Force
        Write-Host "  Backed up: $file" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Copying EA files..." -ForegroundColor Yellow

# Copy main EA files
$copyCount = 0
$errorCount = 0

foreach ($file in $filesToCopy) {
    $sourceFile = Join-Path $EASourceDir $file
    $targetFile = Join-Path $MetaTraderPath $file
    
    if (Test-Path $sourceFile) {
        try {
            Copy-Item $sourceFile $targetFile -Force
            Write-Host "  ✓ Copied: $file" -ForegroundColor Green
            $copyCount++
        } catch {
            Write-Host "  ✗ Failed to copy: $file - $($_.Exception.Message)" -ForegroundColor Red
            $errorCount++
        }
    } else {
        Write-Host "  ✗ Source file not found: $file" -ForegroundColor Red
        $errorCount++
    }
}

# Copy server modules
if (Test-Path $serverDir) {
    foreach ($file in $serverFiles) {
        $sourceFile = Join-Path $serverDir $file
        $targetFile = Join-Path $MetaTraderPath $file
        
        if (Test-Path $sourceFile) {
            try {
                Copy-Item $sourceFile $targetFile -Force
                Write-Host "  ✓ Copied: $file" -ForegroundColor Green
                $copyCount++
            } catch {
                Write-Host "  ✗ Failed to copy: $file - $($_.Exception.Message)" -ForegroundColor Red
                $errorCount++
            }
        }
    }
}

Write-Host ""
Write-Host "Deployment Summary:" -ForegroundColor Cyan
Write-Host "  Files copied: $copyCount" -ForegroundColor Green
Write-Host "  Errors: $errorCount" -ForegroundColor $(if ($errorCount -eq 0) { "Green" } else { "Red" })

if ($createBackup) {
    Write-Host "  Backup created: $backupDir" -ForegroundColor Yellow
}

if ($errorCount -eq 0) {
    Write-Host ""
    Write-Host "✓ Deployment completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Open MetaTrader 5" -ForegroundColor White
    Write-Host "2. Go to Tools → Options → Expert Advisors" -ForegroundColor White
    Write-Host "3. Add these URLs to WebRequest whitelist:" -ForegroundColor White
    Write-Host "   - http://127.0.0.1:5000" -ForegroundColor Gray
    Write-Host "   - https://api.openai.com" -ForegroundColor Gray
    Write-Host "   - https://api.telegram.org" -ForegroundColor Gray
    Write-Host "4. Start the AI server: python core/consolidated_ai_server.py" -ForegroundColor White
    Write-Host "5. Attach AI_Gold_Scalper to a Gold (XAUUSD) chart" -ForegroundColor White
    Write-Host ""
    Write-Host "For detailed instructions, see INSTALLATION_GUIDE.md" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "⚠ Deployment completed with errors. Please check the error messages above." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
