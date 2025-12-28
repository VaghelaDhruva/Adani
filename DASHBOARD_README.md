# Clinker Supply Chain Optimization Dashboard

A production-ready dashboard system that ensures **ONLY clean, validated data** reaches the optimization engine. This comprehensive system implements a strict data quality pipeline with 5-stage validation and provides full visibility into the supply chain optimization process.

## 🎯 Key Features

### ✅ STRICT DATA QUALITY ENFORCEMENT
- **5-Stage Validation Pipeline**: Schema → Business Rules → Referential Integrity → Unit Consistency → Missing Data
- **Optimization Gating**: Model runs ONLY when all validation stages pass
- **Clean Data Pipeline**: Automated normalization and cleaning before optimization
- **Zero Tolerance**: No raw CSVs, unvalidated uploads, or partial data ever reach the model

### 📊 COMPREHENSIVE MONITORING
- **Real-time Data Health**: Live monitoring of all database tables
- **Row-level Error Detection**: Identifies specific problematic records
- **Data Freshness Tracking**: Monitors when data was last updated
- **Validation Status Dashboard**: Visual indicators for each validation stage

### 🚀 CONTROLLED OPTIMIZATION
- **Validation-Gated Execution**: Run button enabled only when data is clean
- **Multiple Solver Support**: HiGHS, CBC, Gurobi with automatic fallback
- **Real-time Progress**: Live status updates during optimization
- **Comprehensive Results**: Cost breakdown, production plans, shipment routing

### 📈 RICH VISUALIZATIONS
- **Interactive Charts**: Plotly-based visualizations for all metrics
- **Export Capabilities**: JSON, CSV, and PDF export options
- **Scenario Comparison**: Side-by-side analysis of different scenarios
- **KPI Dashboards**: Service level, capacity utilization, cost analysis

## 🏗️ System Architecture

```
┌─────────────────────┐
│   Database Tables   │
│  (Raw Data Store)   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Data Health        │
│  Monitoring Service │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  5-Stage Validation │
│  Pipeline           │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Clean Data         │
│  Service            │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Optimization       │
│  Engine (MILP)      │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Results Dashboard  │
│  & Visualization    │
└─────────────────────┘
```

## 📋 Dashboard Pages

### 1. 🏥 Data Health Status Dashboard
**Purpose**: Top-level monitoring of data quality across all tables

**Features**:
- Overall data status indicator (PASS/WARN/FAIL)
- Optimization readiness check
- Table-by-table status grid
- Record counts and last update timestamps
- Data freshness visualization
- Critical error highlighting

**Key Metrics**:
- Total records across all tables
- Tables passing/warning/failing validation
- Missing key fields count
- Referential integrity issues

### 2. 🔍 Data Validation Report
**Purpose**: Comprehensive 5-stage validation pipeline with detailed error reporting

**Validation Stages**:
1. **Schema Validation**: Required columns exist, data types correct
2. **Business Rule Validation**: No negative demand, positive costs, valid transport modes
3. **Referential Integrity**: Foreign key relationships valid
4. **Unit Consistency**: Consistent units (tonnes, km, costs)
5. **Missing Data Scan**: Critical data gaps identified

**Features**:
- Stage-by-stage progress visualization
- Row-level error reporting with context
- Downloadable CSV error reports
- Aggregated error summaries
- Optimization blocking indicators

### 3. 👁️ Raw Data Preview
**Purpose**: Read-only preview of database tables with issue detection

**Features**:
- Sortable, filterable, paginated data views
- Warning icons on problematic rows
- Issue-only filtering
- Data summary charts
- Column information display

**Supported Tables**:
- plant_master
- production_capacity_cost
- transport_routes_modes
- demand_forecast
- initial_inventory
- safety_stock_policy

### 4. ✨ Clean Data Preview
**Purpose**: Shows FINAL cleaned dataset that feeds into optimization

**Features**:
- Cleaned data transparency
- Applied transformations documentation
- Data quality metrics
- Missing value analysis
- Data type information
- All-tables overview

**Cleaning Transformations**:
- ID normalization (uppercase)
- Whitespace trimming
- Data type conversion
- Default value application
- Duplicate removal
- Invalid record filtering

### 5. 🚀 Optimization Console
**Purpose**: Central control panel for running optimization

**Features**:
- Real-time readiness checking
- Solver configuration (HiGHS/CBC/Gurobi)
- Time limit and MIP gap settings
- Progress tracking with live updates
- Validation-gated execution
- Comprehensive result display

**Execution Flow**:
1. Check data health status
2. Run validation pipeline
3. Enable/disable run button based on validation
4. Execute optimization with clean data
5. Display results with full breakdown

### 6. 📊 Results Dashboard
**Purpose**: Comprehensive visualization of optimization results

**Visualizations**:
- Cost breakdown (production, transport, fixed trips, holding)
- Production plan by plant and period
- Shipment routing analysis
- Inventory profiles over time
- Service level metrics
- Capacity utilization analysis
- Constraint violation reporting

**Export Options**:
- JSON (complete results)
- CSV (tabular data)
- PDF (summary report - coming soon)

## 🛡️ Data Quality Guarantee

### STRICT RULE ENFORCEMENT

❌ **The optimization model NEVER consumes**:
- Raw CSV files
- Unvalidated data uploads
- Partial database loads
- Data with validation failures

✅ **The optimization model ONLY consumes**:
- Fully-validated, normalized database tables
- Data passing all 5 validation stages
- Clean data pipeline output
- Referentially consistent datasets

### Validation Pipeline Details

#### Stage 1: Schema Validation
- Required columns present
- Correct data types
- Column naming consistency

#### Stage 2: Business Rule Validation
- No negative demand values
- Production capacity > 0
- Valid transport mode values
- No duplicate keys per (node, period)
- SBQ ≤ vehicle capacity
- Positive cost values

#### Stage 3: Referential Integrity
- plant_id exists in plant_master
- origin_plant_id references valid plants
- destination_node_id references plants/customers
- node_id references known locations

#### Stage 4: Unit Consistency
- All demand in tonnes
- All distances in km
- All costs in consistent currency
- No mixed unit systems

#### Stage 5: Missing Data Scan
- Critical fields populated
- No gaps in time series
- Required relationships present
- Orphaned data identification

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Required Python packages (see requirements.txt)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app/main.py --server.port 8501
```

### Environment Variables
```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost/clinker_db
JWT_SECRET_KEY=your-secret-key
BROKER_URL=redis://localhost:6379
RESULT_BACKEND=redis://localhost:6379

# Frontend
BACKEND_URL=http://localhost:8000
```

## 📊 API Endpoints

### Dashboard Endpoints (`/api/v1/dashboard/`)

#### Data Health
- `GET /health-status` - Overall data health status
- `GET /validation-report` - 5-stage validation pipeline
- `GET /validation-report/csv` - Download validation errors as CSV

#### Data Access
- `GET /raw-data/{table_name}` - Paginated raw data preview
- `GET /clean-data/{table_name}` - Cleaned data preview
- `GET /clean-data` - All clean data previews

#### Optimization
- `POST /run-optimization` - Execute optimization (validation-gated)
- `GET /optimization-status/{job_id}` - Job status tracking
- `POST /run-scenario` - Single scenario execution

#### Results
- `GET /results/{run_id}` - Optimization results
- `GET /results/{run_id}/export` - Export results (JSON/CSV/PDF)

## 🔧 Configuration

### Solver Configuration
```python
# config.py
DEFAULT_SOLVER = "highs"  # highs, cbc, gurobi
SOLVER_TIME_LIMIT_SECONDS = 600
SOLVER_MIP_GAP = 0.01
```

### Validation Configuration
```python
# Validation rules can be customized in:
# backend/app/services/validation/rules.py
# backend/app/services/data_validation_service.py
```

### Dashboard Configuration
```python
# frontend/streamlit_app/config.py
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/v1"
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
# Manual testing via Streamlit interface
streamlit run streamlit_app/main.py
```

## 📈 Monitoring & Logging

### Application Logging
- Structured JSON logging
- Validation failure tracking
- Optimization execution logs
- Error context preservation

### Health Monitoring
- Database connection status
- API endpoint availability
- Data freshness tracking
- Validation pipeline status

## 🔒 Security

### Authentication
- JWT-based authentication
- Role-based access control (RBAC)
- Permission-gated endpoints

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection in frontend

## 📚 Documentation

### Code Documentation
- Comprehensive docstrings
- Type hints throughout
- API documentation via FastAPI/OpenAPI

### User Documentation
- Dashboard user guides
- Validation rule explanations
- Troubleshooting guides

## 🤝 Contributing

### Development Guidelines
- Follow PEP 8 style guide
- Add type hints to all functions
- Write comprehensive docstrings
- Include unit tests for new features

### Code Review Process
1. Create feature branch
2. Implement changes with tests
3. Submit pull request
4. Code review and approval
5. Merge to main branch

## 📞 Support

### Common Issues
1. **Validation Failures**: Check data quality in validation report
2. **Optimization Blocked**: Resolve all critical validation errors
3. **API Connection**: Verify backend is running and accessible
4. **Solver Issues**: Check solver installation and licensing

### Troubleshooting
- Check application logs for detailed error messages
- Verify database connectivity
- Ensure all required environment variables are set
- Validate data against schema requirements

## 🗺️ Roadmap

### Planned Features
- [ ] Real-time data streaming integration
- [ ] Advanced scenario analysis tools
- [ ] Machine learning demand forecasting
- [ ] Mobile-responsive dashboard
- [ ] Advanced export formats (PDF reports)
- [ ] Automated data quality alerts
- [ ] Multi-tenant support

### Performance Improvements
- [ ] Database query optimization
- [ ] Caching layer implementation
- [ ] Async processing for large datasets
- [ ] Progressive data loading

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with FastAPI, Streamlit, and Plotly
- Optimization powered by Pyomo
- Database management with SQLAlchemy
- Validation framework with Pydantic