import streamlit as st

def render_sidebar():
    """
    Renders a unified modern sidebar with branding, developer attribution, and anchor navigation.
    """
    st.sidebar.markdown(
        """
        <div style="text-align: center; padding: 10px 0px;">
            <h2 style="margin: 0; color: #5B21B6; font-size: 26px;">⚡ Antigravity 2.0</h2>
            <p style="margin: 5px 0 15px 0; color: #6B7280; font-size: 14px;">Local Data Analytics Engine</p>
        </div>
        <hr style="margin-top: 0; margin-bottom: 20px; border-color: #E5E7EB;" />
        """,
        unsafe_allow_html=True
    )
    
    st.sidebar.markdown("### 🗂️ Workspace Sections")
    
    # Initialize session state for navigation if not set
    if "active_block" not in st.session_state:
        st.session_state["active_block"] = "Ingestion"
        
    # Navigation buttons
    nav_options = {
        "📥 Data Ingestion": "Ingestion",
        "🔍 Universal Filter & Tri-View": "Filter",
        "📊 Dynamic Pivot Engine": "Pivot",
        "🔗 Dataset Builder (Join)": "Join",
        "⚙️ Diagnostics & Privacy": "Diagnostics"
    }
    
    for label, block_id in nav_options.items():
        # Highlight active block using styling or button types
        is_active = st.session_state["active_block"] == block_id
        if st.sidebar.button(
            label, 
            key=f"nav_{block_id}", 
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state["active_block"] = block_id
            st.rerun()

    st.sidebar.markdown("<br><br><hr style='border-color: #E5E7EB;' />", unsafe_allow_html=True)
    
    # Permanent Developer attribution
    st.sidebar.markdown(
        """
        <div style="background-color: #F3F4F6; border-radius: 8px; padding: 12px; border-left: 4px solid #5B21B6; margin-top: 10px;">
            <p style="margin: 0; font-size: 11px; text-transform: uppercase; color: #6B7280; font-weight: bold; letter-spacing: 0.05em;">Developer Attribution</p>
            <p style="margin: 4px 0 0 0; font-size: 15px; font-weight: bold; color: #1F2937;">Rohit Jain</p>
            <p style="margin: 2px 0 0 0; font-size: 11px; color: #9CA3AF;">Senior Python Software Architect</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Simple help text
    st.sidebar.markdown(
        """
        <div style="margin-top: 20px; font-size: 12px; color: #9CA3AF; text-align: center;">
            <p>100% Offline Processing<br>Secure and Local</p>
        </div>
        """,
        unsafe_allow_html=True
    )
