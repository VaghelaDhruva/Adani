# 🚨 Backend Not Running - Quick Fix

Your frontend is trying to connect to the backend but getting `ECONNREFUSED` errors. This means the backend server isn't running.

## Quick Fix (Choose One)

### Option 1: Automated Script (Easiest)

```bash
cd backend
./quick_start.sh
```

This will:
- Install all dependencies
- Initialize database
- Load sample data
- Start the backend server

### Option 2: Manual Steps

**Step 1: Install Dependencies**
```bash
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy pydantic
pip install -r requirements.txt
```

**Step 2: Initialize Database**
```bash
python3 init_db.py
```

**Step 3: Load Sample Data (Optional)**
```bash
python3 load_sample_data.py
```

**Step 4: Start Backend**
```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verify Backend is Running

Once started, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Then test:
```bash
curl http://localhost:8000/api/v1/health
```

Or open in browser: http://localhost:8000/docs

## Frontend Should Now Work

Once backend is running, refresh your frontend at http://localhost:3000 and the proxy errors should disappear!

## Troubleshooting

**Port 8000 already in use:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python3 -m uvicorn app.main:app --reload --port 8001
# Then update frontend package.json proxy to "http://localhost:8001"
```

**Import errors:**
- Make sure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**Database errors:**
- Delete old database: `rm clinker_supply_chain.db`
- Reinitialize: `python3 init_db.py`

