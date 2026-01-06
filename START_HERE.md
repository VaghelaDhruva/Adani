# 🚀 START HERE - Get Running in 5 Minutes

## Quick Setup

### 1. Backend Setup (Terminal 1)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 init_db.py
python3 load_sample_data.py
```

### 2. Start Backend

```bash
# Still in backend/ directory with venv activated
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ You should see: `INFO: Uvicorn running on http://0.0.0.0:8000`

### 3. Start Frontend (Terminal 2)

```bash
cd frontend
npm install  # First time only
npm start
```

✅ You should see: `Compiled successfully!` and browser opens to http://localhost:3000

## 🎯 Access Points

- **Frontend Dashboard:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## 🧪 Quick Test

1. Open http://localhost:8000/docs - You should see the API documentation
2. Open http://localhost:3000 - You should see the dashboard
3. Go to "Optimization Console" page
4. Click "Run Optimization" with scenario "base"
5. Wait for job to complete (30-60 seconds)
6. View results!

## 📚 More Details

- **Full Setup Guide:** See `LOCAL_SETUP.md`
- **Architecture:** See `PRODUCTION_READINESS_REVIEW.md`
- **Integration:** See `INTEGRATION_GUIDE.md`

## ⚠️ Troubleshooting

**Backend won't start?**
- Make sure you're in `backend/` directory
- Make sure virtual environment is activated: `source venv/bin/activate`
- Check Python version: `python3 --version` (need 3.9+)

**Frontend won't start?**
- Make sure you're in `frontend/` directory
- Run `npm install` first
- Check Node version: `node --version` (need 16+)

**Optimization fails?**
- Make sure sample data is loaded: `python3 load_sample_data.py`
- Check backend logs for errors

## 🎉 That's It!

You're ready to use the Clinker Optimization Platform!

---

**Need help?** Check `LOCAL_SETUP.md` for detailed troubleshooting.

