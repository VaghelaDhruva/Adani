"""
Clean Data Preview Dashboard

Shows the FINAL cleaned dataset that will be fed into the optimization model.
Provides transparency into data cleaning and normalization process.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from config import API_BASE

st.set_page_config(page_title="Clean Data Preview", layout="wide")

def get_clean_data_preview(table_name, limit=100):
    """Fetch clean data preview from API."""
    try:
        params = {"limit": limit}
        response = requests.get(f"{API_BASE}/dashboard/clean-data/{table_name}", params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None

def get_all_clean_data_previews(limit=50):
    """Fetch all clean data previews."""
    try:
        params = {"limit": limit}
        response = requests.get(f"{API_BASE}/dashboard/clean-data", params=params, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None

def display_table_selector():
    """Display table selection interface."""
    tables = [
        ("plants", "🏭 Plants"),
        ("production_capacity_cost", "⚙️ Production Capacity & Cost"),
        ("transport_routes_modes", "🚛 Transport Routes & Modes"),
        ("demand_forecast", "📈 Demand Forecast"),
        ("initial_inventory", "📦 Initial Inventory"),
        ("safety_stock_policy", "🛡️ Safety Stock Policy")
    ]
    
    selected_table = st.selectbox(
        "Select Clean Data View",
        options=[table[0] for table in tables],
        format_func=lambda x: next(table[1] for table in tables if table[0] == x),
        index=0
    )
    
    return selected_table

def display_cleaning_summary(clean_data):
    """Display summary of data cleaning process."""
    if not clean_data:
        return
    
    st.subheader("🧹 Data Cleaning Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Rows", f"{clean_data.get('total_rows', 0):,}")
    
    with col2:
        st.metric("Preview Rows", f"{clean_data.get('preview_rows', 0):,}")
    
    with col3:
        st.metric("Columns", len(clean_data.get('columns', [])))
    
    with col4:
        cleaned_at = clean_data.get('cleaned_at', '')
        if cleaned_at:
            try:
                clean_time = datetime.fromisoformat(cleaned_at.replace('Z', '+00:00'))
                st.metric("Cleaned At", clean_time.strftime('%H:%M:%S'))
            except:
                st.metric("Cleaned At", "Unknown")
    
    # Show null counts
    null_counts = clean_data.get('null_counts', {})
    if null_counts:
        st.subheader("📊 Missing Values After Cleaning")
        
        null_df = pd.DataFrame([
            {"Column": col, "Missing Values": count, "Missing %": f"{count/clean_data.get('total_rows', 1)*100:.1f}%"}
            for col, count in null_counts.items()
            if count > 0
        ])
        
        if not null_df.empty:
            st.dataframe(null_df, use_container_width=True)
        else:
            st.success("✅ No missing values in cleaned data")

def display_data_types_info(clean_data):
    """Display data types information."""
    if not clean_data:
        return
    
    data_types = clean_data.get('data_types', {})
    if data_types:
        st.subheader("🔢 Data Types")
        
        type_df = pd.DataFrame([
            {"Column": col, "Data Type": dtype}
            for col, dtype in data_types.items()
        ])
        
        st.dataframe(type_df, use_container_width=True)

def display_clean_data_table(clean_data):
    """Display the cleaned data table."""
    if not clean_data or not clean_data.get('data'):
        st.warning("No clean data available")
        return
    
    df = pd.DataFrame(clean_data['data'])
    
    st.subheader("✨ Cleaned Data")
    st.info("This is the FINAL dataset that will be used by the optimization model")
    
    # Display the data
    st.dataframe(df, use_container_width=True, height=600)
    
    # Show sample statistics for numeric columns
    numeric_columns = df.select_dtypes(include=['number']).columns
    if len(numeric_columns) > 0:
        st.subheader("📈 Numeric Column Statistics")
        stats_df = df[numeric_columns].describe()
        st.dataframe(stats_df, use_container_width=True)

def display_cleaning_transformations(table_name):
    """Display information about cleaning transformations applied."""
    st.subheader("🔧 Applied Transformations")
    
    transformations = {
        "plants": [
            "✅ Trimmed and normalized plant_id (uppercase)",
            "✅ Trimmed plant_name and plant_type",
            "✅ Converted plant_type to lowercase",
            "✅ Removed rows with missing critical fields",
            "✅ Removed duplicate plant_id entries",
            "✅ Converted coordinates to float"
        ],
        "production_capacity_cost": [
            "✅ Normalized plant_id (uppercase)",
            "✅ Converted numeric fields to float",
            "✅ Added default holding cost (10.0)",
            "✅ Removed rows with non-positive capacity",
            "✅ Removed rows with negative costs",
            "✅ Removed duplicate (plant_id, period) combinations"
        ],
        "transport_routes_modes": [
            "✅ Normalized plant and node IDs (uppercase)",
            "✅ Normalized transport_mode (lowercase)",
            "✅ Applied default values for missing distances/costs",
            "✅ Removed illegal routes (origin = destination)",
            "✅ Removed routes with non-positive vehicle capacity",
            "✅ Ensured SBQ ≤ vehicle capacity",
            "✅ Calculated total cost per tonne",
            "✅ Filtered to active routes only"
        ],
        "demand_forecast": [
            "✅ Normalized customer_node_id (uppercase)",
            "✅ Converted demand to float",
            "✅ Removed rows with negative demand",
            "✅ Removed duplicate (customer, period) combinations",
            "✅ Set default confidence level (0.95)"
        ],
        "initial_inventory": [
            "✅ Normalized node_id (uppercase)",
            "✅ Converted inventory to float",
            "✅ Removed rows with negative inventory",
            "✅ Removed duplicate (node_id, period) combinations"
        ],
        "safety_stock_policy": [
            "✅ Normalized node_id (uppercase)",
            "✅ Normalized policy_type (lowercase)",
            "✅ Converted numeric fields to float",
            "✅ Removed rows with negative safety stock",
            "✅ Removed duplicate node_id entries"
        ]
    }
    
    table_transformations = transformations.get(table_name, [])
    
    for transformation in table_transformations:
        st.write(transformation)

def display_data_quality_metrics(clean_data):
    """Display data quality metrics."""
    if not clean_data or not clean_data.get('data'):
        return
    
    df = pd.DataFrame(clean_data['data'])
    
    st.subheader("📊 Data Quality Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Completeness
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        completeness = (total_cells - missing_cells) / total_cells * 100
        
        st.metric(
            "Data Completeness",
            f"{completeness:.1f}%",
            delta=f"{total_cells - missing_cells:,} / {total_cells:,} cells"
        )
    
    with col2:
        # Uniqueness (for ID columns)
        id_columns = [col for col in df.columns if 'id' in col.lower()]
        if id_columns:
            unique_ratios = []
            for col in id_columns:
                unique_ratio = df[col].nunique() / len(df) * 100
                unique_ratios.append(unique_ratio)
            avg_uniqueness = sum(unique_ratios) / len(unique_ratios)
            st.metric("ID Uniqueness", f"{avg_uniqueness:.1f}%")
        else:
            st.metric("ID Uniqueness", "N/A")
    
    with col3:
        # Consistency (no mixed data types in string columns)
        string_columns = df.select_dtypes(include=['object']).columns
        consistent_columns = 0
        for col in string_columns:
            # Simple check: no numeric values in string columns
            if not df[col].astype(str).str.match(r'^\d+\.?\d*$').any():
                consistent_columns += 1
        
        if len(string_columns) > 0:
            consistency = consistent_columns / len(string_columns) * 100
            st.metric("Type Consistency", f"{consistency:.1f}%")
        else:
            st.metric("Type Consistency", "100%")

def display_all_tables_overview():
    """Display overview of all clean data tables."""
    st.subheader("📋 All Clean Data Tables Overview")
    
    with st.spinner("Loading all clean data previews..."):
        all_previews = get_all_clean_data_previews(limit=10)
    
    if all_previews and all_previews.get('previews'):
        previews = all_previews['previews']
        
        # Create summary table
        summary_data = []
        for table_name, preview in previews.items():
            if 'error' not in preview:
                summary_data.append({
                    "Table": table_name.replace('_', ' ').title(),
                    "Total Rows": f"{preview.get('total_rows', 0):,}",
                    "Columns": len(preview.get('columns', [])),
                    "Missing Values": sum(preview.get('null_counts', {}).values()),
                    "Status": "✅ Clean" if preview.get('total_rows', 0) > 0 else "⚠️ Empty"
                })
            else:
                summary_data.append({
                    "Table": table_name.replace('_', ' ').title(),
                    "Total Rows": "Error",
                    "Columns": "Error",
                    "Missing Values": "Error",
                    "Status": "❌ Error"
                })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
        
        # Show generation time
        generated_at = all_previews.get('generated_at', '')
        if generated_at:
            try:
                gen_time = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                st.caption(f"Generated at: {gen_time.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                st.caption(f"Generated at: {generated_at}")

def main():
    st.title("✨ Clean Data Preview")
    st.markdown("Preview of cleaned, validated data ready for optimization")
    
    # Show overview first
    display_all_tables_overview()
    
    st.divider()
    
    # Table selector
    selected_table = display_table_selector()
    
    # Controls
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        limit = st.selectbox("Preview rows", [50, 100, 200], index=1)
    
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    with col3:
        st.info("This data has been cleaned, validated, and normalized")
    
    # Fetch and display clean data
    with st.spinner(f"Loading clean {selected_table} data..."):
        clean_data = get_clean_data_preview(selected_table, limit=limit)
    
    if clean_data:
        # Display cleaning summary
        display_cleaning_summary(clean_data)
        
        st.divider()
        
        # Display transformations applied
        display_cleaning_transformations(selected_table)
        
        st.divider()
        
        # Display data quality metrics
        display_data_quality_metrics(clean_data)
        
        st.divider()
        
        # Display the clean data table
        display_clean_data_table(clean_data)
        
        st.divider()
        
        # Display data types info
        display_data_types_info(clean_data)
        
        # Show raw response in expander
        with st.expander("🔍 Raw API Response"):
            st.json(clean_data)
    
    else:
        st.error("Failed to load clean data. Please check the backend connection.")

if __name__ == "__main__":
    main()