@echo off

setlocal

:: ------------------------------------------------------------------
:: Скрипт запуска AI Code Review Backend для Windows
:: ------------------------------------------------------------------

:: Находим пути
:: %~dp0 — это директория, где лежит сам скрипт (слэш на конце включен)
set "SCRIPT_DIR=%~dp0"

:: Убираем последний слэш для красоты путей, если нужно, но cmd понимает и так
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Переходим на уровень выше, чтобы найти корень проекта
pushd "%SCRIPT_DIR%\.."
set "PROJECT_ROOT=%CD%"
popd

set "VENV_PATH=%PROJECT_ROOT%\venv"

echo ==========================================
echo 🚀 Start AI Code Review Backend (Windows)
echo ==========================================

:: Проверяем виртуальное окружение
if not exist "%VENV_PATH%" (
    echo ❌ Error: Virtual environment not found!
    echo   Expected: %VENV_PATH%
    echo.
    echo Please create the environment:
    echo   cd "%PROJECT_ROOT%"
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r code_review_backend\requirements.txt
    pause
    exit /b 1
)

:: Активируем окружение (в Windows папка называется Scripts, а не bin)
echo 📦 Activating environment: %VENV_PATH%
call "%VENV_PATH%\Scripts\activate.bat"

:: Проверяем зависимости
echo 🔍 Checking dependencies...
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Dependencies missing. Installing...
    pip install -q -r "%SCRIPT_DIR%\requirements.txt"
    echo ✅ Dependencies installed
) else (
    echo ✅ Dependencies installed
)

:: Устанавливаем PYTHONPATH (корень проекта)
:: В Windows разделитель путей — точка с запятой (;)
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

:: Переходим в директорию backend
cd /d "%SCRIPT_DIR%"

echo 🌐 Starting server at http://localhost:8001
echo   Health check: http://localhost:8001/health
echo   Webhook endpoint: http://localhost:8001/gitlab/webhook
echo.
echo Press Ctrl+C to stop
echo ==========================================
echo.

:: Запускаем сервер
python main.py

:: Чтобы окно не закрывалось сразу после ошибки (опционально)
if %errorlevel% neq 0 pause
