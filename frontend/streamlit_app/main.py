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

# Custom CSS for enhanced styling
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2e7d32 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Navigation buttons styling */
    .nav-button {
        background: linear-gradient(45deg, #007bff, #0056b3);
        color: white;
        border: none;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 0.25rem 0;
        width: 100%;
        text-align: left;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .nav-button:hover {
        background: linear-gradient(45deg, #0056b3, #004085);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Status cards styling */
    .status-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #28a745;
        margin: 1rem 0;
        transition: transform 0.2s ease;
    }
    
    .status-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    
    .status-card h3 {
        color: #2c3e50;
        margin: 0 0 0.5rem 0;
        font-size: 1.1rem;
    }
    
    .status-card .metric {
        font-size: 1.8rem;
        font-weight: 700;
        color: #28a745;
        margin: 0;
    }
    
    /* Feature cards styling */
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(0,0,0,0.2);
    }
    
    .feature-card h3 {
        margin: 0 0 1rem 0;
        font-size: 1.4rem;
        font-weight: 600;
    }
    
    .feature-card p {
        margin: 0 0 1rem 0;
        opacity: 0.9;
        line-height: 1.5;
    }
    
    /* Quick access buttons */
    .quick-access-btn {
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
        width: 100%;
        margin: 0.5rem 0;
    }
    
    .quick-access-btn:hover {
        background: linear-gradient(45deg, #ee5a24, #c44569);
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(116, 185, 255, 0.3);
    }
    
    .success-box {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        box-shadow: 0 6px 20px rgba(0, 184, 148, 0.3);
    }
    
    /* Divider styling */
    .custom-divider {
        height: 3px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 2px;
        margin: 2rem 0;
    }
    
    /* Animation for loading states */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .main-header p {
            font-size: 1rem;
        }
        
        .feature-card {
            padding: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def main():
    # ========================================
    # MAIN DASHBOARD SELECTION
    # Change this to switch between KPI Dashboard or Results Dashboard as main page
    # ========================================
    
    MAIN_DASHBOARD = "KPI"  # Options: "KPI", "RESULTS", or "HOME"
    
    if MAIN_DASHBOARD == "KPI":
        # Redirect to KPI Dashboard as main page
        st.switch_page("pages/01_KPI_Dashboard.py")
    elif MAIN_DASHBOARD == "RESULTS":
        # Redirect to Results Dashboard as main page  
        st.switch_page("pages/06_Results_Dashboard.py")
    else:
        # Show original main page
        show_main_page()

def show_main_page():
    """Show the main landing page."""
    # Create styled header
    st.markdown("""
    <div class="main-header fade-in">
        <h1>🏭 Clinker Supply Chain Optimization Dashboard</h1>
        <p>Enterprise-grade dashboard for supply chain optimization with comprehensive KPI reporting</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("📋 Navigation")
    st.sidebar.markdown("**Essential Dashboard Pages:**")
    
    # Essential dashboard sections only
    if st.sidebar.button("📊 KPI Dashboard", use_container_width=True):
        st.switch_page("pages/01_KPI_Dashboard.py")
    st.sidebar.caption("Primary business dashboard with comprehensive KPI reporting")
    
    if st.sidebar.button("⚖️ Scenario Comparison", use_container_width=True):
        st.switch_page("pages/02_Scenario_Comparison.py")
    st.sidebar.caption("Compare cost and service impacts across scenarios")
    
    if st.sidebar.button("📈 Results Dashboard", use_container_width=True):
        st.switch_page("pages/06_Results_Dashboard.py")
    st.sidebar.caption("Live optimization results visualization")
    
    st.sidebar.markdown("---")
    
    # Main content
    st.info("👈 Use the sidebar to navigate to the essential dashboard sections")
    
    # Quick status overview
    st.subheader("🎯 Quick Status Overview")
    
    # Test backend connection
    try:
        response = requests.get(f"{API_BASE}/dashboard/scenarios/list", timeout=5)
        backend_status = "🟢 Connected" if response.status_code == 200 else "🟡 Issues"
        backend_help = "API connection successful" if response.status_code == 200 else f"API returned {response.status_code}"
    except:
        backend_status = "🔴 Disconnected"
        backend_help = "Cannot connect to backend API"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Backend Status", backend_status, help=backend_help)
    
    with col2:
        st.metric("Dashboard Pages", "3", help="Essential dashboard pages available")
    
    with col3:
        st.metric("Last Updated", datetime.now().strftime("%H:%M:%S"), help="Current time")
    
    # Feature highlights
    st.subheader("✨ Essential Dashboard Features")
    
    features = [
        {
            "title": "📊 KPI Dashboard",
            "description": "Comprehensive business KPIs with INR currency formatting",
            "details": ["Cost summary with INR formatting", "Service performance metrics", "Production & transport utilization", "Inventory & safety stock status"]
        },
        {
            "title": "⚖️ Scenario Comparison", 
            "description": "Compare multiple scenarios side-by-side",
            "details": ["Cost vs service trade-offs", "Utilization comparisons", "Risk analysis", "Automated recommendations"]
        },
        {
            "title": "📈 Results Dashboard",
            "description": "Detailed optimization results visualization", 
            "details": ["Production planning", "Shipment routing", "Cost breakdowns", "Service level analysis"]
        }
    ]
    
    cols = st.columns(3)
    
    for i, feature in enumerate(features):
        with cols[i]:
            with st.container():
                st.markdown(f"### {feature['title']}")
                st.write(feature['description'])
                
                with st.expander("Details"):
                    for detail in feature['details']:
                        st.write(f"• {detail}")
    
    # Data flow guarantee
    st.subheader("🛡️ Enterprise Quality Standards")
    
    st.success("""
    **PRODUCTION-READY FEATURES:**
    
    ✅ **Currency Formatting:** All costs displayed in INR with proper Indian digit grouping (₹X.XX Cr/L)
    
    ✅ **Enterprise KPIs:** Comprehensive business metrics with real-time data
    
    ✅ **Scenario Analysis:** Multi-scenario comparison with automated recommendations
    
    ✅ **Error Handling:** Robust error handling with graceful degradation
    """)
    
    # Quick links
    st.subheader("🔗 Quick Access")
    
    link_cols = st.columns(3)
    
    with link_cols[0]:
        if st.button("📊 KPI Dashboard", use_container_width=True):
            st.switch_page("pages/01_KPI_Dashboard.py")
    
    with link_cols[1]:
        if st.button("⚖️ Scenario Comparison", use_container_width=True):
            st.switch_page("pages/02_Scenario_Comparison.py")
    
    with link_cols[2]:
        if st.button("📈 Results Dashboard", use_container_width=True):
            st.switch_page("pages/06_Results_Dashboard.py")

if __name__ == "__main__":
    main()