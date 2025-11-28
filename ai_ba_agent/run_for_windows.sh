@echo off
setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
set "REQUIREMENTS_FILE=%PROJECT_ROOT%requirements.txt"
set "VENV_PATH=%PROJECT_ROOT%venv"

echo ==========================================
echo 🚀 AI Business Analyst - Автоматическая установка и запуск
echo ==========================================
echo.

REM Проверяем Python 3.10.18
echo 📋 Проверяю Python 3.10.18...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.10.18.
    echo    Скачайте с https://www.python.org/downloads/
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo ✅ Python !PYTHON_VERSION! найден
echo.

REM Проверяем версию Python
python -c "import sys; exit(0 if sys.version_info >= (3, 10, 18) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ❌ Требуется Python 3.10.18 или выше. Найден: Python !PYTHON_VERSION!
    exit /b 1
)

REM Проверяем оба возможных расположения виртуального окружения
if exist "%PROJECT_ROOT%..\AIForte\Scripts\python.exe" (
    set "VENV_PATH=%PROJECT_ROOT%..\AIForte"
    echo ✅ Используется существующее окружение: !VENV_PATH!
) else if exist "%PROJECT_ROOT%venv\Scripts\python.exe" (
    set "VENV_PATH=%PROJECT_ROOT%venv"
    echo ✅ Используется существующее окружение: !VENV_PATH!
) else (
    echo 📦 Создаю виртуальное окружение с Python 3.10...
    python -m venv "%VENV_PATH%"
    if errorlevel 1 (
        echo ❌ Ошибка при создании виртуального окружения
        exit /b 1
    )
    echo ✅ Виртуальное окружение создано: !VENV_PATH!
)
echo.

REM Активируем окружение
echo 🔧 Активирую виртуальное окружение...
call "%VENV_PATH%\Scripts\activate.bat"
echo.

REM Обновляем pip
echo ⬆️  Обновляю pip...
"%VENV_PATH%\Scripts\python.exe" -m pip install --upgrade pip -q
echo ✅ pip обновлен
echo.

REM Проверяем наличие requirements.txt
if not exist "%REQUIREMENTS_FILE%" (
    echo ❌ Файл requirements.txt не найден: %REQUIREMENTS_FILE%
    exit /b 1
)

REM Устанавливаем зависимости из requirements.txt
echo 📥 Устанавливаю зависимости из requirements.txt...
echo    (это может занять несколько минут при первом запуске)
echo.

REM Создаем временный requirements без проблемных пакетов
set "TEMP_REQUIREMENTS=%TEMP%\requirements_temp.txt"
findstr /v "^torch==" "%REQUIREMENTS_FILE%" | findstr /v "^accelerate==" > "%TEMP_REQUIREMENTS%"

REM Устанавливаем зависимости
"%VENV_PATH%\Scripts\python.exe" -m pip install -q -r "%TEMP_REQUIREMENTS%"
if errorlevel 1 (
    echo ⚠️  Некоторые зависимости не установились, продолжаю...
)

REM Пытаемся установить torch и accelerate
echo 📦 Пытаюсь установить PyTorch и accelerate (если доступны)...
"%VENV_PATH%\Scripts\python.exe" -m pip install torch accelerate -q 2>nul || echo ⚠️  PyTorch/accelerate не установлены (не критично для работы с Gemini API)

REM Удаляем временный файл
del "%TEMP_REQUIREMENTS%" >nul 2>&1

echo.
echo ✅ Зависимости установлены
echo.

REM Проверяем критические пакеты
echo 🔍 Проверяю установленные пакеты...
set "MISSING_PACKAGES="

"%VENV_PATH%\Scripts\python.exe" -c "import streamlit" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! streamlit"
"%VENV_PATH%\Scripts\python.exe" -c "import dotenv" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! python-dotenv"
"%VENV_PATH%\Scripts\python.exe" -c "import pydantic" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! pydantic"
"%VENV_PATH%\Scripts\python.exe" -c "import requests" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! requests"
"%VENV_PATH%\Scripts\python.exe" -c "import google.generativeai" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! google-generativeai"
"%VENV_PATH%\Scripts\python.exe" -c "import reportlab" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! reportlab"
"%VENV_PATH%\Scripts\python.exe" -c "import markdown2" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! markdown2"
"%VENV_PATH%\Scripts\python.exe" -c "import loguru" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! loguru"
"%VENV_PATH%\Scripts\python.exe" -c "import selenium" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! selenium"
"%VENV_PATH%\Scripts\python.exe" -c "import webdriver_manager" >nul 2>&1 || set "MISSING_PACKAGES=!MISSING_PACKAGES! webdriver-manager"

if not "!MISSING_PACKAGES!"=="" (
    echo ⚠️  Устанавливаю недостающие критические пакеты:!MISSING_PACKAGES!
    "%VENV_PATH%\Scripts\python.exe" -m pip install -q!MISSING_PACKAGES!
    echo ✅ Критические пакеты установлены
) else (
    echo ✅ Все критические пакеты установлены
)
echo.

REM Проверяем .env файл
set "ENV_FILE=%PROJECT_ROOT%.env"
set "ENV_EXAMPLE=%PROJECT_ROOT%.env.example"

if not exist "%ENV_FILE%" (
    if exist "%ENV_EXAMPLE%" (
        echo 📝 Создаю .env файл из .env.example...
        copy "%ENV_EXAMPLE%" "%ENV_FILE%" >nul
        echo ✅ .env файл создан. Пожалуйста, заполните AI_BA_GEMINI_API_KEY!
        echo    Файл: %ENV_FILE%
    ) else (
        echo ⚠️  .env файл не найден. Создайте его вручную если нужны переменные окружения.
    )
    echo.
) else (
    echo ✅ .env файл найден
    echo.
)

REM Настраиваем окружение
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
set "STREAMLIT_BROWSER_GATHER_USAGE_STATS=0"

cd /d "%PROJECT_ROOT%"

echo ==========================================
echo 🌐 Запускаю приложение...
echo ==========================================
echo.
echo 📍 URL: http://localhost:8501
echo 🛑 Для остановки нажмите Ctrl+C
echo ==========================================
echo.

REM Запускаем приложение
"%VENV_PATH%\Scripts\python.exe" -m streamlit run app/main.py --server.headless true
