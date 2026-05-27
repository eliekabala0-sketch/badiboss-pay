#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[railway-build] ROOT_DIR=$ROOT_DIR"
echo "[railway-build] pwd=$(pwd)"
ls -la

python -m pip install --upgrade pip
pip install -r requirements.txt

echo "[railway-build] Building frontend dashboard..."
cd frontend
npm ci
npm run build

if [[ ! -f dist/index.html ]]; then
  echo "[railway-build] ERROR: frontend/dist/index.html missing after build"
  ls -la
  ls -la dist || true
  exit 1
fi

echo "[railway-build] Frontend build OK"
ls -la dist
ls -la dist/assets || true
