#!/usr/bin/env bash
# Replit free run — install deps, build SPA once, serve FastAPI + static
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

# Replit sets PIP_USER=1 which breaks both plain pip and venvs
export PIP_USER=0
export PYTHONNOUSERSITE=1
unset PYTHONUSERBASE || true

# Prefer Replit system Python (no nested venv) when REPL_ID is set
if [ -n "${REPL_ID:-}" ] || [ -n "${REPL_SLUG:-}" ] || [ -n "${REPLIT_ENVIRONMENT:-}" ]; then
  python3 -m pip install --disable-pip-version-check -q -r backend/requirements.txt
  PY=(python3 -m)
else
  if [ ! -d backend/.venv ]; then
    python3 -m venv backend/.venv
  fi
  # shellcheck disable=SC1091
  source backend/.venv/bin/activate
  python -m pip install --disable-pip-version-check -q -r backend/requirements.txt
  PY=(python -m)
fi

if [ ! -d backend/static/assets ]; then
  (cd frontend && npm install && npm run build)
  mkdir -p backend/static
  cp -r frontend/dist/* backend/static/
fi

mkdir -p backend/data/uploads backend/data/results
cd backend
exec "${PY[@]}" uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
