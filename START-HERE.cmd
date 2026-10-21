@echo off
setlocal
chcp 65001 >nul
title CS50P Assignment Center
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\cs50p-launcher.ps1"
if errorlevel 1 pause
endlocal
