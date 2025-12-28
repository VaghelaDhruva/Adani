import json
import time
from typing import Any, Dict, List

import requests
import streamlit as st

# --- Configuration ---------------------------------------------------------
API_BASE = st.secrets.get("api_base_url", "http://localhost:8000")
SCENARIOS_URL = f"{API_BASE}/api/v1/scenarios/run"


# --- Helper utilities ----------------------------------------------------
def _post_scenarios(payload: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Call the scenarios API and return parsed JSON response."""
    try:
        resp = requests.post(SCENARIOS_URL, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return {}


def _flatten_kpis(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and flatten KPI fields from a scenario result, handling missing."""
    kpis = scenario.get("kpis", {})
    capacity = kpis.get("capacity_utilization", {})
    # Flatten capacity into a string for display in the table
    capacity_str = ", ".join(f"{p}: {v:.2%}" for p, v in capacity.items()) if capacity else "N/A"
    return {
        "name": scenario.get("name", "Unnamed"),
        "type": scenario.get("type", "unknown"),
        "status": scenario.get("status", "unknown"),
        "total_cost": kpis.get("total_cost", 0.0),
        "production_cost": kpis.get("production_cost", 0.0),
        "transport_cost": kpis.get("transport_cost", 0.0),
        "fixed_trip_cost": kpis.get("fixed_trip_cost", 0.0),
        "holding_cost": kpis.get("holding_cost", 0.0),
        "service_level": kpis.get("service_level", 0.0),
        "stockout_risk": kpis.get("stockout_risk", 0.0),
        "capacity_utilization": capacity_str,
    }


def _scenario_form_defaults() -> Dict[str, Any]:
    """Default values for the scenario input form."""
    return {
        "name": "Base Case",
        "type": "base",
        "scaling_factor": 1.0,
        "dist_type": "normal",
        "std_dev": 0.1,
        "tri_low": 0.8,
        "tri_mode": 1.0,
        "tri_high": 1.2,
        "random_seed": None,
    }


# --- UI sections ---------------------------------------------------------
def _render_scenario_input_form() -> List[Dict[str, Any]]:
    """Render the scenario configuration form and return a list of scenario configs."""
    st.header("Configure Scenarios")
    num_scenarios = st.number_input("Number of scenarios to run", min_value=1, max_value=10, value=1, step=1)

    configs: List[Dict[str, Any]] = []
    for i in range(num_scenarios):
        with st.expander(f"Scenario {i+1}", expanded=(i == 0)):
            defaults = _scenario_form_defaults()
            name = st.text_input("Scenario name", value=defaults["name"], key=f"name_{i}")
            scenario_type = st.selectbox(
                "Scenario type",
                options=["base", "high", "low", "stochastic"],
                index=0,
                key=f"type_{i}",
            )
            cfg = {"name": name, "type": scenario_type}
            if scenario_type in {"high", "low"}:
                cfg["scaling_factor"] = st.number_input(
                    "Scaling factor",
                    min_value=0.0,
                    max_value=5.0,
                    value=defaults["scaling_factor"],
                    step=0.1,
                    key=f"scaling_{i}",
                )
            elif scenario_type == "stochastic":
                cfg["dist_type"] = st.selectbox(
                    "Distribution",
                    options=["normal", "triangular"],
                    index=0,
                    key=f"dist_{i}",
                )
                cfg["std_dev"] = st.number_input(
                    "Standard deviation (fraction of mean)",
                    min_value=0.0,
                    max_value=1.0,
                    value=defaults["std_dev"],
                    step=0.01,
                    key=f"std_{i}",
                )
                cfg["tri_low"] = st.number_input(
                    "Triangular low",
                    min_value=0.0,
                    max_value=2.0,
                    value=defaults["tri_low"],
                    step=0.05,
                    key=f"tri_low_{i}",
                )
                cfg["tri_mode"] = st.number_input(
                    "Triangular mode",
                    min_value=0.0,
                    max_value=2.0,
                    value=defaults["tri_mode"],
                    step=0.05,
                    key=f"tri_mode_{i}",
                )
                cfg["tri_high"] = st.number_input(
                    "Triangular high",
                    min_value=0.0,
                    max_value=2.0,
                    value=defaults["tri_high"],
                    step=0.05,
                    key=f"tri_high_{i}",
                )
                cfg["random_seed"] = st.number_input(
                    "Random seed (optional)",
                    min_value=0,
                    max_value=10_000,
                    value=defaults["random_seed"],
                    step=1,
                    key=f"seed_{i}",
                )
            configs.append(cfg)
    return configs


def _render_run_button(configs: List[Dict[str, Any]]) -> bool:
    """Render the Run Scenarios button and trigger API call; return True if results were stored."""
    if not configs:
        st.warning("Add at least one scenario configuration.")
        return False

    if st.button("Run Scenarios", disabled=st.session_state.get("loading", False)):
        st.session_state["loading"] = True
        st.session_state["error"] = None
        st.session_state["results"] = None
        # Rerun to display loading spinner
        st.rerun()

    if st.session_state.get("loading", False):
        with st.spinner("Running scenarios..."):
            # Simulate a brief UI update to show spinner before the API call
            time.sleep(0.2)
            result = _post_scenarios(configs)
            st.session_state["loading"] = False
            if result and "scenarios" in result:
                st.session_state["results"] = result
                st.success("Scenarios completed successfully!")
            else:
                st.session_state["error"] = "Failed to run scenarios or missing results."
        st.rerun()

    if st.session_state.get("error"):
        st.error(st.session_state["error"])
        return False

    return "results" in st.session_state and st.session_state["results"] is not None


def _render_kpi_summary_table():
    """Render a table of KPIs per scenario."""
    st.header("KPI Summary")
    data = st.session_state.get("results", {}).get("scenarios", [])
    if not data:
        st.info("No scenario results to display.")
        return

    rows = [_flatten_kpis(scenario) for scenario in data]
    df = st.dataframe(rows, use_container_width=True)

    # Optional: allow download as CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download KPIs as CSV",
        data=csv,
        file_name="kpis.csv",
        mime="text/csv",
    )


def _render_charts():
    """Render cost and utilization charts."""
    st.header("Charts")
    data = st.session_state.get("results", {}).get("scenarios", [])
    if not data:
        st.info("No scenario results to display.")
        return

    # Prepare data structures
    scenario_names = [s.get("name", "Unnamed") for s in data]
    total_costs = [s.get("kpis", {}).get("total_cost", 0.0) for s in data]
    cost_breakdown = {
        "production": [s.get("kpis", {}).get("production_cost", 0.0) for s in data],
        "transport": [s.get("kpis", {}).get("transport_cost", 0.0) for s in data],
        "fixed_trip": [s.get("kpis", {}).get("fixed_trip_cost", 0.0) for s in data],
        "holding": [s.get("kpis", {}).get("holding_cost", 0.0) for s in data],
    }

    # 1) Total cost per scenario (bar chart)
    st.subheader("Total Cost per Scenario")
    st.bar_chart(data={"Scenario": scenario_names, "Total Cost": total_costs}, x="Scenario", y="Total Cost")

    # 2) Cost breakdown (stacked bar)
    st.subheader("Cost Breakdown per Scenario")
    breakdown_df = {
        "Scenario": scenario_names,
        "Production": cost_breakdown["production"],
        "Transport": cost_breakdown["transport"],
        "Fixed Trip": cost_breakdown["fixed_trip"],
        "Holding": cost_breakdown["holding"],
    }
    st.bar_chart(breakdown_df, x="Scenario", y=["Production", "Transport", "Fixed Trip", "Holding"])

    # 3) Capacity utilization per scenario
    st.subheader("Plant Capacity Utilization per Scenario")
    # Collect all plants across scenarios for consistent ordering
    all_plants = sorted({plant for s in data for plant in s.get("kpis", {}).get("capacity_utilization", {}).keys()})
    if not all_plants:
        st.info("No plant utilization data available.")
        return

    # Build a DataFrame for utilization
    util_rows = []
    for scenario in data:
        name = scenario.get("name", "Unnamed")
        util = scenario.get("kpis", {}).get("capacity_utilization", {})
        for plant in all_plants:
            util_rows.append({"Scenario": name, "Plant": plant, "Utilization": util.get(plant, 0.0)})
    util_df = pd.DataFrame(util_rows)
    # Show per-plant bar chart; you can filter by plant if needed
    st.bar_chart(util_df, x="Plant", y="Utilization", color="Scenario")


# --- Main app ------------------------------------------------------------
def main():
    st.set_page_config(page_title="Scenario Dashboard", layout="wide")
    st.title("Supply-Chain Scenario Dashboard")

    # Initialize session state
    for key in ("loading", "error", "results"):
        if key not in st.session_state:
            st.session_state[key] = None

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Scenario Input", "KPI Summary", "Charts"])

    with tab1:
        configs = _render_scenario_input_form()
        _render_run_button(configs)

    with tab2:
        _render_kpi_summary_table()

    with tab3:
        _render_charts()


if __name__ == "__main__":
    # Import pandas only for chart data prep (lazy import to avoid startup overhead)
    import pandas as pd
    main()
