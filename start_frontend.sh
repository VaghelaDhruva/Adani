#!/bin/bash
# Start Frontend Server

cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start React app
echo "Starting React frontend..."
echo "Frontend will be available at: http://localhost:3000"
echo ""
npm start

