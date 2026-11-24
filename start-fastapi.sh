#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "[INFO] Starting FastAPI server..."
cd "$BACKEND_DIR"

if [[ "${ARXIVER_DRY_RUN:-0}" == "1" ]]; then
    echo "[DRY RUN] cd $BACKEND_DIR"
    echo "[DRY RUN] bash $BACKEND_DIR/start.sh"
    exit 0
fi

exec bash "$BACKEND_DIR/start.sh"