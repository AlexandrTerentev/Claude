@echo off
echo ========================================
echo Installing AvtoOpen dependencies...
echo ========================================
echo.

py -m pip install -r requirements.txt

echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================
    echo Installation completed successfully!
    echo You can now run the application with run.bat
    echo ========================================
) else (
    echo ========================================
    echo ERROR: Installation failed!
    echo Make sure Python is installed correctly.
    echo Download from: https://www.python.org/downloads/
    echo ========================================
)
echo.
pause
