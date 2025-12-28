import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from config import API_BASE


def run():
    """Uncertainty analysis dashboard page."""
    st.title("Uncertainty Analysis & Risk Assessment")
    st.markdown("Compare deterministic vs uncertain optimization results and analyze risk exposure.")
    
    # Sidebar for analysis options
    st.sidebar.title("Analysis Options")
    analysis_type = st.sidebar.selectbox(
        "Analysis Type",
        ["Scenario Comparison", "Risk Metrics", "Service Level Analysis", "Cost Distribution"]
    )
    
    # Data fetching with error handling
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_uncertainty_results():
        """Fetch uncertainty optimization results from API."""
        try:
            response = requests.get(f"{API_BASE}/optimization/uncertainty/results")
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to fetch uncertainty results: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {e}")
            return None
    
    @st.cache_data(ttl=300)
    def get_deterministic_results():
        """Fetch deterministic optimization results for comparison."""
        try:
            response = requests.get(f"{API_BASE}/optimization/deterministic/results")
            if response.status_code == 200:
                return response.json()
            else:
                st.warning(f"Deterministic results not available: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            st.warning(f"Connection error: {e}")
            return None
    
    # Fetch data
    uncertainty_data = get_uncertainty_results()
    deterministic_data = get_deterministic_results()
    
    if not uncertainty_data:
        st.error("No uncertainty optimization results available. Please run an uncertainty optimization first.")
        st.info("You can run uncertainty optimization from the Optimization Console page.")
        return
    
    # Display based on analysis type
    if analysis_type == "Scenario Comparison":
        display_scenario_comparison(uncertainty_data, deterministic_data)
    elif analysis_type == "Risk Metrics":
        display_risk_metrics(uncertainty_data)
    elif analysis_type == "Service Level Analysis":
        display_service_level_analysis(uncertainty_data)
    elif analysis_type == "Cost Distribution":
        display_cost_distribution(uncertainty_data, deterministic_data)


def display_scenario_comparison(uncertainty_data, deterministic_data):
    """Display scenario-by-scenario comparison."""
    st.header("Scenario Comparison")
    
    scenario_results = uncertainty_data.get("scenario_results", [])
    if not scenario_results:
        st.warning("No scenario results available")
        return
    
    # Create comparison table
    comparison_data = []
    for scenario in scenario_results:
        comparison_data.append({
            "Scenario": scenario.get("scenario_name", "Unknown"),
            "Cost": scenario.get("scenario_cost", 0),
            "Service Level": scenario.get("service_level", 0),
            "Capacity Utilization": scenario.get("capacity_utilization", 0)
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    
    # Display table
    st.subheader("Scenario Performance Summary")
    st.dataframe(df_comparison, use_container_width=True)
    
    # Cost comparison chart
    st.subheader("Cost Comparison Across Scenarios")
    fig_cost = px.bar(
        df_comparison,
        x="Scenario",
        y="Cost",
        title="Cost by Scenario",
        color="Cost",
        color_continuous_scale="Viridis"
    )
    fig_cost.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_cost, use_container_width=True)
    
    # Service level comparison
    st.subheader("Service Level by Scenario")
    fig_service = px.bar(
        df_comparison,
        x="Scenario",
        y="Service Level",
        title="Service Level by Scenario",
        color="Service Level",
        range_y=[0, 1],
        color_continuous_scale="RdYlGn"
    )
    fig_service.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_service, use_container_width=True)
    
    # Comparison with deterministic if available
    if deterministic_data:
        st.subheader("Deterministic vs Uncertain Comparison")
        
        det_cost = deterministic_data.get("total_cost", 0)
        agg_stats = uncertainty_data.get("aggregate_statistics", {})
        expected_cost = agg_stats.get("expected_cost", 0)
        worst_cost = agg_stats.get("worst_cost", 0)
        best_cost = agg_stats.get("best_cost", 0)
        
        comparison_metrics = {
            "Deterministic Cost": det_cost,
            "Expected Cost (Uncertain)": expected_cost,
            "Best Case Cost": best_cost,
            "Worst Case Cost": worst_cost
        }
        
        fig_comparison = go.Figure()
        fig_comparison.add_trace(go.Bar(
            x=list(comparison_metrics.keys()),
            y=list(comparison_metrics.values()),
            marker_color=['blue', 'green', 'lightgreen', 'red']
        ))
        
        fig_comparison.update_layout(
            title="Cost Comparison: Deterministic vs Uncertain",
            xaxis_title="Scenario Type",
            yaxis_title="Total Cost ($)"
        )
        st.plotly_chart(fig_comparison, use_container_width=True)


def display_risk_metrics(uncertainty_data):
    """Display risk analysis metrics."""
    st.header("Risk Metrics Analysis")
    
    agg_stats = uncertainty_data.get("aggregate_statistics", {})
    if not agg_stats:
        st.warning("No aggregate statistics available")
        return
    
    # Key risk metrics
    st.subheader("Key Risk Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        expected_cost = agg_stats.get("expected_cost", 0)
        st.metric("Expected Cost", f"${expected_cost:,.2f}")
    
    with col2:
        worst_cost = agg_stats.get("worst_cost", 0)
        st.metric("Worst Case Cost", f"${worst_cost:,.2f}")
    
    with col3:
        cost_variance = agg_stats.get("cost_variance", 0)
        st.metric("Cost Variance", f"{cost_variance:,.2f}")
    
    with col4:
        avg_service = agg_stats.get("average_service_level", 0)
        st.metric("Avg Service Level", f"{avg_service:.2%}")
    
    # Risk distribution chart
    st.subheader("Cost Risk Distribution")
    
    scenario_results = uncertainty_data.get("scenario_results", [])
    if scenario_results:
        costs = [s.get("scenario_cost", 0) for s in scenario_results]
        
        fig_histogram = px.histogram(
            x=costs,
            nbins=20,
            title="Cost Distribution Across Scenarios",
            labels={"x": "Total Cost ($)", "y": "Frequency"}
        )
        fig_histogram.add_vline(
            x=agg_stats.get("expected_cost", 0),
            line_dash="dash",
            line_color="red",
            annotation_text="Expected Cost"
        )
        st.plotly_chart(fig_histogram, use_container_width=True)
    
    # Value at Risk (VaR) calculation
    if scenario_results:
        st.subheader("Value at Risk (VaR) Analysis")
        
        costs_sorted = sorted([s.get("scenario_cost", 0) for s in scenario_results])
        n_scenarios = len(costs_sorted)
        
        # Calculate VaR at different confidence levels
        var_90 = costs_sorted[int(0.9 * n_scenarios)] if n_scenarios > 0 else 0
        var_95 = costs_sorted[int(0.95 * n_scenarios)] if n_scenarios > 0 else 0
        var_99 = costs_sorted[int(0.99 * n_scenarios)] if n_scenarios > 0 else 0
        
        var_data = {
            "Confidence Level": ["90%", "95%", "99%"],
            "Value at Risk": [var_90, var_95, var_99],
            "Expected Cost": [agg_stats.get("expected_cost", 0)] * 3
        }
        
        df_var = pd.DataFrame(var_data)
        
        fig_var = go.Figure()
        fig_var.add_trace(go.Bar(
            name="Value at Risk",
            x=df_var["Confidence Level"],
            y=df_var["Value at Risk"],
            marker_color="red"
        ))
        fig_var.add_trace(go.Bar(
            name="Expected Cost",
            x=df_var["Confidence Level"],
            y=df_var["Expected Cost"],
            marker_color="blue"
        ))
        
        fig_var.update_layout(
            title="Value at Risk (VaR) at Different Confidence Levels",
            barmode="group",
            yaxis_title="Cost ($)"
        )
        st.plotly_chart(fig_var, use_container_width=True)


def display_service_level_analysis(uncertainty_data):
    """Display service level analysis under uncertainty."""
    st.header("Service Level Analysis")
    
    scenario_results = uncertainty_data.get("scenario_results", [])
    if not scenario_results:
        st.warning("No scenario results available")
        return
    
    # Service level distribution
    service_levels = [s.get("service_level", 0) for s in scenario_results]
    
    st.subheader("Service Level Distribution")
    
    fig_service_dist = px.histogram(
        x=service_levels,
        nbins=20,
        title="Service Level Distribution Across Scenarios",
        labels={"x": "Service Level", "y": "Frequency"},
        range_x=[0, 1]
    )
    st.plotly_chart(fig_service_dist, use_container_width=True)
    
    # Service level vs Cost scatter plot
    st.subheader("Service Level vs Cost Trade-off")
    
    cost_service_data = []
    for scenario in scenario_results:
        cost_service_data.append({
            "Cost": scenario.get("scenario_cost", 0),
            "Service Level": scenario.get("service_level", 0),
            "Scenario": scenario.get("scenario_name", "Unknown")
        })
    
    df_cost_service = pd.DataFrame(cost_service_data)
    
    fig_scatter = px.scatter(
        df_cost_service,
        x="Service Level",
        y="Cost",
        color="Scenario",
        title="Service Level vs Cost Trade-off",
        hover_data=["Scenario"]
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Service level reliability metrics
    st.subheader("Service Level Reliability")
    
    # Calculate probability of meeting different service levels
    service_targets = [0.90, 0.95, 0.99]
    reliability_data = []
    
    for target in service_targets:
        probability = sum(1 for sl in service_levels if sl >= target) / len(service_levels)
        reliability_data.append({
            "Target Service Level": f"{target:.0%}",
            "Achievement Probability": f"{probability:.2%}",
            "Probability": probability
        })
    
    df_reliability = pd.DataFrame(reliability_data)
    
    fig_reliability = px.bar(
        df_reliability,
        x="Target Service Level",
        y="Probability",
        title="Probability of Achieving Service Level Targets",
        text="Achievement Probability"
    )
    fig_reliability.update_layout(yaxis_title="Probability", yaxis_range=[0, 1])
    st.plotly_chart(fig_reliability, use_container_width=True)


def display_cost_distribution(uncertainty_data, deterministic_data):
    """Display detailed cost distribution analysis."""
    st.header("Cost Distribution Analysis")
    
    scenario_results = uncertainty_data.get("scenario_results", [])
    if not scenario_results:
        st.warning("No scenario results available")
        return
    
    # Extract cost components if available
    st.subheader("Cost Component Breakdown")
    
    # This would need cost component data from the optimization results
    # For now, showing total cost distribution
    costs = [s.get("scenario_cost", 0) for s in scenario_results]
    
    # Statistical summary
    st.subheader("Cost Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Mean Cost", f"${pd.Series(costs).mean():,.2f}")
    
    with col2:
        st.metric("Median Cost", f"${pd.Series(costs).median():,.2f}")
    
    with col3:
        st.metric("Std Dev", f"${pd.Series(costs).std():,.2f}")
    
    with col4:
        st.metric("Range", f"${pd.Series(costs).max() - pd.Series(costs).min():,.2f}")
    
    # Box plot for cost distribution
    st.subheader("Cost Distribution Box Plot")
    
    fig_box = px.box(
        y=costs,
        title="Cost Distribution Box Plot",
        labels={"y": "Total Cost ($)"}
    )
    st.plotly_chart(fig_box, use_container_width=True)
    
    # Comparison with deterministic
    if deterministic_data:
        st.subheader("Deterministic vs Uncertain Cost Analysis")
        
        det_cost = deterministic_data.get("total_cost", 0)
        
        # Calculate cost differences
        cost_diffs = [cost - det_cost for cost in costs]
        
        fig_diff = px.histogram(
            x=cost_diffs,
            nbins=20,
            title="Cost Difference: Uncertain - Deterministic",
            labels={"x": "Cost Difference ($)", "y": "Frequency"}
        )
        fig_diff.add_vline(
            x=0,
            line_dash="dash",
            line_color="red",
            annotation_text="Deterministic Cost"
        )
        st.plotly_chart(fig_diff, use_container_width=True)
        
        # Summary of differences
        positive_diffs = [d for d in cost_diffs if d > 0]
        negative_diffs = [d for d in cost_diffs if d < 0]
        
        st.subheader("Cost Difference Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Scenarios Higher Cost",
                f"{len(positive_diffs)}/{len(cost_diffs)} ({len(positive_diffs)/len(cost_diffs):.1%})"
            )
        
        with col2:
            avg_increase = sum(positive_diffs) / len(positive_diffs) if positive_diffs else 0
            st.metric("Avg Increase", f"${avg_increase:,.2f}")
        
        with col3:
            avg_decrease = abs(sum(negative_diffs) / len(negative_diffs)) if negative_diffs else 0
            st.metric("Avg Decrease", f"${avg_decrease:,.2f}")


if __name__ == "__main__":
    run()
