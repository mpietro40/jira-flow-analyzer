@echo off
REM =========================================================================
REM Clean Build Artifacts
REM Removes all build and dist folders
REM =========================================================================

echo.
echo ========================================================================
echo  Cleaning Build Artifacts
echo ========================================================================
echo.

REM Activate virtual environment if exists
if exist "Obeya\Scripts\activate.bat" (
    call Obeya\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo Removing build artifacts...
python src\build\build_all.py --clean-only

echo.
echo ========================================================================
echo  Cleanup Complete
echo ========================================================================
echo.
pause
