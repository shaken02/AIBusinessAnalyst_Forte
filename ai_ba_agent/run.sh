#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${PROJECT_ROOT}/venv"

if [ ! -d "${VENV_PATH}" ]; then
  echo "Virtualenv not found at ${VENV_PATH}. Create it first (python3.10 -m venv venv)." >&2
  exit 1
fi

source "${VENV_PATH}/bin/activate"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=0

cd "${PROJECT_ROOT}"
exec streamlit run app/main.py --server.headless true
