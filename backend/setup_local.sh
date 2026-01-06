#!/bin/bash
# Complete Local Setup Script for Clinker Optimization Platform

set -e  # Exit on error

echo "=========================================="
echo "Clinker Optimization Platform - Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Check if Pyomo is installed
echo -e "${YELLOW}Checking optimization packages...${NC}"
python3 -c "import pyomo; print('Pyomo OK')" 2>/dev/null || {
    echo -e "${YELLOW}Installing Pyomo...${NC}"
    pip install pyomo
}

# Check if solver is available
echo -e "${YELLOW}Checking solver availability...${NC}"
python3 -c "from pyomo.opt import SolverFactory; s = SolverFactory('cbc'); print('CBC solver OK')" 2>/dev/null || {
    echo -e "${YELLOW}Note: CBC solver not found. Will use available solver.${NC}"
}

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
python3 init_db.py

# Load sample data if it doesn't exist
if [ ! -f "clinker_supply_chain.db" ] || [ ! -s "clinker_supply_chain.db" ]; then
    echo -e "${YELLOW}Loading sample data...${NC}"
    python3 load_sample_data.py || echo -e "${RED}Warning: Sample data loading failed. You may need to load data manually.${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Start the backend server:"
echo "   ${GREEN}source venv/bin/activate${NC}"
echo "   ${GREEN}python3 -m uvicorn app.main:app --reload${NC}"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   ${GREEN}cd frontend${NC}"
echo "   ${GREEN}npm install${NC}"
echo "   ${GREEN}npm start${NC}"
echo ""
echo "3. Access the application:"
echo "   Backend API: ${GREEN}http://localhost:8000${NC}"
echo "   API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo "   Frontend: ${GREEN}http://localhost:3000${NC}"
echo ""
echo "4. Test the system:"
echo "   ${GREEN}curl http://localhost:8000/api/v1/health${NC}"
echo ""

