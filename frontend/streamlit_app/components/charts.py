import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def cost_breakdown_pie(cost_dict: dict):
    """Pie chart for cost breakdown."""
    df = pd.DataFrame(list(cost_dict.items()), columns=["Category", "Cost"])
    fig = px.pie(df, values="Cost", names="Category", title="Cost Breakdown")
    st.plotly_chart(fig, use_container_width=True)


def capacity_utilization_bar(df: pd.DataFrame, plant_col: str, util_col: str):
    """Bar chart for capacity utilization by plant."""
    fig = px.bar(df, x=plant_col, y=util_col, title="Capacity Utilization")
    st.plotly_chart(fig, use_container_width=True)


def inventory_vs_safety_stock_line(df: pd.DataFrame, period_col: str, inv_col: str, ss_col: str):
    """Line chart comparing inventory to safety stock over time."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[period_col], y=df[inv_col], mode="lines+markers", name="Inventory"))
    fig.add_trace(go.Scatter(x=df[period_col], y=df[ss_col], mode="lines+markers", name="Safety Stock"))
    fig.update_layout(title="Inventory vs Safety Stock")
    st.plotly_chart(fig, use_container_width=True)
