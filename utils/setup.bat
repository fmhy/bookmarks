@echo off
title FMHY Bookmarks Sync Setup Wizard
cd /d "%~dp0"

:: Self-elevate the script to run as Administrator (needed for Task Scheduler registration)
fsutil dirty query %systemdrive% >nul 2>&1
if %errorlevel% equ 0 goto ADMIN_OK
echo [INFO] Requesting Administrator privileges...
powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
exit /b
:ADMIN_OK

echo ===================================================
echo     FMHY Bookmarks Sync - Setup Wizard
echo ===================================================
echo.

:: Check if Python is installed
where python >nul 2>&1
if %errorlevel% equ 0 goto PYTHON_OK
echo [ERROR] Python was not found on your system.
echo Please install Python and make sure it is added to your PATH.
echo.
pause
exit /b 1
:PYTHON_OK

:: Check if config.json exists
set config_exists=0
if exist "%~dp0config.json" set config_exists=1

:: Check if scheduled task exists
set task_exists=0
schtasks /query /tn "FMHY_Bookmarks_Sync" >nul 2>&1
if %errorlevel% equ 0 set task_exists=1

set reconfig=n

if %config_exists% equ 1 echo [INFO] Configuration file (config.json) already exists.
if %config_exists% equ 1 echo.
if %config_exists% equ 1 set /p reconfig="Would you like to overwrite it? [y/n] [default: n]: "

if /i "%reconfig%"=="y" goto RUN_CONFIG

:: User chose not to reconfigure: check if task is already configured too
if %config_exists% equ 1 if %task_exists% equ 1 goto SKIP_ALL
if %config_exists% equ 1 goto REGISTER_TASK

:RUN_CONFIG
echo.
echo ===================================================
echo   Step 1: Configuration Wizard
echo ===================================================
echo.
python "%~dp0create_config.py"
if %errorlevel% equ 0 goto CONFIG_OK
echo.
echo [ERROR] Configuration setup failed or was cancelled.
pause
exit /b 1
:CONFIG_OK

:REGISTER_TASK
echo.
echo ===================================================
echo   Step 2: Windows Task Scheduler Registration
echo ===================================================
echo.

set /p interval="Enter the sync interval in days [default: 3]: "
if "%interval%"=="" set interval=3

:: Validate that interval is numeric and positive
echo %interval%| findstr /r "^[0-9][0-9]*$" >nul
if %errorlevel% neq 0 set interval=3
if %interval% lss 1 set interval=3

:: Get parent directory of script (repo root)
for %%i in ("%~dp0..") do set "ROOT_DIR=%%~fi"

echo.
echo [INFO] Creating scheduled task to trigger every %interval% day(s).
echo [INFO] (Uses '-StartWhenAvailable' so it runs automatically anytime your PC is on).
echo [INFO] Target script: %ROOT_DIR%\utils\run_sync.bat
echo.
powershell -Command "$action = New-ScheduledTaskAction -Execute '%ROOT_DIR%\utils\run_sync.bat' -WorkingDirectory '%ROOT_DIR%\utils'; $triggers = @(New-ScheduledTaskTrigger -Daily -DaysInterval %interval% -At '09:00'); $settings = New-ScheduledTaskSettingsSet -Compatibility Win8 -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; $task = New-ScheduledTask -Action $action -Trigger $triggers -Settings $settings; $task.Settings.Hidden = $true; Register-ScheduledTask -TaskName 'FMHY_Bookmarks_Sync' -InputObject $task -Force"
goto REGISTRATION_RESULT

:REGISTRATION_RESULT
if %errorlevel% equ 0 goto REGISTRATION_SUCCESS
goto REGISTRATION_FAILED

:SKIP_ALL
echo.
echo ===================================================
echo  [INFO] Configuration and Scheduled Task Kept Intact
echo  Everything is already set up and scheduled!
echo ===================================================
goto REGISTRATION_FINISH

:REGISTRATION_SUCCESS
echo.
echo ===================================================
echo  [SUCCESS] Setup Completed Successfully!
echo  The bookmarks will now automatically sync every %interval% day(s).
echo ===================================================
goto REGISTRATION_FINISH

:REGISTRATION_FAILED
echo.
echo [ERROR] Failed to register task.
goto REGISTRATION_FINISH

:REGISTRATION_FINISH
echo.
pause
