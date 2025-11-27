#!/usr/bin/env bash

# Скрипт запуска AI Code Review Backend для macOS/Linux

set -euo pipefail

# Находим корень проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PATH="${PROJECT_ROOT}/venv"

echo "=========================================="
echo "🚀 Запуск AI Code Review Backend"
echo "=========================================="

# Проверяем виртуальное окружение
if [ ! -d "${VENV_PATH}" ]; then
  echo "❌ Ошибка: Виртуальное окружение не найдено!"
  echo "   Ожидалось: ${VENV_PATH}"
  echo ""
  echo "Создайте окружение:"
  echo "  cd '${PROJECT_ROOT}'"
  echo "  python3 -m venv venv"
  echo "  source venv/bin/activate"
  echo "  pip install -r code_review_backend/requirements.txt"
  exit 1
fi

# Активируем окружение
echo "📦 Активирую окружение: ${VENV_PATH}"
source "${VENV_PATH}/bin/activate"

# Проверяем зависимости
echo "🔍 Проверяю зависимости..."
if ! python -c "import fastapi" 2>/dev/null; then
  echo "⚠️  Зависимости не установлены. Устанавливаю..."
  pip install -q -r "${SCRIPT_DIR}/requirements.txt"
  echo "✅ Зависимости установлены"
else
  echo "✅ Зависимости установлены"
fi

# Устанавливаем PYTHONPATH (как в start.sh - корень проекта)
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

# Переходим в директорию backend
cd "${SCRIPT_DIR}"

echo "🌐 Запускаю сервер на http://localhost:8001"
echo "   Health check: http://localhost:8001/health"
echo "   Webhook endpoint: http://localhost:8001/gitlab/webhook"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo "=========================================="
echo ""

# Запускаем сервер через uvicorn (как в start.sh - через python main.py)
exec python main.py

