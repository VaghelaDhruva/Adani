import streamlit as st
import requests
from config import API_BASE


def run():
    st.title("Optimization Console")
    st.markdown("Run optimization for a scenario and view results.")
    scenario_name = st.text_input("Scenario name", "base")
    if st.button("Run Optimization"):
        # TODO: call backend optimization run endpoint
        # resp = requests.post(f"{API_BASE}/optimization/run", params={"scenario_name": scenario_name})
        st.success(f"Queued optimization for scenario: {scenario_name}")
    st.markdown("---")
    st.subheader("Job Status")
    # TODO: poll job status endpoint and display progress
    st.info("Job status placeholder – backend integration pending")
