"""
Enterprise KPI Dashboard

Primary business dashboard providing comprehensive KPI reporting for selected scenarios.
Meets enterprise-grade quality, correctness, clarity, stability, and resilience standards.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import logging
<<<<<<< HEAD
=======
import traceback
>>>>>>> d4196135 (Fixed Bug)

from config import API_BASE
from styles import apply_common_styles, create_page_header, create_section_header, create_status_box, create_custom_divider

st.set_page_config(page_title="KPI Dashboard", layout="wide", page_icon="📊")

# Apply common styling
apply_common_styles()

# Configure logging
logger = logging.getLogger(__name__)

def format_inr(value):
    """Format currency value in Indian Rupees with proper digit grouping."""
    try:
        if value is None or value == 0:
            return "₹0"
        
        amount = float(value)
        negative = amount < 0
        amount = abs(amount)
        
        if amount >= 10000000:  # 1 crore
            crores = amount / 10000000
            return f"{'−' if negative else ''}₹{crores:,.2f} Cr"
        elif amount >= 100000:  # 1 lakh
            lakhs = amount / 100000
            return f"{'−' if negative else ''}₹{lakhs:,.2f} L"
        elif amount >= 1000:  # 1 thousand
            thousands = amount / 1000
            return f"{'−' if negative else ''}₹{thousands:,.1f}K"
        else:
            # Standard Indian number formatting
            return f"{'−' if negative else ''}₹{amount:,.2f}"
    except (ValueError, TypeError):
        return "₹0"

def safe_get(data, key, default=None):
    """Safely get value from nested dictionary."""
    try:
        keys = key.split('.') if isinstance(key, str) else [key]
        result = data
        for k in keys:
            result = result[k]
        return result if result is not None else default
    except (KeyError, TypeError, AttributeError):
        return default

<<<<<<< HEAD
=======
@st.cache_data(ttl=60)  # Cache for 1 minute
>>>>>>> d4196135 (Fixed Bug)
def fetch_kpi_data(scenario_name: str, max_retries: int = 3):
    """Fetch KPI data with retry logic and error handling."""
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{API_BASE}/dashboard/kpi/dashboard/{scenario_name}",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json(), None
            elif response.status_code == 404:
                return None, f"Scenario '{scenario_name}' not found"
            else:
                return None, f"API Error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                return None, "Request timeout - please retry later"
        except requests.exceptions.ConnectionError:
            if attempt == max_retries - 1:
                return None, "Connection error - please check backend service"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"
        
        # Exponential backoff
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    return None, "Failed to fetch KPI data after retries"

<<<<<<< HEAD
=======
@st.cache_data(ttl=300)  # Cache for 5 minutes
>>>>>>> d4196135 (Fixed Bug)
def fetch_available_scenarios():
    """Fetch list of available scenarios."""
    try:
        response = requests.get(f"{API_BASE}/dashboard/scenarios/list", timeout=10)
        if response.status_code == 200:
            return [s["name"] for s in response.json().get("scenarios", [])]
        else:
            return ["base", "high_demand", "low_demand"]  # Fallback
    except:
        return ["base", "high_demand", "low_demand"]  # Fallback

def display_header_context(kpi_data):
    """Display header/context section."""
    create_section_header("📋 Scenario Context", "Current optimization scenario details and data source information")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>Scenario</h3>
            <div class="value" style="font-size: 1.5rem;">{}</div>
        </div>
        """.format(safe_get(kpi_data, "scenario_name", "Unknown")), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="metric-card">
            <h3>Run ID</h3>
            <div class="value" style="font-size: 1rem; color: #6c757d;">{}</div>
        </div>
        """.format(safe_get(kpi_data, "run_id", "N/A")), unsafe_allow_html=True)
    
    with col2:
        timestamp = safe_get(kpi_data, "timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_time = timestamp[:16]
        else:
            formatted_time = "N/A"
            
        st.markdown("""
        <div class="metric-card">
            <h3>Timestamp</h3>
            <div class="value" style="font-size: 1.2rem;">{}</div>
        </div>
        """.format(formatted_time), unsafe_allow_html=True)
        
        uncertainty_mode = safe_get(kpi_data, "uncertainty_mode", "deterministic")
        st.markdown("""
        <div class="metric-card">
            <h3>Analysis Mode</h3>
            <div class="value" style="font-size: 1.3rem;">{}</div>
        </div>
        """.format(uncertainty_mode.title()), unsafe_allow_html=True)
    
    with col3:
        data_source = safe_get(kpi_data, "data_source", {})
        internal_used = safe_get(data_source, "internal_used", True)
        external_used = safe_get(data_source, "external_used", False)
        
        source_text = "Internal"
        if external_used:
            source_text += " + External"
        
        st.markdown("""
        <div class="metric-card">
            <h3>Data Source</h3>
            <div class="value" style="font-size: 1.3rem;">{}</div>
        </div>
        """.format(source_text), unsafe_allow_html=True)
        
        quarantine_count = safe_get(data_source, "quarantine_count", 0)
        status_color = "#28a745" if quarantine_count == 0 else "#dc3545"
        status_icon = "✅" if quarantine_count == 0 else "⚠️"
        
        st.markdown("""
        <div class="metric-card">
            <h3>Quarantine Records</h3>
            <div class="value" style="font-size: 1.5rem; color: {};">{} {}</div>
        </div>
        """.format(status_color, status_icon, quarantine_count), unsafe_allow_html=True)
    
    with col4:
        api_status = safe_get(data_source, "api_status", "unknown")
        status_colors = {"healthy": "#28a745", "degraded": "#ffc107", "down": "#dc3545"}
        status_icons = {"healthy": "🟢", "degraded": "🟡", "down": "🔴"}
        
        color = status_colors.get(api_status, "#6c757d")
        icon = status_icons.get(api_status, "⚪")
        
        st.markdown("""
        <div class="metric-card">
            <h3>API Status</h3>
            <div class="value" style="font-size: 1.3rem; color: {};">{} {}</div>
        </div>
        """.format(color, icon, api_status.title()), unsafe_allow_html=True)
        
        last_refresh = safe_get(data_source, "last_refresh", "")
        if last_refresh:
            try:
                dt = datetime.fromisoformat(last_refresh.replace('Z', '+00:00'))
                refresh_time = dt.strftime('%H:%M')
            except:
                refresh_time = last_refresh[:16]
        else:
            refresh_time = "Unknown"
            
        st.caption(f"Last refresh: {refresh_time}")


def display_cost_summary(kpi_data):
    """Display cost summary section with INR formatting."""
    create_section_header("💰 Cost Summary", "Comprehensive cost breakdown with Indian Rupee formatting")
    
    cost_summary = safe_get(kpi_data, "cost_summary", {})
    
    # Main cost metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_cost = safe_get(cost_summary, "total_cost", 0)
        st.markdown("""
        <div class="metric-card" style="border-left: 4px solid #667eea;">
            <h3>Total Logistics Cost</h3>
            <div class="value" style="color: #667eea;">{}</div>
        </div>
        """.format(format_inr(total_cost)), unsafe_allow_html=True)
    
    with col2:
        production_cost = safe_get(cost_summary, "production_cost", 0)
        st.markdown("""
        <div class="metric-card">
            <h3>Production Cost</h3>
            <div class="value" style="font-size: 1.5rem;">{}</div>
        </div>
        """.format(format_inr(production_cost)), unsafe_allow_html=True)
    
    with col3:
        transport_cost = safe_get(cost_summary, "transport_cost", 0)
        st.markdown("""
        <div class="metric-card">
            <h3>Transportation Cost</h3>
            <div class="value" style="font-size: 1.5rem;">{}</div>
        </div>
        """.format(format_inr(transport_cost)), unsafe_allow_html=True)
    
    with col4:
        inventory_cost = safe_get(cost_summary, "inventory_cost", 0)
        st.markdown("""
        <div class="metric-card">
            <h3>Inventory Holding Cost</h3>
            <div class="value" style="font-size: 1.5rem;">{}</div>
        </div>
        """.format(format_inr(inventory_cost)), unsafe_allow_html=True)
    
    with col5:
        penalty_cost = safe_get(cost_summary, "penalty_cost", 0)
        penalty_color = "#dc3545" if penalty_cost > 0 else "#28a745"
        penalty_icon = "⚠️" if penalty_cost > 0 else "✅"
        
        st.markdown("""
        <div class="metric-card">
            <h3>Penalty Cost</h3>
            <div class="value" style="font-size: 1.5rem; color: {};">{} {}</div>
        </div>
        """.format(penalty_color, penalty_icon, format_inr(penalty_cost)), unsafe_allow_html=True)
    
    # Cost breakdown chart
    if any(cost_summary.values()):
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        cost_data = {
            "Production": safe_get(cost_summary, "production_cost", 0),
            "Transport": safe_get(cost_summary, "transport_cost", 0),
            "Inventory": safe_get(cost_summary, "inventory_cost", 0)
        }
        
        if penalty_cost > 0:
            cost_data["Penalties"] = penalty_cost
        
        # Filter out zero values
        cost_data = {k: v for k, v in cost_data.items() if v > 0}
        
        if cost_data:
            fig = px.pie(
                values=list(cost_data.values()),
                names=list(cost_data.keys()),
                title=f"Cost Breakdown - Total: {format_inr(total_cost)}",
                color_discrete_sequence=['#667eea', '#764ba2', '#f093fb', '#f5576c']
            )
            fig.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                textfont_size=12,
                marker=dict(line=dict(color='#FFFFFF', width=2))
            )
            fig.update_layout(
                font=dict(family="Inter, sans-serif", size=12),
                title_font_size=16,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_service_performance(kpi_data):
    """Display service performance section."""
    st.markdown("### 📈 Service Performance")
    
    service_perf = safe_get(kpi_data, "service_performance", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        service_level = safe_get(service_perf, "service_level", 0)
        delta_color = "normal" if service_level >= 0.95 else "inverse"
        st.metric("Service Level", f"{service_level:.1%}", 
                 delta="Target: 95%" if service_level >= 0.95 else "Below target",
                 delta_color=delta_color)
    
    with col2:
        demand_fulfillment = safe_get(service_perf, "demand_fulfillment", 0)
        st.metric("Demand Fulfillment", f"{demand_fulfillment:.1%}")
    
    with col3:
        on_time_delivery = safe_get(service_perf, "on_time_delivery", 0)
        if on_time_delivery > 0:
            st.metric("On-time Delivery", f"{on_time_delivery:.1%}")
        else:
            st.metric("On-time Delivery", "N/A")
    
    with col4:
        stockout_triggered = safe_get(service_perf, "stockout_triggered", False)
        if stockout_triggered:
            st.metric("Stockout Status", "⚠️ Triggered", delta="Action required")
        else:
            st.metric("Stockout Status", "✅ Normal", delta="Good")

def display_production_utilization(kpi_data):
    """Display production capacity utilization section."""
    st.markdown("### 🏭 Production Capacity Utilization")
    
    production_data = safe_get(kpi_data, "production_utilization", [])
    
    if production_data:
        # Convert to DataFrame
        df = pd.DataFrame(production_data)
        
        # Add color coding for utilization levels
        def get_utilization_color(util):
            if util > 1.0:
                return "🔴"  # Over capacity
            elif util > 0.95:
                return "🟡"  # High utilization
            else:
                return "🟢"  # Normal
        
        df["Status"] = df["utilization_pct"].apply(get_utilization_color)
        df["Utilization %"] = (df["utilization_pct"] * 100).round(1)
        
        # Display table
        display_df = df[["plant_name", "production_used", "production_capacity", "Utilization %", "Status"]].copy()
        display_df.columns = ["Plant Name", "Production Used", "Production Capacity", "Utilization %", "Status"]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Bar chart
        fig = px.bar(
            df,
            x="plant_name",
            y="utilization_pct",
            title="Plant Capacity Utilization",
            color="utilization_pct",
            color_continuous_scale="RdYlGn_r",
            range_color=[0, 1.2]
        )
        fig.update_layout(yaxis_tickformat='.0%')
        fig.add_hline(y=0.95, line_dash="dash", line_color="orange", annotation_text="95% Warning")
        fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="100% Capacity")
        st.plotly_chart(fig, use_container_width=True)

def display_transport_utilization(kpi_data):
    """Display transport utilization, trips, and SBQ enforcement."""
    st.markdown("### 🚛 Transport Utilization & SBQ Enforcement")
    
    transport_data = safe_get(kpi_data, "transport_utilization", [])
    
    if transport_data:
        df = pd.DataFrame(transport_data)
        
        # Format the display
        display_df = df.copy()
        display_df["Capacity Used %"] = (display_df["capacity_used_pct"] * 100).round(1)
        display_df["Route"] = display_df["from"] + " → " + display_df["to"]
        
        # Display table
        table_df = display_df[["Route", "mode", "trips", "Capacity Used %", "sbq_compliance", "violations"]].copy()
        table_df.columns = ["Route", "Mode", "Trips", "Capacity Used %", "SBQ Compliance", "Violations"]
        
        st.dataframe(table_df, use_container_width=True, hide_index=True)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Trips by mode
            mode_trips = df.groupby("mode")["trips"].sum().reset_index()
            fig = px.bar(
                mode_trips,
                x="mode",
                y="trips",
                title="Total Trips by Transport Mode",
                color="trips",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # SBQ compliance
            compliance_counts = df["sbq_compliance"].value_counts()
            fig = px.pie(
                values=compliance_counts.values,
                names=compliance_counts.index,
                title="SBQ Compliance Status",
                color_discrete_map={"Yes": "green", "No": "red", "Partial": "orange"}
            )
            st.plotly_chart(fig, use_container_width=True)

def display_inventory_safety_stock(kpi_data):
    """Display inventory and safety stock section."""
    st.markdown("### 📦 Inventory & Safety Stock")
    
    inventory_data = safe_get(kpi_data, "inventory_status", [])
    safety_compliance = safe_get(kpi_data, "safety_stock_compliance_pct", 0)
    
    # Safety stock compliance metric
    col1, col2 = st.columns([1, 3])
    
    with col1:
        compliance_color = "normal" if safety_compliance >= 90 else "inverse"
        st.metric("Safety Stock Compliance", f"{safety_compliance:.1f}%", 
                 delta="Good" if safety_compliance >= 90 else "Review required",
                 delta_color=compliance_color)
    
    with col2:
        if inventory_data:
            df = pd.DataFrame(inventory_data)
            
            # Add status indicators
            def get_safety_status(row):
                if row["safety_stock_breached"] == "Yes":
                    return "🔴 Breached"
                else:
                    return "🟢 Compliant"
            
            df["Safety Status"] = df.apply(get_safety_status, axis=1)
            
            # Display table
            display_df = df[["location", "opening_inventory", "closing_inventory", "safety_stock", "Safety Status"]].copy()
            display_df.columns = ["Location", "Opening Inventory", "Closing Inventory", "Safety Stock", "Safety Status"]
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)

def display_demand_fulfillment(kpi_data):
    """Display demand fulfillment and backorders section."""
    st.markdown("### 📊 Demand Fulfillment & Backorders")
    
    demand_data = safe_get(kpi_data, "demand_fulfillment", [])
    demand_summary = safe_get(kpi_data, "demand_summary", {})
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_demand = safe_get(demand_summary, "total_demand", 0)
        st.metric("Total Demand", f"{total_demand:,} tonnes")
    
    with col2:
        total_fulfilled = safe_get(demand_summary, "total_fulfilled", 0)
        st.metric("Total Fulfilled", f"{total_fulfilled:,} tonnes")
    
    with col3:
        fulfillment_pct = safe_get(demand_summary, "fulfillment_pct", 0)
        st.metric("Fulfillment Rate", f"{fulfillment_pct:.1f}%")
    
    with col4:
        stockout_pct = safe_get(demand_summary, "stockout_pct", 0)
        st.metric("Stockout Rate", f"{stockout_pct:.1f}%")
    
    # Detailed table
    if demand_data:
        df = pd.DataFrame(demand_data)
        display_df = df[["location", "demand", "fulfilled", "backorder"]].copy()
        display_df.columns = ["Location", "Demand", "Fulfilled", "Backorder"]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Fulfillment chart
        fig = px.bar(
            df,
            x="location",
            y=["fulfilled", "backorder"],
            title="Demand Fulfillment by Location",
            color_discrete_map={"fulfilled": "green", "backorder": "red"}
        )
        st.plotly_chart(fig, use_container_width=True)

def display_uncertainty_analysis(kpi_data):
    """Display uncertainty analysis panel if available."""
    uncertainty_data = safe_get(kpi_data, "uncertainty_analysis")
    
    if uncertainty_data:
        st.markdown("### 🎲 Uncertainty Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            expected_cost = safe_get(uncertainty_data, "expected_cost", 0)
            st.metric("Expected Cost", format_inr(expected_cost))
        
        with col2:
            worst_case_cost = safe_get(uncertainty_data, "worst_case_cost", 0)
            st.metric("Worst-case Cost", format_inr(worst_case_cost))
        
        with col3:
            cost_variance = safe_get(uncertainty_data, "cost_variance", 0)
            st.metric("Cost Variance", f"{cost_variance:,.0f}")
        
        with col4:
            scenarios_evaluated = safe_get(uncertainty_data, "scenarios_evaluated", 0)
            st.metric("Scenarios Evaluated", scenarios_evaluated)
        
        # Scenario results table
        scenario_results = safe_get(uncertainty_data, "scenario_results", [])
        if scenario_results:
            df = pd.DataFrame(scenario_results)
            df["Cost (₹)"] = df["cost"].apply(format_inr)
            df["Service Level"] = (df["service_level"] * 100).round(1).astype(str) + "%"
            df["Probability"] = (df["probability"] * 100).round(1).astype(str) + "%"
            
            display_df = df[["scenario_name", "Cost (₹)", "Service Level", "Probability"]].copy()
            display_df.columns = ["Scenario", "Cost", "Service Level", "Probability"]
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)

def display_data_quality_status(kpi_data):
    """Display data quality and source status badge panel."""
    st.markdown("### 🔍 Data Quality & Source Status")
    
    data_source = safe_get(kpi_data, "data_source", {})
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        internal_used = safe_get(data_source, "internal_used", True)
        st.metric("Internal Data", "✅ Yes" if internal_used else "❌ No")
    
    with col2:
        external_used = safe_get(data_source, "external_used", False)
        st.metric("External Data", "✅ Yes" if external_used else "❌ No")
    
    with col3:
        quarantine_count = safe_get(data_source, "quarantine_count", 0)
        st.metric("Quarantine Records", quarantine_count)
    
    with col4:
        last_refresh = safe_get(data_source, "last_refresh", "")
        if last_refresh:
            try:
                dt = datetime.fromisoformat(last_refresh.replace('Z', '+00:00'))
                st.metric("Last Refresh", dt.strftime("%H:%M"))
            except:
                st.metric("Last Refresh", "Unknown")
        else:
            st.metric("Last Refresh", "Unknown")
    
    with col5:
        api_status = safe_get(data_source, "api_status", "unknown")
        status_colors = {"healthy": "🟢", "degraded": "🟡", "down": "🔴"}
        status_icon = status_colors.get(api_status, "⚪")
        st.metric("API Status", f"{status_icon} {api_status.title()}")

def main():
<<<<<<< HEAD
    # Create styled page header
    create_page_header("📊 Enterprise KPI Dashboard", "Primary business dashboard providing comprehensive KPI reporting")
    
    # Scenario selection with enhanced styling
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        available_scenarios = fetch_available_scenarios()
        scenario_name = st.selectbox(
            "Select Scenario",
            available_scenarios,
            index=0,
            help="Choose the scenario to analyze"
        )
    
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    with col3:
        csv_mode = st.checkbox("CSV Mode", help="Use uploaded CSV data (admin only)")
        if csv_mode:
            create_status_box("⚠️ Using uploaded CSV (non-production dataset)", "warning")
    
    # Load KPI data with loading state
    with st.spinner("Loading KPI data..."):
        kpi_data, error = fetch_kpi_data(scenario_name)
    
    # Error handling with styled messages
    if error and kpi_data is None:
        create_status_box(f"**KPI Service unavailable** — {error}", "error")
        create_status_box("Please retry later or contact system administrator.", "info")
        return
    
    # Warning for partial data
    if error and kpi_data is not None:
        create_status_box(f"**Partial data loaded:** {error}", "warning")
    
    # Data validation
    if kpi_data is None:
        create_status_box("**No KPI data available** — please check scenario configuration.", "error")
        return
    
    # Display all KPI sections with enhanced styling
    try:
        # 1. Header/Context
        display_header_context(kpi_data)
        
        create_custom_divider()
        
        # 2. Cost Summary
        display_cost_summary(kpi_data)
        
        create_custom_divider()
        
        # 3. Service Performance
        display_service_performance(kpi_data)
        
        create_custom_divider()
        
        # 4. Production Utilization
        display_production_utilization(kpi_data)
        
        create_custom_divider()
        
        # 5. Transport Utilization
        display_transport_utilization(kpi_data)
        
        create_custom_divider()
        
        # 6. Inventory & Safety Stock
        display_inventory_safety_stock(kpi_data)
        
        create_custom_divider()
        
        # 7. Demand Fulfillment
        display_demand_fulfillment(kpi_data)
        
        create_custom_divider()
        
        # 8. Uncertainty Analysis (if available)
        display_uncertainty_analysis(kpi_data)
        
        create_custom_divider()
        
        # 9. Data Quality Status
        display_data_quality_status(kpi_data)
        
    except Exception as e:
        logger.error(f"Error displaying KPI dashboard: {e}")
        create_status_box("**Dashboard rendering error** — please refresh the page.", "error")
        create_status_box("If the problem persists, contact system administrator.", "info")

if __name__ == "__main__":
    main()
=======
    """Main function to render the KPI Dashboard."""
    try:
        # Debug info
        st.sidebar.write("🔧 Debug Info:")
        st.sidebar.write(f"API Base: {API_BASE}")
        st.sidebar.write(f"Page loaded at: {datetime.now().strftime('%H:%M:%S')}")
        
        # Create styled page header
        create_page_header("📊 Enterprise KPI Dashboard", "Primary business dashboard providing comprehensive KPI reporting")
        
        # Scenario selection with enhanced styling
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            with st.spinner("Loading available scenarios..."):
                available_scenarios = fetch_available_scenarios()
            
            st.write(f"Available scenarios: {available_scenarios}")  # Debug info
            
            scenario_name = st.selectbox(
                "Select Scenario",
                available_scenarios,
                index=0,
                help="Choose the scenario to analyze"
            )
        
        with col2:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        with col3:
            csv_mode = st.checkbox("CSV Mode", help="Use uploaded CSV data (admin only)")
            if csv_mode:
                create_status_box("⚠️ Using uploaded CSV (non-production dataset)", "warning")
        
        # Load KPI data with loading state
        with st.spinner("Loading KPI data..."):
            kpi_data, error = fetch_kpi_data(scenario_name)
        
        # Debug data state
        st.write("🔍 Data State:")
        st.write(f"- KPI Data loaded: {kpi_data is not None}")
        st.write(f"- Error: {error}")
        if kpi_data:
            st.write(f"- Data keys: {list(kpi_data.keys())}")
        
        # Error handling with styled messages
        if error and kpi_data is None:
            create_status_box(f"**KPI Service unavailable** — {error}", "error")
            create_status_box("Please retry later or contact system administrator.", "info")
            return
        
        # Warning for partial data
        if error and kpi_data is not None:
            create_status_box(f"**Partial data loaded:** {error}", "warning")
        
        # Data validation
        if kpi_data is None:
            create_status_box("**No KPI data available** — please check scenario configuration.", "error")
            return
        
        # Display all KPI sections with enhanced styling
        try:
            # 1. Header/Context
            display_header_context(kpi_data)
            
            create_custom_divider()
            
            # 2. Cost Summary
            display_cost_summary(kpi_data)
            
            create_custom_divider()
            
            # 3. Service Performance
            display_service_performance(kpi_data)
            
            create_custom_divider()
            
            # 4. Production Utilization
            display_production_utilization(kpi_data)
            
            create_custom_divider()
            
            # 5. Transport Utilization
            display_transport_utilization(kpi_data)
            
            create_custom_divider()
            
            # 6. Inventory & Safety Stock
            display_inventory_safety_stock(kpi_data)
            
            create_custom_divider()
            
            # 7. Demand Fulfillment
            display_demand_fulfillment(kpi_data)
            
            create_custom_divider()
            
            # 8. Uncertainty Analysis (if available)
            display_uncertainty_analysis(kpi_data)
            
            create_custom_divider()
            
            # 9. Data Quality Status
            display_data_quality_status(kpi_data)
            
        except Exception as e:
            logger.error(f"Error displaying KPI dashboard sections: {e}")
            st.error(f"Dashboard rendering error: {e}")
            st.code(traceback.format_exc())
            create_status_box("**Dashboard rendering error** — please refresh the page.", "error")
            create_status_box("If the problem persists, contact system administrator.", "info")
            
    except Exception as e:
        logger.error(f"Critical error in KPI Dashboard main: {e}")
        st.error(f"Critical error: {e}")
        st.code(traceback.format_exc())
        st.info("Please refresh the page or contact system administrator.")

# Execute main function directly (not in if __name__ == "__main__")
# This is required for Streamlit multipage apps
try:
    main()
except Exception as e:
    st.error(f"Failed to load KPI Dashboard: {e}")
    st.code(traceback.format_exc())
    st.info("Please refresh the page or check the backend service.")
>>>>>>> d4196135 (Fixed Bug)
