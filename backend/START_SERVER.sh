#!/bin/bash
# Start Backend Server - Ensures correct venv and dependencies

cd "$(dirname "$0")"

echo "=========================================="
echo "Starting Backend Server"
echo "=========================================="
echo ""

# Check if we're in backend directory
if [ ! -f "app/main.py" ]; then
    echo "ERROR: Must run from backend/ directory"
    exit 1
fi

# Use backend's venv (create if needed)
if [ -d "venv" ]; then
    echo "✓ Using backend venv"
    source venv/bin/activate
elif [ -d "../.venv" ]; then
    echo "⚠ Using root .venv (not recommended)"
    source ../.venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Check if fastapi is installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo ""
    echo "FastAPI not found. Installing dependencies..."
    pip install --upgrade pip --quiet
    pip install fastapi uvicorn[standard] sqlalchemy pydantic pydantic-settings --quiet
    pip install python-jose[cryptography] passlib[bcrypt] python-multipart --quiet
    echo "Installing remaining dependencies..."
    pip install -r requirements.txt 2>&1 | grep -E "(Installing|Successfully)" | tail -5
fi

# Verify installation
echo ""
echo "Verifying installation..."
python3 -c "import fastapi; import uvicorn; print('✓ Dependencies OK')" || {
    echo "✗ Dependencies missing. Please install manually:"
    echo "  pip install -r requirements.txt"
    exit 1
}

echo ""
echo "=========================================="
echo "Starting Server"
echo "=========================================="
echo ""
echo "Backend will be available at:"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop"
echo ""

# Start server
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

