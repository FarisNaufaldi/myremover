# Multi-stage image: frontend (Vite) + backend (FastAPI)
# Works free on Render / Railway / Fly (PORT env supported).

# ── Frontend build ──────────────────────────────────────
FROM node:20-bookworm-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build

# ── Backend runtime ─────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ENVIRONMENT=production \
    COOKIE_SECURE=true \
    COOKIE_SAMESITE=lax \
    REMBG_MODEL=u2netp \
    ALPHA_MATTING=false \
    ALPHA_MATTING_MAX_SIDE=1024 \
    INFERENCE_DEVICE=cpu \
    MAX_UPLOAD_MB=10 \
    DATABASE_URL=sqlite:///./data/app.db \
    UPLOAD_DIR=./data/uploads \
    RESULT_DIR=./data/results \
    SKIP_MODEL_LOAD=1 \
    PORT=10000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        libglib2.0-0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY backend/ .

# SPA assets from frontend stage
COPY --from=frontend /fe/dist /app/static

RUN mkdir -p /app/data/uploads /app/data/results \
    && chmod -R 777 /app/data

# Prefetch lightweight model into image (u2netp ~5MB class)
RUN python - <<'PY' || true
from rembg import new_session
print("Prefetching u2netp...")
new_session("u2netp")
print("ok")
PY

EXPOSE 10000

COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
