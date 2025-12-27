import streamlit as st
import pandas as pd
import requests
from config import API_BASE


def run():
    st.title("Data Upload & Validation")
    st.markdown("Upload CSV/Excel files for master data, demand, transport, and inventory.")
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])
    if uploaded_file:
        st.write("Preview:", uploaded_file.name)
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Failed to read file: {e}")

    # Placeholder: API call to upload endpoint
    if st.button("Upload"):
        if uploaded_file:
            files = {"file": uploaded_file.getvalue()}
            # TODO: determine target table based on filename or UI selection
            # resp = requests.post(f"{API_BASE}/data/upload_csv", files=files)
            st.success("Upload placeholder – backend integration pending")
        else:
            st.warning("Please select a file first.")
