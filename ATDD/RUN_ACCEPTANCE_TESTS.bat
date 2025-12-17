@echo off
REM Batch script to run all acceptance tests for the Jira Lead Time Analyzer

echo ========================================
echo Running Acceptance Tests
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo.
echo Running all acceptance tests...
echo.

pytest ATDD/acceptance_tests/ -v --tb=short

echo.
echo ========================================
echo Running with coverage report...
echo ========================================
echo.

pytest ATDD/acceptance_tests/ -v --cov=. --cov-report=html --cov-report=term

echo.
echo ========================================
echo Test execution complete!
echo Coverage report generated in htmlcov/index.html
echo ========================================
echo.

pause
