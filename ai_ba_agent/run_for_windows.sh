#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Проверяем оба возможных расположения виртуального окружения
if [ -d "${PROJECT_ROOT}/../AIForte" ]; then
  VENV_PATH="${PROJECT_ROOT}/../AIForte"
elif [ -d "${PROJECT_ROOT}/venv" ]; then
  VENV_PATH="${PROJECT_ROOT}/venv"
else
  echo "Virtualenv not found. Please create one:" >&2
  echo "  Option 1: python -m venv venv        (из каталога ai_ba_agent)" >&2
  echo "  Option 2: python -m venv ../AIForte  (из каталога AIBusinessAnalyst)" >&2
  exit 1
fi

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=0

cd "${PROJECT_ROOT}"

# Detect correct Python executable inside venv (Linux/macOS: bin/, Windows: Scripts/)
if [ -x "${VENV_PATH}/bin/python" ]; then
  PYTHON_EXEC="${VENV_PATH}/bin/python"
elif [ -x "${VENV_PATH}/Scripts/python.exe" ]; then
  PYTHON_EXEC="${VENV_PATH}/Scripts/python.exe"
else
  echo "Cannot find python in virtualenv at: ${VENV_PATH}" >&2
  echo "Checked:" >&2
  echo "  ${VENV_PATH}/bin/python" >&2
  echo "  ${VENV_PATH}/Scripts/python.exe" >&2
  exit 1
fi

exec "${PYTHON_EXEC}" -m streamlit run app/main.py --server.headless true
