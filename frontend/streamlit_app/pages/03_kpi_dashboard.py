import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from config import API_BASE


def run():
    st.title("KPI Dashboard")
    scenario_name = st.selectbox("Select scenario", ["base", "high", "low"])
    # TODO: fetch KPIs from backend
    # resp = requests.get(f"{API_BASE}/kpi/dashboard/{scenario_name}")
    # kpis = resp.json()
    st.info("KPI data placeholder – backend integration pending")
    # Example charts (stub)
    st.subheader("Cost Breakdown")
    df_cost = pd.DataFrame({
        "Category": ["Production", "Transport", "Holding"],
        "Cost": [5000, 3000, 800],
    })
    fig = px.pie(df_cost, values="Cost", names="Category")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Capacity Utilization")
    df_cap = pd.DataFrame({
        "Plant": ["P1", "P2", "P3"],
        "Utilization": [0.85, 0.62, 0.94],
    })
    fig2 = px.bar(df_cap, x="Plant", y="Utilization")
    st.plotly_chart(fig2, use_container_width=True)
