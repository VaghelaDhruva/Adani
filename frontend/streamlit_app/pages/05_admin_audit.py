import streamlit as st
import requests
import pandas as pd
from config import API_BASE


def run():
    st.title("Admin & Audit")
    st.markdown("User management and audit log (placeholder).")
    # TODO: user management UI
    st.subheader("Audit Log")
    # resp = requests.get(f"{API_BASE}/audit/logs")
    # logs = resp.json()
    # df = pd.DataFrame(logs)
    # st.dataframe(df)
    st.info("Audit log placeholder – backend integration pending")
