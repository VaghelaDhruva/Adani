#!/bin/bash
# Start Backend Server

cd "$(dirname "$0")/backend"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start server
echo "Starting FastAPI backend server..."
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

