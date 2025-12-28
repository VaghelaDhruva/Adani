import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
import logging
from datetime import datetime
from pathlib import Path
import sys

from config import API_BASE

# Ensure the frontend directory (containing the streamlit_app package) is on sys.path
_THIS_FILE = Path(__file__).resolve()
_APP_DIR = _THIS_FILE.parent            # .../frontend/streamlit_app
_FRONTEND_ROOT = _APP_DIR.parent        # .../frontend
if str(_FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_FRONTEND_ROOT))

st.set_page_config(
    page_title="Clinker Supply Chain Optimization",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging
logger = logging.getLogger(__name__)

def main():
    st.title("🏭 Clinker Supply Chain Optimization Dashboard")
    st.markdown("Production-ready dashboard for supply chain optimization with comprehensive data validation")
    
    # Sidebar navigation
    st.sidebar.title("📋 Navigation")
    st.sidebar.markdown("Select a dashboard section:")
    
    # Dashboard sections
    sections = {
        "🏥 Data Health Status": "Monitor data quality and readiness for optimization",
        "🚀 Optimization Console": "Run optimization with validated data",
        "📊 Results Dashboard": "Comprehensive results visualization"
    }
    
    for section, description in sections.items():
        st.sidebar.markdown(f"**{section}**")
        st.sidebar.caption(description)
        st.sidebar.markdown("---")
    
    # Main content
    st.info("👈 Use the sidebar to navigate to different dashboard sections")
    
    # Quick status overview
    st.subheader("🎯 Quick Status Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Backend Status", "🟢 Connected", help="API connection status")
    
    with col2:
        st.metric("Dashboard Sections", len(sections), help="Available dashboard pages")
    
    with col3:
        st.metric("Last Updated", datetime.now().strftime("%H:%M:%S"), help="Current time")
    
    # Feature highlights
    st.subheader("✨ Dashboard Features")
    
    features = [
        {
            "title": "🔒 Data Validation Pipeline",
            "description": "5-stage validation ensures only clean data reaches optimization",
            "details": ["Schema validation", "Business rules", "Referential integrity", "Unit consistency", "Missing data scan"]
        },
        {
            "title": "📊 Real-time Monitoring",
            "description": "Live data health status with automatic issue detection",
            "details": ["Table-level validation", "Row-level error reporting", "Data freshness tracking", "Optimization readiness"]
        },
        {
            "title": "🚀 Controlled Optimization",
            "description": "Optimization runs only with validated, clean data",
            "details": ["Validation-gated execution", "Multiple solver support", "Real-time progress", "Comprehensive results"]
        },
        {
            "title": "📈 Rich Visualizations",
            "description": "Interactive charts and comprehensive result analysis",
            "details": ["Cost breakdowns", "Production planning", "Shipment routing", "Service level metrics"]
        }
    ]
    
    cols = st.columns(2)
    
    for i, feature in enumerate(features):
        with cols[i % 2]:
            with st.container():
                st.markdown(f"### {feature['title']}")
                st.write(feature['description'])
                
                with st.expander("Details"):
                    for detail in feature['details']:
                        st.write(f"• {detail}")
    
    # # System architecture
    # st.subheader("🏗️ System Architecture")
    
    # st.markdown("""
    # ```
    # Raw Database Tables
    #         ↓
    # Data Health Monitoring ← Validation Pipeline (5 stages)
    #         ↓
    # Clean Data Service ← Normalization & Cleaning
    #         ↓
    # Optimization Engine ← MILP Model (Pyomo)
    #         ↓
    # Results Dashboard ← KPI Calculation & Visualization
    # ```
    # """)
    
    # Data flow guarantee
    st.subheader("🛡️ Data Quality Guarantee")
    
    st.success("""
    **STRICT RULE ENFORCEMENT:**
    
    ❌ The optimization model NEVER consumes:
    - Raw CSVs
    - Unvalidated uploads  
    - Partial database loads
    
    ✅ The optimization model ONLY consumes:
    - Fully-validated, normalized DB tables
    - Data that passes all 5 validation stages
    - Clean data pipeline output
    """)
    
    # Quick links
    st.subheader("🔗 Quick Links")
    
    link_cols = st.columns(3)
    
    with link_cols[0]:
        if st.button("🏥 Check Data Health", use_container_width=True):
            st.switch_page("pages/01_Data_Health_Dashboard.py")
    
    with link_cols[1]:
        if st.button("🚀 Start Optimization", use_container_width=True):
            st.switch_page("pages/05_Optimization_Console.py")
    
    with link_cols[2]:
        if st.button("📊 View Results", use_container_width=True):
            st.switch_page("pages/06_Results_Dashboard.py")

if __name__ == "__main__":
    main()