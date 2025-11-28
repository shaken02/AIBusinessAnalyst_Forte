#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"
VENV_PATH="${PROJECT_ROOT}/venv"

echo "=========================================="
echo "🚀 AI Business Analyst - Автоматическая установка и запуск"
echo "=========================================="
echo ""

# Проверяем Python 3.10.18
echo "📋 Проверяю Python 3.10.18..."
if ! command -v python3.10 &> /dev/null; then
    echo "❌ Python 3.10.18 не найден! Установите Python 3.10.18."
    echo "   На macOS: brew install python@3.10"
    echo "   Или скачайте с https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3.10 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
PYTHON_PATCH=$(echo $PYTHON_VERSION | cut -d'.' -f3)

if [ "$PYTHON_MAJOR" -ne 3 ] || [ "$PYTHON_MINOR" -ne 10 ] || [ "$PYTHON_PATCH" -lt 18 ]; then
    echo "❌ Требуется Python 3.10.18 или выше. Найден: Python ${PYTHON_VERSION}"
    exit 1
fi

echo "✅ Python ${PYTHON_VERSION} найден"
echo ""

# Проверяем оба возможных расположения виртуального окружения
if [ -d "${PROJECT_ROOT}/../AIForte" ]; then
    VENV_PATH="${PROJECT_ROOT}/../AIForte"
    echo "✅ Используется существующее окружение: ${VENV_PATH}"
elif [ -d "${PROJECT_ROOT}/venv" ]; then
    VENV_PATH="${PROJECT_ROOT}/venv"
    echo "✅ Используется существующее окружение: ${VENV_PATH}"
else
    echo "📦 Создаю виртуальное окружение с Python 3.10..."
    python3.10 -m venv "${VENV_PATH}"
    echo "✅ Виртуальное окружение создано: ${VENV_PATH}"
fi
echo ""

# Активируем окружение
echo "🔧 Активирую виртуальное окружение..."
source "${VENV_PATH}/bin/activate"
echo ""

# Обновляем pip
echo "⬆️  Обновляю pip..."
"${VENV_PATH}/bin/pip" install --upgrade pip -q
echo "✅ pip обновлен"
echo ""

# Проверяем наличие requirements.txt
if [ ! -f "${REQUIREMENTS_FILE}" ]; then
    echo "❌ Файл requirements.txt не найден: ${REQUIREMENTS_FILE}"
    exit 1
fi

# Устанавливаем зависимости из requirements.txt
echo "📥 Устанавливаю зависимости из requirements.txt..."
echo "   (это может занять несколько минут при первом запуске)"
echo ""

# Создаем временный requirements без проблемных пакетов (torch, accelerate могут не установиться на некоторых системах)
TEMP_REQUIREMENTS=$(mktemp)
grep -v "^torch==" "${REQUIREMENTS_FILE}" | grep -v "^accelerate==" > "${TEMP_REQUIREMENTS}" || true

# Устанавливаем зависимости
"${VENV_PATH}/bin/pip" install -q -r "${TEMP_REQUIREMENTS}" 2>&1 | grep -v "ERROR: Could not find a version" || true

# Пытаемся установить torch и accelerate (если доступны)
echo "📦 Пытаюсь установить PyTorch и accelerate (если доступны)..."
"${VENV_PATH}/bin/pip" install torch accelerate -q 2>&1 | grep -v "ERROR" || echo "⚠️  PyTorch/accelerate не установлены (не критично для работы с Gemini API)"

# Очищаем временный файл
rm -f "${TEMP_REQUIREMENTS}"

echo ""
echo "✅ Зависимости установлены"
echo ""

# Проверяем критические пакеты (все используемые в проекте)
echo "🔍 Проверяю установленные пакеты..."
MISSING_PACKAGES=()

# Основные зависимости
if ! "${VENV_PATH}/bin/python" -c "import streamlit" 2>/dev/null; then
    MISSING_PACKAGES+=("streamlit")
fi
if ! "${VENV_PATH}/bin/python" -c "import dotenv" 2>/dev/null; then
    MISSING_PACKAGES+=("python-dotenv")
fi
if ! "${VENV_PATH}/bin/python" -c "import pydantic" 2>/dev/null; then
    MISSING_PACKAGES+=("pydantic")
fi
if ! "${VENV_PATH}/bin/python" -c "import requests" 2>/dev/null; then
    MISSING_PACKAGES+=("requests")
fi

# LLM модели
if ! "${VENV_PATH}/bin/python" -c "import google.generativeai" 2>/dev/null; then
    MISSING_PACKAGES+=("google-generativeai")
fi

# Генерация документов
if ! "${VENV_PATH}/bin/python" -c "import reportlab" 2>/dev/null; then
    MISSING_PACKAGES+=("reportlab")
fi
if ! "${VENV_PATH}/bin/python" -c "import markdown2" 2>/dev/null; then
    MISSING_PACKAGES+=("markdown2")
fi

# Логирование
if ! "${VENV_PATH}/bin/python" -c "import loguru" 2>/dev/null; then
    MISSING_PACKAGES+=("loguru")
fi

# Selenium (опционально, но проверяем)
if ! "${VENV_PATH}/bin/python" -c "import selenium" 2>/dev/null; then
    MISSING_PACKAGES+=("selenium")
fi
if ! "${VENV_PATH}/bin/python" -c "import webdriver_manager" 2>/dev/null; then
    MISSING_PACKAGES+=("webdriver-manager")
fi

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "⚠️  Устанавливаю недостающие критические пакеты: ${MISSING_PACKAGES[*]}"
    "${VENV_PATH}/bin/pip" install -q "${MISSING_PACKAGES[@]}"
    echo "✅ Критические пакеты установлены"
else
    echo "✅ Все критические пакеты установлены"
fi
echo ""

# Проверяем .env файл
ENV_FILE="${PROJECT_ROOT}/.env"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"

if [ ! -f "${ENV_FILE}" ]; then
    if [ -f "${ENV_EXAMPLE}" ]; then
        echo "📝 Создаю .env файл из .env.example..."
        cp "${ENV_EXAMPLE}" "${ENV_FILE}"
        echo "✅ .env файл создан. Пожалуйста, заполните AI_BA_GEMINI_API_KEY!"
        echo "   Файл: ${ENV_FILE}"
    else
        echo "⚠️  .env файл не найден. Создайте его вручную если нужны переменные окружения."
    fi
    echo ""
else
    echo "✅ .env файл найден"
    echo ""
fi

# Настраиваем окружение
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=0

cd "${PROJECT_ROOT}"

echo "=========================================="
echo "🌐 Запускаю приложение..."
echo "=========================================="
echo ""
echo "📍 URL: http://localhost:8501"
echo "🛑 Для остановки нажмите Ctrl+C"
echo "=========================================="
echo ""

# Запускаем приложение
exec "${VENV_PATH}/bin/python" -m streamlit run app/main.py --server.headless true
