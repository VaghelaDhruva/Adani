import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from config import API_BASE


def run():
    st.title("Scenario Comparison")
    scenarios = st.multiselect("Select scenarios to compare", ["base", "high", "low"], default=["base", "high"])
    if not scenarios:
        st.warning("Select at least one scenario.")
        return
    # TODO: fetch comparison from backend
    # resp = requests.post(f"{API_BASE}/kpi/compare", json=scenarios)
    # comp = resp.json()
    st.info("Comparison data placeholder – backend integration pending")
    # Example side-by-side bar chart
    df = pd.DataFrame({
        "Scenario": ["base", "high", "low"],
        "Total Cost": [8800, 10500, 7100],
        "Service Level": [0.98, 0.96, 0.99],
    })
    st.subheader("Total Cost")
    fig = px.bar(df, x="Scenario", y="Total Cost")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Service Level")
    fig2 = px.bar(df, x="Scenario", y="Service Level")
    st.plotly_chart(fig2, use_container_width=True)
