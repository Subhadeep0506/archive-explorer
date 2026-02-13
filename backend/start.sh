#!/usr/bin/env bash
set -e
if uname -s | grep -q "Linux"; then
    echo "[INFO] Linux env detected. Running app on Linux..."
    source .venv/bin/activate
else
    echo "[INFO] Windows env detected. Running app on Windows..."
    source .venv/Scripts/activate
fi

PORT="${PORT:-8000}"

uvicorn main:app --host 0.0.0.0 --port "$PORT"
