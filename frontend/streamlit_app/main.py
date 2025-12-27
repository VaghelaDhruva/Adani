import streamlit as st
from pages import data_upload_and_validation, optimization_console, kpi_dashboard, scenario_comparison, admin_audit

st.set_page_config(layout="wide", page_title="Clinker Supply Chain Optimization")

PAGES = {
    "Data Upload & Validation": data_upload_and_validation,
    "Optimization Console": optimization_console,
    "KPI Dashboard": kpi_dashboard,
    "Scenario Comparison": scenario_comparison,
    "Admin & Audit": admin_audit,
}

def main():
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))
    page = PAGES[selection]
    page.run()

if __name__ == "__main__":
    main()
