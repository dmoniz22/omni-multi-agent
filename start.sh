#!/bin/bash
set -e

# Start uvicorn in background
echo "Starting OMNI API on port ${API_PORT:-8000}..."
python -m uvicorn omni.api.app:app --host 0.0.0.0 --port ${API_PORT:-8000} &

# Start dashboard
echo "Starting OMNI Dashboard on port 7860..."
python -m omni.dashboard.main
