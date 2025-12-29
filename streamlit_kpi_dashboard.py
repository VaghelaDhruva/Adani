"""
Production-Quality Streamlit KPI Dashboard
Connects to real SQLite database with instant loading and error resilience.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import logging
import traceback
from typing import Dict, Any, Optional, Tuple
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = "sqlite:///test.db"
CACHE_TTL = 60  # Cache for 60 seconds
TREND_DAYS = 30  # Days for trend analysis

# Page configuration
st.set_page_config(
    page_title="KPI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection with error handling
@st.cache_resource
def get_database_engine():
    """Create and cache database engine."""
    try:
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection established successfully")
        return engine
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

# Data loading functions with caching and error handling
@st.cache_data(ttl=CACHE_TTL)
def load_today_kpis() -> Dict[str, Any]:
    """Load today's KPI metrics with error handling."""
    engine = get_database_engine()
    if not engine:
        return {"error": "Database connection failed"}
    
    try:
        with engine.connect() as conn:
            # Total revenue today
            revenue_query = text("""
                SELECT COALESCE(SUM(amount), 0) as total_revenue
                FROM orders 
                WHERE date(order_date) = date('now', 'localtime')
            """)
            
            # Total orders today
            orders_query = text("""
                SELECT COUNT(*) as total_orders
                FROM orders 
                WHERE date(order_date) = date('now', 'localtime')
            """)
            
            # Active users today (users who placed orders)
            users_query = text("""
                SELECT COUNT(DISTINCT user_id) as active_users
                FROM orders 
                WHERE date(order_date) = date('now', 'localtime')
            """)
            
            # Conversion rate (orders/unique visitors - assuming we have a visits table)
            conversion_query = text("""
                SELECT 
                    CASE 
                        WHEN v.total_visits > 0 
                        THEN ROUND((o.total_orders * 100.0 / v.total_visits), 2)
                        ELSE 0 
                    END as conversion_rate
                FROM 
                    (SELECT COUNT(*) as total_orders FROM orders 
                     WHERE date(order_date) = date('now', 'localtime')) o,
                    (SELECT COUNT(DISTINCT user_id) as total_visits FROM visits 
                     WHERE date(visit_date) = date('now', 'localtime')) v
            """)
            
            # Execute queries
            revenue_result = conn.execute(revenue_query).fetchone()
            orders_result = conn.execute(orders_query).fetchone()
            users_result = conn.execute(users_query).fetchone()
            
            # Try conversion rate, fallback if visits table doesn't exist
            try:
                conversion_result = conn.execute(conversion_query).fetchone()
                conversion_rate = conversion_result[0] if conversion_result else 0
            except:
                # Fallback: simple conversion based on orders/users
                conversion_rate = (orders_result[0] / max(users_result[0], 1)) * 100 if users_result[0] > 0 else 0
            
            return {
                "total_revenue": float(revenue_result[0]) if revenue_result else 0,
                "total_orders": int(orders_result[0]) if orders_result else 0,
                "active_users": int(users_result[0]) if users_result else 0,
                "conversion_rate": float(conversion_rate),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": None
            }
            
    except Exception as e:
        logger.error(f"Error loading today's KPIs: {e}")
        return {
            "error": f"Failed to load KPIs: {str(e)}",
            "total_revenue": 0,
            "total_orders": 0,
            "active_users": 0,
            "conversion_rate": 0,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

@st.cache_data(ttl=CACHE_TTL)
def load_revenue_trend(days: int = TREND_DAYS) -> pd.DataFrame:
    """Load revenue trend data for the past N days."""
    engine = get_database_engine()
    if not engine:
        return pd.DataFrame()
    
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    date(order_date) as day,
                    SUM(amount) as revenue,
                    COUNT(*) as orders
                FROM orders 
                WHERE date(order_date) >= date('now', 'localtime', '-{} days')
                GROUP BY date(order_date)
                ORDER BY day DESC
                LIMIT :days
            """.format(days))
            
            result = conn.execute(query, {"days": days})
            df = pd.DataFrame(result.fetchall(), columns=['day', 'revenue', 'orders'])
            
            if not df.empty:
                df['day'] = pd.to_datetime(df['day'])
                df = df.sort_values('day')
            
            return df
            
    except Exception as e:
        logger.error(f"Error loading revenue trend: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_user_activity_trend(days: int = TREND_DAYS) -> pd.DataFrame:
    """Load user activity trend for the past N days."""
    engine = get_database_engine()
    if not engine:
        return pd.DataFrame()
    
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    date(order_date) as day,
                    COUNT(DISTINCT user_id) as active_users
                FROM orders 
                WHERE date(order_date) >= date('now', 'localtime', '-{} days')
                GROUP BY date(order_date)
                ORDER BY day DESC
                LIMIT :days
            """.format(days))
            
            result = conn.execute(query, {"days": days})
            df = pd.DataFrame(result.fetchall(), columns=['day', 'active_users'])
            
            if not df.empty:
                df['day'] = pd.to_datetime(df['day'])
                df = df.sort_values('day')
            
            return df
            
    except Exception as e:
        logger.error(f"Error loading user activity trend: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_kpi_summary() -> Optional[Dict[str, Any]]:
    """Load from pre-aggregated KPI summary table if available."""
    engine = get_database_engine()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    total_revenue_today,
                    total_orders_today,
                    active_users_today,
                    conversion_rate_today,
                    updated_at
                FROM kpi_summary 
                WHERE date(updated_at) = date('now', 'localtime')
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
            
            result = conn.execute(query).fetchone()
            if result:
                return {
                    "total_revenue": float(result[0]),
                    "total_orders": int(result[1]),
                    "active_users": int(result[2]),
                    "conversion_rate": float(result[3]),
                    "last_updated": result[4],
                    "source": "kpi_summary_table"
                }
            return None
            
    except Exception as e:
        logger.debug(f"KPI summary table not available: {e}")
        return None

# UI Components
def render_kpi_metrics(kpi_data: Dict[str, Any]):
    """Render KPI metrics with error handling."""
    st.subheader("📊 Today's KPIs")
    
    # Show error if data loading failed
    if kpi_data.get("error"):
        st.error(f"⚠️ {kpi_data['error']}")
        st.info("Showing cached or fallback values below:")
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        revenue = kpi_data.get("total_revenue", 0)
        st.metric(
            label="💰 Total Revenue Today",
            value=f"${revenue:,.2f}",
            delta=None,
            help="Total revenue from orders placed today"
        )
    
    with col2:
        orders = kpi_data.get("total_orders", 0)
        st.metric(
            label="📦 Total Orders Today",
            value=f"{orders:,}",
            delta=None,
            help="Number of orders placed today"
        )
    
    with col3:
        users = kpi_data.get("active_users", 0)
        st.metric(
            label="👥 Active Users Today",
            value=f"{users:,}",
            delta=None,
            help="Unique users who placed orders today"
        )
    
    with col4:
        conversion = kpi_data.get("conversion_rate", 0)
        st.metric(
            label="📈 Conversion Rate",
            value=f"{conversion:.2f}%",
            delta=None,
            help="Percentage of users who placed orders"
        )
    
    # Last updated timestamp
    last_updated = kpi_data.get("last_updated", "Unknown")
    st.caption(f"Last updated: {last_updated}")

def render_revenue_trend_chart(df: pd.DataFrame):
    """Render revenue trend chart."""
    st.subheader("💹 Revenue Trend (Last 30 Days)")
    
    if df.empty:
        st.warning("No revenue trend data available")
        return
    
    try:
        # Create line chart
        fig = px.line(
            df, 
            x='day', 
            y='revenue',
            title="Daily Revenue Trend",
            labels={'revenue': 'Revenue ($)', 'day': 'Date'},
            markers=True
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Revenue ($)",
            hovermode='x unified',
            showlegend=False
        )
        
        fig.update_traces(
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=6)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show summary stats
        if len(df) > 1:
            avg_revenue = df['revenue'].mean()
            total_revenue = df['revenue'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Daily Revenue", f"${avg_revenue:,.2f}")
            with col2:
                st.metric("Total Period Revenue", f"${total_revenue:,.2f}")
            with col3:
                st.metric("Days with Data", len(df))
                
    except Exception as e:
        st.error(f"Error rendering revenue trend: {e}")
        logger.error(f"Revenue trend chart error: {e}")

def render_user_activity_chart(df: pd.DataFrame):
    """Render user activity trend chart."""
    st.subheader("👥 User Activity Trend (Last 30 Days)")
    
    if df.empty:
        st.warning("No user activity data available")
        return
    
    try:
        # Create bar chart
        fig = px.bar(
            df,
            x='day',
            y='active_users',
            title="Daily Active Users",
            labels={'active_users': 'Active Users', 'day': 'Date'},
            color='active_users',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Active Users",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show summary stats
        if len(df) > 1:
            avg_users = df['active_users'].mean()
            max_users = df['active_users'].max()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average Daily Users", f"{avg_users:.1f}")
            with col2:
                st.metric("Peak Daily Users", f"{max_users}")
                
    except Exception as e:
        st.error(f"Error rendering user activity chart: {e}")
        logger.error(f"User activity chart error: {e}")

def render_database_status():
    """Render database connection status."""
    st.sidebar.subheader("🔧 System Status")
    
    engine = get_database_engine()
    if engine:
        st.sidebar.success("✅ Database Connected")
        st.sidebar.info(f"📍 Database: {DATABASE_URL}")
    else:
        st.sidebar.error("❌ Database Disconnected")
        st.sidebar.warning("Using cached data only")
    
    # Show cache info
    st.sidebar.info(f"🔄 Cache TTL: {CACHE_TTL}s")
    st.sidebar.info(f"📅 Trend Period: {TREND_DAYS} days")

def render_refresh_controls():
    """Render refresh controls."""
    st.sidebar.subheader("🔄 Data Controls")
    
    if st.sidebar.button("Refresh All Data", use_container_width=True):
        # Clear all caches
        st.cache_data.clear()
        st.rerun()
    
    if st.sidebar.button("Clear Cache", use_container_width=True):
        st.cache_data.clear()
        st.sidebar.success("Cache cleared!")
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto-refresh (60s)", value=False)
    if auto_refresh:
        import time
        time.sleep(60)
        st.rerun()

def main():
    """Main dashboard function with comprehensive error handling."""
    try:
        # Page header
        st.title("📊 Real-Time KPI Dashboard")
        st.markdown("---")
        
        # Render sidebar controls
        render_database_status()
        render_refresh_controls()
        
        # Load data with progress indicators
        with st.spinner("Loading KPI data..."):
            # Try to load from pre-aggregated table first
            kpi_data = load_kpi_summary()
            if not kpi_data:
                # Fallback to real-time queries
                kpi_data = load_today_kpis()
        
        # Render KPI metrics (always renders, even with errors)
        render_kpi_metrics(kpi_data)
        
        st.markdown("---")
        
        # Load and render charts
        col1, col2 = st.columns(2)
        
        with col1:
            with st.spinner("Loading revenue trend..."):
                revenue_df = load_revenue_trend()
            render_revenue_trend_chart(revenue_df)
        
        with col2:
            with st.spinner("Loading user activity..."):
                activity_df = load_user_activity_trend()
            render_user_activity_chart(activity_df)
        
        # Footer with system info
        st.markdown("---")
        st.caption(f"Dashboard updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        # Critical error handling - dashboard still renders
        logger.error(f"Critical dashboard error: {e}")
        st.error("⚠️ Dashboard encountered an error, but is still functional")
        st.code(traceback.format_exc())
        
        # Show minimal fallback UI
        st.subheader("📊 KPI Dashboard (Fallback Mode)")
        st.info("Some features may be unavailable. Please refresh the page.")
        
        # Show basic metrics with zero values
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Revenue Today", "$0.00")
        with col2:
            st.metric("Total Orders Today", "0")
        with col3:
            st.metric("Active Users Today", "0")
        with col4:
            st.metric("Conversion Rate", "0.00%")

# Execute main function
if __name__ == "__main__":
    main()
else:
    # For Streamlit multipage apps
    main()