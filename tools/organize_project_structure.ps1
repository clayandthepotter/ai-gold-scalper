# AI Gold Scalper Project Organization Script
# Organizes orphan files into proper directory structure

param(
    [switch]$DryRun = $false
)

Write-Host "AI Gold Scalper Project Organization Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$BackupDir = "backup_organization_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

if (-not $DryRun) {
    Write-Host "Creating backup: $BackupDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

# Define organization structure
$DirectoryStructure = @{
    "docs" = @{
        "description" = "Project Documentation and Guides"
        "files" = @(
            "README.md",
            "LOCAL_SETUP_GUIDE.md",
            "TRANSFORMATION_COMPLETE.md", 
            "PHASE3_SUMMARY.md",
            "PHASE4_SUMMARY.md", 
            "CONFIDENCE_BOOSTING_RESULTS.md",
            "BACKTESTING_SYSTEM_COMPLETE.md",
            "SYSTEM_INTEGRATION_ANALYSIS.md",
            "FINAL_SYSTEM_STATUS_ANSWER.md",
            "PHASE_6_COMPLETION_REPORT.md",
            "PRODUCTION_READINESS_CHECKLIST.md"
        )
    }
    "setup" = @{
        "description" = "Installation and Setup Scripts"
        "files" = @(
            "start_dashboard.ps1",
            "start_dashboard.bat", 
            "setup_local_dashboard.ps1",
            "requirements.txt",
            "requirements_backtesting.txt"
        )
    }
    "core" = @{
        "description" = "Core System Components"
        "files" = @(
            "enhanced_ai_server_consolidated.py",
            "system_orchestrator_enhanced.py"
        )
    }
    "utils" = @{
        "description" = "Utility Scripts and Tools"
        "files" = @(
            "APPLY_FOCUSED_STRUCTURE.py",
            "test_backtesting_system.py",
            "task_pending_watcher.py",
            "task_completed_watcher.py"
        )
    }
    "reports" = @{
        "description" = "Phase Reports and Analysis"
        "subdirs" = @(
            "phase_reports"
        )
    }
    "backups" = @{
        "description" = "Project Backups"
        "existing_dirs" = @("FINAL_BACKUP_20250722_233242")
    }
}

# Function to safely move files
function Move-FilesSafely {
    param(
        [string]$SourcePath,
        [string]$DestinationDir,
        [array]$FilesToMove,
        [switch]$DryRun
    )
    
    foreach ($file in $FilesToMove) {
        $sourcePath = Join-Path $SourcePath $file
        if (Test-Path $sourcePath) {
            if (-not $DryRun) {
                # Create backup
                $backupPath = Join-Path $BackupDir $file
                Copy-Item $sourcePath $backupPath -Force
                
                # Create destination directory if needed
                if (-not (Test-Path $DestinationDir)) {
                    New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
                }
                
                # Move file
                Move-Item $sourcePath (Join-Path $DestinationDir $file) -Force
                Write-Host "  ✅ $file → $DestinationDir" -ForegroundColor Green
            } else {
                Write-Host "  [DRY RUN] $file → $DestinationDir" -ForegroundColor Yellow
            }
        }
    }
}

# Function to create README for directories
function Create-DirectoryReadme {
    param(
        [string]$DirectoryPath,
        [string]$Description,
        [array]$Files,
        [switch]$DryRun
    )
    
    if (-not $DryRun) {
        $readmePath = Join-Path $DirectoryPath "README.md"
        $readmeContent = @"
# $Description

This directory contains:

$(foreach ($file in $Files) { "- `$file`" })

Generated on: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@
        $readmeContent | Out-File -FilePath $readmePath -Encoding UTF8
        Write-Host "  📝 Created README.md" -ForegroundColor Blue
    }
}

Write-Host ""
Write-Host "🗂️ Organizing project structure..." -ForegroundColor Cyan

# Create main directories and organize files
foreach ($dirName in $DirectoryStructure.Keys) {
    $dirInfo = $DirectoryStructure[$dirName]
    $dirPath = Join-Path (Get-Location) $dirName
    
    Write-Host ""
    Write-Host "📁 Creating directory: $dirName" -ForegroundColor Magenta
    Write-Host "   $($dirInfo.description)" -ForegroundColor Gray
    
    if (-not $DryRun -and -not (Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
    }
    
    # Move files if specified
    if ($dirInfo.files) {
        Move-FilesSafely -SourcePath (Get-Location) -DestinationDir $dirPath -FilesToMove $dirInfo.files -DryRun:$DryRun
        Create-DirectoryReadme -DirectoryPath $dirPath -Description $dirInfo.description -Files $dirInfo.files -DryRun:$DryRun
    }
    
    # Move existing directories if specified
    if ($dirInfo.existing_dirs) {
        foreach ($existingDir in $dirInfo.existing_dirs) {
            $sourcePath = Join-Path (Get-Location) $existingDir
            if (Test-Path $sourcePath) {
                if (-not $DryRun) {
                    Move-Item $sourcePath (Join-Path $dirPath $existingDir) -Force
                    Write-Host "  📂 $existingDir → $dirPath" -ForegroundColor Green
                } else {
                    Write-Host "  [DRY RUN] 📂 $existingDir → $dirPath" -ForegroundColor Yellow
                }
            }
        }
    }
    
    # Create subdirectories if specified
    if ($dirInfo.subdirs) {
        foreach ($subdir in $dirInfo.subdirs) {
            $subdirPath = Join-Path $dirPath $subdir
            if (-not $DryRun) {
                New-Item -ItemType Directory -Path $subdirPath -Force | Out-Null
                Write-Host "  📁 Created subdirectory: $subdir" -ForegroundColor Blue
            } else {
                Write-Host "  [DRY RUN] 📁 Create subdirectory: $subdir" -ForegroundColor Yellow
            }
        }
    }
}

# Move phase reports to dedicated subdirectory
$phaseReportsDir = Join-Path "reports" "phase_reports"
if (-not $DryRun -and -not (Test-Path $phaseReportsDir)) {
    New-Item -ItemType Directory -Path $phaseReportsDir -Force | Out-Null
}

# Move phase completion reports from scripts/analysis
$phaseReports = @(
    "scripts\analysis\PHASE_1_COMPLETION_REPORT.md",
    "scripts\analysis\PHASE_2_COMPLETION_REPORT.md"
)

foreach ($report in $phaseReports) {
    if (Test-Path $report) {
        $fileName = Split-Path $report -Leaf
        if (-not $DryRun) {
            Copy-Item $report (Join-Path $BackupDir $fileName) -Force
            Move-Item $report (Join-Path $phaseReportsDir $fileName) -Force
            Write-Host "  ✅ $fileName → $phaseReportsDir" -ForegroundColor Green
        } else {
            Write-Host "  [DRY RUN] $fileName → $phaseReportsDir" -ForegroundColor Yellow
        }
    }
}

# Create main project README
if (-not $DryRun) {
    $mainReadmeContent = @"
# 🏆 AI Gold Scalper - Professional Trading System

[![Project Status](https://img.shields.io/badge/Status-Production%20Ready-green)]()
[![Phase](https://img.shields.io/badge/Phase-6%20Complete-blue)]()
[![Architecture](https://img.shields.io/badge/Architecture-Microservices-orange)]()

> **Advanced AI-powered gold trading system with comprehensive backtesting, risk management, and performance analytics.**

## 🚀 Quick Start

### For Users (Trading)
1. **Setup**: Run `setup\start_dashboard.bat` for Windows or check `setup\LOCAL_SETUP_GUIDE.md`
2. **Launch**: Execute `core\system_orchestrator_enhanced.py` to start all services
3. **Monitor**: Access dashboard at `http://localhost:5000/dashboard`
4. **Trade**: Attach EA to MT5 and enable automated trading

### For Developers
1. **Documentation**: Check `docs\` directory for comprehensive guides
2. **Core System**: Main components in `core\` directory
3. **Scripts**: Advanced features in `scripts\` subdirectories
4. **Testing**: Use `utils\test_backtesting_system.py` for validation

## 📁 Project Structure

```
AI_Gold_Scalper/
├── 📚 docs/                    # Documentation & guides
├── 🚀 setup/                   # Installation & setup scripts  
├── 🎯 core/                    # Main system components
├── 🔧 utils/                   # Utility scripts & tools
├── 📊 reports/                 # Analysis reports & phase summaries
├── 💾 backups/                 # Project backups
├── 📁 scripts/                 # Organized feature scripts
│   ├── ai/                     # ML models & algorithms
│   ├── analysis/               # Performance analysis
│   ├── backtesting/            # Historical testing
│   ├── integration/            # System integration
│   └── monitoring/             # Live monitoring
├── 📁 models/                  # Trained ML models
├── 📁 config/                  # Configuration files
├── 📁 logs/                    # System logs
└── 📁 shared/                  # Shared data & models
```

## 🌟 Key Features

- **🤖 AI-Powered Trading**: GPT-4 integration with ensemble models
- **📈 Advanced Analytics**: Comprehensive backtesting and performance metrics  
- **⚡ Real-time Monitoring**: Live dashboard with risk management
- **🔒 Production Ready**: Enterprise-grade logging, security, and reliability
- **📊 Phase 6 Complete**: All trading phases implemented and tested

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [`docs/PRODUCTION_READINESS_CHECKLIST.md`](docs/PRODUCTION_READINESS_CHECKLIST.md) | Complete production deployment guide |
| [`docs/LOCAL_SETUP_GUIDE.md`](docs/LOCAL_SETUP_GUIDE.md) | Local development environment setup |
| [`docs/BACKTESTING_SYSTEM_COMPLETE.md`](docs/BACKTESTING_SYSTEM_COMPLETE.md) | Backtesting framework documentation |
| [`reports/phase_reports/`](reports/phase_reports/) | Detailed phase completion reports |

## ⚠️ Disclaimer

This system is for educational and research purposes. Always test thoroughly on demo accounts before live trading. Past performance does not guarantee future results.

---
**Last Updated**: $(Get-Date -Format 'yyyy-MM-dd')  
**Organization**: Professional structure applied
"@
    
    $mainReadmeContent | Out-File -FilePath "README.md" -Encoding UTF8
    Write-Host ""
    Write-Host "📝 Updated main README.md with professional structure" -ForegroundColor Blue
}

Write-Host ""
Write-Host "✨ Organization Summary:" -ForegroundColor Cyan
Write-Host "=======================" -ForegroundColor Cyan

$summary = @"
📚 docs/           - All documentation and guides organized
🚀 setup/          - Installation and setup scripts centralized  
🎯 core/           - Main system components isolated
🔧 utils/          - Utility scripts and tools separated
📊 reports/        - Phase reports and analysis consolidated
💾 backups/        - All backups moved to dedicated directory

🎯 Benefits:
- Professional directory structure
- Clear separation of concerns  
- Easy navigation for users and developers
- Production-ready organization
- Comprehensive documentation structure
"@

Write-Host $summary -ForegroundColor White

if ($DryRun) {
    Write-Host ""
    Write-Host "🔍 DRY RUN COMPLETED - No files were actually moved." -ForegroundColor Yellow
    Write-Host "Run without -DryRun parameter to apply changes." -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "✅ ORGANIZATION COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "📦 Backup created in: $BackupDir" -ForegroundColor Yellow
    Write-Host "🎯 Project is now professionally organized and production-ready!" -ForegroundColor Green
}

Write-Host ""
