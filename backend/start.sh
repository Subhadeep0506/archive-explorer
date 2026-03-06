#!/usr/bin/env bash
set -e

# Activate virtual environment based on OS
if [[ "$(uname -s)" == "Linux" ]]; then
    source .venv/bin/activate
else
    source .venv/Scripts/activate
fi

# Set default port
export PORT="${PORT:-8000}"

# Run the application
python run.py
