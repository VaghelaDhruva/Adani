import importlib
import sys
from pathlib import Path

import streamlit as st

# Ensure the frontend directory (containing the streamlit_app package) is on sys.path
_THIS_FILE = Path(__file__).resolve()
_APP_DIR = _THIS_FILE.parent            # .../frontend/streamlit_app
_FRONTEND_ROOT = _APP_DIR.parent        # .../frontend
if str(_FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_FRONTEND_ROOT))

st.set_page_config(layout="wide", page_title="Clinker Supply Chain Optimization")

# Map human-friendly page names to their underlying module paths.
# The modules are named with numeric prefixes (e.g. "01_...") so we
# import them dynamically via importlib instead of static from-imports.
PAGE_MODULES = {
	"Data Upload & Validation": "streamlit_app.pages.01_data_upload_and_validation",
	"Optimization Console": "streamlit_app.pages.02_optimization_console",
	"KPI Dashboard": "streamlit_app.pages.03_kpi_dashboard",
	"Scenario Comparison": "streamlit_app.pages.04_scenario_comparison",
	"Admin & Audit": "streamlit_app.pages.05_admin_audit",
}


def main() -> None:
	st.sidebar.title("Navigation")
	selection = st.sidebar.radio("Go to", list(PAGE_MODULES.keys()))

	module_path = PAGE_MODULES[selection]
	page_module = importlib.import_module(module_path)
	# Each page module exposes a `run()` entrypoint.
	page_module.run()


if __name__ == "__main__":
	main()
