@echo off
REM =========================================================================
REM Start All Jira Analyzer Suite Applications
REM Launches all 10 services in separate windows
REM =========================================================================

echo.
echo ========================================================================
echo  Starting Jira Analyzer Suite - All 10 Applications
echo ========================================================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if exist "..\Obeya\Scripts\activate.bat" (
    set VENV_ACTIVATE="..\Obeya\Scripts\activate.bat"
) else (
    set VENV_ACTIVATE=""
)

REM Start each application in a new window
echo Starting applications...
echo.

echo [1/10] Starting Unified Dashboard (Port 5000)...
start "Unified Dashboard - 5000" cmd /k "if not %VENV_ACTIVATE%=="""" call %VENV_ACTIVATE% & python apps\unified_dashboard\app.py"
timeout /t 2 /nobreak >nul

echo [2/10] Starting Lead Time Analyzer (Port 5001)...
start "Lead Time Analyzer - 5001" cmd /k "if not %VENV_ACTIVATE%=="""" call %VENV_ACTIVATE% & python apps\lead_time_analyzer\app.py"
timeout /t 2 /nobreak >nul

echo [3/10] Starting Initiative Viewer (Port 5011)...
start "Initiative Viewer - 5011" cmd /k "if not %VENV_ACTIVATE%=="""" call %VENV_ACTIVATE% & python apps\initiative_viewer\app.py"
timeout /t 2 /nobreak >nul

echo [4/10] Starting Epic Report (Port 5002)...
start "Epic Report - 5002" cmd /k "if not %VENV_ACTIVATE%=="""" call %VENV_ACTIVATE% & python apps\epic_report\app.py"
timeout /t 2 /nobreak >nul

echo [5/10] Starting PI Analyzer (Port 5003)...
start "PI Analyzer - 5003" cmd /k "if not %VENV_ACTIVATE%=="""" call %VENV_ACTIVATE% & python apps\pi_analyzer\app.py"
timeout /t 2 /nobreak >nul

echo [6/10] Starting Sprint Analyzer (Port 5004)...
start "Sprint Analyzer - 5004" cmd /k "if not %VENV_ACTIVATE%=="""" call %VENV_ACTIVATE% & python apps\sprint_analyzer\app.py"
timeout /t 2 /nobreak >nul

echo [7/10] Starting PBC Analyzer (Port 5005)...
start "PBC Analyzer - 5005" cmd /k "if not %VENV_ACTIVATE%=="""" call %VENV_ACTIVATE% & python apps\pbc_analyzer\app.py"
timeout /t 2 /nobreak >nul

echo [8/10] Starting Duplicate Detector (Port 5006)...
start "Duplicate Detector - 5006" cmd /k "if not %VENV_ACTIVATE%=="""" call %VENV_ACTIVATE% & python apps\duplicate_detector\app.py"
timeout /t 2 /nobreak >nul

echo [9/10] Starting Psychological Safety (Port 5007)...
start "Psychological Safety - 5007" cmd /k "if not %VENV_ACTIVATE%=="""" call %VENV_ACTIVATE% & python apps\psychological_safety\app.py"
timeout /t 2 /nobreak >nul

echo [10/10] Starting Epic Fix Version (Port 5008)...
start "Epic Fix Version - 5008" cmd /k "if not %VENV_ACTIVATE%=="""" call %VENV_ACTIVATE% & python apps\epic_fixversion\app.py"
timeout /t 2 /nobreak >nul

echo.
echo ========================================================================
echo  All Applications Started!
echo ========================================================================
echo.
echo Main Dashboard: http://localhost:5000
echo.
echo All 10 applications are running in separate windows.
echo Close individual windows to stop each service.
echo.
echo Applications:
echo   1. Unified Dashboard       - http://localhost:5000
echo   2. Lead Time Analyzer      - http://localhost:5001
echo   3. Initiative Viewer       - http://localhost:5011
echo   4. Epic Report             - http://localhost:5002
echo   5. PI Analyzer             - http://localhost:5003
echo   6. Sprint Analyzer         - http://localhost:5004
echo   7. PBC Analyzer            - http://localhost:5005
echo   8. Duplicate Detector      - http://localhost:5006
echo   9. Psychological Safety    - http://localhost:5007
echo  10. Epic Fix Version        - http://localhost:5008
echo.
echo Press any key to open the dashboard in your browser...
pause >nul

start http://localhost:5000

echo.
echo Dashboard opened in browser!
echo.
