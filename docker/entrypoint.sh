#!/bin/bash
set -e

# Activate poetry's virtual environment
source /app/.venv/bin/activate

# Add source to Python path
export PYTHONPATH="/app/src:$PYTHONPATH"

# Execute the command with all arguments
exec python -m ocat.cli "$@"
