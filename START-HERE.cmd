@echo off
setlocal
chcp 65001 >nul
title CS50P Assignment Center
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\cs50p-launcher.ps1"
if errorlevel 1 (
    echo.
    echo The CS50P launcher stopped because the environment check failed.
    echo Read the message above, then press any key to close this window.
    pause >nul
)
endlocal
