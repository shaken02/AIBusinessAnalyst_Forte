@echo off
setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
set "REQUIREMENTS_FILE=%PROJECT_ROOT%requirements.txt"
set "VENV_PATH=%PROJECT_ROOT%venv"

echo ==========================================
echo AI Business Analyst - Windows (CMD/PowerShell)
echo ==========================================
echo.

REM Locate a usable Python interpreter (3.10.18+ required)
echo Checking for Python 3.10.18+...
set "PY_CMD="
for %%P in (python3.10 python3 python) do (
    where %%P >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=%%P"
        goto :found_python
    )
)
echo ERROR: Python 3.10.18+ not found in PATH. Install it and rerun.
exit /b 1

:found_python
for /f "tokens=2" %%v in ('"%PY_CMD%" --version 2^>^&1') do set "PYTHON_VERSION=%%v"
echo Found Python !PYTHON_VERSION!
"%PY_CMD%" -c "import sys; exit(0 if sys.version_info >= (3, 10, 18) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.10.18 or newer required. Found: !PYTHON_VERSION!
    exit /b 1
)
echo.

REM Reuse existing venv if present; otherwise create a new one
if exist "%PROJECT_ROOT%..\AIForte\Scripts\python.exe" (
    set "VENV_PATH=%PROJECT_ROOT%..\AIForte"
    echo Using existing virtual environment: !VENV_PATH!
) else if exist "%PROJECT_ROOT%venv\Scripts\python.exe" (
    set "VENV_PATH=%PROJECT_ROOT%venv"
    echo Using existing virtual environment: !VENV_PATH!
) else (
    echo Creating virtual environment with %PY_CMD%...
    %PY_CMD% -m venv "%VENV_PATH%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        exit /b 1
    )
    echo Created virtual environment: !VENV_PATH!
)
echo.

REM Activate the venv
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo ERROR: activate.bat not found at "%VENV_PATH%\Scripts\activate.bat"
    exit /b 1
)
echo Activating virtual environment...
call "%VENV_PATH%\Scripts\activate.bat"
echo.

set "VENV_PY=%VENV_PATH%\Scripts\python.exe"
if not exist "%VENV_PY%" set "VENV_PY=%VENV_PATH%\Scripts\python"

REM Upgrade pip
echo Upgrading pip...
"%VENV_PY%" -m pip install --upgrade pip -q
echo pip upgraded.
echo.

REM Check requirements file
if not exist "%REQUIREMENTS_FILE%" (
    echo ERROR: requirements.txt not found at %REQUIREMENTS_FILE%
    exit /b 1
)

REM Install base requirements (torch/accelerate handled separately)
echo Installing base dependencies from requirements.txt...
set "TEMP_REQUIREMENTS=%TEMP%\requirements_temp.txt"
findstr /v "^torch==" "%REQUIREMENTS_FILE%" | findstr /v "^accelerate==" > "%TEMP_REQUIREMENTS%"
"%VENV_PY%" -m pip install -q -r "%TEMP_REQUIREMENTS%"
if errorlevel 1 (
    echo WARN: Some packages from requirements.txt may have failed to install.
)
echo Installing torch and accelerate...
"%VENV_PY%" -m pip install -q torch accelerate 2>nul
if errorlevel 1 (
    echo WARN: torch/accelerate could not be installed ^(OK if using Gemini API only^).
)
del "%TEMP_REQUIREMENTS%" >nul 2>&1
echo Dependency installation complete.
echo.

REM Verify critical packages and backfill any missing ones
echo Verifying required Python packages...
set "MISSING_PACKAGES="

"%VENV_PY%" -c "import streamlit" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! streamlit"
"%VENV_PY%" -c "import dotenv" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! python-dotenv"
"%VENV_PY%" -c "import pydantic" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! pydantic"
"%VENV_PY%" -c "import requests" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! requests"
"%VENV_PY%" -c "import google.generativeai" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! google-generativeai"
"%VENV_PY%" -c "import reportlab" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! reportlab"
"%VENV_PY%" -c "import markdown2" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! markdown2"
"%VENV_PY%" -c "import loguru" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! loguru"
"%VENV_PY%" -c "import selenium" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! selenium"
"%VENV_PY%" -c "import webdriver_manager" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! webdriver-manager"

if not "!MISSING_PACKAGES!"=="" (
    echo Installing missing packages:!MISSING_PACKAGES!
    "%VENV_PY%" -m pip install -q !MISSING_PACKAGES!
    echo Missing packages installed.
) else (
    echo All required packages are present.
)
echo.

REM Ensure .env exists
set "ENV_FILE=%PROJECT_ROOT%.env"
set "ENV_EXAMPLE=%PROJECT_ROOT%.env.example"
if not exist "%ENV_FILE%" (
    if exist "%ENV_EXAMPLE%" (
        echo Creating .env from .env.example...
        copy "%ENV_EXAMPLE%" "%ENV_FILE%" >nul
        echo .env created. Update AI_BA_GEMINI_API_KEY in %ENV_FILE%.
    ) else (
        echo WARN: .env is missing and .env.example not found. Create %ENV_FILE% manually.
    )
    echo.
) else (
    echo .env already present.
    echo.
)

REM Set environment variables for runtime
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
set "STREAMLIT_BROWSER_GATHER_USAGE_STATS=0"

cd /d "%PROJECT_ROOT%"

echo ==========================================
echo Launching Streamlit app...
echo URL: http://localhost:8501
echo Press Ctrl+C to stop.
echo ==========================================
echo.

"%VENV_PY%" -m streamlit run app/main.py --server.headless true
