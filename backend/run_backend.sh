#!/bin/bash
# Stable backend startup script

# Kill any existing processes on port 8000
echo "Cleaning up existing processes on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

# Start the backend server
echo "Starting backend server..."
cd "$(dirname "$0")"

# Try the simple startup first (no auto-reload)
python3 start_server_simple.py