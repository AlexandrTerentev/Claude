@echo off
echo Starting AvtoOpen...
py src/main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Application failed to start!
    echo Make sure you ran install.bat first.
)
pause
