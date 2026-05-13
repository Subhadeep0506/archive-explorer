#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-5173}"

echo "[INFO] Starting React app..."
cd "$FRONTEND_DIR"

if ! command -v bun >/dev/null 2>&1; then
    echo "[ERROR] bun is required but was not found in PATH." >&2
    exit 1
fi

if [[ "${ARXIVER_DRY_RUN:-0}" == "1" ]]; then
    echo "[DRY RUN] cd $FRONTEND_DIR"
    echo "[DRY RUN] bun run dev -- --host $HOST --port $PORT"
    exit 0
fi

exec bun run dev -- --host "$HOST" --port "$PORT"