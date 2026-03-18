@echo off
REM =========================================================================
REM Install Missing Dependencies - Jira Analyzer Suite
REM Installs waitress and pandas for the 3 remaining apps
REM =========================================================================

echo.
echo ========================================================================
echo  Installing Missing Dependencies
echo ========================================================================
echo.

REM Navigate to project root
cd /d "%~dp0"

echo Current directory: %CD%
echo.

REM Check if virtual environment exists
if exist "..\Obeya\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\Obeya\Scripts\activate.bat
    echo.
) else (
    echo WARNING: Virtual environment not found at ..\Obeya\Scripts\activate.bat
    echo Installing to system Python...
    echo.
)

echo Installing missing packages...
echo.

echo [1/2] Installing waitress (for Initiative Viewer and Epic Report)...
pip install waitress
if %ERRORLEVEL% EQU 0 (
    echo ✅ waitress installed successfully
) else (
    echo ❌ Failed to install waitress
)
echo.

echo [2/2] Installing pandas (for Sprint Analyzer)...
pip install pandas
if %ERRORLEVEL% EQU 0 (
    echo ✅ pandas installed successfully  
) else (
    echo ❌ Failed to install pandas
)
echo.

echo ========================================================================
echo  Testing All Imports
echo ========================================================================
echo.

python test_all_imports.py

echo.
echo ========================================================================
echo  Installation Complete
echo ========================================================================
echo.
echo If all 9/9 apps passed, you're ready to go!
echo Run the dashboard: run_dashboard.bat
echo.

pause
