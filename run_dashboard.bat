@echo off
REM =========================================================================
REM Run Unified Dashboard - Jira Analyzer Suite
REM Main entry point for the Jira Analytics Suite
REM =========================================================================

echo.
echo ========================================================================
echo  Starting Jira Analytics Suite - Unified Dashboard
echo ========================================================================
echo.

REM Navigate to project root
cd /d "%~dp0"

REM Check if virtual environment exists and activate it
if exist "..\Obeya\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\Obeya\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found. Using system Python.
)

echo.
echo Starting Unified Dashboard on http://localhost:5000
echo Press Ctrl+C to stop
echo.

REM Run the dashboard
python apps\unified_dashboard\app.py

pause
