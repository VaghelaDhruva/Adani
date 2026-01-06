#!/bin/bash
# Complete Setup and Start Script

set -e

cd "$(dirname "$0")"

echo "=========================================="
echo "Backend Setup & Start"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "init_db.py" ]; then
    echo "ERROR: init_db.py not found!"
    echo "Make sure you're in the backend/ directory"
    exit 1
fi

# Create/activate virtual environment
if [ -d "venv" ]; then
    echo "✓ Using existing virtual environment"
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ Virtual environment created"
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install core dependencies first
echo ""
echo "Installing core dependencies..."
pip install fastapi uvicorn[standard] sqlalchemy pydantic pydantic-settings --quiet
pip install python-jose[cryptography] passlib[bcrypt] python-multipart --quiet

# Install remaining dependencies
echo "Installing remaining dependencies (this may take a few minutes)..."
pip install -r requirements.txt 2>&1 | grep -E "(Installing|Requirement|Successfully|ERROR)" | tail -10

# Verify critical packages
echo ""
echo "Verifying installation..."
python3 -c "import fastapi; import uvicorn; import sqlalchemy; print('✓ Core packages installed')" || {
    echo "ERROR: Core packages not installed correctly"
    exit 1
}

# Initialize database
echo ""
echo "Initializing database..."
python3 init_db.py 2>&1 || {
    echo "Trying alternative database initialization..."
    python3 -c "
from app.db.session import engine
from app.db.base import Base
import app.db.models
Base.metadata.create_all(bind=engine)
print('✓ Database initialized')
"
}

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Starting backend server..."
echo ""
echo "Backend will be available at:"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start server
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

