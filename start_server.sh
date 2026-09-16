#!/bin/bash

echo "Starting Medica AI Medical Assistant Server..."

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the API server on port 8080 (which also serves the frontend UI)
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8080 --reload
