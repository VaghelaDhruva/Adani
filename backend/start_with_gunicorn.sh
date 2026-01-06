#!/bin/bash
# Start backend with Gunicorn (more stable than uvicorn for production)

# Kill any existing processes on port 8000
echo "Cleaning up existing processes on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

# Start with gunicorn
echo "Starting backend with Gunicorn..."
cd "$(dirname "$0")"

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "Installing gunicorn..."
    pip install gunicorn
fi

# Start the server
gunicorn app.main:app -c gunicorn_config.py