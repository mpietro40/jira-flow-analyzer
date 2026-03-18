@echo off
REM =========================================================================
REM Build Single Jira Analytics Application
REM Usage: build_single_app.bat [app_name]
REM =========================================================================

if "%1"=="" (
    echo.
    echo Usage: build_single_app.bat [app_name]
    echo        build_single_app.bat --all
    echo.
    echo Available applications:
    echo   unified_dashboard      - Central Dashboard ^(Port 5000^)
    echo   initiative_viewer      - Initiative Viewer ^(Port 5001^)
    echo   epic_report            - Epic Report Generator ^(Port 5002^)
    echo   pi_analyzer            - PI Analyzer ^(Port 5003^)
    echo   sprint_analyzer        - Sprint Analyzer ^(Port 5004^)
    echo   pbc_analyzer           - PBC Analyzer ^(Port 5005^)
    echo   duplicate_detector     - Duplicate Detector ^(Port 5006^)
    echo   psychological_safety   - Psychological Safety ^(Port 5007^)
    echo   epic_fixversion        - Epic Fix Version ^(Port 5008^)
    echo.
    echo Run without arguments to show an interactive menu:
    echo   build_single_app.bat
    echo.
    echo Or run directly:
    echo   python build_executable.py
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo  Building: %1
echo ========================================================================
echo.

REM Activate virtual environment if present
if exist "Obeya\Scripts\activate.bat" (
    call Obeya\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

if "%1"=="--all" (
    python build_executable.py --all
) else (
    python build_executable.py %1
)

if errorlevel 1 (
    echo.
    echo BUILD FAILED!
    pause
    exit /b 1
)

echo.
echo BUILD COMPLETED!
echo.
pause

