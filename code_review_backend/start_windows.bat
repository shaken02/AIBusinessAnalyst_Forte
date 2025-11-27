@echo off
REM Скрипт запуска AI Code Review Backend для Windows

setlocal enabledelayedexpansion

REM Находим корень проекта
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "VENV_PATH=%PROJECT_ROOT%\venv"

echo ==========================================
echo 🚀 Запуск AI Code Review Backend
echo ==========================================
echo.

REM Проверяем виртуальное окружение
if not exist "%VENV_PATH%" (
  echo ❌ Ошибка: Виртуальное окружение не найдено!
  echo    Ожидалось: %VENV_PATH%
  echo.
  echo Создайте окружение:
  echo   cd "%PROJECT_ROOT%"
  echo   python -m venv venv
  echo   venv\Scripts\activate
  echo   pip install -r code_review_backend\requirements.txt
  pause
  exit /b 1
)

REM Активируем окружение
echo 📦 Активирую окружение: %VENV_PATH%
call "%VENV_PATH%\Scripts\activate.bat"

REM Проверяем зависимости
echo 🔍 Проверяю зависимости...
python -c "import fastapi" 2>nul
if errorlevel 1 (
  echo ⚠️  Зависимости не установлены. Устанавливаю...
  pip install -q -r "%SCRIPT_DIR%requirements.txt"
  echo ✅ Зависимости установлены
) else (
  echo ✅ Зависимости установлены
)

REM Устанавливаем PYTHONPATH
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"

REM Переходим в директорию backend
cd /d "%SCRIPT_DIR%"

echo.
echo 🌐 Запускаю сервер на http://localhost:8001
echo    Health check: http://localhost:8001/health
echo    Webhook endpoint: http://localhost:8001/gitlab/webhook
echo.
echo Для остановки нажмите Ctrl+C
echo ==========================================
echo.

REM Запускаем сервер через uvicorn
uvicorn code_review_backend.main:app --host 0.0.0.0 --port 8001 --reload

pause

