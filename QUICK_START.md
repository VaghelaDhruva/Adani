# Quick Start Guide - Local Setup

## Prerequisites

- Python 3.9+ installed
- Node.js 16+ installed (for frontend)
- Git (already have it since you cloned)

## Step 1: Backend Setup

### Option A: Automated Setup (Recommended)

```bash
cd backend
chmod +x setup_local.sh
./setup_local.sh
```

### Option B: Manual Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database
python3 init_db.py

# Load sample data
python3 load_sample_data.py
```

## Step 2: Start Backend Server

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 3: Frontend Setup (New Terminal)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

You should see:
```
Compiled successfully!
You can now view clinker-supply-chain-frontend in the browser.
  Local:            http://localhost:3000
```

## Step 4: Verify Setup

### Test Backend API

Open in browser: http://localhost:8000/docs

Or test with curl:
```bash
curl http://localhost:8000/api/v1/health
```

### Test Frontend

Open in browser: http://localhost:3000

## Step 5: Run Your First Optimization

### Via API (using curl or Postman)

```bash
# Submit optimization job
curl -X POST "http://localhost:8000/api/v1/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_name": "base",
    "solver": "cbc",
    "time_limit": 300,
    "mip_gap": 0.01
  }'

# This returns a job_id. Poll for status:
curl "http://localhost:8000/api/v1/optimize/{job_id}/status"

# When status is "success", get results:
curl "http://localhost:8000/api/v1/optimize/{job_id}/results"
```

### Via Frontend Dashboard

1. Navigate to http://localhost:3000
2. Go to "Optimization Console" page
3. Select scenario and click "Run Optimization"
4. Monitor job status
5. View results when complete

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Use different port
python3 -m uvicorn app.main:app --reload --port 8001
```

**Database errors:**
```bash
# Reinitialize database
cd backend
python3 init_db.py
python3 load_sample_data.py
```

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Issues

**Port 3000 already in use:**
```bash
# React will automatically use next available port (3001, 3002, etc.)
```

**npm install fails:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Proxy errors:**
- Make sure backend is running on port 8000
- Check `package.json` has `"proxy": "http://localhost:8000"`

### Solver Issues

**Pyomo not found:**
```bash
pip install pyomo
```

**Solver not available:**
```bash
# Install CBC solver (recommended)
# On macOS:
brew install cbc

# On Linux:
sudo apt-get install coinor-cbc

# Or use HiGHS (Python package)
pip install highspy
```

## What to Expect

### Backend Endpoints

- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health
- **System Info:** http://localhost:8000/api/v1/system/info

### Frontend Pages

- **Dashboard:** http://localhost:3000/dashboard
- **Optimization Console:** http://localhost:3000/optimization
- **Results:** http://localhost:3000/results
- **Scenarios:** http://localhost:3000/scenarios

## Next Steps

1. **Explore the API:** Visit http://localhost:8000/docs
2. **Run an optimization:** Use the Optimization Console
3. **View results:** Check the Results page
4. **Compare scenarios:** Use the Scenario Comparison page

## Need Help?

- Check `PRODUCTION_READINESS_REVIEW.md` for architecture details
- Check `INTEGRATION_GUIDE.md` for integration details
- Review backend logs in terminal
- Review frontend logs in browser console (F12)

