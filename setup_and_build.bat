@echo off
REM =============================================================================
REM  setup_and_build.bat
REM  One-shot script: install dependencies from PyPI, then build an executable.
REM
REM  Usage:
REM    setup_and_build.bat                   <- interactive app menu
REM    setup_and_build.bat initiative_viewer <- build specific app
REM    setup_and_build.bat --all             <- build every app
REM
REM  On a fresh clone this script:
REM    1. Creates a virtual environment (Obeya\) if it does not exist
REM    2. Installs all packages from requirements-build.txt (from PyPI)
REM    3. Runs build_executable.py to produce dist\<AppName>.exe
REM
REM  Nothing from dist\ or build\ is committed to git — only source code is.
REM  Re-run this script any time to rebuild after a git pull.
REM =============================================================================

setlocal EnableDelayedExpansion

echo.
echo  =========================================================================
echo   Jira Analytics Suite — Setup ^& Build
echo  =========================================================================
echo.

REM ── 1. Locate or create virtual environment ──────────────────────────────────
set VENV_DIR=Obeya

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo  [1/3] Creating virtual environment in %VENV_DIR%\ ...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo.
        echo  ERROR: Could not create virtual environment.
        echo         Make sure Python 3.10+ is installed and on your PATH.
        pause
        exit /b 1
    )
    echo        Done.
) else (
    echo  [1/3] Virtual environment already exists in %VENV_DIR%\
)

set PYTHON=%VENV_DIR%\Scripts\python.exe
set PIP=%VENV_DIR%\Scripts\pip.exe

REM ── 2. Install / update packages from PyPI ───────────────────────────────────
echo.
echo  [2/3] Installing packages from requirements-build.txt ...
echo        (downloads from PyPI — internet connection required)
echo.
%PIP% install --upgrade pip --quiet
%PIP% install -r requirements-build.txt

if errorlevel 1 (
    echo.
    echo  ERROR: Package installation failed.
    echo         Check your internet connection and try again.
    pause
    exit /b 1
)
echo.
echo        Packages installed successfully.

REM ── 3. Build the executable ───────────────────────────────────────────────────
echo.
echo  [3/3] Building executable ...
echo.

if "%1"=="" (
    REM No argument → let build_executable.py show the interactive menu
    %PYTHON% build_executable.py
) else if "%1"=="--all" (
    %PYTHON% build_executable.py --all
) else (
    %PYTHON% build_executable.py %1
)

if errorlevel 1 (
    echo.
    echo  BUILD FAILED. See output above for details.
    pause
    exit /b 1
)

echo.
echo  =========================================================================
echo   Finished. Executables are in the dist\ folder.
echo  =========================================================================
echo.
pause
