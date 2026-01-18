@echo off
REM Aventa HFT Pro 2026 - Code Signing Script
REM This script signs the executable and installer with a code signing certificate

echo ========================================
echo Aventa HFT Pro 2026 - Code Signing
echo ========================================

REM Check if signtool is available
where signtool >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: signtool not found in PATH
    echo.
    echo Please install Windows SDK or Visual Studio Build Tools
    echo Download from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/
    echo.
    pause
    exit /b 1
)

set EXE_NAME=Aventa_HFT_Pro_2026_v7_3_3.exe
set SETUP_NAME=Aventa_HFT_Pro_2026_v7_3_3_setup.exe
set CERT_THUMBPRINT=3152A250B85E1AB0CDD1804146D80DC2D1EF1984

echo.
echo Signing executable: %EXE_NAME%
signtool sign /fd SHA256 /sha1 %CERT_THUMBPRINT% %EXE_NAME%

if %ERRORLEVEL% EQU 0 (
    echo ✓ Executable signed successfully
) else (
    echo ✗ Failed to sign executable
    pause
    exit /b 1
)

echo.
echo Verifying signature...
signtool verify /pa %EXE_NAME%

if %ERRORLEVEL% EQU 0 (
    echo ✓ Signature verified
) else (
    echo ✗ Signature verification failed
)

echo.
echo ========================================
echo Code signing completed!
echo ========================================
echo.
echo Next steps for production:
echo 1. Purchase commercial code signing certificate from:
echo    - DigiCert (recommended)
echo    - GlobalSign
echo    - Sectigo
echo    - Comodo
echo.
echo 2. Update SignTool directive in AventaHFT733.iss:
echo    SignTool=signtool sign /fd SHA256 /t http://timestamp.digicert.com /n "PT Aventa Intelligent Power" $f
echo.
echo 3. For EV certificate (green publisher name):
echo    SignTool=signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /n "PT Aventa Intelligent Power" $f
echo.
pause