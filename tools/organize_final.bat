@echo off
echo =========================================
echo AI Gold Scalper Final Organization
echo =========================================

REM Create directories if they don't exist
if not exist "docs" mkdir "docs"
if not exist "setup" mkdir "setup"
if not exist "core" mkdir "core"  
if not exist "utils" mkdir "utils"
if not exist "tools" mkdir "tools"

echo.
echo Moving documentation files to docs/...

REM Move documentation files
if exist "TRANSFORMATION_COMPLETE.md" move "TRANSFORMATION_COMPLETE.md" "docs\" >nul && echo   MOVED: TRANSFORMATION_COMPLETE.md
if exist "PHASE3_SUMMARY.md" move "PHASE3_SUMMARY.md" "docs\" >nul && echo   MOVED: PHASE3_SUMMARY.md
if exist "PHASE4_SUMMARY.md" move "PHASE4_SUMMARY.md" "docs\" >nul && echo   MOVED: PHASE4_SUMMARY.md
if exist "CONFIDENCE_BOOSTING_RESULTS.md" move "CONFIDENCE_BOOSTING_RESULTS.md" "docs\" >nul && echo   MOVED: CONFIDENCE_BOOSTING_RESULTS.md
if exist "BACKTESTING_SYSTEM_COMPLETE.md" move "BACKTESTING_SYSTEM_COMPLETE.md" "docs\" >nul && echo   MOVED: BACKTESTING_SYSTEM_COMPLETE.md
if exist "SYSTEM_INTEGRATION_ANALYSIS.md" move "SYSTEM_INTEGRATION_ANALYSIS.md" "docs\" >nul && echo   MOVED: SYSTEM_INTEGRATION_ANALYSIS.md
if exist "FINAL_SYSTEM_STATUS_ANSWER.md" move "FINAL_SYSTEM_STATUS_ANSWER.md" "docs\" >nul && echo   MOVED: FINAL_SYSTEM_STATUS_ANSWER.md
if exist "PHASE_6_COMPLETION_REPORT.md" move "PHASE_6_COMPLETION_REPORT.md" "docs\" >nul && echo   MOVED: PHASE_6_COMPLETION_REPORT.md
if exist "PRODUCTION_READINESS_CHECKLIST.md" move "PRODUCTION_READINESS_CHECKLIST.md" "docs\" >nul && echo   MOVED: PRODUCTION_READINESS_CHECKLIST.md

echo.
echo Moving setup files to setup/...

REM Move setup files
if exist "start_dashboard.bat" move "start_dashboard.bat" "setup\" >nul && echo   MOVED: start_dashboard.bat
if exist "setup_local_dashboard.ps1" move "setup_local_dashboard.ps1" "setup\" >nul && echo   MOVED: setup_local_dashboard.ps1
if exist "requirements_backtesting.txt" move "requirements_backtesting.txt" "setup\" >nul && echo   MOVED: requirements_backtesting.txt

echo.
echo Moving core system files to core/...

REM Move core files
if exist "system_orchestrator_enhanced.py" move "system_orchestrator_enhanced.py" "core\" >nul && echo   MOVED: system_orchestrator_enhanced.py

echo.
echo Moving utility files to utils/...

REM Move utility files
if exist "test_backtesting_system.py" move "test_backtesting_system.py" "utils\" >nul && echo   MOVED: test_backtesting_system.py
if exist "task_pending_watcher.py" move "task_pending_watcher.py" "utils\" >nul && echo   MOVED: task_pending_watcher.py
if exist "task_completed_watcher.py" move "task_completed_watcher.py" "utils\" >nul && echo   MOVED: task_completed_watcher.py

echo.
echo Moving organization scripts to tools/...

REM Move organization tools
if exist "organize_project_structure.ps1" move "organize_project_structure.ps1" "tools\" >nul && echo   MOVED: organize_project_structure.ps1
if exist "organize_clean.ps1" move "organize_clean.ps1" "tools\" >nul && echo   MOVED: organize_clean.ps1
if exist "complete_organization.ps1" move "complete_organization.ps1" "tools\" >nul && echo   MOVED: complete_organization.ps1

echo.
echo =========================================
echo Organization Summary:
echo =========================================
echo.
echo docs/      - All documentation files organized
echo setup/     - Installation and setup scripts centralized
echo core/      - Main system components isolated  
echo utils/     - Utility scripts organized
echo tools/     - Organization scripts archived
echo.
echo PROFESSIONAL STRUCTURE ACHIEVED!
echo - Clear separation of concerns
echo - Easy navigation for users and developers
echo - Production-ready organization
echo - All orphan files organized
echo.
echo AI Gold Scalper is now professionally organized!
echo =========================================

pause
