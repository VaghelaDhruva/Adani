# Local Setup & Run Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Backend Setup

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

### Step 2: Start Backend

**Option A: Using the script**
```bash
# From project root
./start_backend.sh
```

**Option B: Manual**
```bash
cd backend
source venv/bin/activate
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 3: Start Frontend (New Terminal)

**Option A: Using the script**
```bash
# From project root
./start_frontend.sh
```

**Option B: Manual**
```bash
cd frontend
npm install  # First time only
npm start
```

You should see:
```
Compiled successfully!
You can now view clinker-supply-chain-frontend in the browser.
  Local:            http://localhost:3000
```

### Step 4: Access the Application

- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Frontend Dashboard:** http://localhost:3000

## 📋 Detailed Setup

### Prerequisites Check

```bash
# Check Python version (need 3.9+)
python3 --version

# Check Node.js version (need 16+)
node --version
npm --version
```

### Backend Dependencies

The backend requires:
- FastAPI
- SQLAlchemy
- Pyomo (optimization)
- CBC/HiGHS solver

Install all with:
```bash
cd backend
pip install -r requirements.txt
```

### Database Setup

The database is SQLite (no separate server needed). It will be created automatically:

```bash
cd backend
python3 init_db.py
```

This creates:
- All core tables (plants, demand, routes, etc.)
- Job queue tables
- RBAC tables (users, roles)
- KPI tables
- Scenario tables

### Sample Data

Load sample data for testing:

```bash
cd backend
python3 load_sample_data.py
```

This creates:
- 3 plants (Mumbai, Delhi, Chennai)
- 7 customers
- 9 transport routes
- Monthly demand forecasts
- Cost data

## 🧪 Testing the Setup

### Test Backend

```bash
# Health check
curl http://localhost:8000/api/v1/health

# System info
curl http://localhost:8000/api/v1/system/info

# Open API docs
open http://localhost:8000/docs  # macOS
# Or visit in browser
```

### Test Frontend

1. Open http://localhost:3000
2. You should see the dashboard
3. Navigate to different pages:
   - Dashboard
   - Optimization Console
   - Results
   - Scenarios

### Test Optimization

**Via API:**
```bash
# Submit job
curl -X POST "http://localhost:8000/api/v1/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_name": "base",
    "solver": "cbc",
    "time_limit": 300,
    "mip_gap": 0.01
  }'

# Response will include job_id
# Poll for status:
curl "http://localhost:8000/api/v1/optimize/{job_id}/status"

# Get results when complete:
curl "http://localhost:8000/api/v1/optimize/{job_id}/results"
```

**Via Frontend:**
1. Go to http://localhost:3000/optimization
2. Select scenario "base"
3. Click "Run Optimization"
4. Monitor job status
5. View results when complete

## 🔧 Troubleshooting

### Backend Won't Start

**Port 8000 already in use:**
```bash
# Use different port
python3 -m uvicorn app.main:app --reload --port 8001
```

**Import errors:**
```bash
# Make sure you're in the backend directory
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Database errors:**
```bash
# Reinitialize database
python3 init_db.py
python3 load_sample_data.py
```

**Pyomo not found:**
```bash
pip install pyomo
```

**Solver not available:**
```bash
# Install CBC solver
# macOS:
brew install cbc

# Linux:
sudo apt-get install coinor-cbc

# Or use HiGHS (Python package)
pip install highspy
```

### Frontend Won't Start

**Port 3000 already in use:**
- React will automatically use the next available port (3001, 3002, etc.)

**npm install fails:**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Proxy errors:**
- Make sure backend is running on port 8000
- Check `package.json` has `"proxy": "http://localhost:8000"`

**Module not found:**
```bash
npm install
```

### Optimization Fails

**No data:**
```bash
cd backend
python3 load_sample_data.py
```

**Solver timeout:**
- Increase `time_limit` in request
- Use faster solver (HiGHS instead of CBC)

**Infeasible solution:**
- Check data validation: http://localhost:8000/api/v1/data/validation
- Review demand vs capacity

## 📁 Project Structure

```
Adani/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   ├── core/             # Config, security, RBAC
│   │   ├── db/               # Database models
│   │   ├── services/         # Business logic
│   │   └── utils/             # Utilities
│   ├── init_db.py            # Database initialization
│   ├── load_sample_data.py   # Sample data loader
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   └── services/         # API clients
│   └── package.json         # Node dependencies
├── start_backend.sh          # Backend startup script
└── start_frontend.sh         # Frontend startup script
```

## 🎯 What You Can Do

### 1. Run Optimizations
- Submit optimization jobs via API or UI
- Monitor job status in real-time
- View detailed results

### 2. View Dashboards
- KPI dashboard with cost breakdowns
- Production utilization charts
- Transport efficiency metrics
- Service level tracking

### 3. Manage Scenarios
- Create multiple scenarios
- Compare scenario results
- Approve plans as baseline

### 4. Data Management
- Upload data via CSV/Excel
- Validate data quality
- View data health metrics

## 📚 Next Steps

1. **Explore API:** Visit http://localhost:8000/docs
2. **Run optimization:** Use Optimization Console
3. **View results:** Check Results page
4. **Compare scenarios:** Use Scenario Comparison
5. **Read documentation:**
   - `PRODUCTION_READINESS_REVIEW.md` - Architecture
   - `INTEGRATION_GUIDE.md` - Integration details
   - `QUICK_START.md` - Quick reference

## 💡 Tips

- **Keep both terminals open:** One for backend, one for frontend
- **Check logs:** Backend logs show in terminal, frontend in browser console (F12)
- **API docs:** Use http://localhost:8000/docs to test endpoints
- **Database:** SQLite file is at `backend/clinker_supply_chain.db`

## 🆘 Need Help?

1. Check this guide
2. Review error messages in terminal/browser
3. Check `PRODUCTION_READINESS_REVIEW.md` for architecture details
4. Verify all prerequisites are installed
5. Try re-running setup steps

---

**You're all set!** 🎉

Start the backend and frontend, then visit http://localhost:3000 to see your dashboard.

