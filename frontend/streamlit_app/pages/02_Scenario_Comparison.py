"""
Scenario Comparison Dashboard

Compare cost and service impacts across multiple scenarios.
Enterprise-grade comparison with uncertainty impact analysis.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

from config import API_BASE
from styles import apply_common_styles, create_page_header, create_section_header, create_status_box, create_custom_divider

st.set_page_config(page_title="Scenario Comparison", layout="wide", page_icon="⚖️")

# Apply common styling
apply_common_styles()

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
            return f"{'−' if negative else ''}₹{amount:,.2f}"
    except (ValueError, TypeError):
        return "₹0"

def fetch_available_scenarios():
    """Fetch list of available scenarios."""
    try:
        response = requests.get(f"{API_BASE}/dashboard/scenarios/list", timeout=10)
        if response.status_code == 200:
            scenarios = response.json().get("scenarios", [])
            return [(s["name"], s["description"]) for s in scenarios]
        else:
            return [("base", "Base case"), ("high_demand", "High demand"), ("low_demand", "Low demand")]
    except:
        return [("base", "Base case"), ("high_demand", "High demand"), ("low_demand", "Low demand")]

def fetch_scenario_comparison(scenario_names):
    """Fetch comparison data for selected scenarios."""
    try:
        response = requests.post(
            f"{API_BASE}/dashboard/scenarios/compare",
            json=scenario_names,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("comparison_data", []), None
        else:
            return None, f"API Error: {response.status_code}"
            
    except requests.exceptions.Timeout:
        return None, "Request timeout - please retry"
    except requests.exceptions.ConnectionError:
        return None, "Connection error - check backend service"
    except Exception as e:
        return None, f"Error: {str(e)}"

def display_comparison_table(comparison_data):
    """Display comparison table with highlighting."""
    st.markdown("### 📊 Scenario Comparison Table")
    
    if not comparison_data:
        st.warning("No comparison data available")
        return
    
    df = pd.DataFrame(comparison_data)
    
    # Format the data for display
    display_df = df.copy()
    display_df["Total Cost"] = display_df["total_cost"].apply(format_inr)
    display_df["Service Level"] = (display_df["service_level"] * 100).round(1).astype(str) + "%"
    display_df["Demand Fulfillment"] = (display_df["demand_fulfillment"] * 100).round(1).astype(str) + "%"
    display_df["Safety Stock Compliance"] = display_df["safety_stock_compliance"].round(1).astype(str) + "%"
    display_df["Penalty Cost"] = display_df["penalty_cost"].apply(format_inr)
    display_df["Avg Utilization"] = (display_df["avg_utilization"] * 100).round(1).astype(str) + "%"
    
    # Rename columns
    display_df = display_df.rename(columns={
        "scenario_name": "Scenario",
        "total_cost": "Total Cost (Raw)",
        "service_level": "Service Level (Raw)",
        "demand_fulfillment": "Demand Fulfillment (Raw)",
        "safety_stock_compliance": "Safety Stock Compliance (Raw)",
        "penalty_cost": "Penalty Cost (Raw)",
        "avg_utilization": "Avg Utilization (Raw)"
    })
    
    # Select display columns
    table_columns = ["Scenario", "Total Cost", "Service Level", "Demand Fulfillment", 
                    "Safety Stock Compliance", "Penalty Cost", "Avg Utilization"]
    
    st.dataframe(display_df[table_columns], use_container_width=True, hide_index=True)
    
    # Highlight best values
    st.markdown("**Best Values:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Lowest cost
        min_cost_idx = df["total_cost"].idxmin()
        best_cost_scenario = df.loc[min_cost_idx, "scenario_name"]
        best_cost_value = df.loc[min_cost_idx, "total_cost"]
        st.success(f"**Lowest Cost:** {best_cost_scenario} - {format_inr(best_cost_value)}")
    
    with col2:
        # Highest service level
        max_service_idx = df["service_level"].idxmax()
        best_service_scenario = df.loc[max_service_idx, "scenario_name"]
        best_service_value = df.loc[max_service_idx, "service_level"]
        st.success(f"**Highest Service:** {best_service_scenario} - {best_service_value:.1%}")
    
    with col3:
        # Best compliance
        max_compliance_idx = df["safety_stock_compliance"].idxmax()
        best_compliance_scenario = df.loc[max_compliance_idx, "scenario_name"]
        best_compliance_value = df.loc[max_compliance_idx, "safety_stock_compliance"]
        st.success(f"**Best Compliance:** {best_compliance_scenario} - {best_compliance_value:.1f}%")

def display_cost_comparison_charts(comparison_data):
    """Display cost comparison charts."""
    st.markdown("### 💰 Cost Comparison Analysis")
    
    if not comparison_data:
        return
    
    df = pd.DataFrame(comparison_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Total cost comparison
        fig = px.bar(
            df,
            x="scenario_name",
            y="total_cost",
            title="Total Cost by Scenario",
            color="total_cost",
            color_continuous_scale="RdYlGn_r",
            text="total_cost"
        )
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig.update_layout(yaxis_title="Cost (₹)", xaxis_title="Scenario")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Cost vs Service Level scatter
        fig = px.scatter(
            df,
            x="service_level",
            y="total_cost",
            color="scenario_name",
            size="penalty_cost",
            title="Cost vs Service Level Trade-off",
            hover_data=["demand_fulfillment", "avg_utilization"]
        )
        fig.update_layout(
            xaxis_title="Service Level",
            yaxis_title="Total Cost (₹)",
            xaxis_tickformat='.0%'
        )
        st.plotly_chart(fig, use_container_width=True)

def display_service_comparison_charts(comparison_data):
    """Display service performance comparison."""
    st.markdown("### 📈 Service Performance Comparison")
    
    if not comparison_data:
        return
    
    df = pd.DataFrame(comparison_data)
    
    # Service metrics comparison
    service_metrics = df[["scenario_name", "service_level", "demand_fulfillment", "safety_stock_compliance"]].copy()
    service_metrics["service_level"] *= 100
    service_metrics["demand_fulfillment"] *= 100
    
    # Melt for grouped bar chart
    melted = service_metrics.melt(
        id_vars=["scenario_name"],
        value_vars=["service_level", "demand_fulfillment", "safety_stock_compliance"],
        var_name="Metric",
        value_name="Percentage"
    )
    
    # Rename metrics for display
    metric_names = {
        "service_level": "Service Level",
        "demand_fulfillment": "Demand Fulfillment",
        "safety_stock_compliance": "Safety Stock Compliance"
    }
    melted["Metric"] = melted["Metric"].map(metric_names)
    
    fig = px.bar(
        melted,
        x="scenario_name",
        y="Percentage",
        color="Metric",
        title="Service Performance Metrics by Scenario",
        barmode="group"
    )
    fig.update_layout(yaxis_title="Percentage (%)", xaxis_title="Scenario")
    fig.add_hline(y=95, line_dash="dash", line_color="red", annotation_text="95% Target")
    st.plotly_chart(fig, use_container_width=True)

def display_utilization_comparison(comparison_data):
    """Display utilization comparison."""
    st.markdown("### ⚙️ Utilization Comparison")
    
    if not comparison_data:
        return
    
    df = pd.DataFrame(comparison_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Average utilization by scenario
        fig = px.bar(
            df,
            x="scenario_name",
            y="avg_utilization",
            title="Average Capacity Utilization",
            color="avg_utilization",
            color_continuous_scale="RdYlGn",
            text="avg_utilization"
        )
        fig.update_traces(texttemplate='%{text:.1%}', textposition='outside')
        fig.update_layout(yaxis_title="Utilization", yaxis_tickformat='.0%', xaxis_title="Scenario")
        fig.add_hline(y=0.95, line_dash="dash", line_color="orange", annotation_text="95% Warning")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Penalty cost indicator
        fig = px.bar(
            df,
            x="scenario_name",
            y="penalty_cost",
            title="Penalty Costs by Scenario",
            color="penalty_cost",
            color_continuous_scale="Reds",
            text="penalty_cost"
        )
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig.update_layout(yaxis_title="Penalty Cost (₹)", xaxis_title="Scenario")
        st.plotly_chart(fig, use_container_width=True)

def display_uncertainty_impact(comparison_data):
    """Display uncertainty impact analysis if available."""
    st.markdown("### 🎲 Uncertainty Impact Analysis")
    
    # This would be populated if uncertainty data is available
    st.info("**Uncertainty analysis** will be displayed here when uncertainty scenarios are selected.")
    
    # Placeholder for uncertainty metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Expected vs Worst-case", "Analysis pending")
    
    with col2:
        st.metric("Risk Exposure", "Analysis pending")
    
    with col3:
        st.metric("Confidence Interval", "Analysis pending")

def display_recommendations(comparison_data):
    """Display scenario recommendations based on analysis."""
    st.markdown("### 💡 Recommendations")
    
    if not comparison_data:
        return
    
    df = pd.DataFrame(comparison_data)
    
    # Calculate recommendation scores
    # Normalize metrics (lower cost is better, higher service is better)
    df_norm = df.copy()
    df_norm["cost_score"] = 1 - (df["total_cost"] - df["total_cost"].min()) / (df["total_cost"].max() - df["total_cost"].min())
    df_norm["service_score"] = df["service_level"]
    df_norm["compliance_score"] = df["safety_stock_compliance"] / 100
    df_norm["penalty_score"] = 1 - (df["penalty_cost"] / df["penalty_cost"].max()) if df["penalty_cost"].max() > 0 else 1
    
    # Overall score (weighted)
    df_norm["overall_score"] = (
        df_norm["cost_score"] * 0.4 +
        df_norm["service_score"] * 0.3 +
        df_norm["compliance_score"] * 0.2 +
        df_norm["penalty_score"] * 0.1
    )
    
    # Get top recommendation
    best_idx = df_norm["overall_score"].idxmax()
    best_scenario = df.loc[best_idx, "scenario_name"]
    best_score = df_norm.loc[best_idx, "overall_score"]
    
    st.success(f"**Recommended Scenario:** {best_scenario} (Score: {best_score:.2f})")
    
    # Detailed recommendations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**For Cost Optimization:**")
        cost_best_idx = df["total_cost"].idxmin()
        cost_best = df.loc[cost_best_idx, "scenario_name"]
        st.write(f"• Choose **{cost_best}** for lowest total cost")
        
        st.markdown("**For Service Excellence:**")
        service_best_idx = df["service_level"].idxmax()
        service_best = df.loc[service_best_idx, "scenario_name"]
        st.write(f"• Choose **{service_best}** for highest service level")
    
    with col2:
        st.markdown("**Risk Considerations:**")
        penalty_scenarios = df[df["penalty_cost"] > 0]["scenario_name"].tolist()
        if penalty_scenarios:
            st.warning(f"• Scenarios with penalties: {', '.join(penalty_scenarios)}")
        else:
            st.success("• No penalty costs in any scenario")
        
        st.markdown("**Capacity Utilization:**")
        high_util_scenarios = df[df["avg_utilization"] > 0.95]["scenario_name"].tolist()
        if high_util_scenarios:
            st.warning(f"• High utilization (>95%): {', '.join(high_util_scenarios)}")
        else:
            st.success("• All scenarios within capacity limits")

def main():
    # Create styled page header
    create_page_header("⚖️ Scenario Comparison Dashboard", "Compare cost and service impacts across multiple scenarios")
    
    # Scenario selection with enhanced styling
    available_scenarios = fetch_available_scenarios()
    scenario_options = [name for name, desc in available_scenarios]
    scenario_descriptions = {name: desc for name, desc in available_scenarios}
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_scenarios = st.multiselect(
            "Select Scenarios to Compare",
            scenario_options,
            default=scenario_options[:3] if len(scenario_options) >= 3 else scenario_options,
            help="Choose 2 or more scenarios for comparison"
        )
    
    with col2:
        if st.button("🔄 Refresh Comparison", use_container_width=True):
            st.rerun()
    
    # Validation
    if len(selected_scenarios) < 2:
        create_status_box("⚠️ Please select at least 2 scenarios for comparison.", "warning")
        return
    
    # Display selected scenarios info with enhanced styling
    create_section_header("Selected Scenarios", "Overview of scenarios included in the comparison")
    
    scenario_cols = st.columns(len(selected_scenarios))
    for i, scenario in enumerate(selected_scenarios):
        with scenario_cols[i]:
            description = scenario_descriptions.get(scenario, "No description")
            st.markdown(f"""
            <div class="metric-card">
                <h3>{scenario}</h3>
                <div style="color: #6c757d; font-size: 0.9rem;">{description}</div>
            </div>
            """, unsafe_allow_html=True)
    
    create_custom_divider()
    
    # Fetch comparison data with loading state
    with st.spinner("Loading scenario comparison data..."):
        comparison_data, error = fetch_scenario_comparison(selected_scenarios)
    
    # Error handling with styled messages
    if error:
        create_status_box(f"**Scenario comparison service unavailable** — {error}", "error")
        create_status_box("Please retry later or contact system administrator.", "info")
        return
    
    if not comparison_data:
        create_status_box("**No comparison data available** — please check scenario configuration.", "error")
        return
    
    # Display comparison sections with enhanced styling
    try:
        # Comparison table
        display_comparison_table(comparison_data)
        
        create_custom_divider()
        
        # Cost comparison
        display_cost_comparison_charts(comparison_data)
        
        create_custom_divider()
        
        # Service comparison
        display_service_comparison_charts(comparison_data)
        
        create_custom_divider()
        
        # Utilization comparison
        display_utilization_comparison(comparison_data)
        
        create_custom_divider()
        
        # Uncertainty impact
        display_uncertainty_impact(comparison_data)
        
        create_custom_divider()
        
        # Recommendations
        display_recommendations(comparison_data)
        
    except Exception as e:
        create_status_box("**Dashboard rendering error** — please refresh the page.", "error")
        create_status_box("If the problem persists, contact system administrator.", "info")

if __name__ == "__main__":
    main()