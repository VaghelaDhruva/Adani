#!/bin/bash
# Quick Start Script - Install dependencies and start backend

set -e

cd "$(dirname "$0")"

echo "=========================================="
echo "Starting Backend Setup"
echo "=========================================="
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    echo "✓ Virtual environment found"
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install dependencies
echo ""
echo "Installing Python dependencies..."
echo "This may take a few minutes..."
pip install --upgrade pip --quiet
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings --quiet
pip install -r requirements.txt 2>&1 | grep -v "already satisfied" | tail -5

# Initialize database
echo ""
echo "Initializing database..."
python3 init_db.py 2>&1 || {
    echo "Database initialization..."
    python3 -c "
from app.db.session import engine
from app.db.base import Base
import app.db.models
Base.metadata.create_all(bind=engine)
print('✓ Database initialized')
"
}

# Load sample data if database is empty
if [ ! -f "clinker_supply_chain.db" ] || [ ! -s "clinker_supply_chain.db" ]; then
    echo ""
    echo "Loading sample data..."
    python3 load_sample_data.py 2>&1 | tail -3 || echo "Note: Sample data loading may have issues, but continuing..."
fi

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Starting backend server..."
echo "Backend will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start server
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

