#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

echo "OpenRastr Evolve bootstrap"
echo "Workspace: ${ROOT_DIR}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found."
  exit 1
fi

if [ ! -d "${VENV_DIR}" ]; then
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install setuptools wheel
python -m pip install --no-build-isolation -e "${ROOT_DIR}"

echo
echo "Installation complete."
echo

if [ "${OPENRASTR_SKIP_ONBOARD:-0}" = "1" ]; then
  echo "Skipping onboarding because OPENRASTR_SKIP_ONBOARD=1"
  exit 0
fi

openrastr-evolve onboard --workspace-root "${ROOT_DIR}"
