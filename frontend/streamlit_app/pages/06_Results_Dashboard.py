"""
Results Dashboard

Live optimization results from backend API with comprehensive visualization:
- Cost breakdown and analysis
- Production plan visualization  
- Shipment routing analysis
- Inventory profiles
- Service level metrics
- Real-time data with caching
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import time

from config import API_BASE
from styles import apply_common_styles, create_page_header, create_section_header, create_status_box, create_custom_divider

st.set_page_config(page_title="Results Dashboard", layout="wide")

# Apply common styling
apply_common_styles()


def format_inr(value):
    """Format currency value in Indian Rupees with lakh/crore notation."""
    try:
        if value is None or value == 0:
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


@st.cache_data(ttl=30)
def fetch_results(run_id: str):
    """
    Fetch optimization results from backend API with caching.
    
    Args:
        run_id: The optimization run ID to fetch results for
        
    Returns:
        tuple: (results_data, error_message)
    """
    try:
        # Try the new optimization engine endpoint first
        response = requests.get(
            f"{API_BASE}/optimize/{run_id}/results",
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 202:
            return None, "Optimization still running — please check back in a few minutes"
        elif response.status_code == 404:
            # Try the old endpoint as fallback
            response = requests.get(
                f"{API_BASE}/runs/{run_id}/results",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json(), None
            elif response.status_code == 404:
                return None, "No results yet — run still processing"
            else:
                return None, f"API Error: {response.status_code}"
        elif response.status_code == 500:
            return None, "Backend error — please try again later"
        else:
            return None, f"API Error: {response.status_code}"
            
    except requests.exceptions.Timeout:
        return None, "Request timeout — backend may be overloaded"
    except requests.exceptions.ConnectionError:
        return None, "Backend unavailable — please try again"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


def get_solver_status_icon(status: str) -> str:
    """Get appropriate icon for solver status."""
    status_lower = status.lower() if status else ""
    
    if status_lower in ["optimal", "feasible"]:
        return "✅"
    elif status_lower in ["infeasible", "unbounded"]:
        return "❌"
    elif status_lower in ["running", "processing"]:
        return "🔄"
    elif status_lower in ["timeout", "limit_reached"]:
        return "⏱️"
    else:
        return "⚠️"


def fetch_available_runs():
    """Fetch list of available optimization runs."""
    try:
        # Try the new optimization engine endpoint first
        response = requests.get(f"{API_BASE}/optimize/runs", timeout=10)
        if response.status_code == 200:
            runs = response.json().get("runs", [])
            return [(run["run_id"], f"{run['run_id']} - {run.get('status', 'Unknown')}") for run in runs]
        
        # Fallback to old endpoint
        response = requests.get(f"{API_BASE}/runs", timeout=10)
        if response.status_code == 200:
            runs = response.json().get("runs", [])
            return [(run["run_id"], f"{run['run_id']} - {run.get('status', 'Unknown')}") for run in runs]
        else:
            # Fallback with sample run IDs
            return [
                ("RUN_20250101_120000", "RUN_20250101_120000 - Completed"),
                ("RUN_20250101_110000", "RUN_20250101_110000 - Completed"),
                ("RUN_20250101_100000", "RUN_20250101_100000 - Failed")
            ]
    except:
        # Fallback with sample run IDs
        return [
            ("RUN_20250101_120000", "RUN_20250101_120000 - Completed"),
            ("RUN_20250101_110000", "RUN_20250101_110000 - Completed"),
            ("RUN_20250101_100000", "RUN_20250101_100000 - Failed")
        ]

def display_results_overview(results):
    """Display high-level results overview from live API data."""
    st.subheader("📊 Optimization Results Overview")
    
    # Key metrics from API response
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_cost = results.get("total_cost", 0)
        st.metric("Total Cost", format_inr(total_cost))
    
    with col2:
        service_level = results.get("service_level", 0)
        if isinstance(service_level, (int, float)):
            st.metric("Service Level", f"{service_level:.1%}")
        else:
            st.metric("Service Level", "N/A")
    
    with col3:
        solver_status = results.get("solver_status", "Unknown")
        status_icon = get_solver_status_icon(solver_status)
        st.metric("Solver Status", f"{status_icon} {solver_status.title()}")
    
    with col4:
        runtime = results.get("runtime_seconds", 0)
        if isinstance(runtime, (int, float)):
            st.metric("Runtime", f"{runtime:.1f}s")
        else:
            st.metric("Runtime", "N/A")
    
    with col5:
        gap = results.get("optimality_gap", 0)
        if isinstance(gap, (int, float)):
            st.metric("Optimality Gap", f"{gap:.2%}")
        else:
            st.metric("Optimality Gap", "N/A")


def display_cost_breakdown(results):
    """Display detailed cost breakdown from live API data."""
    st.subheader("💰 Cost Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Cost metrics from API
        production_cost = results.get("production_cost", 0)
        transportation_cost = results.get("transportation_cost", 0)
        fixed_trip_cost = results.get("fixed_trip_cost", 0)
        holding_cost = results.get("holding_cost", 0)
        
        st.metric("Production Cost", format_inr(production_cost))
        st.metric("Transportation Cost", format_inr(transportation_cost))
        st.metric("Fixed Trip Cost", format_inr(fixed_trip_cost))
        st.metric("Holding Cost", format_inr(holding_cost))
        
        # Check for penalty costs (may be in different fields)
        penalty_cost = results.get("penalty_cost", 0) or results.get("total_penalty_cost", 0)
        if penalty_cost > 0:
            st.metric("Penalty Cost", format_inr(penalty_cost), delta="⚠️ Constraints violated")
    
    with col2:
        # Cost breakdown pie chart
        cost_data = {}
        
        if production_cost > 0:
            cost_data["Production"] = production_cost
        if transportation_cost > 0:
            cost_data["Transportation"] = transportation_cost
        if fixed_trip_cost > 0:
            cost_data["Fixed Trips"] = fixed_trip_cost
        if holding_cost > 0:
            cost_data["Holding"] = holding_cost
        if penalty_cost > 0:
            cost_data["Penalties"] = penalty_cost
        
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
        else:
            st.info("No cost breakdown data available")


def display_production_plan(results):
    """Display production plan from live API data."""
    st.subheader("🏭 Production Plan")
    
    # Check for production data in various possible formats
    production_data = (
        results.get("production", []) or 
        results.get("production_plan", []) or
        results.get("solution", {}).get("production", [])
    )
    
    if not production_data:
        st.info("No production plan data available from API")
        return
    
    try:
        prod_df = pd.DataFrame(production_data)
        
        # Filter out zero production
        if "tonnes" in prod_df.columns:
            prod_df = prod_df[prod_df["tonnes"] > 0]
        elif "quantity" in prod_df.columns:
            prod_df = prod_df[prod_df["quantity"] > 0]
            prod_df = prod_df.rename(columns={"quantity": "tonnes"})
        
        if prod_df.empty:
            st.info("No production scheduled")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Production table
            st.write("**Production Schedule**")
            st.dataframe(prod_df, use_container_width=True)
            
            # Summary statistics
            if "tonnes" in prod_df.columns:
                total_production = prod_df["tonnes"].sum()
                st.metric("Total Production", f"{total_production:,.0f} tonnes")
        
        with col2:
            # Production by plant/facility
            plant_col = "plant" if "plant" in prod_df.columns else "facility"
            if plant_col in prod_df.columns and "tonnes" in prod_df.columns:
                plant_production = prod_df.groupby(plant_col)["tonnes"].sum().reset_index()
                
                fig = px.bar(
                    plant_production,
                    x=plant_col,
                    y="tonnes",
                    title="Total Production by Plant",
                    color="tonnes",
                    color_continuous_scale="Blues"
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        # Production over time
        if "period" in prod_df.columns and "tonnes" in prod_df.columns:
            st.write("**Production Over Time**")
            
            period_production = prod_df.groupby(["period", plant_col])["tonnes"].sum().reset_index()
            
            fig = px.bar(
                period_production,
                x="period",
                y="tonnes",
                color=plant_col,
                title="Production by Period and Plant",
                barmode="stack"
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error displaying production plan: {str(e)}")
        st.info("Raw production data:")
        st.json(production_data[:5])  # Show first 5 records for debugging


def display_shipment_analysis(results):
    """Display shipment analysis from live API data."""
    st.subheader("🚛 Shipment Analysis")
    
    # Check for shipment data in various formats
    shipment_data = (
        results.get("shipments", []) or
        results.get("shipment_plan", []) or
        results.get("solution", {}).get("shipments", [])
    )
    
    if not shipment_data:
        st.info("No shipment data available from API")
        return
    
    try:
        ship_df = pd.DataFrame(shipment_data)
        
        # Standardize column names
        quantity_col = "tonnes" if "tonnes" in ship_df.columns else "quantity"
        if quantity_col in ship_df.columns:
            ship_df = ship_df[ship_df[quantity_col] > 0]
            if quantity_col != "tonnes":
                ship_df = ship_df.rename(columns={quantity_col: "tonnes"})
        
        if ship_df.empty:
            st.info("No shipments scheduled")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Shipments by transport mode
            if "mode" in ship_df.columns:
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
            origin_col = "origin" if "origin" in ship_df.columns else "from"
            if origin_col in ship_df.columns:
                origin_shipments = ship_df.groupby(origin_col)["tonnes"].sum().reset_index()
                
                fig = px.bar(
                    origin_shipments,
                    x=origin_col,
                    y="tonnes",
                    title="Shipments by Origin",
                    color="tonnes",
                    color_continuous_scale="Greens"
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        # Detailed shipment table
        st.write("**Shipment Details**")
        st.dataframe(ship_df, use_container_width=True)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_shipments = ship_df["tonnes"].sum()
            st.metric("Total Shipments", f"{total_shipments:,.0f} tonnes")
        
        with col2:
            if "trips" in ship_df.columns:
                total_trips = ship_df["trips"].sum()
                st.metric("Total Trips", f"{total_trips:,.0f}")
        
        with col3:
            unique_routes = len(ship_df.drop_duplicates(subset=[origin_col, "destination"] if "destination" in ship_df.columns else [origin_col]))
            st.metric("Unique Routes", unique_routes)
            
    except Exception as e:
        st.error(f"Error displaying shipment analysis: {str(e)}")
        st.info("Raw shipment data:")
        st.json(shipment_data[:5])  # Show first 5 records for debugging

def display_inventory_profile(results):
    """Display inventory analysis from live API data."""
    st.subheader("📦 Inventory Profile")
    
    # Check for inventory data in various formats
    inventory_data = (
        results.get("inventory", []) or
        results.get("inventory_plan", []) or
        results.get("solution", {}).get("inventory", [])
    )
    
    if not inventory_data:
        st.info("No inventory data available from API")
        return
    
    try:
        inv_df = pd.DataFrame(inventory_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Inventory table
            st.write("**Inventory Levels**")
            st.dataframe(inv_df, use_container_width=True)
            
            # Summary statistics
            if "tonnes" in inv_df.columns:
                total_inventory = inv_df["tonnes"].sum()
                avg_inventory = inv_df["tonnes"].mean()
                
                st.metric("Total Inventory", f"{total_inventory:,.0f} tonnes")
                st.metric("Average Inventory", f"{avg_inventory:.0f} tonnes")
        
        with col2:
            # Inventory by plant/location
            location_col = "plant" if "plant" in inv_df.columns else "location"
            if location_col in inv_df.columns and "tonnes" in inv_df.columns:
                location_inventory = inv_df.groupby(location_col)["tonnes"].sum().reset_index()
                
                fig = px.bar(
                    location_inventory,
                    x=location_col,
                    y="tonnes",
                    title=f"Total Inventory by {location_col.title()}",
                    color="tonnes",
                    color_continuous_scale="Oranges"
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        # Inventory over time
        if "period" in inv_df.columns and "tonnes" in inv_df.columns:
            st.write("**Inventory Over Time**")
            
            fig = px.line(
                inv_df,
                x="period",
                y="tonnes",
                color=location_col,
                title="Inventory Levels Over Time",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error displaying inventory profile: {str(e)}")
        st.info("Raw inventory data:")
        st.json(inventory_data[:5])


def display_service_level_metrics(results):
    """Display service level and performance metrics from live API data."""
    st.subheader("📈 Service Level & Performance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        service_level = results.get("service_level", 0)
        if isinstance(service_level, (int, float)):
            delta_text = "Target: 95%" if service_level >= 0.95 else "Below target"
            st.metric("Service Level", f"{service_level:.1%}", delta=delta_text)
        else:
            st.metric("Service Level", "N/A")
    
    with col2:
        # Check for stockout risk or similar metrics
        stockout_risk = results.get("stockout_risk", results.get("unmet_demand_rate", 0))
        if isinstance(stockout_risk, (int, float)):
            delta_text = "Low risk" if stockout_risk <= 0.05 else "High risk"
            st.metric("Stockout Risk", f"{stockout_risk:.1%}", delta=delta_text)
        else:
            st.metric("Stockout Risk", "N/A")
    
    with col3:
        # Check for capacity utilization
        capacity_util = results.get("capacity_utilization", results.get("avg_utilization", 0))
        if isinstance(capacity_util, (int, float)):
            delta_text = "Optimal" if 0.8 <= capacity_util <= 0.95 else "Review"
            st.metric("Avg Capacity Utilization", f"{capacity_util:.1%}", delta=delta_text)
        elif isinstance(capacity_util, dict):
            avg_util = sum(capacity_util.values()) / len(capacity_util)
            delta_text = "Optimal" if 0.8 <= avg_util <= 0.95 else "Review"
            st.metric("Avg Capacity Utilization", f"{avg_util:.1%}", delta=delta_text)
        else:
            st.metric("Avg Capacity Utilization", "N/A")
    
    # Detailed capacity utilization if available
    capacity_util = results.get("capacity_utilization", {})
    if isinstance(capacity_util, dict) and capacity_util:
        st.write("**Capacity Utilization by Plant**")
        
        util_df = pd.DataFrame([
            {"Plant": plant, "Utilization": util}
            for plant, util in capacity_util.items()
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
    """Display any constraint violations or penalties from live API data."""
    # Check for penalty costs in various fields
    penalty_cost = (
        results.get("penalty_cost", 0) or 
        results.get("total_penalty_cost", 0) or
        results.get("violation_cost", 0)
    )
    
    if penalty_cost > 0:
        st.subheader("⚠️ Constraint Violations")
        st.error(f"Total penalty cost: {format_inr(penalty_cost)}")
        
        # Look for detailed penalty breakdown
        penalty_details = []
        
        unmet_demand = results.get("unmet_demand_penalty", 0)
        if unmet_demand > 0:
            penalty_details.append({
                "Type": "Unmet Demand",
                "Cost": unmet_demand,
                "Description": "Demand that could not be satisfied"
            })
        
        safety_stock_violation = results.get("safety_stock_violation_penalty", 0)
        if safety_stock_violation > 0:
            penalty_details.append({
                "Type": "Safety Stock Violation", 
                "Cost": safety_stock_violation,
                "Description": "Inventory below safety stock levels"
            })
        
        capacity_violation = results.get("capacity_violation_penalty", 0)
        if capacity_violation > 0:
            penalty_details.append({
                "Type": "Capacity Violation",
                "Cost": capacity_violation,
                "Description": "Production exceeding plant capacity"
            })
        
        if penalty_details:
            penalty_df = pd.DataFrame(penalty_details)
            penalty_df["Cost"] = penalty_df["Cost"].apply(format_inr)
            st.dataframe(penalty_df, use_container_width=True)
        
        st.warning("⚠️ Consider reviewing constraints or increasing capacity to eliminate penalties")
    else:
        st.success("✅ No constraint violations - all constraints satisfied")


def display_export_options(results, run_id):
    """Display export options for results."""
    st.subheader("📤 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export JSON"):
            json_data = json.dumps(results, indent=2)
            st.download_button(
                label="💾 Download JSON",
                data=json_data,
                file_name=f"optimization_results_{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 Export CSV"):
            # Create CSV from available data
            csv_data = []
            
            # Add cost summary
            csv_data.append({
                "Type": "Cost Summary",
                "Item": "Total Cost",
                "Value": results.get("total_cost", 0),
                "Unit": "INR"
            })
            
            for cost_type in ["production_cost", "transportation_cost", "fixed_trip_cost", "holding_cost"]:
                if cost_type in results:
                    csv_data.append({
                        "Type": "Cost Breakdown",
                        "Item": cost_type.replace("_", " ").title(),
                        "Value": results[cost_type],
                        "Unit": "INR"
                    })
            
            # Add performance metrics
            if "service_level" in results:
                csv_data.append({
                    "Type": "Performance",
                    "Item": "Service Level",
                    "Value": results["service_level"],
                    "Unit": "Percentage"
                })
            
            if "runtime_seconds" in results:
                csv_data.append({
                    "Type": "Performance", 
                    "Item": "Runtime",
                    "Value": results["runtime_seconds"],
                    "Unit": "Seconds"
                })
            
            if csv_data:
                csv_df = pd.DataFrame(csv_data)
                csv_string = csv_df.to_csv(index=False)
                
                st.download_button(
                    label="💾 Download CSV",
                    data=csv_string,
                    file_name=f"optimization_results_{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    with col3:
        st.info("📄 PDF export coming soon")


def main():
    # Create styled page header
    create_page_header("📊 Results Dashboard", "Live optimization results from backend API")
    
    # Run selection and refresh controls with enhanced styling
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        available_runs = fetch_available_runs()
        if available_runs:
            run_options = [run_id for run_id, display_name in available_runs]
            run_display_names = [display_name for run_id, display_name in available_runs]
            
            selected_run = st.selectbox(
                "Select Optimization Run",
                run_options,
                format_func=lambda x: dict(available_runs)[x],
                help="Choose the optimization run to view results for"
            )
        else:
            create_status_box("No optimization runs available", "error")
            return
    
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            # Clear the cache for the selected run
            fetch_results.clear()
            st.rerun()
    
    with col3:
        # Show cache status with styled info
        st.markdown("""
        <div class="metric-card">
            <h3>Cache Status</h3>
            <div style="color: #667eea; font-size: 1rem;">30s TTL</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Fetch results with loading state
    with st.spinner("Loading results..."):
        results, error = fetch_results(selected_run)
    
    # Handle different states with styled messages
    if error and results is None:
        if "processing" in error.lower():
            create_status_box(f"⏳ {error}", "info")
            create_status_box("The optimization is still running. Please check back in a few minutes.", "info")
        elif "unavailable" in error.lower():
            create_status_box(f"🔌 {error}", "error")
            create_status_box("Please check if the backend service is running and try again.", "info")
        else:
            create_status_box(f"❌ {error}", "error")
            create_status_box("Please try refreshing or selecting a different run.", "info")
        return
    
    # Warning for partial data
    if error and results is not None:
        create_status_box(f"⚠️ Partial data loaded: {error}", "warning")
    
    # Validate results data
    if results is None:
        create_status_box("❌ No results data available", "error")
        create_status_box("Please ensure the optimization run completed successfully.", "info")
        return
    
    # Display all result sections with enhanced styling
    try:
        # Results overview
        display_results_overview(results)
        
        create_custom_divider()
        
        # Cost breakdown
        display_cost_breakdown(results)
        
        create_custom_divider()
        
        # Production plan
        display_production_plan(results)
        
        create_custom_divider()
        
        # Shipment analysis
        display_shipment_analysis(results)
        
        create_custom_divider()
        
        # Inventory profile
        display_inventory_profile(results)
        
        create_custom_divider()
        
        # Service level metrics
        display_service_level_metrics(results)
        
        create_custom_divider()
        
        # Constraint violations
        display_constraint_violations(results)
        
        create_custom_divider()
        
        # Export options
        display_export_options(results, selected_run)
        
        # Raw data in expander for debugging
        with st.expander("🔍 Raw API Response (JSON)"):
            st.json(results)
    
    except Exception as e:
        create_status_box("❌ Dashboard rendering error", "error")
        create_status_box(f"Error details: {str(e)}", "error")
        create_status_box("Please refresh the page or contact system administrator.", "info")
        
        # Show raw data for debugging
        with st.expander("🔍 Raw API Response for Debugging"):
            st.json(results)


if __name__ == "__main__":
    main()