"""
Optimization Console

Central control panel for running optimization with clean, validated data.
Button is enabled ONLY IF all validation stages pass.
Provides real-time job status and streaming logs.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import json

from config import API_BASE

st.set_page_config(page_title="Optimization Console", layout="wide")


def format_inr(value):
    """Format currency value in Indian Rupees with lakh/crore notation."""
    try:
        if value is None:
            return "₹0"
        
        amount = float(value)
        negative = amount < 0
        amount = abs(amount)
        
        if amount >= 10000000:  # 1 crore
            crores = amount / 10000000
            return f"{'−' if negative else ''}₹{crores:.2f} Cr"
        elif amount >= 100000:  # 1 lakh
            lakhs = amount / 100000
            return f"{'−' if negative else ''}₹{lakhs:.2f} L"
        elif amount >= 1000:  # 1 thousand
            thousands = amount / 1000
            return f"{'−' if negative else ''}₹{thousands:.1f}K"
        else:
            return f"{'−' if negative else ''}₹{amount:,.0f}"
    except (ValueError, TypeError):
        return "₹0"

def get_data_health_status():
    """Check if data is ready for optimization."""
    try:
        response = requests.get(f"{API_BASE}/dashboard/health-status", timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_validation_report():
    """Get validation report to check optimization readiness."""
    try:
        response = requests.get(f"{API_BASE}/dashboard/validation-report", timeout=60)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def run_optimization(solver, time_limit, mip_gap):
    """Run optimization with specified parameters."""
    try:
        params = {
            "solver": solver,
            "time_limit": time_limit,
            "mip_gap": mip_gap
        }
        response = requests.post(f"{API_BASE}/dashboard/run-optimization", params=params, timeout=3600)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code} - {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

def display_readiness_check():
    """Display optimization readiness status."""
    st.subheader("🔍 Optimization Readiness Check")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.spinner("Checking data health..."):
            health_data = get_data_health_status()
        
        if health_data:
            overall_status = health_data.get("overall_status", "UNKNOWN")
            optimization_ready = health_data.get("optimization_ready", False)
            
            status_color = {
                "PASS": "🟢",
                "WARN": "🟡", 
                "FAIL": "🔴"
            }.get(overall_status, "⚪")
            
            st.metric(
                "Data Health Status",
                f"{status_color} {overall_status}"
            )
            
            ready_icon = "✅" if optimization_ready else "❌"
            st.metric(
                "Ready for Optimization",
                f"{ready_icon} {'Yes' if optimization_ready else 'No'}"
            )
        else:
            st.error("Failed to check data health")
            optimization_ready = False
    
    with col2:
        with st.spinner("Running validation checks..."):
            validation_data = get_validation_report()
        
        if validation_data:
            validation_ready = validation_data.get("optimization_ready", False)
            summary = validation_data.get("summary", {})
            
            st.metric("Validation Status", "✅ Passed" if validation_ready else "❌ Failed")
            st.metric("Total Errors", summary.get("total_errors", 0))
            st.metric("Total Warnings", summary.get("total_warnings", 0))
            
            # Show stage status
            stages = validation_data.get("stages", [])
            stage_statuses = [stage.get("status") for stage in stages]
            
            st.write("**Validation Stages:**")
            for i, stage in enumerate(stages):
                status = stage.get("status", "UNKNOWN")
                stage_name = stage.get("stage", "").replace("_", " ").title()
                status_icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(status, "❓")
                st.write(f"{i+1}. {status_icon} {stage_name}")
        else:
            st.error("Failed to run validation")
            validation_ready = False
    
    return health_data and health_data.get("optimization_ready", False) and validation_data and validation_data.get("optimization_ready", False)

def display_optimization_controls(optimization_ready):
    """Display optimization control panel."""
    st.subheader("⚙️ Optimization Settings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        solver = st.selectbox(
            "Solver",
            options=["highs", "cbc", "gurobi"],
            index=0,
            help="HiGHS: Fast open-source solver\nCBC: Reliable fallback\nGurobi: Commercial (if licensed)"
        )
    
    with col2:
        time_limit = st.slider(
            "Time Limit (seconds)",
            min_value=60,
            max_value=3600,
            value=600,
            step=60,
            help="Maximum time to spend solving"
        )
    
    with col3:
        mip_gap = st.slider(
            "MIP Gap Tolerance",
            min_value=0.001,
            max_value=0.1,
            value=0.01,
            step=0.001,
            format="%.3f",
            help="Optimality gap tolerance (1% = 0.01)"
        )
    
    # Run button
    st.divider()
    
    if optimization_ready:
        run_button = st.button(
            "🚀 Run Optimization",
            type="primary",
            use_container_width=True,
            help="All validation checks passed - ready to optimize!"
        )
    else:
        st.error("❌ Optimization is blocked due to data validation failures")
        run_button = st.button(
            "🚀 Run Optimization",
            type="primary",
            use_container_width=True,
            disabled=True,
            help="Fix data validation errors before running optimization"
        )
    
    return run_button, solver, time_limit, mip_gap

def display_optimization_progress():
    """Display optimization progress and logs."""
    st.subheader("📊 Optimization Progress")
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Log area
    log_container = st.container()
    
    return progress_bar, status_text, log_container

def display_optimization_results(result):
    """Display optimization results."""
    if "error" in result:
        st.error(f"Optimization failed: {result['error']}")
        return
    
    st.success("✅ Optimization completed successfully!")
    
    # Solver information
    solver_result = result.get("solver_result", {})
    solution = result.get("solution", {})
    kpis = result.get("kpis", {})
    
    st.subheader("🔧 Solver Information")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Solver", solver_result.get("solver", "Unknown"))
    
    with col2:
        st.metric("Status", solver_result.get("status", "Unknown"))
    
    with col3:
        runtime = solver_result.get("runtime_seconds")
        if runtime:
            st.metric("Runtime", f"{runtime:.1f}s")
        else:
            st.metric("Runtime", "Unknown")
    
    with col4:
        gap = solver_result.get("gap")
        if gap:
            st.metric("Final Gap", f"{gap:.3f}")
        else:
            st.metric("Final Gap", "Unknown")
    
    # Cost breakdown
    costs = solution.get("costs", {})
    if costs:
        st.subheader("💰 Cost Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cost metrics
            total_cost = costs.get('production_cost', 0) + costs.get('transport_cost', 0) + costs.get('fixed_trip_cost', 0) + costs.get('holding_cost', 0)
            st.metric("Total Cost", format_inr(total_cost))
            st.metric("Production Cost", format_inr(costs.get('production_cost', 0)))
            st.metric("Transport Cost", format_inr(costs.get('transport_cost', 0)))
            st.metric("Fixed Trip Cost", format_inr(costs.get('fixed_trip_cost', 0)))
            st.metric("Holding Cost", format_inr(costs.get('holding_cost', 0)))
        
        with col2:
            # Cost breakdown pie chart
            cost_data = {
                "Production": costs.get('production_cost', 0),
                "Transport": costs.get('transport_cost', 0),
                "Fixed Trips": costs.get('fixed_trip_cost', 0),
                "Holding": costs.get('holding_cost', 0)
            }
            
            # Filter out zero costs
            cost_data = {k: v for k, v in cost_data.items() if v > 0}
            
            if cost_data:
                fig = px.pie(
                    values=list(cost_data.values()),
                    names=list(cost_data.keys()),
                    title="Cost Breakdown"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Production plan
    production = solution.get("production", [])
    if production:
        st.subheader("🏭 Production Plan")
        
        prod_df = pd.DataFrame(production)
        
        # Filter out zero production
        prod_df = prod_df[prod_df["tonnes"] > 0]
        
        if not prod_df.empty:
            # Production by plant
            plant_production = prod_df.groupby("plant")["tonnes"].sum().reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(prod_df, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    plant_production,
                    x="plant",
                    y="tonnes",
                    title="Total Production by Plant"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Shipments
    shipments = solution.get("shipments", [])
    if shipments:
        st.subheader("🚛 Shipment Plan")
        
        ship_df = pd.DataFrame(shipments)
        
        # Filter out zero shipments
        ship_df = ship_df[ship_df["tonnes"] > 0]
        
        if not ship_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(ship_df.head(20), use_container_width=True)
                if len(ship_df) > 20:
                    st.caption(f"Showing first 20 of {len(ship_df)} shipments")
            
            with col2:
                # Shipments by mode
                mode_shipments = ship_df.groupby("mode")["tonnes"].sum().reset_index()
                fig = px.bar(
                    mode_shipments,
                    x="mode",
                    y="tonnes",
                    title="Shipments by Transport Mode"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Inventory
    inventory = solution.get("inventory", [])
    if inventory:
        st.subheader("📦 Inventory Profile")
        
        inv_df = pd.DataFrame(inventory)
        
        # Filter out zero inventory
        inv_df = inv_df[inv_df["tonnes"] > 0]
        
        if not inv_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(inv_df, use_container_width=True)
            
            with col2:
                # Inventory over time (if period data available)
                if "period" in inv_df.columns:
                    period_inv = inv_df.groupby("period")["tonnes"].sum().reset_index()
                    fig = px.line(
                        period_inv,
                        x="period",
                        y="tonnes",
                        title="Total Inventory Over Time"
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    # KPIs
    if kpis:
        st.subheader("📈 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            service_level = kpis.get("service_level", 0)
            st.metric("Service Level", f"{service_level:.1%}")
        
        with col2:
            stockout_risk = kpis.get("stockout_risk", 0)
            st.metric("Stockout Risk", f"{stockout_risk:.1%}")
        
        with col3:
            total_cost = kpis.get("total_cost", 0)
            st.metric("Total Cost", f"${total_cost:,.2f}")
        
        with col4:
            # Average capacity utilization
            utilization = kpis.get("capacity_utilization", {})
            if utilization:
                avg_util = sum(utilization.values()) / len(utilization)
                st.metric("Avg Capacity Utilization", f"{avg_util:.1%}")
    
    # Export options
    st.subheader("📤 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export JSON"):
            st.download_button(
                label="💾 Download JSON",
                data=json.dumps(result, indent=2),
                file_name=f"optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 Export CSV"):
            # Convert key results to CSV
            csv_data = []
            
            # Add production data
            for prod in production:
                csv_data.append({
                    "Type": "Production",
                    "Plant": prod.get("plant", ""),
                    "Period": prod.get("period", ""),
                    "Tonnes": prod.get("tonnes", 0),
                    "Origin": "",
                    "Destination": "",
                    "Mode": ""
                })
            
            # Add shipment data
            for ship in shipments:
                csv_data.append({
                    "Type": "Shipment",
                    "Plant": "",
                    "Period": ship.get("period", ""),
                    "Tonnes": ship.get("tonnes", 0),
                    "Origin": ship.get("origin", ""),
                    "Destination": ship.get("destination", ""),
                    "Mode": ship.get("mode", "")
                })
            
            if csv_data:
                csv_df = pd.DataFrame(csv_data)
                csv_string = csv_df.to_csv(index=False)
                
                st.download_button(
                    label="💾 Download CSV",
                    data=csv_string,
                    file_name=f"optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    with col3:
        st.info("PDF export coming soon")

def main():
    st.title("🚀 Optimization Console")
    st.markdown("Central control panel for running supply chain optimization")
    
    # Check optimization readiness
    optimization_ready = display_readiness_check()
    
    st.divider()
    
    # Optimization controls
    run_button, solver, time_limit, mip_gap = display_optimization_controls(optimization_ready)
    
    # Handle optimization execution
    if run_button and optimization_ready:
        st.divider()
        
        # Show progress
        progress_bar, status_text, log_container = display_optimization_progress()
        
        # Simulate progress updates
        progress_steps = [
            (10, "Validating data..."),
            (25, "Preparing model inputs..."),
            (40, "Building MILP model..."),
            (60, "Solving optimization..."),
            (90, "Extracting solution..."),
            (100, "Computing KPIs...")
        ]
        
        for progress, message in progress_steps:
            progress_bar.progress(progress)
            status_text.text(message)
            time.sleep(0.5)  # Simulate work
        
        # Run actual optimization
        status_text.text("Running optimization...")
        
        with st.spinner("Solving optimization problem..."):
            result = run_optimization(solver, time_limit, mip_gap)
        
        progress_bar.progress(100)
        status_text.text("Optimization completed!")
        
        st.divider()
        
        # Display results
        display_optimization_results(result)
    
    elif run_button and not optimization_ready:
        st.error("Cannot run optimization - please fix data validation errors first")

if __name__ == "__main__":
    main()