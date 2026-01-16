@echo off
echo ========================================
echo   Aventa HFT Pro 2026 - GUI Launcher
echo ========================================
echo.

cd /d "%~dp0"

python Aventa_HFT_Pro_2026_v7_3_3.py

if errorlevel 1 (
    echo.
    echo Error occurred!
    pause
)
