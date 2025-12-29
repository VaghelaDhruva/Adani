# Supply Chain Optimization System - Complete Setup Guide

This guide will help you set up the complete supply chain optimization system with real calculated figures and interactive dashboards.

## 🚀 Quick Start (Automated Setup)

### Prerequisites
- Python 3.9+ installed
- Virtual environment activated in the `backend` directory

### One-Command Setup
```bash
cd backend
python3 setup_system.py
```

This will:
1. ✅ Initialize the database with all required tables
2. ✅ Load realistic sample data (plants, routes, demand, etc.)
3. ✅ Run a test optimization to verify everything works
4. ✅ Generate real KPI data for the dashboard

## 📋 Manual Setup (Step by Step)

If you prefer to set up manually or need to troubleshoot:

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
python3 install_optimization_packages.py
```

### Step 2: Initialize Database
```bash
python3 init_db.py
```

### Step 3: Load Sample Data
```bash
python3 load_sample_data.py
```

### Step 4: Start Backend Server
```bash
python3 -m uvicorn app.main:app --reload
```

### Step 5: Start Frontend Dashboard
```bash
cd ../frontend
streamlit run streamlit_app/main.py
```

## 🎯 What You Get

### Real Optimization Engine
- **Pyomo-based MILP model** with HiGHS/CBC solvers
- **Production planning** across multiple plants
- **Transport optimization** with multiple modes
- **Inventory management** with safety stock constraints
- **Cost minimization** with realistic Indian cement industry data

### Calculated KPI Dashboard
- **Real cost breakdowns** from optimization results
- **Production utilization** by plant and period
- **Transport efficiency** with SBQ compliance tracking
- **Service level metrics** with demand fulfillment analysis
- **Inventory status** with safety stock monitoring

### Interactive Charts & Visualizations
- **Cost summary pie charts** with INR formatting
- **Plant utilization bar charts** with capacity warnings
- **Transport mode analysis** with compliance tracking
- **Demand fulfillment tracking** by location
- **Service performance trends** over time

## 📊 Sample Data Included

### Plants (3 locations)
- **Mumbai Clinker Plant** - 100,000 tonnes capacity
- **Delhi Grinding Unit** - 75,000 tonnes capacity  
- **Chennai Terminal** - 60,000 tonnes capacity

### Transport Network
- **9 routes** across road/rail modes
- **Realistic costs** based on Indian logistics
- **Capacity constraints** and lead times

### Demand Patterns
- **7 customer locations** across India
- **Monthly demand forecasts** with seasonality
- **108,000 tonnes total monthly demand**

### Cost Structure
- **Production costs**: ₹1,650-1,850 per tonne
- **Transport costs**: ₹75-140 per tonne
- **Inventory holding**: ₹10 per tonne per period
- **Stockout penalties**: ₹2,000 per tonne

## 🔧 System Architecture

```
┌─────────────────────┐
│   Streamlit         │
│   Dashboard         │ ← Real-time KPI display
└──────────┬──────────┘
           │ HTTP API calls
┌──────────▼──────────┐
│   FastAPI           │
│   Backend           │ ← REST API endpoints
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Optimization      │
│   Service           │ ← Pyomo + HiGHS solver
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   SQLite            │
│   Database          │ ← Results persistence
└─────────────────────┘
```

## 🎮 How to Use

### 1. Run Optimization
```bash
# Via API
curl -X POST "http://localhost:8000/api/v1/kpi/run-optimization?scenario_name=base"

# Via Dashboard
# Go to Optimization Console page and click "Run Optimization"
```

### 2. View Results
- **KPI Dashboard**: Real calculated costs, utilization, service levels
- **Scenario Comparison**: Compare multiple optimization runs
- **Results Dashboard**: Detailed production plans and shipment routing

### 3. Try Different Scenarios
- **Base**: Normal operations
- **High Demand**: 25% demand increase
- **Low Demand**: 20% demand decrease
- **Capacity Constrained**: 15% capacity reduction
- **Transport Disruption**: 35% transport cost increase

## 📈 Key Features

### ✅ Real Optimization Results
- No more mock data - all figures calculated from actual MILP solver
- Production plans optimized across plants and periods
- Transport routing with mode selection and capacity constraints
- Inventory management with safety stock compliance

### ✅ Enterprise-Grade KPIs
- **Financial**: Total cost, cost per tonne, cost breakdown
- **Operational**: Capacity utilization, production efficiency
- **Service**: Demand fulfillment, on-time delivery, service level
- **Quality**: SBQ compliance, safety stock adherence

### ✅ Interactive Visualizations
- Cost breakdown pie charts with Indian Rupee formatting
- Plant utilization with capacity warning indicators
- Transport mode analysis with compliance tracking
- Demand fulfillment by location and period

### ✅ Data Quality Pipeline
- 5-stage validation before optimization
- Clean data service ensures data integrity
- Validation gating prevents optimization with bad data

## 🔍 API Endpoints

### Optimization
- `POST /api/v1/kpi/run-optimization` - Execute optimization
- `GET /api/v1/kpi/optimization-status/{run_id}` - Check status
- `GET /api/v1/kpi/scenarios/list` - List available scenarios

### KPI Data
- `GET /api/v1/kpi/dashboard/{scenario_name}` - Get KPI dashboard
- `GET /api/v1/dashboard/kpi/dashboard/{scenario_name}` - Alternative endpoint
- `POST /api/v1/kpi/compare` - Compare scenarios

### System Health
- `GET /api/v1/dashboard/health-status` - System health check
- `GET /api/v1/kpi/health` - KPI service health

## 🐛 Troubleshooting

### Common Issues

**1. Solver Not Found**
```bash
# Install HiGHS solver
pip install highspy

# Or use CBC as fallback
pip install pulp
```

**2. Database Connection Error**
```bash
# Reinitialize database
python3 init_db.py
```

**3. Import Errors**
```bash
# Ensure all packages installed
pip install -r requirements.txt
python3 install_optimization_packages.py
```

**4. Optimization Fails**
```bash
# Check data validation
curl http://localhost:8000/api/v1/dashboard/health-status

# Reload sample data
python3 load_sample_data.py
```

### Logs and Debugging
- Backend logs: Check terminal running uvicorn
- Frontend logs: Check Streamlit terminal
- Database: SQLite file at `backend/clinker_supply_chain.db`

## 🎉 Success Indicators

When everything is working correctly, you should see:

1. **Backend API**: http://localhost:8000/docs shows all endpoints
2. **Health Check**: Returns "HEALTHY" status with validation passed
3. **KPI Dashboard**: Shows real calculated costs (not mock data)
4. **Optimization**: Completes in 30-60 seconds with optimal solution
5. **Charts**: Display real production, transport, and service data

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are installed
3. Run the automated setup script again
4. Check logs for specific error messages

The system is now ready to display real calculated figures and interactive charts based on actual supply chain optimization results!