"""
Data Validation Report Dashboard

Comprehensive 5-stage validation pipeline with detailed error reporting.
Provides row-level error details and downloadable CSV reports.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

from config import API_BASE

st.set_page_config(page_title="Data Validation Report", layout="wide")

def get_validation_report():
    """Fetch comprehensive validation report from API."""
    try:
        response = requests.get(f"{API_BASE}/dashboard/validation-report", timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None

def download_validation_csv():
    """Download validation report as CSV."""
    try:
        response = requests.get(f"{API_BASE}/dashboard/validation-report/csv", timeout=30)
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Download failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Download error: {str(e)}")
        return None

def display_validation_overview(validation_data):
    """Display validation pipeline overview."""
    if not validation_data:
        return
    
    overall_status = validation_data.get("overall_status", "UNKNOWN")
    optimization_ready = validation_data.get("optimization_ready", False)
    summary = validation_data.get("summary", {})
    
    # Status indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = {
            "PASS": "🟢",
            "WARN": "🟡", 
            "FAIL": "🔴"
        }.get(overall_status, "⚪")
        
        st.metric(
            label="Validation Status",
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
            label="Total Errors",
            value=summary.get("total_errors", 0),
            delta=None if summary.get("total_errors", 0) == 0 else "Critical"
        )
    
    with col4:
        st.metric(
            label="Total Warnings", 
            value=summary.get("total_warnings", 0)
        )

def display_stage_pipeline(validation_data):
    """Display the 5-stage validation pipeline."""
    if not validation_data:
        return
    
    stages = validation_data.get("stages", [])
    
    st.subheader("🔍 5-Stage Validation Pipeline")
    
    # Create pipeline visualization
    stage_names = []
    stage_statuses = []
    error_counts = []
    warning_counts = []
    
    for stage in stages:
        stage_names.append(stage.get("stage", "").replace("_", " ").title())
        stage_statuses.append(stage.get("status", "UNKNOWN"))
        error_counts.append(stage.get("error_count", 0) + stage.get("row_error_count", 0))
        warning_counts.append(stage.get("warning_count", 0))
    
    # Display stages in columns
    cols = st.columns(len(stages))
    
    for i, (col, stage) in enumerate(zip(cols, stages)):
        with col:
            status = stage.get("status", "UNKNOWN")
            stage_name = stage.get("stage", "").replace("_", " ").title()
            
            status_color = {
                "PASS": "#28a745",
                "WARN": "#ffc107", 
                "FAIL": "#dc3545"
            }.get(status, "#6c757d")
            
            status_icon = {
                "PASS": "✅",
                "WARN": "⚠️",
                "FAIL": "❌"
            }.get(status, "❓")
            
            # Stage card
            st.markdown(f"""
            <div style="
                border: 2px solid {status_color};
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
                text-align: center;
                background-color: rgba({','.join(str(int(status_color[i:i+2], 16)) for i in (1, 3, 5))}, 0.1);
            ">
                <h4 style="margin: 0; color: {status_color};">
                    Stage {i+1}
                </h4>
                <p style="margin: 5px 0; font-weight: bold;">{stage_name}</p>
                <p style="margin: 5px 0;">{status_icon} {status}</p>
                <p style="margin: 5px 0; font-size: 0.9em;">
                    Errors: {error_counts[i]}<br>
                    Warnings: {warning_counts[i]}
                </p>
            </div>
            """, unsafe_allow_html=True)

def display_stage_details(validation_data):
    """Display detailed results for each validation stage."""
    if not validation_data:
        return
    
    stages = validation_data.get("stages", [])
    
    st.subheader("📋 Detailed Stage Results")
    
    # Create tabs for each stage
    stage_tabs = st.tabs([
        f"Stage {i+1}: {stage.get('stage', '').replace('_', ' ').title()}" 
        for i, stage in enumerate(stages)
    ])
    
    for tab, stage in zip(stage_tabs, stages):
        with tab:
            stage_name = stage.get("stage", "")
            status = stage.get("status", "UNKNOWN")
            
            # Stage description
            stage_descriptions = {
                "schema_validation": "Validates that required columns exist and data types are correct",
                "business_rules": "Enforces business logic constraints (no negative demand, positive costs, etc.)",
                "referential_integrity": "Ensures foreign key relationships are valid",
                "unit_consistency": "Checks for consistent units across related data",
                "missing_data_scan": "Identifies missing critical data that would block optimization"
            }
            
            st.info(stage_descriptions.get(stage_name, "Validation stage"))
            
            # Status summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", status)
            with col2:
                st.metric("Errors", stage.get("error_count", 0) + stage.get("row_error_count", 0))
            with col3:
                st.metric("Warnings", stage.get("warning_count", 0))
            
            # Display errors
            errors = stage.get("errors", []) + stage.get("row_level_errors", [])
            if errors:
                st.subheader("❌ Errors")
                error_df = pd.DataFrame(errors)
                st.dataframe(error_df, use_container_width=True)
            
            # Display warnings
            warnings = stage.get("warnings", [])
            if warnings:
                st.subheader("⚠️ Warnings")
                warning_df = pd.DataFrame(warnings)
                st.dataframe(warning_df, use_container_width=True)
            
            if not errors and not warnings:
                st.success("✅ No issues found in this stage")

def display_error_summary_charts(validation_data):
    """Display error summary visualizations."""
    if not validation_data:
        return
    
    stages = validation_data.get("stages", [])
    
    # Collect error data by stage
    stage_data = []
    table_errors = {}
    
    for stage in stages:
        stage_name = stage.get("stage", "").replace("_", " ").title()
        error_count = stage.get("error_count", 0) + stage.get("row_error_count", 0)
        warning_count = stage.get("warning_count", 0)
        
        stage_data.append({
            "Stage": stage_name,
            "Errors": error_count,
            "Warnings": warning_count
        })
        
        # Collect table-level errors
        for error in stage.get("errors", []) + stage.get("row_level_errors", []):
            table = error.get("table", "Unknown")
            if table not in table_errors:
                table_errors[table] = {"errors": 0, "warnings": 0}
            table_errors[table]["errors"] += 1
        
        for warning in stage.get("warnings", []):
            table = warning.get("table", "Unknown")
            if table not in table_errors:
                table_errors[table] = {"errors": 0, "warnings": 0}
            table_errors[table]["warnings"] += 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        if stage_data:
            st.subheader("📊 Errors by Validation Stage")
            df = pd.DataFrame(stage_data)
            
            fig = px.bar(
                df,
                x="Stage",
                y=["Errors", "Warnings"],
                title="Issues by Validation Stage",
                color_discrete_map={"Errors": "#dc3545", "Warnings": "#ffc107"}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if table_errors:
            st.subheader("📊 Issues by Table")
            table_data = []
            for table, counts in table_errors.items():
                table_data.append({
                    "Table": table.replace("_", " ").title(),
                    "Errors": counts["errors"],
                    "Warnings": counts["warnings"]
                })
            
            df = pd.DataFrame(table_data)
            
            fig = px.bar(
                df,
                x="Table",
                y=["Errors", "Warnings"],
                title="Issues by Data Table",
                color_discrete_map={"Errors": "#dc3545", "Warnings": "#ffc107"}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("🔍 Data Validation Report")
    st.markdown("Comprehensive 5-stage validation pipeline with detailed error reporting")
    
    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🔄 Run Validation", type="primary"):
            st.rerun()
    
    with col2:
        if st.button("📥 Download CSV Report"):
            with st.spinner("Downloading..."):
                csv_data = download_validation_csv()
                if csv_data:
                    st.download_button(
                        label="💾 Save CSV",
                        data=csv_data,
                        file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
    
    with col3:
        st.caption(f"Generated: {datetime.now().strftime('%H:%M:%S')}")
    
    # Fetch validation data
    with st.spinner("Running comprehensive validation..."):
        validation_data = get_validation_report()
    
    if validation_data:
        # Display overview
        display_validation_overview(validation_data)
        
        st.divider()
        
        # Display pipeline
        display_stage_pipeline(validation_data)
        
        st.divider()
        
        # Display error summary charts
        display_error_summary_charts(validation_data)
        
        st.divider()
        
        # Display detailed stage results
        display_stage_details(validation_data)
        
        # Show raw data in expander
        with st.expander("🔍 Raw Validation Data (JSON)"):
            st.json(validation_data)
    
    else:
        st.error("Failed to load validation report. Please check the backend connection.")

if __name__ == "__main__":
    main()