import streamlit as st


def sidebar_header():
    """Standard sidebar header."""
    st.sidebar.markdown("### Clinker Supply Chain Optimization")


def main_header(title: str):
    """Standard main page header."""
    st.title(title)
