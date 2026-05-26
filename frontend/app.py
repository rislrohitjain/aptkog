import sys
import os
# Dynamically add the parent directory to sys.path to ensure 'frontend' package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
from frontend.api_client import AntigravityAPIClient
from frontend.components.sidebar import render_sidebar
from frontend.components.tabs import render_ingestion_container
from frontend.components.filters import render_filters_container
from frontend.components.pivot import render_pivot_container
from frontend.components.join import render_join_container
from frontend.components.diagnostics import render_diagnostics_panel

# Set page configuration for visual elegance
st.set_page_config(
    page_title="Antigravity 2.0 - Local Data Analytics Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling via markdown
st.markdown(
    """
    <style>
        /* Import Outfit Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
        }
        
        /* Premium custom heading stylings */
        .main-title {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #C084FC 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 42px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .subtitle {
            font-size: 16px;
            color: #6B7280;
            margin-bottom: 25px;
        }
        
        /* Modern expander styling */
        .streamlit-expanderHeader {
            font-size: 18px !important;
            font-weight: 600 !important;
            color: #1E293B !important;
            background-color: #F8FAFC !important;
            border-radius: 6px !important;
            border: 1px solid #E2E8F0 !important;
            margin-bottom: 10px;
        }
        
        /* Metric widget styling */
        [data-testid="stMetricValue"] {
            font-size: 28px !important;
            font-weight: 700 !important;
            color: #4F46E5 !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

def main():
    # Instantiate backend API client
    api_client = AntigravityAPIClient()
    
    # Render global sidebar navigation
    render_sidebar()
    
    # Render Main Page Header
    st.markdown(
        """
        <div>
            <h1 class="main-title">Antigravity 2.0</h1>
            <p class="subtitle">Advanced Local Data Analytics Engine - Powered by Polars, LangChain, & Scikit-Learn</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Active navigation block from sidebar session state
    active_block = st.session_state.get("active_block", "Ingestion")
    
    # Renders all panels as independent, expandable/collapsible containers
    # We dynamically expand the container that corresponds to the active navigation choice
    
    # Ingestion Block
    with st.expander("📥 Ingestion Container (Files & Sheets)", expanded=(active_block == "Ingestion")):
        render_ingestion_container(api_client)
        
    # Filtering & Tri-View Block
    with st.expander("🔍 Filtering & Tri-View Container", expanded=(active_block == "Filter")):
        render_filters_container(api_client)
        
    # Pivot Engine Block
    with st.expander("📊 Pivot Engine Container", expanded=(active_block == "Pivot")):
        render_pivot_container(api_client)
        
    # Dataset Join Builder Block
    with st.expander("🔗 Dataset Builder Container (Join/Merge)", expanded=(active_block == "Join")):
        render_join_container(api_client)
        
    # Infrastructure Diagnostics & Local Privacy Block
    with st.expander("⚙️ Infrastructure Diagnostic Panel", expanded=(active_block == "Diagnostics")):
        render_diagnostics_panel(api_client)

if __name__ == "__main__":
    main()
