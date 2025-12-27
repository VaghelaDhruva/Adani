import streamlit as st


def plant_filter(plants: list) -> list:
    """Multiselect filter for plants."""
    return st.multiselect("Select plants", plants, default=plants)


def period_filter(periods: list) -> list:
    """Multiselect filter for time periods."""
    return st.multiselect("Select periods", periods, default=periods)


def mode_filter(modes: list) -> list:
    """Multiselect filter for transport modes."""
    return st.multiselect("Select transport modes", modes, default=modes)
