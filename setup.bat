@echo off
:: ╔══════════════════════════════════════════════════════════════════╗
:: ║         B-POINT Setup Script — Windows (setup.bat)              ║
:: ║         Creates venv on E:\BPOINT_PRO and installs deps         ║
:: ╚══════════════════════════════════════════════════════════════════╝

title B-POINT Setup

echo.
echo  ██████╗       ██████╗  ██████╗ ██╗███╗   ██╗████████╗
echo  ██╔══██╗      ██╔══██╗██╔═══██╗██║████╗  ██║╚══██╔══╝
echo  ██████╔╝█████╗██████╔╝██║   ██║██║██╔██╗ ██║   ██║
echo  ██╔══██╗╚════╝██╔═══╝ ██║   ██║██║██║╚██╗██║   ██║
echo  ██████╔╝      ██║     ╚██████╔╝██║██║ ╚████║   ██║
echo  ╚═════╝       ╚═╝      ╚═════╝ ╚═╝╚═╝  ╚═══╝   ╚═╝
echo.
echo  Virtual AI Mouse — BSSE Final Year Project
echo  Developer: Babar   License: MIT   Stack: 100%% Open Source
echo  ════════════════════════════════════════════════════════
echo.

:: ── Step 1: Verify Python 3.10+ is installed ─────────────────────
echo [1/5] Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH.
    echo         Download from: https://www.python.org/downloads/
    pause & exit /b 1
)
python -c "import sys; assert sys.version_info >= (3,10), 'Need 3.10+'" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10 or newer required.
    pause & exit /b 1
)
echo        OK

:: ── Step 2: Create project directory on E: ───────────────────────
echo [2/5] Creating project directory at E:\BPOINT_PRO...
if not exist "E:\BPOINT_PRO" mkdir "E:\BPOINT_PRO"
echo        OK

:: ── Step 3: Create Virtual Environment ───────────────────────────
echo [3/5] Creating virtual environment (avoids shadowing/AttributeError)...
python -m venv "E:\BPOINT_PRO\venv"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create venv.
    pause & exit /b 1
)
echo        OK

:: ── Step 4: Upgrade pip inside venv ──────────────────────────────
echo [4/5] Upgrading pip...
"E:\BPOINT_PRO\venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
echo        OK

:: ── Step 5: Install all open-source dependencies ─────────────────
echo [5/5] Installing open-source dependencies...
echo.
echo  Package           License    Purpose
echo  ─────────────────────────────────────────────────────────────
echo  mediapipe         Apache 2.0  21-point hand landmark detection
echo  opencv-python     Apache 2.0  Camera stream + GUI overlay
echo  pyautogui         BSD         Native Windows mouse injection
echo  numpy             BSD         Coordinate math + smoothing
echo  (tkinter is built into Python stdlib — no install needed)
echo.

"E:\BPOINT_PRO\venv\Scripts\pip.exe" install ^
    mediapipe ^
    opencv-python ^
    pyautogui ^
    numpy

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Dependency installation failed.
    echo         Check your internet connection and try again.
    pause & exit /b 1
)

:: ── Copy main.py to project directory ────────────────────────────
echo.
echo Copying main.py to E:\BPOINT_PRO\...
copy /Y "%~dp0main.py" "E:\BPOINT_PRO\main.py" >nul
echo        OK

:: ── Create VS Code launch shortcut ───────────────────────────────
echo Creating VS Code workspace settings...
if not exist "E:\BPOINT_PRO\.vscode" mkdir "E:\BPOINT_PRO\.vscode"
(
echo {
echo     "python.defaultInterpreterPath": "E:\\BPOINT_PRO\\venv\\Scripts\\python.exe",
echo     "python.terminal.activateEnvironment": true
echo }
) > "E:\BPOINT_PRO\.vscode\settings.json"

:: ── Create run shortcut ───────────────────────────────────────────
(
echo @echo off
echo title B-POINT Running
echo "E:\BPOINT_PRO\venv\Scripts\python.exe" "E:\BPOINT_PRO\main.py"
echo pause
) > "E:\BPOINT_PRO\run_bpoint.bat"

echo.
echo ════════════════════════════════════════════════════════════════
echo  ✅  Setup complete!
echo.
echo  To run B-POINT:
echo    Option A) Double-click  E:\BPOINT_PRO\run_bpoint.bat
echo    Option B) In VS Code terminal:
echo              E:\BPOINT_PRO\venv\Scripts\activate
echo              python E:\BPOINT_PRO\main.py
echo ════════════════════════════════════════════════════════════════
echo.
pause
