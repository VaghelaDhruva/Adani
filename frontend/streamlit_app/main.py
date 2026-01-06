import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
import logging
import traceback
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
</style>
""", unsafe_allow_html=True)

def main():
    """Main function to render the home page."""
    try:
        # Debug info
        st.sidebar.write("🔧 Debug Info:")
        st.sidebar.write(f"API Base: {API_BASE}")
        st.sidebar.write(f"Main page loaded at: {datetime.now().strftime('%H:%M:%S')}")
        
        # ========================================
        # MAIN DASHBOARD SELECTION
        # Change this to switch between KPI Dashboard or Results Dashboard as main page
        # ========================================
        
        MAIN_DASHBOARD = "HOME"  # Options: "KPI", "RESULTS", or "HOME"
        
        if MAIN_DASHBOARD == "KPI":
            # Redirect to KPI Dashboard as main page
            st.switch_page("pages/01_KPI_Dashboard.py")
        elif MAIN_DASHBOARD == "RESULTS":
            # Redirect to Results Dashboard as main page  
            st.switch_page("pages/06_Results_Dashboard.py")
        else:
            # Show original main page
            show_main_page()
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        st.error(f"Error loading main page: {e}")
        st.code(traceback.format_exc())
        st.info("Please refresh the page.")

def show_main_page():
    """Show the main landing page."""
    try:
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
            with st.spinner("Testing backend connection..."):
                response = requests.get(f"{API_BASE}/dashboard/scenarios/list", timeout=5)
            backend_status = "🟢 Connected" if response.status_code == 200 else "🟡 Issues"
            backend_help = "API connection successful" if response.status_code == 200 else f"API returned {response.status_code}"
        except Exception as e:
            backend_status = "🔴 Disconnected"
            backend_help = f"Cannot connect to backend API: {str(e)}"
        
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
                
    except Exception as e:
        logger.error(f"Error in show_main_page: {e}")
        st.error(f"Error displaying main page: {e}")
        st.code(traceback.format_exc())

# Execute main function directly (not in if __name__ == "__main__")
# This is required for Streamlit multipage apps
try:
    main()
except Exception as e:
    st.error(f"Failed to load application: {e}")
    st.code(traceback.format_exc())
    st.info("Please refresh the page or check the system status.")