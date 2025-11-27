#!/usr/bin/env bash

# Простой скрипт запуска - работает из любой директории

set -e

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
fi

# Устанавливаем PYTHONPATH
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

# Переходим в директорию backend
cd "${SCRIPT_DIR}"

echo "🌐 Запускаю сервер на http://localhost:8001"
echo "   Health check: http://localhost:8001/health"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo "=========================================="
echo ""

# Запускаем сервер
exec python main.py
