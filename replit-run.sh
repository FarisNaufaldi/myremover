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
# Replit Agent often injects Postgres DATABASE_URL; free run uses local SQLite.
# Set ALLOW_EXTERNAL_DATABASE=1 to keep whatever DATABASE_URL is already set.
if [ "${ALLOW_EXTERNAL_DATABASE:-0}" != "1" ]; then
  export DATABASE_URL="sqlite:///${PWD}/backend/data/app.db"
fi
export UPLOAD_DIR="${UPLOAD_DIR:-${PWD}/backend/data/uploads}"
export RESULT_DIR="${RESULT_DIR:-${PWD}/backend/data/results}"

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

# Always ensure SPA is present (reset/clean can leave API without UI)
if [ ! -f backend/static/index.html ] || [ ! -d backend/static/assets ]; then
  echo "Building frontend into backend/static ..."
  (cd frontend && npm install && npm run build)
  rm -rf backend/static
  mkdir -p backend/static
  cp -r frontend/dist/. backend/static/
fi
if [ ! -f backend/static/index.html ]; then
  echo "ERROR: backend/static/index.html missing after build" >&2
  exit 1
fi
echo "Frontend OK: backend/static/index.html present"
echo ""
echo "=============================================="
echo " JANGAN pakai Preview Replit (minta Core)."
echo " Buka di Chrome/Safari Mac — copy URL di bawah:"
echo "----------------------------------------------"
if [ -n "${REPLIT_DEV_DOMAIN:-}" ]; then
  echo "  https://${REPLIT_DEV_DOMAIN}"
fi
if [ -n "${REPLIT_DOMAINS:-}" ]; then
  echo "  REPLIT_DOMAINS=${REPLIT_DOMAINS}"
fi
if [ -n "${REPL_SLUG:-}" ] && [ -n "${REPL_OWNER:-}" ]; then
  echo "  https://${REPL_SLUG}.${REPL_OWNER}.repl.co"
  echo "  https://${REPL_SLUG}-${REPL_OWNER}.replit.app"
fi
echo "  (internal check) curl http://127.0.0.1:${PORT:-8000}/api/ping"
echo "=============================================="
echo ""

mkdir -p backend/data/uploads backend/data/results
cd backend
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
