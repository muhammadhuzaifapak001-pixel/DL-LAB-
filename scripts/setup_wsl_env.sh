#!/usr/bin/env bash
set -euo pipefail

# Setup script for WSL/Ubuntu with Python 3.12
# Usage: bash scripts/setup_wsl_env.sh

PYTHON_BIN=python3.12
VENV_DIR=.venv312
REQ_FILE=requirements.txt

echo "Checking for ${PYTHON_BIN}..."
if ! command -v ${PYTHON_BIN} >/dev/null 2>&1; then
  echo "${PYTHON_BIN} not found. Install Python 3.12 on Ubuntu (example):"
  echo "  sudo apt update"
  echo "  sudo apt install -y software-properties-common"
  echo "  sudo add-apt-repository ppa:deadsnakes/ppa"
  echo "  sudo apt update"
  echo "  sudo apt install -y python3.12 python3.12-venv python3.12-dev"
  echo "After installing, re-run this script."
  exit 1
fi

echo "Creating venv at ${VENV_DIR} using ${PYTHON_BIN}..."
${PYTHON_BIN} -m venv ${VENV_DIR}
source ${VENV_DIR}/bin/activate

echo "Upgrading pip and installing build essentials..."
python -m pip install --upgrade pip setuptools wheel

if [ ! -f "${REQ_FILE}" ]; then
  echo "requirements.txt not found in project root."
  deactivate || true
  exit 1
fi

echo "Installing requirements from ${REQ_FILE} (this may take a while)..."
# Try installing normally; if torch fails, instruct user how to install CPU wheel
if python -m pip install -r ${REQ_FILE}; then
  echo "Requirements installed successfully."
else
  echo "Failed to install some packages (likely torch). Trying CPU-only PyTorch wheel..."
  python -m pip install --upgrade pip
  python -m pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
  python -m pip install -r ${REQ_FILE} || true
  echo "If torch installation still fails, follow https://pytorch.org/get-started/locally/ to select the correct wheel."
fi

echo "Setup complete. Activate the environment with: source ${VENV_DIR}/bin/activate"
