#!/usr/bin/env bash
# Prepara el backend en desarrollo (Ubuntu / WSL / Git Bash).
set -euo pipefail
cd "$(dirname "$0")/../../backend"
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env && echo "Edita backend/.env con tu DATABASE_URL"
