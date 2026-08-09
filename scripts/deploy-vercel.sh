#!/usr/bin/env bash
# Deploy MyRemover frontend to Vercel.
# Prerequisites:
#   - npm i -g vercel  OR use npx vercel
#   - vercel login
#   - backend already live (Hugging Face) and vercel.json points to it
#
# Usage: ./scripts/deploy-vercel.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

if ! command -v vercel >/dev/null 2>&1; then
  echo "Installing vercel CLI locally for this project..."
  npm install --save-dev vercel@latest
fi

echo "==> Building & deploying frontend (production)"
# Use local binary if present
VERCEL_BIN="npx vercel"
$VERCEL_BIN --prod --yes

echo ""
echo "After deploy:"
echo "1. Copy your Vercel domain (e.g. https://myremover.vercel.app)"
echo "2. Optional: set HF Space variable CORS_ORIGINS to that exact domain"
echo "3. Login with the HF bootstrap admin credentials"
