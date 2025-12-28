"""
Data Health Status Dashboard

Displays comprehensive data health monitoring for all tables required by optimization.
Shows validation status, record counts, and data quality indicators.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

from config import API_BASE

st.set_page_config(page_title="Data Health Dashboard", layout="wide")

def get_data_health_status():
    """Fetch data health status from API."""
    try:
        response = requests.get(f"{API_BASE}/dashboard/health-status", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None

def display_overall_status(health_data):
    """Display overall data health status."""
    if not health_data:
        return
    
    overall_status = health_data.get("overall_status", "UNKNOWN")
    optimization_ready = health_data.get("optimization_ready", False)
    summary = health_data.get("summary", {})
    
    # Status indicator
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_color = {
            "PASS": "🟢",
            "WARN": "🟡", 
            "FAIL": "🔴"
        }.get(overall_status, "⚪")
        
        st.metric(
            label="Overall Data Status",
            value=f"{status_color} {overall_status}"
        )
    
    with col2:
        ready_icon = "✅" if optimization_ready else "❌"
        st.metric(
            label="Optimization Ready",
            value=f"{ready_icon} {'Yes' if optimization_ready else 'No'}"
        )
    
    with col3:
        st.metric(
            label="Total Records",
            value=f"{summary.get('total_records', 0):,}"
        )
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tables Passing", summary.get("tables_passing", 0))
    
    with col2:
        st.metric("Tables with Warnings", summary.get("tables_warning", 0))
    
    with col3:
        st.metric("Tables Failing", summary.get("tables_failing", 0))
    
    with col4:
        st.metric("Total Errors", summary.get("total_errors", 0))

def display_table_status_grid(health_data):
    """Display table-by-table status grid."""
    if not health_data:
        return
    
    table_status = health_data.get("table_status", {})
    
    st.subheader("📊 Table Status Overview")
    
    # Create grid layout
    cols = st.columns(3)
    
    for i, (table_name, status) in enumerate(table_status.items()):
        col_idx = i % 3
        
        with cols[col_idx]:
            # Status card
            validation_status = status.get("validation_status", "UNKNOWN")
            record_count = status.get("record_count", 0)
            
            status_color = {
                "PASS": "#28a745",
                "WARN": "#ffc107", 
                "FAIL": "#dc3545"
            }.get(validation_status, "#6c757d")
            
            status_icon = {
                "PASS": "✅",
                "WARN": "⚠️",
                "FAIL": "❌"
            }.get(validation_status, "❓")
            
            # Create card-like display
            st.markdown(f"""
            <div style="
                border: 2px solid {status_color};
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                background-color: rgba({','.join(str(int(status_color[i:i+2], 16)) for i in (1, 3, 5))}, 0.1);
            ">
                <h4 style="margin: 0; color: {status_color};">
                    {status_icon} {table_name.replace('_', ' ').title()}
                </h4>
                <p style="margin: 5px 0;"><strong>Status:</strong> {validation_status}</p>
                <p style="margin: 5px 0;"><strong>Records:</strong> {record_count:,}</p>
                <p style="margin: 5px 0;"><strong>Errors:</strong> {len(status.get('validation_errors', []))}</p>
                <p style="margin: 5px 0;"><strong>Warnings:</strong> {len(status.get('warnings', []))}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show last update if available
            last_update = status.get("last_update")
            if last_update:
                try:
                    update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    st.caption(f"Last updated: {update_time.strftime('%Y-%m-%d %H:%M')}")
                except:
                    st.caption(f"Last updated: {last_update}")

def display_detailed_errors(health_data):
    """Display detailed error information."""
    if not health_data:
        return
    
    table_status = health_data.get("table_status", {})
    
    # Collect all errors and warnings
    all_errors = []
    all_warnings = []
    
    for table_name, status in table_status.items():
        for error in status.get("validation_errors", []):
            all_errors.append({
                "Table": table_name,
                "Error": error,
                "Type": "Error"
            })
        
        for warning in status.get("warnings", []):
            all_warnings.append({
                "Table": table_name,
                "Warning": warning,
                "Type": "Warning"
            })
    
    if all_errors:
        st.subheader("🚨 Critical Errors")
        st.error("The following errors must be resolved before optimization can run:")
        
        error_df = pd.DataFrame(all_errors)
        st.dataframe(error_df, use_container_width=True)
    
    if all_warnings:
        st.subheader("⚠️ Warnings")
        st.warning("The following warnings should be reviewed:")
        
        warning_df = pd.DataFrame(all_warnings)
        st.dataframe(warning_df, use_container_width=True)

def display_data_freshness_chart(health_data):
    """Display data freshness visualization."""
    if not health_data:
        return
    
    table_status = health_data.get("table_status", {})
    
    # Extract last update times
    freshness_data = []
    for table_name, status in table_status.items():
        last_update = status.get("last_update")
        if last_update:
            try:
                update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                hours_ago = (datetime.now() - update_time.replace(tzinfo=None)).total_seconds() / 3600
                freshness_data.append({
                    "Table": table_name.replace('_', ' ').title(),
                    "Hours Since Update": hours_ago,
                    "Last Update": update_time.strftime('%Y-%m-%d %H:%M')
                })
            except:
                pass
    
    if freshness_data:
        st.subheader("📅 Data Freshness")
        
        df = pd.DataFrame(freshness_data)
        
        # Create horizontal bar chart
        fig = px.bar(
            df,
            x="Hours Since Update",
            y="Table",
            orientation='h',
            title="Hours Since Last Data Update",
            color="Hours Since Update",
            color_continuous_scale="RdYlGn_r"
        )
        
        fig.update_layout(
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("🏥 Data Health Status Dashboard")
    st.markdown("Monitor data quality and readiness for optimization")
    
    # Auto-refresh controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        auto_refresh = st.checkbox("Auto-refresh every 30 seconds", value=False)
    
    with col2:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
    with col3:
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    # Fetch data
    with st.spinner("Loading data health status..."):
        health_data = get_data_health_status()
    
    if health_data:
        # Display overall status
        display_overall_status(health_data)
        
        st.divider()
        
        # Display table status grid
        display_table_status_grid(health_data)
        
        st.divider()
        
        # Display data freshness
        display_data_freshness_chart(health_data)
        
        st.divider()
        
        # Display detailed errors
        display_detailed_errors(health_data)
        
        # Show raw data in expander
        with st.expander("🔍 Raw Health Data (JSON)"):
            st.json(health_data)
    
    else:
        st.error("Failed to load data health status. Please check the backend connection.")
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()