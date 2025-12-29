# 📊 Data Ingestion Sources - Complete Analysis

## 🎯 **ACTUAL Data Sources in Your System**

Based on the codebase analysis, here are the **real data sources** your Clinker Supply Chain Optimization System uses:

---

## 1. 📁 **File Upload Sources (Primary)**

### **A. CSV File Upload**
```python
# Location: frontend/streamlit_app/pages/01_data_upload_and_validation.py
# API Endpoint: POST /api/v1/data/upload_csv

SUPPORTED_FILE_TYPES = [".csv", ".xlsx", ".xls"]

# Users can upload files through the web interface:
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])

# Files are processed by:
# backend/app/services/ingestion/csv_ingestion.py
# backend/app/services/ingestion/excel_ingestion.py
```

### **B. File Processing Pipeline**
```python
# Location: backend/app/services/ingestion/tabular_ingestion.py

def ingest_dataframe(df, db, filename, explicit_table_name=None):
    """
    Complete ingestion pipeline:
    1. Table Detection (from filename)
    2. Schema Validation (Pydantic models)
    3. Business Rules Validation
    4. Referential Integrity Checks
    5. Database Insert
    6. Audit Logging
    """
```

### **C. Table Detection Logic**
```python
def _detect_table_name(df, filename, explicit):
    """
    Automatic table detection based on filename:
    """
    lowered = filename.lower()
    
    if lowered.startswith("plant"):
        return "plant_master"
    elif lowered.startswith("demand"):
        return "demand_forecast"
    elif lowered.startswith("route") or "transport" in lowered:
        return "transport_routes_modes"
    elif "safety" in lowered:
        return "safety_stock_policy"
    elif "inventory" in lowered:
        return "initial_inventory"
```

---

## 2. 🗄️ **Database Sources (Current)**

### **A. Sample Data Generation**
```python
# Location: backend/create_sample_data.py
# Purpose: Creates realistic demo data for testing

def create_sample_data():
    """
    Creates complete sample dataset:
    - 4 Plants (Mumbai, Delhi, Chennai, Kolkata)
    - 4 Periods (2025-01 to 2025-04)
    - 13 Transport Routes
    - 11 Customers with demand forecasts
    - Production capacity data
    - Safety stock policies
    - Initial inventory levels
    """
```

### **B. Demo Seed Data**
```python
# Location: scripts/demo_seed_data.py
# Purpose: Minimal demo data for quick testing

def seed():
    """
    Creates minimal demo dataset:
    - 2 Plants (P1, P2)
    - 1 Customer (C1)
    - 3 Periods (2025-W01 to 2025-W03)
    - Basic transport routes
    - Simple demand patterns
    """
```

### **C. Database Tables Structure**
```sql
-- Current tables that receive data:
plant_master              -- Plant information
production_capacity_cost  -- Production capacity by period
transport_routes_modes    -- Transport routes and costs
demand_forecast          -- Customer demand by period
initial_inventory        -- Starting inventory levels
safety_stock_policy      -- Safety stock requirements
```

---

## 3. 📈 **Generated/Calculated Data Sources**

### **A. KPI Dashboard Data**
```python
# Location: backend/app/api/v1/routes_dashboard_demo.py

def _generate_enterprise_kpi_data(scenario_name):
    """
    GENERATES data dynamically based on:
    - Scenario parameters (base, high_demand, etc.)
    - Run ID hashing for consistency
    - Time-based variations
    - Realistic business patterns
    
    NOT from database - purely calculated!
    """
```

### **B. Optimization Results**
```python
# Location: backend/app/api/v1/routes_runs.py

def _generate_optimization_result(run_id):
    """
    SIMULATES optimization results:
    - Production plans by plant/period
    - Shipment plans by route/mode
    - Inventory levels over time
    - Cost breakdowns
    - Performance metrics
    
    Uses mathematical formulas, not real optimization!
    """
```

---

## 4. 🔄 **Data Flow Architecture**

### **Current Data Flow:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Upload   │    │   Database      │    │   Generated     │
│   (CSV/Excel)   │───►│   Storage       │───►│   Results       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌────▼────┐             ┌────▼────┐             ┌────▼────┐
    │Validation│             │ Sample  │             │Dashboard│
    │Pipeline  │             │  Data   │             │  KPIs   │
    └─────────┘             └─────────┘             └─────────┘
```

### **Validation Pipeline (5 Stages):**
```python
# Location: backend/app/services/ingestion/tabular_ingestion.py

def _validate_and_normalize(df, table_name, db):
    """
    Stage 1: Schema Validation (Pydantic)
    Stage 2: Business Rules (no negative values, valid modes)
    Stage 3: Referential Integrity (foreign keys exist)
    Stage 4: Unit Consistency (tonnes, km, INR)
    Stage 5: Missing Data Handling
    """
```

---

## 5. 📋 **Expected File Formats**

### **A. Plant Master CSV**
```csv
plant_id,plant_name,plant_type,latitude,longitude,region,country
PLANT_MUM,Mumbai Clinker Plant,clinker,19.0760,72.8777,West,India
PLANT_DEL,Delhi Grinding Unit,grinding,28.7041,77.1025,North,India
```

### **B. Demand Forecast CSV**
```csv
customer_node_id,period,demand_tonnes,confidence_level,source
CUST_MUM_001,2025-01,8000,0.85,forecast_model
CUST_DEL_001,2025-01,7000,0.85,forecast_model
```

### **C. Transport Routes CSV**
```csv
origin_plant_id,destination_node_id,transport_mode,distance_km,cost_per_tonne,vehicle_capacity_tonnes
PLANT_MUM,CUST_MUM_001,road,50,150,25
PLANT_DEL,CUST_DEL_001,road,40,120,25
```

### **D. Production Capacity CSV**
```csv
plant_id,period,max_capacity_tonnes,variable_cost_per_tonne,fixed_cost_per_period
PLANT_MUM,2025-01,50000,2500,500000
PLANT_DEL,2025-01,30000,2800,500000
```

### **E. Initial Inventory CSV**
```csv
node_id,period,inventory_tonnes
PLANT_MUM,2025-01,5000
PLANT_DEL,2025-01,5000
```

### **F. Safety Stock Policy CSV**
```csv
node_id,policy_type,policy_value,safety_stock_tonnes
PLANT_MUM,days_of_cover,7,3500
PLANT_DEL,days_of_cover,5,2500
```

---

## 6. 🚫 **What's NOT Currently Implemented**

### **Missing Data Sources:**
- ❌ **ERP System Integration** (SAP, Oracle)
- ❌ **External API Connections** (Weather, Market Data)
- ❌ **Real-time Data Streams**
- ❌ **IoT Sensor Data**
- ❌ **Automated Data Refresh**

### **Placeholder Code Found:**
```python
# Location: scripts/ingest_company_reports.py - EXISTS but not implemented
# Location: scripts/ingest_iea.py - EXISTS but not implemented  
# Location: scripts/ingest_usgs.py - EXISTS but not implemented
# Location: scripts/backfill_routes_osrm.py - EXISTS but not implemented
```

---

## 7. 🎯 **Summary: Where Data Actually Comes From**

### **✅ ACTIVE Data Sources:**
1. **Manual File Upload** - Users upload CSV/Excel files via web interface
2. **Sample Data Generator** - `create_sample_data.py` creates realistic demo data
3. **Demo Seed Script** - `demo_seed_data.py` creates minimal test data
4. **Generated KPI Data** - Mathematical calculations simulate business metrics
5. **Simulated Results** - Algorithms generate realistic optimization outcomes

### **📊 Data Processing:**
1. **File Upload** → **Validation Pipeline** → **Database Storage**
2. **Database Query** → **Business Logic** → **Dashboard Display**
3. **Scenario Parameters** → **Mathematical Generation** → **KPI Metrics**

### **🔄 Current Limitations:**
- **No real ERP integration** - All data is manually uploaded or generated
- **No external APIs** - Weather, market data not connected
- **No real optimization** - Results are mathematically simulated
- **No automated refresh** - Data updates require manual intervention

### **💡 Key Insight:**
Your system is currently a **sophisticated simulation platform** that:
- Accepts real data through file uploads
- Validates and stores it properly
- Generates realistic business scenarios
- Displays professional dashboards
- But doesn't run actual optimization algorithms

The infrastructure is **production-ready** for real data integration - you just need to connect actual data sources and implement the real optimization engine!