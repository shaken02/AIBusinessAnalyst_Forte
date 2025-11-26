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
  echo "  Option 1: python3.10 -m venv venv (in ai_ba_agent directory)" >&2
  echo "  Option 2: python3.10 -m venv ../AIForte (in AIBusinessAnalyst directory)" >&2
  exit 1
fi

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=0

# Choose the right python inside the venv for Unix/Windows layouts
if [ -x "${VENV_PATH}/bin/python" ]; then
  PYTHON="${VENV_PATH}/bin/python"
elif [ -x "${VENV_PATH}/Scripts/python" ]; then
  PYTHON="${VENV_PATH}/Scripts/python"
elif [ -x "${VENV_PATH}/Scripts/python.exe" ]; then
  PYTHON="${VENV_PATH}/Scripts/python.exe"
else
  echo "Python executable not found in virtualenv at ${VENV_PATH}" >&2
  exit 1
fi

cd "${PROJECT_ROOT}"
exec "${PYTHON}" -m streamlit run app/main.py --server.headless true
