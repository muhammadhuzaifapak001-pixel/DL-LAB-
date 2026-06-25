#!/usr/bin/env bash
# Prepare a Python 3.12 virtual environment and install requirements (for WSL/Ubuntu)
# Usage: bash scripts/prepare_env_py312.sh

set -euo pipefail

PYTHON=python3.12
VENV_DIR=.venv312
REQS=requirements.txt

if ! command -v $PYTHON &> /dev/null; then
  echo "${PYTHON} not found. Install Python 3.12 in your WSL distro first."
  exit 1
fi

$PYTHON -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
# Consider using extra-index-url for torch wheels if needed for your platform
pip install -r "$REQS"

echo "Setup complete. Activate with: source $VENV_DIR/bin/activate"
