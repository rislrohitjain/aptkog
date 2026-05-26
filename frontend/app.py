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
    page_title="AptKogMatrix - Data Analytics Engine",
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
        
        /* Hide default Streamlit decoration elements & header space */
        #MainMenu {visibility: hidden; display: none !important;}
        footer {visibility: hidden; display: none !important;}
        header {visibility: hidden; display: none !important;}
        [data-testid="stHeader"] {display: none !important;}
        
        .main .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 0rem !important;
            margin-top: 0px !important;
        }
        
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
            background-color: #0F172A !important;
            color: #F8FAFC !important;
        }
        
        /* Premium custom heading stylings */
        .main-title {
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 42px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .subtitle {
            font-size: 16px;
            color: #94A3B8;
            margin-bottom: 25px;
        }
        
        /* Modern expander styling optimized for dark theme */
        .streamlit-expanderHeader {
            font-size: 18px !important;
            font-weight: 600 !important;
            color: #F8FAFC !important;
            background-color: #1E293B !important;
            border-radius: 6px !important;
            border: 1px solid #334155 !important;
            margin-bottom: 10px;
        }
        
        /* Metric widget styling */
        [data-testid="stMetricValue"] {
            font-size: 28px !important;
            font-weight: 700 !important;
            color: #6366F1 !important;
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
            <h1 class="main-title">AptKogMatrix</h1>
            <p class="subtitle">Secure Offline Data Analytics Engine</p>
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
    import os
    hide_tech = os.environ.get("HIDE_TECH_INFO", "False").lower() in ["true", "1", "yes"]
    if not hide_tech:
        with st.expander("⚙️ Infrastructure Diagnostic Panel", expanded=(active_block == "Diagnostics")):
            render_diagnostics_panel(api_client)

    # Render Sticky Developer Attribution Footer
    st.markdown(
        """
        <hr style="margin-top: 40px; border-color: #334155;" />
        <div style="text-align: center; padding: 15px 0 30px 0; color: #94A3B8; font-size: 13px;">
            <p style="margin: 0;"><strong>AptKogMatrix</strong> - Data Analytics Engine</p>
            <p style="margin: 5px 0 0 0;">Developer Attribution: <a href="https://rohitjain-resume.vercel.app/" target="_blank" style="color: #6366F1; text-decoration: none; font-weight: 600;">Rohit Jain</a> | Senior Software Architect</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
