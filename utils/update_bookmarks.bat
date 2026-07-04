@echo off
title FMHY Bookmarks Sync Tool
echo ===================================================
echo   Updating Brave/Chrome/Edge Bookmarks from FMHY
echo ===================================================
echo.

:: Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your system.
    echo Please install Python and make sure it is added to your PATH.
    echo.
    pause
    exit /b 1
)

:: Run script
python "%~dp0update_browser_bookmarks.py"
echo.
pause
