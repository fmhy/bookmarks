@echo off
:: Headless runner for FMHY Bookmarks Sync Scheduler
cd /d "%~dp0"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd'"') do set today=%%i

if exist last_run.txt (
    findstr /C:"%today%" last_run.txt >nul 2>&1 && exit /b 0
)

where uv >nul 2>&1
if %errorlevel% equ 0 (
    uv run python update_browser_bookmarks.py --non-interactive
) else (
    python update_browser_bookmarks.py --non-interactive
)

if not errorlevel 1 (
    echo %today%> last_run.txt
)
exit /b %errorlevel%
