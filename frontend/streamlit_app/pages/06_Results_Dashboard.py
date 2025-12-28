"""
Results Dashboard

Comprehensive visualization of optimization results including:
- Cost breakdown and analysis
- Production plan visualization
- Shipment routing maps
- Inventory profiles
- Service level metrics
- Scenario comparison
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

from config import API_BASE

st.set_page_config(page_title="Results Dashboard", layout="wide")


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

# Sample results data for demonstration (replace with actual API calls)
SAMPLE_RESULTS = {
    "solver_result": {
        "solver": "highs",
        "status": "optimal",
        "runtime_seconds": 45.2,
        "gap": 0.008,
        "termination": "optimal"
    },
    "solution": {
        "production": [
            {"plant": "PLANT_A", "period": "2025-01", "tonnes": 1500},
            {"plant": "PLANT_A", "period": "2025-02", "tonnes": 1800},
            {"plant": "PLANT_B", "period": "2025-01", "tonnes": 2200},
            {"plant": "PLANT_B", "period": "2025-02", "tonnes": 2000},
            {"plant": "PLANT_C", "period": "2025-01", "tonnes": 1200},
            {"plant": "PLANT_C", "period": "2025-02", "tonnes": 1400}
        ],
        "shipments": [
            {"origin": "PLANT_A", "destination": "CUSTOMER_1", "mode": "road", "period": "2025-01", "tonnes": 800},
            {"origin": "PLANT_A", "destination": "CUSTOMER_2", "mode": "rail", "period": "2025-01", "tonnes": 700},
            {"origin": "PLANT_B", "destination": "CUSTOMER_3", "mode": "road", "period": "2025-01", "tonnes": 1200},
            {"origin": "PLANT_B", "destination": "CUSTOMER_4", "mode": "sea", "period": "2025-01", "tonnes": 1000},
            {"origin": "PLANT_C", "destination": "CUSTOMER_5", "mode": "road", "period": "2025-01", "tonnes": 600},
            {"origin": "PLANT_C", "destination": "CUSTOMER_6", "mode": "rail", "period": "2025-01", "tonnes": 600}
        ],
        "inventory": [
            {"plant": "PLANT_A", "period": "2025-01", "tonnes": 200},
            {"plant": "PLANT_A", "period": "2025-02", "tonnes": 150},
            {"plant": "PLANT_B", "period": "2025-01", "tonnes": 300},
            {"plant": "PLANT_B", "period": "2025-02", "tonnes": 250},
            {"plant": "PLANT_C", "period": "2025-01", "tonnes": 100},
            {"plant": "PLANT_C", "period": "2025-02", "tonnes": 120}
        ],
        "trips": [
            {"origin": "PLANT_A", "destination": "CUSTOMER_1", "mode": "road", "period": "2025-01", "trips": 32},
            {"origin": "PLANT_A", "destination": "CUSTOMER_2", "mode": "rail", "period": "2025-01", "trips": 14},
            {"origin": "PLANT_B", "destination": "CUSTOMER_3", "mode": "road", "period": "2025-01", "trips": 48},
            {"origin": "PLANT_B", "destination": "CUSTOMER_4", "mode": "sea", "period": "2025-01", "trips": 2},
            {"origin": "PLANT_C", "destination": "CUSTOMER_5", "mode": "road", "period": "2025-01", "trips": 24},
            {"origin": "PLANT_C", "destination": "CUSTOMER_6", "mode": "rail", "period": "2025-01", "trips": 12}
        ],
        "costs": {
            "production_cost": 2850000,
            "transport_cost": 1240000,
            "fixed_trip_cost": 185000,
            "holding_cost": 45000,
            "total_penalty_cost": 0
        },
        "total_cost": 4320000
    },
    "kpis": {
        "total_cost": 4320000,
        "service_level": 0.98,
        "stockout_risk": 0.02,
        "capacity_utilization": {
            "PLANT_A": 0.85,
            "PLANT_B": 0.92,
            "PLANT_C": 0.78
        }
    }
}

def get_optimization_results(run_id=None):
    """Fetch optimization results from API."""
    # For demo purposes, return sample data
    # In production, this would call the actual API
    return SAMPLE_RESULTS

def display_results_overview(results):
    """Display high-level results overview."""
    solver_result = results.get("solver_result", {})
    solution = results.get("solution", {})
    kpis = results.get("kpis", {})
    
    st.subheader("📊 Optimization Results Overview")
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_cost = solution.get("total_cost", 0)
        st.metric("Total Cost", format_inr(total_cost))
    
    with col2:
        service_level = kpis.get("service_level", 0)
        st.metric("Service Level", f"{service_level:.1%}")
    
    with col3:
        solver_status = solver_result.get("status", "Unknown")
        status_icon = "✅" if solver_status == "optimal" else "⚠️"
        st.metric("Solver Status", f"{status_icon} {solver_status.title()}")
    
    with col4:
        runtime = solver_result.get("runtime_seconds", 0)
        st.metric("Runtime", f"{runtime:.1f}s")
    
    with col5:
        gap = solver_result.get("gap", 0)
        st.metric("Optimality Gap", f"{gap:.2%}")

def display_cost_breakdown(results):
    """Display detailed cost breakdown."""
    solution = results.get("solution", {})
    costs = solution.get("costs", {})
    
    st.subheader("💰 Cost Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Cost metrics
        st.metric("Production Cost", format_inr(costs.get('production_cost', 0)))
        st.metric("Transport Cost", format_inr(costs.get('transport_cost', 0)))
        st.metric("Fixed Trip Cost", format_inr(costs.get('fixed_trip_cost', 0)))
        st.metric("Holding Cost", format_inr(costs.get('holding_cost', 0)))
        
        penalty_cost = costs.get('total_penalty_cost', 0)
        if penalty_cost > 0:
            st.metric("Penalty Cost", format_inr(penalty_cost), delta="⚠️ Constraints violated")
    
    with col2:
        # Cost breakdown pie chart
        cost_data = {
            "Production": costs.get('production_cost', 0),
            "Transport": costs.get('transport_cost', 0),
            "Fixed Trips": costs.get('fixed_trip_cost', 0),
            "Holding": costs.get('holding_cost', 0)
        }
        
        # Add penalty costs if present
        if costs.get('total_penalty_cost', 0) > 0:
            cost_data["Penalties"] = costs.get('total_penalty_cost', 0)
        
        # Filter out zero costs
        cost_data = {k: v for k, v in cost_data.items() if v > 0}
        
        if cost_data:
            total_cost = sum(cost_data.values())
            fig = px.pie(
                values=list(cost_data.values()),
                names=list(cost_data.keys()),
                title=f"Cost Distribution - Total: {format_inr(total_cost)}",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

def display_production_plan(results):
    """Display production plan visualization."""
    solution = results.get("solution", {})
    production = solution.get("production", [])
    
    if not production:
        st.warning("No production data available")
        return
    
    st.subheader("🏭 Production Plan")
    
    prod_df = pd.DataFrame(production)
    
    # Filter out zero production
    prod_df = prod_df[prod_df["tonnes"] > 0]
    
    if prod_df.empty:
        st.warning("No production scheduled")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Production table
        st.write("**Production Schedule**")
        st.dataframe(prod_df, use_container_width=True)
        
        # Summary statistics
        total_production = prod_df["tonnes"].sum()
        st.metric("Total Production", f"{total_production:,.0f} tonnes")
    
    with col2:
        # Production by plant
        plant_production = prod_df.groupby("plant")["tonnes"].sum().reset_index()
        
        fig = px.bar(
            plant_production,
            x="plant",
            y="tonnes",
            title="Total Production by Plant",
            color="tonnes",
            color_continuous_scale="Blues"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Production over time
    if "period" in prod_df.columns:
        st.write("**Production Over Time**")
        
        period_production = prod_df.groupby(["period", "plant"])["tonnes"].sum().reset_index()
        
        fig = px.bar(
            period_production,
            x="period",
            y="tonnes",
            color="plant",
            title="Production by Period and Plant",
            barmode="stack"
        )
        st.plotly_chart(fig, use_container_width=True)

def display_shipment_analysis(results):
    """Display shipment routing and analysis."""
    solution = results.get("solution", {})
    shipments = solution.get("shipments", [])
    trips = solution.get("trips", [])
    
    if not shipments:
        st.warning("No shipment data available")
        return
    
    st.subheader("🚛 Shipment Analysis")
    
    ship_df = pd.DataFrame(shipments)
    trip_df = pd.DataFrame(trips) if trips else pd.DataFrame()
    
    # Filter out zero shipments
    ship_df = ship_df[ship_df["tonnes"] > 0]
    
    if ship_df.empty:
        st.warning("No shipments scheduled")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Shipments by transport mode
        mode_shipments = ship_df.groupby("mode")["tonnes"].sum().reset_index()
        
        fig = px.pie(
            mode_shipments,
            values="tonnes",
            names="mode",
            title="Shipments by Transport Mode",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Shipments by origin
        origin_shipments = ship_df.groupby("origin")["tonnes"].sum().reset_index()
        
        fig = px.bar(
            origin_shipments,
            x="origin",
            y="tonnes",
            title="Shipments by Origin Plant",
            color="tonnes",
            color_continuous_scale="Greens"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed shipment table
    st.write("**Shipment Details**")
    
    # Add trip information if available
    if not trip_df.empty:
        # Merge shipments with trips
        merged_df = ship_df.merge(
            trip_df[["origin", "destination", "mode", "period", "trips"]],
            on=["origin", "destination", "mode", "period"],
            how="left"
        )
        
        # Calculate tonnes per trip
        merged_df["tonnes_per_trip"] = merged_df["tonnes"] / merged_df["trips"].fillna(1)
        
        st.dataframe(merged_df, use_container_width=True)
        
        # Trip summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_trips = trip_df["trips"].sum()
            st.metric("Total Trips", f"{total_trips:,.0f}")
        
        with col2:
            total_shipments = ship_df["tonnes"].sum()
            st.metric("Total Shipments", f"{total_shipments:,.0f} tonnes")
        
        with col3:
            if total_trips > 0:
                avg_load = total_shipments / total_trips
                st.metric("Avg Load per Trip", f"{avg_load:.1f} tonnes")
    else:
        st.dataframe(ship_df, use_container_width=True)

def display_inventory_profile(results):
    """Display inventory analysis."""
    solution = results.get("solution", {})
    inventory = solution.get("inventory", [])
    
    if not inventory:
        st.warning("No inventory data available")
        return
    
    st.subheader("📦 Inventory Profile")
    
    inv_df = pd.DataFrame(inventory)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Inventory table
        st.write("**Inventory Levels**")
        st.dataframe(inv_df, use_container_width=True)
        
        # Summary statistics
        total_inventory = inv_df["tonnes"].sum()
        avg_inventory = inv_df["tonnes"].mean()
        
        st.metric("Total Inventory", f"{total_inventory:,.0f} tonnes")
        st.metric("Average Inventory", f"{avg_inventory:.0f} tonnes")
    
    with col2:
        # Inventory by plant
        if "plant" in inv_df.columns:
            plant_inventory = inv_df.groupby("plant")["tonnes"].sum().reset_index()
            
            fig = px.bar(
                plant_inventory,
                x="plant",
                y="tonnes",
                title="Total Inventory by Plant",
                color="tonnes",
                color_continuous_scale="Oranges"
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    # Inventory over time
    if "period" in inv_df.columns:
        st.write("**Inventory Over Time**")
        
        # Inventory trend by plant
        fig = px.line(
            inv_df,
            x="period",
            y="tonnes",
            color="plant",
            title="Inventory Levels Over Time",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

def display_service_level_metrics(results):
    """Display service level and performance metrics."""
    kpis = results.get("kpis", {})
    
    st.subheader("📈 Service Level & Performance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        service_level = kpis.get("service_level", 0)
        st.metric(
            "Service Level",
            f"{service_level:.1%}",
            delta=f"Target: 95%" if service_level >= 0.95 else f"Below target"
        )
    
    with col2:
        stockout_risk = kpis.get("stockout_risk", 0)
        st.metric(
            "Stockout Risk",
            f"{stockout_risk:.1%}",
            delta="Low risk" if stockout_risk <= 0.05 else "High risk"
        )
    
    with col3:
        # Average capacity utilization
        utilization = kpis.get("capacity_utilization", {})
        if utilization:
            avg_util = sum(utilization.values()) / len(utilization)
            st.metric(
                "Avg Capacity Utilization",
                f"{avg_util:.1%}",
                delta="Optimal" if 0.8 <= avg_util <= 0.95 else "Review"
            )
    
    # Capacity utilization by plant
    if utilization:
        st.write("**Capacity Utilization by Plant**")
        
        util_df = pd.DataFrame([
            {"Plant": plant, "Utilization": util}
            for plant, util in utilization.items()
        ])
        
        fig = px.bar(
            util_df,
            x="Plant",
            y="Utilization",
            title="Capacity Utilization by Plant",
            color="Utilization",
            color_continuous_scale="RdYlGn",
            range_color=[0, 1]
        )
        fig.update_layout(showlegend=False)
        fig.add_hline(y=0.8, line_dash="dash", line_color="orange", annotation_text="Target Min (80%)")
        fig.add_hline(y=0.95, line_dash="dash", line_color="red", annotation_text="Target Max (95%)")
        st.plotly_chart(fig, use_container_width=True)

def display_constraint_violations(results):
    """Display any constraint violations or penalties."""
    solution = results.get("solution", {})
    costs = solution.get("costs", {})
    
    penalty_cost = costs.get("total_penalty_cost", 0)
    
    if penalty_cost > 0:
        st.subheader("⚠️ Constraint Violations")
        st.error(f"Total penalty cost: ${penalty_cost:,.0f}")
        
        # Break down penalty types
        penalty_types = []
        
        if costs.get("unmet_demand_penalty", 0) > 0:
            penalty_types.append({
                "Type": "Unmet Demand",
                "Cost": costs.get("unmet_demand_penalty", 0),
                "Description": "Demand that could not be satisfied"
            })
        
        if costs.get("safety_stock_violation_penalty", 0) > 0:
            penalty_types.append({
                "Type": "Safety Stock Violation",
                "Cost": costs.get("safety_stock_violation_penalty", 0),
                "Description": "Inventory below safety stock levels"
            })
        
        if costs.get("capacity_violation_penalty", 0) > 0:
            penalty_types.append({
                "Type": "Capacity Violation",
                "Cost": costs.get("capacity_violation_penalty", 0),
                "Description": "Production exceeding plant capacity"
            })
        
        if penalty_types:
            penalty_df = pd.DataFrame(penalty_types)
            st.dataframe(penalty_df, use_container_width=True)
            
            st.warning("⚠️ Consider reviewing constraints or increasing capacity to eliminate penalties")
    else:
        st.success("✅ No constraint violations - all constraints satisfied")

def display_export_options(results):
    """Display export options for results."""
    st.subheader("📤 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export JSON"):
            json_data = json.dumps(results, indent=2)
            st.download_button(
                label="💾 Download JSON",
                data=json_data,
                file_name=f"optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 Export CSV"):
            # Create comprehensive CSV export
            csv_data = []
            
            # Production data
            for prod in results.get("solution", {}).get("production", []):
                csv_data.append({
                    "Type": "Production",
                    "Plant": prod.get("plant", ""),
                    "Period": prod.get("period", ""),
                    "Tonnes": prod.get("tonnes", 0),
                    "Origin": "",
                    "Destination": "",
                    "Mode": "",
                    "Trips": ""
                })
            
            # Shipment data
            shipments = results.get("solution", {}).get("shipments", [])
            trips = results.get("solution", {}).get("trips", [])
            
            # Create trip lookup
            trip_lookup = {}
            for trip in trips:
                key = (trip.get("origin"), trip.get("destination"), trip.get("mode"), trip.get("period"))
                trip_lookup[key] = trip.get("trips", 0)
            
            for ship in shipments:
                key = (ship.get("origin"), ship.get("destination"), ship.get("mode"), ship.get("period"))
                trip_count = trip_lookup.get(key, "")
                
                csv_data.append({
                    "Type": "Shipment",
                    "Plant": "",
                    "Period": ship.get("period", ""),
                    "Tonnes": ship.get("tonnes", 0),
                    "Origin": ship.get("origin", ""),
                    "Destination": ship.get("destination", ""),
                    "Mode": ship.get("mode", ""),
                    "Trips": trip_count
                })
            
            # Inventory data
            for inv in results.get("solution", {}).get("inventory", []):
                csv_data.append({
                    "Type": "Inventory",
                    "Plant": inv.get("plant", ""),
                    "Period": inv.get("period", ""),
                    "Tonnes": inv.get("tonnes", 0),
                    "Origin": "",
                    "Destination": "",
                    "Mode": "",
                    "Trips": ""
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
        st.info("📄 PDF export coming soon")

def main():
    st.title("📊 Results Dashboard")
    st.markdown("Comprehensive visualization of optimization results")
    
    # For demo purposes, load sample results
    # In production, this would have run_id selection
    st.info("📝 Demo mode - showing sample optimization results")
    
    results = get_optimization_results()
    
    if results:
        # Results overview
        display_results_overview(results)
        
        st.divider()
        
        # Cost breakdown
        display_cost_breakdown(results)
        
        st.divider()
        
        # Production plan
        display_production_plan(results)
        
        st.divider()
        
        # Shipment analysis
        display_shipment_analysis(results)
        
        st.divider()
        
        # Inventory profile
        display_inventory_profile(results)
        
        st.divider()
        
        # Service level metrics
        display_service_level_metrics(results)
        
        st.divider()
        
        # Constraint violations
        display_constraint_violations(results)
        
        st.divider()
        
        # Export options
        display_export_options(results)
        
        # Raw data in expander
        with st.expander("🔍 Raw Results Data (JSON)"):
            st.json(results)
    
    else:
        st.error("No results available. Please run an optimization first.")

if __name__ == "__main__":
    main()