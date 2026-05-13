#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ACTIVATE_SCRIPT=""
if [[ -f "$SCRIPT_DIR/.venv/bin/activate" ]]; then
    ACTIVATE_SCRIPT="$SCRIPT_DIR/.venv/bin/activate"
elif [[ -f "$SCRIPT_DIR/.venv/Scripts/activate" ]]; then
    ACTIVATE_SCRIPT="$SCRIPT_DIR/.venv/Scripts/activate"
else
    echo "[ERROR] No virtual environment activation script found in $SCRIPT_DIR/.venv." >&2
    exit 1
fi

export PORT="${PORT:-8000}"

if [[ "${ARXIVER_DRY_RUN:-0}" == "1" ]]; then
    echo "[DRY RUN] cd $SCRIPT_DIR"
    echo "[DRY RUN] source $ACTIVATE_SCRIPT"
    echo "[DRY RUN] PORT=$PORT python run.py"
    exit 0
fi

# Select the activation script by filesystem layout so this works in Linux, macOS,
# WSL, and Git Bash without relying on uname quirks.
source "$ACTIVATE_SCRIPT"

exec python run.py
