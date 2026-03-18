@echo off
REM =========================================================================
REM Build All Jira Analytics Suite Applications
REM Creates Windows executables for all 9 applications
REM =========================================================================

echo.
echo ========================================================================
echo  Jira Analytics Suite - Master Build Script
echo ========================================================================
echo.

REM Activate virtual environment if exists
if exist "Obeya\Scripts\activate.bat" (
    echo Activating virtual environment...
    call Obeya\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo WARNING: No virtual environment found. Using system Python.
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller is not installed!
    echo Please install it with: pip install pyinstaller
    echo.
    pause
    exit /b 1
)

REM Run the build script
echo.
echo Starting build process...
echo.

python src\build\build_all.py %*

if errorlevel 1 (
    echo.
    echo ========================================================================
    echo  BUILD FAILED!
    echo ========================================================================
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo  BUILD COMPLETED SUCCESSFULLY!
echo ========================================================================
echo.
echo Executables are located in the 'dist' folder
echo.
pause
