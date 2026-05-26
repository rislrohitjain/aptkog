import streamlit as st

@st.dialog("Flow of Application / कार्यप्रवाह")
def show_flow_dialog():
    col1, col2 = st.columns([3, 1])
    with col2:
        lang_toggle = st.toggle("हिन्दी", key="lang_toggle_flow")
    
    if not lang_toggle:
        st.markdown(
            """
            ### 🔄 AptKogMatrix Application Flow
            1. **📥 Data Ingestion**: Upload Excel or CSV files (e.g., active ledgers, customer profiles) in the ingestion tab and set the active sheet.
            2. **🔍 Universal Filter**: Apply robust query operations (Credit Score > 720, Debt-to-Income < 40%) to quickly isolate records.
            3. **📊 Pivot Engine**: Construct multi-dimensional pivot grids (e.g., group default counts by officer).
            4. **🔗 Dataset Joiner**: Combine tables (e.g., merge Ledger with Credit Scores on `Customer_ID`) and download a unified spreadsheet.
            """
        )
    else:
        st.markdown(
            """
            ### 🔄 AptKogMatrix एप्लिकेशन कार्यप्रवाह
            1. **📥 डेटा इनजेशन (अपलोड)**: इनजेशन टैब में अपनी एक्सेल या सीएसवी फ़ाइलें (जैसे सक्रिय बहीखाता, ग्राहक प्रोफाइल) अपलोड करें और कार्य करने के लिए सक्रिय शीट चुनें।
            2. **🔍 यूनिवर्सल फ़िल्टर**: रिकॉर्ड्स को जल्दी से फ़िल्टर करने के लिए मजबूत शर्तें लागू करें (जैसे क्रेडिट स्कोर > 720, ऋण-से-आय < 40%)।
            3. **📊 पिवट इंजन**: पिवट ग्रिड बनाएं (जैसे अधिकारी द्वारा डिफॉल्ट खातों को समूहित करना)।
            4. **🔗 डेटासेट जॉइनर**: तालिकाओं को आपस में जोड़ें (जैसे `ग्राहक_आईडी` पर क्रेडिट स्कोर के साथ बहीखाता का मिलान करना) और एकीकृत एक्सेल शीट डाउनलोड करें।
            """
        )

@st.dialog("How It's Secure / सुरक्षा विवरण")
def show_security_dialog():
    col1, col2 = st.columns([3, 1])
    with col2:
        lang_toggle = st.toggle("हिन्दी", key="lang_toggle_security")
        
    if not lang_toggle:
        st.markdown(
            """
            ### 🛡️ 100% Offline Processing - Secure & Local
            - **Local Execution**: All calculations, filtering, and joins are executed purely in memory on this machine.
            - **No External Cloud Calls**: Your files, customer details, and proprietary data matrices are never sent to external servers.
            - **Offline-First Privacy**: Works fully disconnected from the internet to guarantee compliance with internal confidentiality standards.
            """
        )
    else:
        st.markdown(
            """
            ### 🛡️ 100% ऑफ़लाइन प्रोसेसिंग - सुरक्षित और स्थानीय
            - **स्थानीय निष्पादन**: सभी गणनाएँ, फ़िल्टर और जॉइन विशुद्ध रूप से आपकी स्थानीय मशीन की मेमोरी में निष्पादित होते हैं।
            - **कोई बाहरी क्लाउड कॉल नहीं**: आपकी फाइलें, ग्राहक विवरण और स्वामित्व वाली डेटा मैट्रिक्स कभी भी बाहरी सर्वर पर नहीं भेजी जाती हैं।
            - **ऑफ़लाइन-प्रथम गोपनीयता**: आंतरिक गोपनीयता मानकों के अनुपालन की गारंटी के लिए इंटरनेट से पूरी तरह से डिस्कनेक्ट होकर काम करता है।
            """
        )

def render_sidebar():
    """
    Renders a unified modern sidebar with branding, developer attribution, and anchor navigation.
    """
    try:
        from PIL import Image
        import os
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.png")
        logo_img = Image.open(logo_path)
        col_side1, col_side2, col_side3 = st.sidebar.columns([1, 3, 1])
        with col_side2:
            st.image(logo_img, width=140)
    except Exception:
        st.sidebar.markdown(
            """
            <div style="text-align: center; padding: 10px 0px;">
                <h2 style="margin: 0; color: #6366F1; font-size: 28px;">⚡ AptKogMatrix</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.sidebar.markdown(
        """
        <div style="text-align: center;">
            <p style="margin: 5px 0 15px 0; color: #94A3B8; font-size: 13px; font-weight: 500;">Data Analytics Engine</p>
        </div>
        <hr style="margin-top: 0; margin-bottom: 20px; border-color: #334155;" />
        """,
        unsafe_allow_html=True
    )
    
    st.sidebar.markdown("### 🗂️ Workspace Sections")
    
    # Initialize session state for navigation if not set
    if "active_block" not in st.session_state:
        st.session_state["active_block"] = "Ingestion"
        
    import os
    hide_tech = os.environ.get("HIDE_TECH_INFO", "False").lower() in ["true", "1", "yes"]

    # Navigation buttons
    nav_options = {
        "📥 Data Ingestion": ("Ingestion", "Upload Excel or CSV files and choose the active workspace sheet."),
        "🔍 Universal Filter & Tri-View": ("Filter", "Query ledgers, run K-Means credit clustering, and view tree structures."),
        "📊 Dynamic Pivot Engine": ("Pivot", "Group and aggregate amounts by branch, status, or officer."),
        "🔗 Dataset Builder (Join)": ("Join", "Perform relation joins between client lists and credit reports using a key column.")
    }
    if not hide_tech:
        nav_options["⚙️ Diagnostics & Privacy"] = ("Diagnostics", "Check local memory usage, thread diagnostics, and server health.")
    
    for label, (block_id, tooltip) in nav_options.items():
        is_active = st.session_state["active_block"] == block_id
        if st.sidebar.button(
            label, 
            key=f"nav_{block_id}", 
            use_container_width=True,
            type="primary" if is_active else "secondary",
            help=tooltip
        ):
            st.session_state["active_block"] = block_id
            st.rerun()

    st.sidebar.markdown("<hr style='border-color: #334155; margin: 15px 0;' />", unsafe_allow_html=True)
    st.sidebar.markdown("### 🔄 Operations")
    col_ref1, col_ref2 = st.sidebar.columns(2)
    with col_ref1:
        if st.button("🔄 Refresh", key="btn_refresh", use_container_width=True, help="Reload page layout without losing active data"):
            st.rerun()
    with col_ref2:
        if st.button("🧹 Reset All", key="btn_reset_all", use_container_width=True, help="Wipe all loaded files, query states, and history"):
            curr_block = st.session_state.get("active_block", "Ingestion")
            st.session_state.clear()
            st.session_state["active_block"] = curr_block
            st.rerun()

    st.sidebar.markdown("<hr style='border-color: #334155; margin: 20px 0;' />", unsafe_allow_html=True)
    st.sidebar.markdown("### ℹ️ Info & Security")
    
    if st.sidebar.button(
        "🔄 Flow of Application", 
        key="btn_flow", 
        use_container_width=True,
        help="Click to see the step-by-step workflow of this application in English or Hindi"
    ):
        show_flow_dialog()
        
    if st.sidebar.button(
        "🛡️ How it's secure", 
        key="btn_security", 
        use_container_width=True,
        help="Click to see how your data is kept 100% secure and offline"
    ):
        show_security_dialog()

    st.sidebar.markdown("<br><hr style='border-color: #334155;' />", unsafe_allow_html=True)
    
    # Permanent Developer attribution optimized for dark theme
    st.sidebar.markdown(
        """
        <div style="background-color: #1E293B; border-radius: 8px; padding: 12px; border-left: 4px solid #6366F1; margin-top: 10px;">
            <p style="margin: 0; font-size: 11px; text-transform: uppercase; color: #94A3B8; font-weight: bold; letter-spacing: 0.05em;">Developer Attribution</p>
            <p style="margin: 4px 0 0 0; font-size: 15px; font-weight: bold; color: #F8FAFC;">
                <a href="https://rohitjain-resume.vercel.app/" target="_blank" style="color: #F8FAFC; text-decoration: none;">Rohit Jain</a>
            </p>
            <p style="margin: 2px 0 0 0; font-size: 11px; color: #94A3B8;">Senior Software Architect</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Simple help text
    st.sidebar.markdown(
        """
        <div style="margin-top: 15px; font-size: 11px; color: #64748B; text-align: center;">
            <p>100% Offline Processing<br>Secure and Local</p>
        </div>
        """,
        unsafe_allow_html=True
    )
