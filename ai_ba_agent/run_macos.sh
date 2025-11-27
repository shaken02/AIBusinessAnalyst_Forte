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

cd "${PROJECT_ROOT}"
exec "${VENV_PATH}/bin/python" -m streamlit run app/main.py --server.headless true
