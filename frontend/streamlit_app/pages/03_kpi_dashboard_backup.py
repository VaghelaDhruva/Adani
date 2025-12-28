import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import time
import logging
from datetime import datetime

from config import API_BASE


# Configure logging
logger = logging.getLogger(__name__)


# Lightweight schema expectations for validation warnings only.
# Dashboard remains tolerant if these fields are missing.
REQUIRED_KPI_FIELDS = {
    "total_cost",
    "cost_breakdown",
    "production_utilization",
    "transport_utilization",
    "inventory_report",
    "demand_report",
    "data_sources",
    "run_id",
    "timestamp",
}

REQUIRED_COST_FIELDS = {
    "production_cost",
    "transport_cost",
    "inventory_cost",
    "penalty_cost",
}

REQUIRED_SERVICE_FIELDS = {
    "service_level",
}

REQUIRED_INVENTORY_FIELDS = {
    "location",
    "opening",
    "closing",
    "safety_stock",
    "breach",
}


def safe_get_number(container, key, default: float = 0.0) -> float:
    """Safely extract a numeric value from a dict-like container."""
    try:
        if not isinstance(container, dict):
            return default
        val = container.get(key, default)
        if val is None:
            return default
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            # Best-effort numeric conversion
            try:
                return float(val)
            except ValueError:
                return default
        return default
    except Exception:  # pragma: no cover - defensive
        return default


def safe_get_string(container, key, default: str = "") -> str:
    """Safely extract a string value from a dict-like container."""
    if not isinstance(container, dict):
        return default
    val = container.get(key, default)
    return str(val) if val is not None else default


def safe_get_list(container, key) -> list:
    """Safely extract a list value from a dict-like container."""
    if not isinstance(container, dict):
        return []
    val = container.get(key, [])
    return val if isinstance(val, list) else []


def validate_kpi_schema(kpis: dict) -> tuple[bool, list[str]]:
    """Validate KPI payload schema and return (is_valid, error_messages)."""
    errors = []
    
    # Check required top-level fields
    missing_fields = REQUIRED_KPI_FIELDS - set(kpis.keys())
    if missing_fields:
        errors.append(f"Missing required fields: {missing_fields}")
    
    # Validate cost breakdown
    if "cost_breakdown" in kpis:
        cost_breakdown = kpis["cost_breakdown"]
        if not isinstance(cost_breakdown, dict):
            errors.append("cost_breakdown must be a dictionary")
        else:
            missing_costs = REQUIRED_COST_FIELDS - set(cost_breakdown.keys())
            if missing_costs:
                errors.append(f"Missing cost fields: {missing_costs}")
    
    # Validate service performance
    if "service_performance" in kpis:
        service_perf = kpis["service_performance"]
        if not isinstance(service_perf, dict):
            errors.append("service_performance must be a dictionary")
        else:
            missing_service = REQUIRED_SERVICE_FIELDS - set(service_perf.keys())
            if missing_service:
                errors.append(f"Missing service fields: {missing_service}")
    
    # Validate inventory metrics
    if "inventory_metrics" in kpis:
        inventory = kpis["inventory_metrics"]
        if not isinstance(inventory, dict):
            errors.append("inventory_metrics must be a dictionary")
        else:
            missing_inventory = REQUIRED_INVENTORY_FIELDS - set(inventory.keys())
            if missing_inventory:
                errors.append(f"Missing inventory fields: {missing_inventory}")
    
    return len(errors) == 0, errors


def fetch_kpis_with_retry(scenario_name: str, max_retries: int = 3) -> tuple[dict | None, str | None]:
    """Fetch KPIs with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{API_BASE}/kpi/dashboard/{scenario_name}",
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    kpis = response.json()
                    is_valid, errors = validate_kpi_schema(kpis)
                    
                    if is_valid:
                        logger.info(f"Successfully fetched and validated KPIs for {scenario_name}")
                        return kpis, None
                    else:
                        logger.warning(f"KPI schema validation failed: {errors}")
                        # Return partial data with validation warnings
                        return kpis, f"Schema validation warnings: {'; '.join(errors)}"
                
                except ValueError as e:
                    logger.error(f"JSON parsing failed for {scenario_name}: {e}")
                    if attempt == max_retries - 1:
                        return None, f"Failed to parse response data: {str(e)}"
                    
            elif response.status_code == 404:
                logger.warning(f"KPI data not found for scenario {scenario_name}")
                return None, f"Scenario '{scenario_name}' not found"
            
            elif response.status_code >= 500:
                logger.error(f"Server error fetching KPIs for {scenario_name}: {response.status_code}")
                if attempt == max_retries - 1:
                    return None, f"Server error: {response.status_code}"
            
            else:
                logger.warning(f"Unexpected response status: {response.status_code}")
                return None, f"Unexpected error: {response.status_code}"
        
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching KPIs for {scenario_name} (attempt {attempt + 1})")
            if attempt == max_retries - 1:
                return None, "Request timeout - please try again"
        
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error fetching KPIs for {scenario_name} (attempt {attempt + 1})")
            if attempt == max_retries - 1:
                return None, "Connection error - please check your network"
        
        except Exception as e:
            logger.error(f"Unexpected error fetching KPIs for {scenario_name}: {e}")
            return None, f"Unexpected error: {str(e)}"
        
        # Exponential backoff
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    return None, "Failed to fetch KPI data"


def get_safe_kpi_value(value, default=0):
    """Get safe numeric value with fallback."""
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            return float(value) if value.replace('.', '', 1).isdigit() else default
        return default
    except (ValueError, TypeError):
        return default


def format_currency(value):
    """Format currency value safely."""
    try:
        return f"${value:,.0f}"
    except (ValueError, TypeError):
        return "$0"


def format_percentage(value):
    """Format percentage safely."""
    try:
        return f"{value:.1%}"
    except (ValueError, TypeError):
        return "0.0%"


def run():
    """Production-ready KPI dashboard with enterprise error handling."""
    st.title("KPI Dashboard")
    
    # Scenario selection
    scenario_name = st.selectbox("Select scenario", ["base", "high", "low"])
    
    # Loading state
    with st.spinner("Loading KPI data..."):
        kpis, error = fetch_kpis_with_retry(scenario_name)
    
    # Error handling
    if error and kpis is None:
        st.error(f"Failed to load KPI data: {error}")
        st.info("Please try again or select a different scenario.")
        return
    
    # Warning for partial data
    if error and kpis is not None:
        st.warning(f"Data loaded with warnings: {error}")
    
    # Data validation fallback
    if kpis is None:
        st.warning("Using fallback data - some metrics may be unavailable")
        kpis = get_fallback_kpis(scenario_name)
    
    # Display data source information
    data_sources = kpis.get("data_sources", {})
    source_info = f"Primary: {data_sources.get('primary', 'unknown')}"
    if data_sources.get("external_used"):
        source_info += " | External: YES"
    if data_sources.get("quarantine_count", 0) > 0:
        source_info += f" | Quarantined: {data_sources['quarantine_count']}"
    
    st.caption(f"Data Source: {source_info}")
    
    # Timestamp
    timestamp = kpis.get("timestamp", datetime.utcnow().isoformat())
    st.caption(f"Last Updated: {timestamp}")
    
    # Main KPI Cards
    display_kpi_cards(kpis)
    
    # Cost Breakdown Chart
    display_cost_breakdown(kpis)
    
    # Utilization Charts
    display_utilization_charts(kpis)
    
    # Service Performance
    display_service_performance(kpis)
    
    # Inventory Metrics
    display_inventory_metrics(kpis)


def get_fallback_kpis(scenario_name: str) -> dict:
    """Fallback KPI data for graceful degradation."""
    return {
        "scenario_name": scenario_name,
        "total_cost": 0.0,
        "cost_breakdown": {
            "production_cost": 0.0,
            "transport_cost": 0.0,
            "fixed_trip_cost": 0.0,
            "holding_cost": 0.0,
            "penalty_cost": 0.0
        },
        "production_utilization": {},
        "transport_utilization": {},
        "inventory_metrics": {
            "safety_stock_compliance": 0.0,
            "stockout_events": 0,
            "average_inventory_days": 0.0
        },
        "service_performance": {
            "demand_fulfillment_rate": 0.0,
            "on_time_delivery": 0.0,
            "service_level": 0.0
        },
        "data_sources": {"primary": "fallback", "external_used": False, "quarantine_count": 0},
        "timestamp": datetime.utcnow().isoformat()
    }


def display_kpi_cards(kpis: dict):
    """Display main KPI cards with safe formatting."""
    st.subheader("Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_cost = get_safe_kpi_value(kpis.get("total_cost"))
        st.metric(
            "Total Cost",
            format_currency(total_cost),
            delta=None
        )
    
    with col2:
        service_level = get_safe_kpi_value(kpis.get("service_performance", {}).get("service_level"))
        st.metric(
            "Service Level",
            format_percentage(service_level),
            delta=None
        )
    
    with col3:
        fulfillment_rate = get_safe_kpi_value(kpis.get("service_performance", {}).get("demand_fulfillment_rate"))
        st.metric(
            "Demand Fulfillment",
            format_percentage(fulfillment_rate),
            delta=None
        )
    
    with col4:
        stockouts = get_safe_kpi_value(kpis.get("inventory_metrics", {}).get("stockout_events"))
        st.metric(
            "Stockout Events",
            f"{int(stockouts)}",
            delta=None
        )


def display_cost_breakdown(kpis: dict):
    """Display cost breakdown chart."""
    st.subheader("Cost Breakdown")
    
    cost_breakdown = kpis.get("cost_breakdown", {})
    if not cost_breakdown:
        st.warning("No cost data available")
        return
    
    # Prepare data for chart
    cost_data = []
    for category, cost in cost_breakdown.items():
        if cost > 0:
            cost_data.append({
                "Category": category.replace("_", " ").title(),
                "Cost": get_safe_kpi_value(cost)
            })
    
    if not cost_data:
        st.warning("No positive cost values to display")
        return
    
    df_cost = pd.DataFrame(cost_data)
    
    try:
        fig = px.pie(
            df_cost, 
            values="Cost", 
            names="Category",
            title=f"Total Cost: {format_currency(kpis.get('total_cost', 0))}"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        logger.error(f"Error creating cost chart: {e}")
        st.error("Unable to display cost breakdown chart")


def display_utilization_charts(kpis: dict):
    """Display production and transport utilization charts."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Production Utilization")
        prod_util = kpis.get("production_utilization", {})
        if prod_util:
            try:
                df_prod = pd.DataFrame([
                    {"Plant": plant, "Utilization": get_safe_kpi_value(util)}
                    for plant, util in prod_util.items()
                ])
                
                fig = px.bar(
                    df_prod, 
                    x="Plant", 
                    y="Utilization",
                    title="Plant Capacity Utilization",
                    range_y=[0, 1]
                )
                fig.update_layout(yaxis_tickformat='.0%')
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                logger.error(f"Error creating production chart: {e}")
                st.error("Unable to display production utilization")
        else:
            st.warning("No production utilization data available")
    
    with col2:
        st.subheader("Transport Utilization")
        trans_util = kpis.get("transport_utilization", {})
        if trans_util:
            try:
                df_trans = pd.DataFrame([
                    {"Mode": mode, "Utilization": get_safe_kpi_value(util)}
                    for mode, util in trans_util.items()
                ])
                
                fig = px.bar(
                    df_trans, 
                    x="Mode", 
                    y="Utilization",
                    title="Transport Mode Utilization",
                    range_y=[0, 1]
                )
                fig.update_layout(yaxis_tickformat='.0%')
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                logger.error(f"Error creating transport chart: {e}")
                st.error("Unable to display transport utilization")
        else:
            st.warning("No transport utilization data available")


def display_service_performance(kpis: dict):
    """Display service performance metrics."""
    st.subheader("Service Performance")
    
    service_perf = kpis.get("service_performance", {})
    if not service_perf:
        st.warning("No service performance data available")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fulfillment = get_safe_kpi_value(service_perf.get("demand_fulfillment_rate"))
        st.metric("Demand Fulfillment", format_percentage(fulfillment))
    
    with col2:
        on_time = get_safe_kpi_value(service_perf.get("on_time_delivery"))
        st.metric("On-Time Delivery", format_percentage(on_time))
    
    with col3:
        service_level = get_safe_kpi_value(service_perf.get("service_level"))
        st.metric("Service Level", format_percentage(service_level))


def display_inventory_metrics(kpis: dict):
    """Display inventory metrics."""
    st.subheader("Inventory Metrics")
    
    inventory = kpis.get("inventory_metrics", {})
    if not inventory:
        st.warning("No inventory metrics available")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        compliance = get_safe_kpi_value(inventory.get("safety_stock_compliance"))
        st.metric("Safety Stock Compliance", format_percentage(compliance))
    
    with col2:
        stockouts = get_safe_kpi_value(inventory.get("stockout_events"))
        st.metric("Stockout Events", f"{int(stockouts)}")
    
    with col3:
        avg_days = get_safe_kpi_value(inventory.get("average_inventory_days"))
        st.metric("Avg Inventory Days", f"{avg_days:.1f}")
