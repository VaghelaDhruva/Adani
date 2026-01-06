#!/bin/bash
# Start Backend - Install dependencies if needed and start server

cd "$(dirname "$0")"

echo "=========================================="
echo "Backend Startup"
echo "=========================================="

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Check if fastapi is installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo ""
    echo "Installing dependencies (this may take a few minutes)..."
    pip install --upgrade pip --quiet
    pip install fastapi uvicorn[standard] sqlalchemy pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] --quiet
    echo "Installing remaining dependencies..."
    pip install -r requirements.txt 2>&1 | grep -E "(Installing|Requirement|Successfully)" | tail -3
    echo "✓ Dependencies installed"
fi

# Initialize database if needed
if [ ! -f "clinker_supply_chain.db" ]; then
    echo ""
    echo "Initializing database..."
    python3 init_db.py 2>&1 | tail -3 || {
        echo "Initializing database (alternative method)..."
        python3 -c "
from app.db.session import engine
from app.db.base import Base
import app.db.models
Base.metadata.create_all(bind=engine)
print('✓ Database initialized')
"
    }
fi

echo ""
echo "=========================================="
echo "Starting Backend Server"
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

