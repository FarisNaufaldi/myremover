#!/usr/bin/env bash
# Replit free run — venv (writable) + build SPA once + uvicorn
set -euo pipefail
cd "$(dirname "$0")"

export ENVIRONMENT="${ENVIRONMENT:-production}"
export COOKIE_SECURE="${COOKIE_SECURE:-true}"
export COOKIE_SAMESITE="${COOKIE_SAMESITE:-lax}"
export REMBG_MODEL="${REMBG_MODEL:-u2netp}"
export ALPHA_MATTING="${ALPHA_MATTING:-false}"
export INFERENCE_DEVICE="${INFERENCE_DEVICE:-cpu}"
export MAX_UPLOAD_MB="${MAX_UPLOAD_MB:-10}"
export SKIP_MODEL_LOAD="${SKIP_MODEL_LOAD:-1}"
export SESSION_SECRET="${SESSION_SECRET:-replit-dev-change-me-please-32chars}"
export ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-MyRemoverChangeMe123}"
export ADMIN_NAME="${ADMIN_NAME:-Admin}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./data/app.db}"
export UPLOAD_DIR="${UPLOAD_DIR:-./data/uploads}"
export RESULT_DIR="${RESULT_DIR:-./data/results}"

# Replit: system site-packages is Nix (read-only). Use a project venv only.
# Replit also sets PIP_USER=1 which breaks venvs — force it off.
export PIP_USER=0
export PYTHONNOUSERSITE=1
unset PYTHONUSERBASE || true
export PIP_CONFIG_FILE=/dev/null

VENV_DIR="${PWD}/.venv"
if [ ! -x "${VENV_DIR}/bin/python" ]; then
  rm -rf "${VENV_DIR}"
  python3 -m venv "${VENV_DIR}"
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

python -m pip install --disable-pip-version-check -q --upgrade pip setuptools wheel
python -m pip install --disable-pip-version-check -q -r backend/requirements.txt

if [ ! -d backend/static/assets ]; then
  (cd frontend && npm install && npm run build)
  mkdir -p backend/static
  cp -r frontend/dist/* backend/static/
fi

mkdir -p backend/data/uploads backend/data/results
cd backend
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
