"""
Shared styling module for all dashboard pages.
Provides consistent UI styling across the entire application.
"""

import streamlit as st

def apply_common_styles():
    """Apply common CSS styles to all dashboard pages."""
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global styling */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 1400px;
            font-family: 'Inter', sans-serif;
        }
        
        /* Header styling */
        .page-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            color: white;
            text-align: center;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        
        .page-header h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .page-header p {
            margin: 0.5rem 0 0 0;
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        /* Metric cards styling */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
            margin: 0.5rem 0;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }
        
        .metric-card h3 {
            color: #2c3e50;
            margin: 0 0 0.5rem 0;
            font-size: 0.9rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric-card .value {
            font-size: 2rem;
            font-weight: 700;
            color: #667eea;
            margin: 0;
            line-height: 1.2;
        }
        
        .metric-card .delta {
            font-size: 0.8rem;
            margin-top: 0.5rem;
            font-weight: 500;
        }
        
        /* Section headers */
        .section-header {
            background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 1rem 1.5rem;
            border-radius: 10px;
            border-left: 5px solid #667eea;
            margin: 2rem 0 1rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .section-header h2 {
            margin: 0;
            color: #2c3e50;
            font-size: 1.4rem;
            font-weight: 600;
        }
        
        .section-header h3 {
            margin: 0;
            color: #2c3e50;
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        /* Data tables styling */
        .dataframe {
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
        }
        
        .dataframe thead th {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            padding: 1rem;
            border: none;
        }
        
        .dataframe tbody td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #f1f3f4;
        }
        
        .dataframe tbody tr:hover {
            background-color: #f8f9fa;
        }
        
        /* Chart containers */
        .chart-container {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
            margin: 1rem 0;
        }
        
        /* Status indicators */
        .status-success {
            background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3);
        }
        
        .status-warning {
            background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(253, 203, 110, 0.3);
        }
        
        .status-error {
            background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(253, 121, 168, 0.3);
        }
        
        .status-info {
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(116, 185, 255, 0.3);
        }
        
        /* Buttons styling */
        .stButton > button {
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 25px;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            width: 100%;
        }
        
        .stButton > button:hover {
            background: linear-gradient(45deg, #5a67d8 0%, #6b46c1 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        
        /* Selectbox styling */
        .stSelectbox > div > div {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        .stSelectbox > div > div:focus-within {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        }
        
        .sidebar .sidebar-content {
            padding: 1rem;
        }
        
        /* Loading spinner */
        .stSpinner > div {
            border-top-color: #667eea !important;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            border: 1px solid #e9ecef;
            font-weight: 600;
        }
        
        .streamlit-expanderContent {
            background: white;
            border: 1px solid #e9ecef;
            border-top: none;
            border-radius: 0 0 10px 10px;
        }
        
        /* Custom dividers */
        .custom-divider {
            height: 3px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 2px;
            margin: 2rem 0;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .page-header h1 {
                font-size: 2rem;
            }
            
            .page-header p {
                font-size: 1rem;
            }
            
            .metric-card {
                padding: 1rem;
            }
            
            .metric-card .value {
                font-size: 1.5rem;
            }
        }
        
        /* Animation classes */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .loading {
            animation: pulse 2s infinite;
        }
        
        /* Plotly chart styling */
        .js-plotly-plot .plotly .modebar {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 5px;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, #5a67d8 0%, #6b46c1 100%);
        }
    </style>
    """, unsafe_allow_html=True)

def create_metric_card(title, value, delta=None, delta_color="normal"):
    """Create a styled metric card."""
    delta_html = ""
    if delta:
        color = "#28a745" if delta_color == "normal" else "#dc3545" if delta_color == "inverse" else "#6c757d"
        delta_html = f'<div class="delta" style="color: {color};">{delta}</div>'
    
    st.markdown(f"""
    <div class="metric-card">
        <h3>{title}</h3>
        <div class="value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def create_section_header(title, subtitle=None):
    """Create a styled section header."""
    subtitle_html = f"<p style='margin: 0.5rem 0 0 0; color: #6c757d; font-size: 0.9rem;'>{subtitle}</p>" if subtitle else ""
    
    st.markdown(f"""
    <div class="section-header">
        <h2>{title}</h2>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)

def create_status_box(message, status_type="info"):
    """Create a styled status box."""
    st.markdown(f"""
    <div class="status-{status_type}">
        {message}
    </div>
    """, unsafe_allow_html=True)

def create_page_header(title, subtitle):
    """Create a styled page header."""
    st.markdown(f"""
    <div class="page-header fade-in">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def create_custom_divider():
    """Create a styled divider."""
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)