"""
Integration Services Dashboard

Dashboard for monitoring and managing all integration services:
- ERP Integration (SAP/Oracle)
- External APIs (Weather, Market Data, Fuel Prices)
- Real-time Streams (IoT, Vehicle Tracking)
- Automated Refresh Services
- Optimization Engine
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import asyncio

from config import API_BASE
from styles import apply_common_styles, create_page_header, create_section_header, create_status_box, create_custom_divider

st.set_page_config(page_title="Integration Dashboard", layout="wide", page_icon="🔗")

# Apply common styling
apply_common_styles()


def get_integration_health():
    """Get health status of all integration services."""
    try:
        response = requests.get(f"{API_BASE}/integrations/health", timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return None, "Backend unavailable"
    except Exception as e:
        return None, str(e)


def get_erp_data(endpoint: str):
    """Get data from ERP integration endpoints."""
    try:
        response = requests.get(f"{API_BASE}/integrations/erp/{endpoint}", timeout=30)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code}"
    except Exception as e:
        return None, str(e)


def get_external_data(endpoint: str):
    """Get data from external API endpoints."""
    try:
        response = requests.get(f"{API_BASE}/integrations/external/{endpoint}", timeout=30)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code}"
    except Exception as e:
        return None, str(e)


def get_realtime_data(endpoint: str):
    """Get real-time data."""
    try:
        response = requests.get(f"{API_BASE}/integrations/realtime/{endpoint}", timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code}"
    except Exception as e:
        return None, str(e)


def get_refresh_status():
    """Get automated refresh service status."""
    try:
        response = requests.get(f"{API_BASE}/integrations/refresh/status", timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code}"
    except Exception as e:
        return None, str(e)


def trigger_manual_refresh(refresh_type: str):
    """Trigger manual refresh for a specific type."""
    try:
        response = requests.post(f"{API_BASE}/integrations/refresh/trigger/{refresh_type}", timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code}"
    except Exception as e:
        return None, str(e)


def run_optimization(scenario: str, solver: str):
    """Run optimization with the actual optimization engine."""
    try:
        payload = {
            "scenario_name": scenario,
            "solver": solver,
            "time_limit": 300,
            "use_sample_data": True
        }
        response = requests.post(f"{API_BASE}/optimize/optimize", json=payload, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code}"
    except Exception as e:
        return None, str(e)


def display_integration_health():
    """Display overall integration health status."""
    create_section_header("🏥 Integration Health Status", "Overall health of all integration services")
    
    health_data, error = get_integration_health()
    
    if error:
        create_status_box(f"❌ Health check failed: {error}", "error")
        return
    
    if not health_data:
        create_status_box("❌ No health data available", "error")
        return
    
    # Overall status
    overall_status = health_data.get("overall_status", "unknown")
    status_colors = {"healthy": "🟢", "degraded": "🟡", "down": "🔴"}
    status_icon = status_colors.get(overall_status, "⚪")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Overall Status</h3>
            <div class="value" style="font-size: 1.5rem;">{status_icon} {overall_status.title()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        erp_status = health_data.get("erp_integration", {}).get("status", "unknown")
        erp_icon = status_colors.get(erp_status, "⚪")
        st.markdown(f"""
        <div class="metric-card">
            <h3>ERP Integration</h3>
            <div class="value" style="font-size: 1.3rem;">{erp_icon} {erp_status.title()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        api_status = health_data.get("external_apis", {}).get("status", "unknown")
        api_icon = status_colors.get(api_status, "⚪")
        st.markdown(f"""
        <div class="metric-card">
            <h3>External APIs</h3>
            <div class="value" style="font-size: 1.3rem;">{api_icon} {api_status.title()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        realtime_status = health_data.get("realtime_streams", {}).get("status", "unknown")
        realtime_icon = status_colors.get(realtime_status, "⚪")
        st.markdown(f"""
        <div class="metric-card">
            <h3>Real-time Streams</h3>
            <div class="value" style="font-size: 1.3rem;">{realtime_icon} {realtime_status.title()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Service details
    st.markdown("### Service Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ERP Services
        erp_services = health_data.get("erp_integration", {}).get("services", [])
        if erp_services:
            st.markdown("**ERP Services:**")
            for service in erp_services:
                st.markdown(f"• {service}")
        
        # External API Services
        api_services = health_data.get("external_apis", {}).get("services", [])
        if api_services:
            st.markdown("**External API Services:**")
            for service in api_services:
                st.markdown(f"• {service}")
    
    with col2:
        # Real-time Streams
        realtime_streams = health_data.get("realtime_streams", {}).get("active_streams", [])
        if realtime_streams:
            st.markdown("**Active Real-time Streams:**")
            for stream in realtime_streams:
                st.markdown(f"• {stream.title()}")
        
        # Automated Refresh
        refresh_status = health_data.get("automated_refresh", {}).get("status", "unknown")
        last_run = health_data.get("automated_refresh", {}).get("last_run", "Never")
        st.markdown("**Automated Refresh:**")
        st.markdown(f"• Status: {refresh_status.title()}")
        st.markdown(f"• Last Run: {last_run}")


def display_erp_integration():
    """Display ERP integration section."""
    create_section_header("🏢 ERP Integration", "SAP and Oracle system integration")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Plants", "Capacity", "Demand Forecast", "Inventory"])
    
    with tab1:
        st.markdown("#### Plant Master Data from SAP")
        if st.button("🔄 Fetch Plants Data"):
            with st.spinner("Fetching plants data from SAP..."):
                data, error = get_erp_data("plants")
                
                if error:
                    create_status_box(f"❌ Failed to fetch plants data: {error}", "error")
                elif data:
                    plants_df = pd.DataFrame(data.get("plants", []))
                    if not plants_df.empty:
                        st.dataframe(plants_df, use_container_width=True)
                        st.success(f"✅ Fetched {data.get('count', 0)} plants from SAP")
                    else:
                        st.info("No plants data available")
    
    with tab2:
        st.markdown("#### Production Capacity from Oracle")
        col1, col2 = st.columns(2)
        with col1:
            start_period = st.text_input("Start Period", value="2025-01", placeholder="YYYY-MM")
        with col2:
            end_period = st.text_input("End Period", value="2025-03", placeholder="YYYY-MM")
        
        if st.button("🔄 Fetch Capacity Data"):
            with st.spinner("Fetching capacity data from Oracle..."):
                # Note: This would need query parameters in a real implementation
                data, error = get_erp_data("capacity")
                
                if error:
                    create_status_box(f"❌ Failed to fetch capacity data: {error}", "error")
                elif data:
                    capacity_df = pd.DataFrame(data.get("capacity", []))
                    if not capacity_df.empty:
                        st.dataframe(capacity_df, use_container_width=True)
                        st.success(f"✅ Fetched {data.get('count', 0)} capacity records from Oracle")
                    else:
                        st.info("No capacity data available")
    
    with tab3:
        st.markdown("#### Demand Forecast from SAP APO/IBP")
        horizon_months = st.slider("Forecast Horizon (months)", 1, 24, 6)
        
        if st.button("🔄 Fetch Demand Forecast"):
            with st.spinner("Fetching demand forecast from SAP..."):
                data, error = get_erp_data("demand-forecast")
                
                if error:
                    create_status_box(f"❌ Failed to fetch demand forecast: {error}", "error")
                elif data:
                    demand_df = pd.DataFrame(data.get("demand_forecast", []))
                    if not demand_df.empty:
                        st.dataframe(demand_df, use_container_width=True)
                        
                        # Visualization
                        if "demand_tonnes" in demand_df.columns and "period" in demand_df.columns:
                            fig = px.line(
                                demand_df,
                                x="period",
                                y="demand_tonnes",
                                color="customer_node_id" if "customer_node_id" in demand_df.columns else None,
                                title="Demand Forecast Trend"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"✅ Fetched {data.get('count', 0)} demand forecast records")
                    else:
                        st.info("No demand forecast data available")
    
    with tab4:
        st.markdown("#### Current Inventory Levels")
        if st.button("🔄 Fetch Inventory Data"):
            with st.spinner("Fetching inventory data from ERP..."):
                data, error = get_erp_data("inventory")
                
                if error:
                    create_status_box(f"❌ Failed to fetch inventory data: {error}", "error")
                elif data:
                    inventory_df = pd.DataFrame(data.get("inventory", []))
                    if not inventory_df.empty:
                        st.dataframe(inventory_df, use_container_width=True)
                        
                        # Visualization
                        if "inventory_tonnes" in inventory_df.columns and "node_id" in inventory_df.columns:
                            fig = px.bar(
                                inventory_df,
                                x="node_id",
                                y="inventory_tonnes",
                                title="Current Inventory Levels by Location"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"✅ Fetched {data.get('count', 0)} inventory records")
                    else:
                        st.info("No inventory data available")


def display_external_apis():
    """Display external APIs section."""
    create_section_header("🌐 External APIs", "Weather, market data, and fuel prices")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Weather", "Fuel Prices", "Market Data", "Economic Indicators"])
    
    with tab1:
        st.markdown("#### Weather Forecast Data")
        days_ahead = st.slider("Days Ahead", 1, 14, 7)
        
        if st.button("🔄 Fetch Weather Data"):
            with st.spinner("Fetching weather data..."):
                data, error = get_external_data("weather")
                
                if error:
                    create_status_box(f"❌ Failed to fetch weather data: {error}", "error")
                elif data:
                    weather_df = pd.DataFrame(data.get("weather", []))
                    if not weather_df.empty:
                        st.dataframe(weather_df, use_container_width=True)
                        
                        # Temperature chart
                        if "temperature_celsius" in weather_df.columns and "city" in weather_df.columns:
                            fig = px.line(
                                weather_df,
                                x="date",
                                y="temperature_celsius",
                                color="city",
                                title="Temperature Forecast by City"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"✅ Fetched {data.get('count', 0)} weather records")
                    else:
                        st.info("No weather data available")
    
    with tab2:
        st.markdown("#### Fuel Price Data")
        if st.button("🔄 Fetch Fuel Prices"):
            with st.spinner("Fetching fuel price data..."):
                data, error = get_external_data("fuel-prices")
                
                if error:
                    create_status_box(f"❌ Failed to fetch fuel prices: {error}", "error")
                elif data:
                    fuel_df = pd.DataFrame(data.get("fuel_prices", []))
                    if not fuel_df.empty:
                        st.dataframe(fuel_df, use_container_width=True)
                        
                        # Price trend chart
                        if "price_inr_per_liter" in fuel_df.columns and "date" in fuel_df.columns:
                            fig = px.line(
                                fuel_df,
                                x="date",
                                y="price_inr_per_liter",
                                title="Fuel Price Trend (INR per Liter)"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"✅ Fetched {data.get('count', 0)} fuel price records")
                    else:
                        st.info("No fuel price data available")
    
    with tab3:
        st.markdown("#### Cement Market Data")
        if st.button("🔄 Fetch Market Data"):
            with st.spinner("Fetching market data..."):
                data, error = get_external_data("market-data")
                
                if error:
                    create_status_box(f"❌ Failed to fetch market data: {error}", "error")
                elif data:
                    market_df = pd.DataFrame(data.get("market_data", []))
                    if not market_df.empty:
                        st.dataframe(market_df, use_container_width=True)
                        
                        # Price by market chart
                        if "price_inr_per_tonne" in market_df.columns and "market" in market_df.columns:
                            latest_data = market_df.groupby("market")["price_inr_per_tonne"].last().reset_index()
                            fig = px.bar(
                                latest_data,
                                x="market",
                                y="price_inr_per_tonne",
                                title="Latest Cement Prices by Market (INR per Tonne)"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"✅ Fetched {data.get('count', 0)} market data records")
                    else:
                        st.info("No market data available")
    
    with tab4:
        st.markdown("#### Economic Indicators")
        if st.button("🔄 Fetch Economic Indicators"):
            with st.spinner("Fetching economic indicators..."):
                data, error = get_external_data("economic-indicators")
                
                if error:
                    create_status_box(f"❌ Failed to fetch economic indicators: {error}", "error")
                elif data:
                    economic_df = pd.DataFrame(data.get("economic_indicators", []))
                    if not economic_df.empty:
                        st.dataframe(economic_df, use_container_width=True)
                        
                        # Indicators chart
                        if "value" in economic_df.columns and "indicator_name" in economic_df.columns:
                            latest_data = economic_df.groupby("indicator_name")["value"].last().reset_index()
                            fig = px.bar(
                                latest_data,
                                x="indicator_name",
                                y="value",
                                title="Latest Economic Indicators"
                            )
                            fig.update_xaxis(tickangle=45)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"✅ Fetched {data.get('count', 0)} economic indicator records")
                    else:
                        st.info("No economic indicators available")


def display_realtime_streams():
    """Display real-time streams section."""
    create_section_header("📡 Real-time Data Streams", "IoT sensors, vehicle tracking, and production monitoring")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Production", "Vehicles", "Inventory", "Quality", "Energy"])
    
    with tab1:
        st.markdown("#### Production Sensor Data")
        if st.button("🔄 Get Latest Production Data"):
            with st.spinner("Fetching real-time production data..."):
                data, error = get_realtime_data("production")
                
                if error:
                    create_status_box(f"❌ Failed to fetch production data: {error}", "error")
                elif data:
                    production_df = pd.DataFrame(data.get("production_data", []))
                    if not production_df.empty:
                        st.dataframe(production_df, use_container_width=True)
                        
                        # Production rate chart
                        if "production_rate_tph" in production_df.columns and "plant_id" in production_df.columns:
                            fig = px.bar(
                                production_df,
                                x="plant_id",
                                y="production_rate_tph",
                                color="line_id" if "line_id" in production_df.columns else None,
                                title="Current Production Rates (Tonnes per Hour)"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"✅ Fetched {data.get('count', 0)} production data points")
                    else:
                        st.info("No production data available")
    
    with tab2:
        st.markdown("#### Vehicle Tracking Data")
        if st.button("🔄 Get Latest Vehicle Data"):
            with st.spinner("Fetching real-time vehicle data..."):
                data, error = get_realtime_data("vehicles")
                
                if error:
                    create_status_box(f"❌ Failed to fetch vehicle data: {error}", "error")
                elif data:
                    vehicle_df = pd.DataFrame(data.get("vehicle_data", []))
                    if not vehicle_df.empty:
                        st.dataframe(vehicle_df, use_container_width=True)
                        
                        # Vehicle status chart
                        if "status" in vehicle_df.columns:
                            status_counts = vehicle_df["status"].value_counts()
                            fig = px.pie(
                                values=status_counts.values,
                                names=status_counts.index,
                                title="Vehicle Status Distribution"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"✅ Fetched {data.get('count', 0)} vehicle data points")
                    else:
                        st.info("No vehicle data available")
    
    with tab3:
        st.markdown("#### Inventory Sensor Data")
        if st.button("🔄 Get Latest Inventory Data"):
            with st.spinner("Fetching real-time inventory data..."):
                data, error = get_realtime_data("inventory")
                
                if error:
                    create_status_box(f"❌ Failed to fetch inventory data: {error}", "error")
                elif data:
                    inventory_df = pd.DataFrame(data.get("inventory_data", []))
                    if not inventory_df.empty:
                        st.dataframe(inventory_df, use_container_width=True)
                        
                        # Inventory levels chart
                        if "level_percent" in inventory_df.columns and "plant_id" in inventory_df.columns:
                            fig = px.bar(
                                inventory_df,
                                x="plant_id",
                                y="level_percent",
                                color="silo_id" if "silo_id" in inventory_df.columns else None,
                                title="Current Inventory Levels (%)"
                            )
                            fig.add_hline(y=20, line_dash="dash", line_color="red", annotation_text="Low Level Alert")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"✅ Fetched {data.get('count', 0)} inventory data points")
                    else:
                        st.info("No inventory data available")
    
    with tab4:
        st.markdown("#### Quality Control Data")
        if st.button("🔄 Get Latest Quality Data"):
            with st.spinner("Fetching real-time quality data..."):
                data, error = get_realtime_data("quality")
                
                if error:
                    create_status_box(f"❌ Failed to fetch quality data: {error}", "error")
                elif data:
                    quality_df = pd.DataFrame(data.get("quality_data", []))
                    if not quality_df.empty:
                        st.dataframe(quality_df, use_container_width=True)
                        
                        # Quality pass/fail chart
                        if "quality_passed" in quality_df.columns:
                            pass_counts = quality_df["quality_passed"].value_counts()
                            fig = px.pie(
                                values=pass_counts.values,
                                names=pass_counts.index,
                                title="Quality Test Results",
                                color_discrete_map={True: "green", False: "red"}
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"✅ Fetched {data.get('count', 0)} quality data points")
                    else:
                        st.info("No quality data available")
    
    with tab5:
        st.markdown("#### Energy Monitoring Data")
        if st.button("🔄 Get Latest Energy Data"):
            with st.spinner("Fetching real-time energy data..."):
                data, error = get_realtime_data("energy")
                
                if error:
                    create_status_box(f"❌ Failed to fetch energy data: {error}", "error")
                elif data:
                    energy_df = pd.DataFrame(data.get("energy_data", []))
                    if not energy_df.empty:
                        st.dataframe(energy_df, use_container_width=True)
                        
                        # Energy consumption chart
                        if "power_kw" in energy_df.columns and "equipment_type" in energy_df.columns:
                            fig = px.bar(
                                energy_df,
                                x="equipment_type",
                                y="power_kw",
                                color="plant_id" if "plant_id" in energy_df.columns else None,
                                title="Current Power Consumption (kW)"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"✅ Fetched {data.get('count', 0)} energy data points")
                    else:
                        st.info("No energy data available")


def display_optimization_engine():
    """Display optimization engine section."""
    create_section_header("⚙️ Optimization Engine", "Mathematical optimization with actual solver")
    
    col1, col2 = st.columns(2)
    
    with col1:
        scenario = st.selectbox(
            "Scenario",
            ["base", "high_demand", "low_demand", "capacity_constrained", "transport_disruption", "fuel_price_spike"],
            help="Select optimization scenario"
        )
    
    with col2:
        solver = st.selectbox(
            "Solver",
            ["PULP_CBC_CMD", "HIGHS", "GUROBI"],
            help="Select optimization solver"
        )
    
    if st.button("🚀 Run Optimization", type="primary"):
        with st.spinner("Starting optimization..."):
            result, error = run_optimization(scenario, solver)
            
            if error:
                create_status_box(f"❌ Failed to start optimization: {error}", "error")
            elif result:
                run_id = result.get("run_id")
                st.success(f"✅ Optimization started successfully!")
                st.info(f"**Run ID:** {run_id}")
                st.info(f"**Status:** {result.get('status')}")
                st.info(f"**Estimated Runtime:** {result.get('estimated_runtime')}")
                
                # Show link to results dashboard
                st.markdown("---")
                st.markdown("**Next Steps:**")
                st.markdown("1. Go to the **Results Dashboard** to monitor progress")
                st.markdown("2. Use the Run ID above to track your optimization")
                st.markdown("3. Results will be available once optimization completes")


def display_automated_refresh():
    """Display automated refresh section."""
    create_section_header("🔄 Automated Refresh", "Scheduled data refresh and synchronization")
    
    # Get refresh status
    refresh_data, error = get_refresh_status()
    
    if error:
        create_status_box(f"❌ Failed to get refresh status: {error}", "error")
        return
    
    if not refresh_data:
        create_status_box("❌ No refresh status available", "error")
        return
    
    # Service status
    service_status = refresh_data.get("service_status", "unknown")
    status_colors = {"running": "🟢", "stopped": "🔴"}
    status_icon = status_colors.get(service_status, "⚪")
    
    st.markdown(f"""
    <div class="metric-card">
        <h3>Service Status</h3>
        <div class="value" style="font-size: 1.5rem;">{status_icon} {service_status.title()}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Manual refresh triggers
    st.markdown("#### Manual Refresh Triggers")
    
    refresh_types = [
        ("erp_master_data", "ERP Master Data"),
        ("erp_transactional_data", "ERP Transactional Data"),
        ("external_weather", "Weather Data"),
        ("external_market_data", "Market Data"),
        ("external_fuel_prices", "Fuel Prices"),
        ("realtime_aggregation", "Real-time Aggregation"),
        ("data_quality_check", "Data Quality Check")
    ]
    
    col1, col2 = st.columns(2)
    
    for i, (refresh_type, display_name) in enumerate(refresh_types):
        with col1 if i % 2 == 0 else col2:
            if st.button(f"🔄 {display_name}", key=f"refresh_{refresh_type}"):
                with st.spinner(f"Triggering {display_name.lower()} refresh..."):
                    result, error = trigger_manual_refresh(refresh_type)
                    
                    if error:
                        st.error(f"❌ Failed to trigger refresh: {error}")
                    elif result:
                        st.success(f"✅ {display_name} refresh triggered successfully!")
    
    # Refresh statistics
    if "refresh_statistics" in refresh_data:
        st.markdown("#### Refresh Statistics")
        
        stats = refresh_data["refresh_statistics"]
        if stats:
            stats_df = pd.DataFrame([
                {
                    "Refresh Type": refresh_type.replace("_", " ").title(),
                    "Total Runs": data.get("total_runs", 0),
                    "Successful": data.get("successful_runs", 0),
                    "Failed": data.get("failed_runs", 0),
                    "Success Rate": f"{(data.get('successful_runs', 0) / max(1, data.get('total_runs', 1))) * 100:.1f}%",
                    "Avg Duration": f"{data.get('avg_duration_seconds', 0):.1f}s",
                    "Last Status": data.get("last_run_status", "Never")
                }
                for refresh_type, data in stats.items()
            ])
            
            st.dataframe(stats_df, use_container_width=True)


def main():
    # Create styled page header
    create_page_header("🔗 Integration Services Dashboard", "Monitor and manage all integration services")
    
    # Main sections
    display_integration_health()
    
    create_custom_divider()
    
    # Tabbed interface for different integration services
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏢 ERP Integration",
        "🌐 External APIs", 
        "📡 Real-time Streams",
        "⚙️ Optimization Engine",
        "🔄 Automated Refresh"
    ])
    
    with tab1:
        display_erp_integration()
    
    with tab2:
        display_external_apis()
    
    with tab3:
        display_realtime_streams()
    
    with tab4:
        display_optimization_engine()
    
    with tab5:
        display_automated_refresh()


if __name__ == "__main__":
    main()