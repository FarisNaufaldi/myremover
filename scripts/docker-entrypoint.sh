#!/bin/sh
set -e
PORT="${PORT:-10000}"
echo "Starting MyRemover on 0.0.0.0:${PORT}"
exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --timeout-keep-alive 120
