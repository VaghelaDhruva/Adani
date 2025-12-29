<<<<<<< HEAD
# Clinker Supply Chain Optimization System

Production-grade system for real-time and batch data ingestion, MILP optimization, scenario simulation, and visualization dashboards for clinker logistics.

## Architecture

- **Backend**: FastAPI + SQLAlchemy + Pydantic + Celery + Redis
- **DB**: PostgreSQL
- **Optimization**: Pyomo (CBC/HiGHS default; Gurobi optional)
- **Frontend**: Streamlit
- **Auth**: JWT with role-based access (admin, planner, viewer)
- **Infra**: Docker Compose (backend, frontend, postgres, worker, redis)

## Quick Start

```bash
# Copy environment file and configure
cp infra/env.example .env
# Edit .env with your DB, routing, and auth settings

# Start services
docker-compose -f infra/docker-compose.yml up --build -d

# Run migrations
docker-compose -f infra/docker-compose.yml exec backend alembic upgrade head

# Access
# - Streamlit UI: http://localhost:8501
# - FastAPI docs: http://localhost:8000/docs
# - API health: http://localhost:8000/health
```

## Project Structure

See `docs/architecture.md` for detailed module breakdown.

## Data Ingestion

- CSV/Excel upload via API
- External routing APIs (OSRM, OpenRouteService) with caching
- Optional demand streaming via REST polling or Kafka (scaffolded)

## Optimization

- MILP model with production, transport, inventory, and batch constraints
- Scenario engine for demand uncertainty and batch runs
- KPI calculation and visualization

## Development

```bash
# Backend dev
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend dev
cd frontend/streamlit_app
pip install -r requirements.txt
streamlit run main.py --server.port 8501
```

## Testing

```bash
cd backend
pytest
```

## License

Internal use.
=======
# Production-Quality Streamlit KPI Dashboard

A real-world Streamlit KPI dashboard that connects to SQLite database with instant loading, comprehensive error handling, and production-ready features.

## 🎯 Features

### ✅ **Real Database Integration**
- Connects to SQLite via SQLAlchemy with proper connection pooling
- Uses efficient SQL aggregations instead of loading entire tables
- Supports both Docker and host deployments

### ⚡ **Instant Performance**
- `@st.cache_data(ttl=60)` for instant reloads
- Pre-aggregated KPI summary table option
- Optimized SQL queries with proper indexing
- Never blocks UI rendering

### 🛡️ **Production Error Handling**
- Dashboard always renders, even with database failures
- Shows cached values when database is unavailable
- Comprehensive logging and error tracking
- Graceful degradation with helpful fallback messages

### 📊 **Real KPIs**
- **Total Revenue Today**: Sum of all orders placed today
- **Total Orders Today**: Count of orders placed today  
- **Active Users Today**: Unique users who placed orders today
- **Conversion Rate**: Percentage of visitors who placed orders
- **30-Day Trends**: Revenue and user activity trend charts

### 🔧 **Production Features**
- Database connection status monitoring
- Manual refresh controls
- Auto-refresh option
- Cache management
- Comprehensive logging

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Database
```bash
# Create database with sample data
python database_setup.py
```

### 3. Run Dashboard
```bash
streamlit run streamlit_kpi_dashboard.py
```

### 4. Optional: Start KPI Aggregation Job
```bash
# In a separate terminal - runs background job to pre-calculate KPIs
python kpi_aggregation_job.py
```

## 📁 File Structure

```
├── streamlit_kpi_dashboard.py    # Main dashboard application
├── database_setup.py             # Database creation script
├── setup_database.sql            # SQL schema and sample data
├── kpi_aggregation_job.py        # Background KPI calculation job
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🗄️ Database Schema

### Core Tables
- **orders**: Order transactions with user_id, amount, order_date
- **users**: User information
- **visits**: Website visits for conversion rate calculation
- **kpi_summary**: Pre-aggregated KPIs (optional, for performance)

### Sample Data
- 10 users with realistic profiles
- 30 days of order history with random realistic amounts
- Website visits data for conversion rate calculations
- Proper indexes for query performance

## ⚡ Performance Optimizations

### 1. **Efficient SQL Queries**
```sql
-- Revenue today (aggregated, not SELECT *)
SELECT SUM(amount) FROM orders 
WHERE date(order_date) = date('now','localtime');

-- Trend data (limited to needed days)
SELECT date(order_date) AS day, SUM(amount) AS revenue 
FROM orders 
GROUP BY date(order_date) 
ORDER BY day DESC LIMIT 30;
```

### 2. **Smart Caching Strategy**
- KPI data cached for 60 seconds
- Trend data cached for 60 seconds  
- Database engine cached as resource
- Pre-aggregated table cached for 5 minutes

### 3. **Database Optimizations**
- Proper indexes on date and user_id columns
- Connection pooling with SQLAlchemy
- Efficient date filtering using SQLite date functions

## 🧯 Error Handling Strategy

### 1. **Database Connection Failures**
```python
# Dashboard still renders with fallback UI
if not engine:
    st.error("Database unavailable - showing cached data")
    # Show last cached values or zeros
```

### 2. **Query Failures**
```python
# Individual queries wrapped in try/except
try:
    result = conn.execute(query)
except Exception as e:
    logger.error(f"Query failed: {e}")
    return {"error": str(e), "fallback_value": 0}
```

### 3. **UI Rendering Failures**
```python
# Each UI component has error boundaries
try:
    render_kpi_metrics(data)
except Exception as e:
    st.error("KPI section unavailable")
    # Show minimal fallback metrics
```

## 🔧 Configuration

### Database URL
```python
DATABASE_URL = "sqlite:///test.db"  # Relative path works in Docker
```

### Cache Settings
```python
CACHE_TTL = 60        # Cache for 60 seconds
TREND_DAYS = 30       # Days for trend analysis
```

### Docker Support
The code uses relative paths and proper SQLAlchemy configuration to work in both host and Docker environments.

## 📊 KPI Calculations

### Today's Revenue
```sql
SELECT SUM(amount) FROM orders 
WHERE date(order_date) = date('now','localtime');
```

### Active Users Today
```sql
SELECT COUNT(DISTINCT user_id) FROM orders 
WHERE date(order_date) = date('now','localtime');
```

### Conversion Rate
```sql
SELECT (orders.count * 100.0 / visits.count) as conversion_rate
FROM 
  (SELECT COUNT(*) as count FROM orders WHERE date(order_date) = date('now','localtime')) orders,
  (SELECT COUNT(DISTINCT user_id) as count FROM visits WHERE date(visit_date) = date('now','localtime')) visits;
```

### Revenue Trend (30 days)
```sql
SELECT 
    date(order_date) as day,
    SUM(amount) as revenue,
    COUNT(*) as orders
FROM orders 
WHERE date(order_date) >= date('now', 'localtime', '-30 days')
GROUP BY date(order_date)
ORDER BY day DESC;
```

## 🚀 Production Deployment

### Option 1: Host Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
python database_setup.py

# Start KPI aggregation job (optional, in background)
nohup python kpi_aggregation_job.py &

# Start dashboard
streamlit run streamlit_kpi_dashboard.py --server.port 8501
```

### Option 2: Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python database_setup.py

EXPOSE 8501
CMD ["streamlit", "run", "streamlit_kpi_dashboard.py", "--server.address", "0.0.0.0"]
```

## 🔍 What Was Improved

### ❌ **Previous Issues Fixed**
- "KPI Data Loaded: False" → Now always loads with fallback
- "Request Timeout" → Cached data prevents timeouts
- Blank UI → Dashboard always renders with error boundaries
- Slow loading → Instant loading with caching
- No error visibility → Comprehensive error messages

### ✅ **New Production Features**
- Real SQLite database integration
- Efficient SQL aggregations
- Comprehensive error handling
- Smart caching strategy
- Database connection monitoring
- Pre-aggregated KPI table option
- Production-ready logging
- Docker compatibility

### ⚡ **Performance Improvements**
- **Before**: Loading entire tables, no caching
- **After**: Aggregated queries with 60-second caching
- **Before**: Blocking UI during data loads
- **After**: Instant UI with spinner for data updates
- **Before**: No fallback for failures
- **After**: Cached values and graceful degradation

## 🧪 Testing

The dashboard includes comprehensive error simulation:
- Database connection failures
- Individual query failures  
- Network timeouts
- Invalid data scenarios

All scenarios result in a functional dashboard with helpful error messages, never a blank page.

## 📈 Monitoring

### Built-in Monitoring
- Database connection status in sidebar
- Last updated timestamps
- Cache status indicators
- Error logging with details

### Optional Enhancements
- Add health check endpoint
- Integrate with monitoring tools (Prometheus, etc.)
- Add performance metrics collection
- Set up alerting for database failures

This dashboard is production-ready and will never show blank pages or "KPI Data Loaded: False" messages again!
>>>>>>> d4196135 (Fixed Bug)
