@echo off
setlocal

echo ============================================================
echo  AVENTA HFT PRO 2026 - AUTO ENV LAUNCHER
echo ============================================================
echo.

REM ============================================================
REM 1. CEK PYTHON
REM ============================================================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak terdeteksi di sistem
    pause
    exit /b 1
)

REM ============================================================
REM 2. BUAT VENV JIKA BELUM ADA
REM ============================================================
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Virtual environment tidak ditemukan
    echo [INFO] Membuat virtual environment...
    python -m venv venv

    if %errorlevel% neq 0 (
        echo [ERROR] Gagal membuat virtual environment
        pause
        exit /b 1
    )
)

REM ============================================================
REM 3. AKTIFKAN VENV
REM ============================================================
echo [INFO] Mengaktifkan virtual environment...
call venv\Scripts\activate.bat

REM ============================================================
REM 4. UPGRADE PIP
REM ============================================================
python -m pip install --upgrade pip >nul

REM ============================================================
REM 5. INSTALL DEPENDENCY
REM ============================================================
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt tidak ditemukan
    pause
    exit /b 1
)

echo [INFO] Mengecek dan menginstall dependency...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] Dependency gagal diinstall
    pause
    exit /b 1
)

REM ============================================================
REM 6. JALANKAN PROGRAM UTAMA
REM ============================================================
if not exist "Aventa_HFT_Pro_2026_v7_3_3.py" (
    echo [ERROR] File utama tidak ditemukan
    pause
    exit /b 1
)

echo.
echo [INFO] Menjalankan Aventa HFT Pro 2026...
echo ============================================================
python Aventa_HFT_Pro_2026_v7_3_3.py

echo.
echo ============================================================
echo [INFO] Launcher selesai
pause
