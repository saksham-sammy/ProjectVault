@echo off
title ProjectVault
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ProjectVault exited with code %ERRORLEVEL%.
    pause
)
