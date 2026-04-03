@echo off
REM ============================================================
REM  build_windows.bat — Build Cold Outreach Automator for Windows
REM  Run this script from the PROJECT ROOT directory:
REM      build_scripts\build_windows.bat
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  Cold Outreach Automator — Windows Build Script
echo ============================================================
echo.

REM ── Step 1: Verify Python is available ───────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found on PATH. Install Python 3.9+ from python.org
    exit /b 1
)
python --version
echo.

REM ── Step 2: Create/activate virtual environment ──────────────
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat

REM ── Step 3: Install dependencies ─────────────────────────────
echo [INFO] Installing requirements...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet
echo [INFO] Dependencies installed.
echo.

REM ── Step 4: Convert PNG icon to ICO ──────────────────────────
if not exist "assets\icon.ico" (
    echo [INFO] Generating icon.ico from icon.png...
    python -c "from PIL import Image; img = Image.open('assets/icon.png').convert('RGBA'); sizes = [16, 32, 48, 64, 128, 256]; img.save('assets/icon.ico', format='ICO', sizes=[(s, s) for s in sizes]); print('icon.ico created.')"
    if not exist "assets\icon.ico" (
        echo [WARN] Icon conversion failed. Place icon.ico manually in assets\.
    )
"
    if errorlevel 1 (
        echo [WARN] Pillow not available; icon conversion skipped. Place icon.ico manually in assets\.
    )
)

REM ── Step 5: Clean previous build artifacts ───────────────────
echo [INFO] Cleaning previous build...
if exist "build" rmdir /s /q build
if exist "dist"  rmdir /s /q dist

REM ── Step 6: Run PyInstaller ───────────────────────────────────
echo [INFO] Running PyInstaller...
pyinstaller ColdOutreachAutomator.spec --noconfirm --clean
if errorlevel 1 (
    echo [ERROR] PyInstaller failed. See output above.
    exit /b 1
)
echo [INFO] PyInstaller build complete.
echo.

REM ── Step 7: Run Inno Setup to create the installer ───────────
set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_PATH% (
    echo [WARN] Inno Setup not found at %INNO_PATH%.
    echo        Download from https://jrsoftware.org/isdl.php
    echo        Then re-run this script, or run ISCC manually:
    echo          ISCC build_scripts\installer_windows.iss
    echo.
    echo [INFO] The raw EXE folder is at: dist\ColdOutreachAutomator\
    goto :done
)

echo [INFO] Running Inno Setup compiler...
%INNO_PATH% build_scripts\installer_windows.iss
if errorlevel 1 (
    echo [ERROR] Inno Setup compilation failed.
    exit /b 1
)

:done
echo.
echo ============================================================
echo  BUILD COMPLETE
echo  Installer: dist\ColdOutreachAutomator_Setup.exe
echo ============================================================
echo.

deactivate
endlocal
