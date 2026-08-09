# Hugging Face Spaces (Docker) — MyRemover backend API
# Port 7860 is required by HF Spaces health checks.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ENVIRONMENT=production \
    COOKIE_SECURE=true \
    COOKIE_SAMESITE=lax \
    REMBG_MODEL=u2net \
    ALPHA_MATTING=true \
    ALPHA_MATTING_MAX_SIDE=1280 \
    INFERENCE_DEVICE=cpu \
    MAX_UPLOAD_MB=15 \
    DATABASE_URL=sqlite:///./data/app.db \
    UPLOAD_DIR=./data/uploads \
    RESULT_DIR=./data/results \
    SKIP_MODEL_LOAD=0

WORKDIR /app

# System deps for pillow / onnxruntime
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        libglib2.0-0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/data/uploads /app/data/results \
    && chmod -R 777 /app/data

# Warm u2net weights into the image so first request is faster
RUN python - <<'PY'
from rembg import new_session
print("Downloading u2net model for image bake...")
new_session("u2net")
print("Model ready.")
PY

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD curl -fsS http://127.0.0.1:7860/api/ping || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--timeout-keep-alive", "120"]
