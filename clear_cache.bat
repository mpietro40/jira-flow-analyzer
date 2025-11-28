@echo off
echo Clearing analysis cache...
del /Q analysis_cache\*.json 2>nul
echo Cache cleared! Run your analysis again to see projects.
pause
