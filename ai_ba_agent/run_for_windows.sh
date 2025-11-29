#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"
VENV_PATH="${PROJECT_ROOT}/venv"

echo "=========================================="
echo " AI Business Analyst - Windows (Git Bash)"
echo "=========================================="
echo ""

# Pick a usable Python interpreter (3.10.18+).
PY_CMD=""
for candidate in python3.10 python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PY_CMD="$candidate"
    break
  fi
done

if [ -z "${PY_CMD}" ]; then
  echo "Python 3.10.18+ is required but was not found in PATH."
  exit 1
fi

PY_VERSION="$("$PY_CMD" --version 2>&1 | awk '{print $2}')"
if ! "$PY_CMD" - <<'PY' >/dev/null 2>&1; then
import sys
sys.exit(0 if sys.version_info >= (3, 10, 18) else 1)
PY
  echo "Python 3.10.18+ is required. Found: ${PY_VERSION:-unknown}"
  exit 1
fi

echo "OK: Python ${PY_VERSION} detected."
echo ""

# Reuse existing venv if present; otherwise, create it.
if [ -x "${PROJECT_ROOT}/../AIForte/Scripts/python.exe" ]; then
  VENV_PATH="${PROJECT_ROOT}/../AIForte"
  echo "Using existing virtual environment: ${VENV_PATH}"
elif [ -x "${PROJECT_ROOT}/venv/Scripts/python.exe" ]; then
  VENV_PATH="${PROJECT_ROOT}/venv"
  echo "Using existing virtual environment: ${VENV_PATH}"
else
  echo "Creating virtual environment with Python 3.10..."
  "$PY_CMD" -m venv "${VENV_PATH}"
  echo "Created virtual environment: ${VENV_PATH}"
fi
echo ""

ACTIVATE="${VENV_PATH}/Scripts/activate"
if [ ! -f "${ACTIVATE}" ]; then
  echo "activate script not found at ${ACTIVATE}"
  exit 1
fi

echo "Activating virtual environment..."
source "${ACTIVATE}"

VENV_PY="${VENV_PATH}/Scripts/python.exe"
if [ ! -x "${VENV_PY}" ]; then
  VENV_PY="${VENV_PATH}/Scripts/python"
fi

echo "Upgrading pip..."
"${VENV_PY}" -m pip install --upgrade pip -q
echo "pip upgraded."
echo ""

if [ ! -f "${REQUIREMENTS_FILE}" ]; then
  echo "requirements.txt not found at ${REQUIREMENTS_FILE}"
  exit 1
fi

echo "Installing base dependencies from requirements.txt (torch/accelerate handled separately)..."
TEMP_REQUIREMENTS=$(mktemp)
grep -v "^torch==" "${REQUIREMENTS_FILE}" | grep -v "^accelerate==" > "${TEMP_REQUIREMENTS}" || true
"${VENV_PY}" -m pip install -q -r "${TEMP_REQUIREMENTS}" || echo "Warning: some packages from requirements.txt may have failed to install."
echo "Installing torch and accelerate..."
"${VENV_PY}" -m pip install -q torch accelerate 2>/dev/null || echo "Warning: torch/accelerate could not be installed (OK if using Gemini API only)."
rm -f "${TEMP_REQUIREMENTS}"
echo "Dependency installation complete."
echo ""

echo "Verifying required Python packages..."
MISSING_PACKAGES=()

check_import() {
  local module="$1"
  "${VENV_PY}" - <<PY >/dev/null 2>&1 || return 1
import importlib.util, sys
sys.exit(0 if importlib.util.find_spec("${module}") else 1)
PY
}

declare -A PACKAGE_MODULE_MAP=(
  ["streamlit"]="streamlit"
  ["python-dotenv"]="dotenv"
  ["pydantic"]="pydantic"
  ["requests"]="requests"
  ["google-generativeai"]="google.generativeai"
  ["reportlab"]="reportlab"
  ["markdown2"]="markdown2"
  ["loguru"]="loguru"
  ["selenium"]="selenium"
  ["webdriver-manager"]="webdriver_manager"
)

for pkg in "${!PACKAGE_MODULE_MAP[@]}"; do
  module="${PACKAGE_MODULE_MAP[$pkg]}"
  if ! check_import "${module}"; then
    MISSING_PACKAGES+=("${pkg}")
  fi
done

if [ "${#MISSING_PACKAGES[@]}" -gt 0 ]; then
  echo "Installing missing packages: ${MISSING_PACKAGES[*]}"
  "${VENV_PY}" -m pip install -q "${MISSING_PACKAGES[@]}"
else
  echo "All required packages are present."
fi
echo ""

ENV_FILE="${PROJECT_ROOT}/.env"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"
if [ ! -f "${ENV_FILE}" ] && [ -f "${ENV_EXAMPLE}" ]; then
  echo "Creating .env from .env.example..."
  cp "${ENV_EXAMPLE}" "${ENV_FILE}"
  echo ".env created. Update AI_BA_GEMINI_API_KEY in ${ENV_FILE}."
elif [ ! -f "${ENV_FILE}" ]; then
  echo ".env is missing and .env.example not found. Please create ${ENV_FILE} manually."
fi
echo ""

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=0

cd "${PROJECT_ROOT}"

echo "=========================================="
echo " Launching Streamlit app..."
echo " URL: http://localhost:8501"
echo " Press Ctrl+C to stop."
echo "=========================================="
echo ""

exec "${VENV_PY}" -m streamlit run app/main.py --server.headless true
