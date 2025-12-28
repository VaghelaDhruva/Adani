"""
Raw Data Preview Dashboard

Read-only preview of raw data from database tables with sorting, filtering, and pagination.
Shows warning icons on problematic rows.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

from config import API_BASE

st.set_page_config(page_title="Raw Data Preview", layout="wide")

def get_raw_data(table_name, limit=100, offset=0):
    """Fetch raw data from API."""
    try:
        params = {"limit": limit, "offset": offset}
        response = requests.get(f"{API_BASE}/dashboard/raw-data/{table_name}", params=params, timeout=30)
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
        ("plant_master", "🏭 Plant Master"),
        ("production_capacity_cost", "⚙️ Production Capacity & Cost"),
        ("transport_routes_modes", "🚛 Transport Routes & Modes"),
        ("demand_forecast", "📈 Demand Forecast"),
        ("initial_inventory", "📦 Initial Inventory"),
        ("safety_stock_policy", "🛡️ Safety Stock Policy")
    ]
    
    selected_table = st.selectbox(
        "Select Table to Preview",
        options=[table[0] for table in tables],
        format_func=lambda x: next(table[1] for table in tables if table[0] == x),
        index=0
    )
    
    return selected_table

def identify_problematic_rows(df, table_name):
    """Identify rows with potential issues and add warning flags."""
    if df.empty:
        return df
    
    df = df.copy()
    df['_warnings'] = ""
    df['_has_issues'] = False
    
    # Table-specific validation rules
    if table_name == "demand_forecast":
        # Negative demand
        if "demand_tonnes" in df.columns:
            negative_mask = df["demand_tonnes"] < 0
            df.loc[negative_mask, '_warnings'] += "Negative demand; "
            df.loc[negative_mask, '_has_issues'] = True
    
    elif table_name == "production_capacity_cost":
        # Non-positive capacity
        if "max_capacity_tonnes" in df.columns:
            zero_capacity_mask = df["max_capacity_tonnes"] <= 0
            df.loc[zero_capacity_mask, '_warnings'] += "Non-positive capacity; "
            df.loc[zero_capacity_mask, '_has_issues'] = True
        
        # Negative costs
        if "variable_cost_per_tonne" in df.columns:
            negative_cost_mask = df["variable_cost_per_tonne"] < 0
            df.loc[negative_cost_mask, '_warnings'] += "Negative cost; "
            df.loc[negative_cost_mask, '_has_issues'] = True
    
    elif table_name == "transport_routes_modes":
        # Origin equals destination
        if "origin_plant_id" in df.columns and "destination_node_id" in df.columns:
            same_origin_dest = df["origin_plant_id"] == df["destination_node_id"]
            df.loc[same_origin_dest, '_warnings'] += "Origin = Destination; "
            df.loc[same_origin_dest, '_has_issues'] = True
        
        # Non-positive vehicle capacity
        if "vehicle_capacity_tonnes" in df.columns:
            zero_capacity_mask = df["vehicle_capacity_tonnes"] <= 0
            df.loc[zero_capacity_mask, '_warnings'] += "Non-positive vehicle capacity; "
            df.loc[zero_capacity_mask, '_has_issues'] = True
        
        # SBQ > vehicle capacity
        if "min_batch_quantity_tonnes" in df.columns and "vehicle_capacity_tonnes" in df.columns:
            sbq_violation = (df["min_batch_quantity_tonnes"].notna() & 
                           df["vehicle_capacity_tonnes"].notna() &
                           (df["min_batch_quantity_tonnes"] > df["vehicle_capacity_tonnes"]))
            df.loc[sbq_violation, '_warnings'] += "SBQ > Vehicle capacity; "
            df.loc[sbq_violation, '_has_issues'] = True
    
    elif table_name == "plant_master":
        # Missing critical fields
        critical_fields = ["plant_id", "plant_name", "plant_type"]
        for field in critical_fields:
            if field in df.columns:
                missing_mask = df[field].isna() | (df[field] == "")
                df.loc[missing_mask, '_warnings'] += f"Missing {field}; "
                df.loc[missing_mask, '_has_issues'] = True
    
    elif table_name == "initial_inventory":
        # Negative inventory
        if "inventory_tonnes" in df.columns:
            negative_mask = df["inventory_tonnes"] < 0
            df.loc[negative_mask, '_warnings'] += "Negative inventory; "
            df.loc[negative_mask, '_has_issues'] = True
    
    elif table_name == "safety_stock_policy":
        # Negative safety stock
        if "safety_stock_tonnes" in df.columns:
            negative_mask = df["safety_stock_tonnes"] < 0
            df.loc[negative_mask, '_warnings'] += "Negative safety stock; "
            df.loc[negative_mask, '_has_issues'] = True
    
    # Clean up warnings
    df['_warnings'] = df['_warnings'].str.rstrip('; ')
    
    return df

def display_data_table(data, table_name):
    """Display data table with pagination and issue highlighting."""
    if not data:
        return
    
    df = pd.DataFrame(data["data"])
    pagination = data["pagination"]
    columns = data["columns"]
    
    if df.empty:
        st.warning(f"No data found in {table_name}")
        return
    
    # Identify problematic rows
    df_with_warnings = identify_problematic_rows(df, table_name)
    
    # Display summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", f"{pagination['total_count']:,}")
    
    with col2:
        st.metric("Showing", f"{len(df):,}")
    
    with col3:
        issues_count = df_with_warnings['_has_issues'].sum()
        st.metric("Rows with Issues", issues_count, delta="⚠️" if issues_count > 0 else None)
    
    with col4:
        st.metric("Columns", len(columns))
    
    # Filter controls
    col1, col2 = st.columns(2)
    
    with col1:
        show_issues_only = st.checkbox("Show only rows with issues", value=False)
    
    with col2:
        if df_with_warnings['_has_issues'].any():
            st.info(f"⚠️ {df_with_warnings['_has_issues'].sum()} rows have validation issues")
    
    # Apply filter
    display_df = df_with_warnings.copy()
    if show_issues_only:
        display_df = display_df[display_df['_has_issues']]
    
    # Prepare display dataframe
    display_columns = [col for col in columns if col in display_df.columns]
    
    # Add warning column if there are issues
    if display_df['_has_issues'].any():
        display_df['⚠️ Issues'] = display_df.apply(
            lambda row: f"⚠️ {row['_warnings']}" if row['_has_issues'] else "",
            axis=1
        )
        display_columns = ['⚠️ Issues'] + display_columns
    
    # Display table
    st.dataframe(
        display_df[display_columns],
        use_container_width=True,
        height=600
    )
    
    # Pagination controls
    if pagination['total_count'] > pagination['limit']:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            current_page = pagination['offset'] // pagination['limit'] + 1
            total_pages = (pagination['total_count'] - 1) // pagination['limit'] + 1
            st.write(f"Page {current_page} of {total_pages}")
        
        with col2:
            # Page navigation would require state management
            st.info("Use the limit parameter above to load more records")
        
        with col3:
            if pagination['has_more']:
                st.write("More data available")

def display_data_summary_charts(data, table_name):
    """Display summary charts for the data."""
    if not data or not data["data"]:
        return
    
    df = pd.DataFrame(data["data"])
    
    if df.empty:
        return
    
    st.subheader("📊 Data Summary")
    
    # Table-specific charts
    if table_name == "demand_forecast" and "demand_tonnes" in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Demand distribution
            fig = px.histogram(
                df,
                x="demand_tonnes",
                title="Demand Distribution",
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Demand by period (if period column exists)
            if "period" in df.columns:
                period_demand = df.groupby("period")["demand_tonnes"].sum().reset_index()
                fig = px.bar(
                    period_demand,
                    x="period",
                    y="demand_tonnes",
                    title="Total Demand by Period"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    elif table_name == "production_capacity_cost" and "max_capacity_tonnes" in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Capacity distribution
            fig = px.histogram(
                df,
                x="max_capacity_tonnes",
                title="Production Capacity Distribution",
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Cost vs capacity scatter
            if "variable_cost_per_tonne" in df.columns:
                fig = px.scatter(
                    df,
                    x="max_capacity_tonnes",
                    y="variable_cost_per_tonne",
                    title="Cost vs Capacity",
                    hover_data=["plant_id"] if "plant_id" in df.columns else None
                )
                st.plotly_chart(fig, use_container_width=True)
    
    elif table_name == "transport_routes_modes":
        col1, col2 = st.columns(2)
        
        with col1:
            # Transport mode distribution
            if "transport_mode" in df.columns:
                mode_counts = df["transport_mode"].value_counts()
                fig = px.pie(
                    values=mode_counts.values,
                    names=mode_counts.index,
                    title="Transport Mode Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Distance distribution
            if "distance_km" in df.columns:
                fig = px.histogram(
                    df,
                    x="distance_km",
                    title="Distance Distribution (km)",
                    nbins=20
                )
                st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("👁️ Raw Data Preview")
    st.markdown("Read-only preview of database tables with issue detection")
    
    # Table selector
    selected_table = display_table_selector()
    
    # Controls
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        limit = st.selectbox("Records per page", [50, 100, 200, 500], index=1)
    
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    with col3:
        st.info("⚠️ Warning icons indicate rows that may cause validation issues")
    
    # Fetch and display data
    with st.spinner(f"Loading {selected_table} data..."):
        data = get_raw_data(selected_table, limit=limit)
    
    if data:
        # Display data table
        display_data_table(data, selected_table)
        
        st.divider()
        
        # Display summary charts
        display_data_summary_charts(data, selected_table)
        
        # Show column info
        with st.expander("📋 Column Information"):
            if data.get("columns"):
                col_df = pd.DataFrame({
                    "Column": data["columns"],
                    "Position": range(1, len(data["columns"]) + 1)
                })
                st.dataframe(col_df, use_container_width=True)
    
    else:
        st.error("Failed to load data. Please check the backend connection.")

if __name__ == "__main__":
    main()