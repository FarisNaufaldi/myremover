#!/usr/bin/env bash
# Deploy MyRemover backend to Hugging Face Spaces (Docker).
# Requires: hf CLI logged in, and HF PRO for Docker Spaces (cpu-basic).
# Usage: ./scripts/deploy-hf.sh [admin_password]

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SPACE_ID="${HF_SPACE_ID:-FeynmanProject/myremover-api}"
STAGE="$(mktemp -d)/hf-space"
ADMIN_PASS="${1:-}"

if [[ -z "$ADMIN_PASS" ]]; then
  ADMIN_PASS="$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))')"
fi
SESSION_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"

echo "==> Preparing staging directory"
mkdir -p "$STAGE"
rsync -a \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.env' \
  --exclude 'data/*.db' \
  --exclude 'data/uploads/*' \
  --exclude 'data/results/*' \
  --exclude '.deploy-credentials.txt' \
  --exclude 'README_SPACE.md' \
  "$ROOT/backend/" "$STAGE/"
cp "$ROOT/backend/README_SPACE.md" "$STAGE/README.md"
mkdir -p "$STAGE/data/uploads" "$STAGE/data/results"
touch "$STAGE/data/uploads/.gitkeep" "$STAGE/data/results/.gitkeep"

echo "==> Creating Space $SPACE_ID (Docker)"
hf repos create "$SPACE_ID" --type space --space-sdk docker --public --exist-ok

echo "==> Uploading files"
hf upload "$SPACE_ID" "$STAGE" . --repo-type=space

echo "==> Setting secrets & variables"
hf spaces secrets add "$SPACE_ID" \
  -s "SESSION_SECRET=${SESSION_SECRET}" \
  -s "ADMIN_USERNAME=admin" \
  -s "ADMIN_PASSWORD=${ADMIN_PASS}" \
  -s "ADMIN_NAME=Admin"
hf spaces variables add "$SPACE_ID" \
  -e "ENVIRONMENT=production" \
  -e "COOKIE_SECURE=true" \
  -e "COOKIE_SAMESITE=lax" \
  -e "REMBG_MODEL=u2net" \
  -e "INFERENCE_DEVICE=cpu" \
  -e "MAX_UPLOAD_MB=15" \
  -e "ALPHA_MATTING=true" \
  -e "ALPHA_MATTING_MAX_SIDE=1280"

SPACE_SLUG="$(echo "$SPACE_ID" | tr '[:upper:]' '[:lower:]' | tr '/' '-')"
API_URL="https://${SPACE_SLUG}.hf.space"
CREDS="$ROOT/backend/.deploy-credentials.txt"
cat >"$CREDS" <<EOF
HF_SPACE=https://huggingface.co/spaces/${SPACE_ID}
HF_API=${API_URL}
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${ADMIN_PASS}
SESSION_SECRET_SET=yes
EOF
chmod 600 "$CREDS"

echo ""
echo "Done."
echo "Space page : https://huggingface.co/spaces/${SPACE_ID}"
echo "API URL    : ${API_URL}"
echo "Admin user : admin"
echo "Admin pass : saved in backend/.deploy-credentials.txt"
echo ""
echo "Wait for the Space build (first build 10–20 min)."
echo "Then set frontend/vercel.json rewrite destination to ${API_URL}/api/:path*"
