import streamlit as st
import os
from frontend.api_client import AntigravityAPIClient

def render_ingestion_container(api_client: AntigravityAPIClient):
    """
    Renders the data ingestion block with a multi-file upload component
    and a Multi-Tier Nested Tab Navigation layout for uploaded files and sheets.
    """
    st.markdown(
        """
        <div style="margin-bottom: 15px;">
            <h3 style="margin:0; color:#5B21B6; font-size:20px;">📥 Data Ingestion Panel</h3>
            <p style="margin: 2px 0 10px 0; color:#6B7280; font-size:14px;">Upload up to 10 Excel files (max 500MB each) for local processing.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # File Uploader
    uploaded_files = st.file_uploader(
        "Choose Excel (.xlsx) files",
        type=["xlsx"],
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    # Process uploads when files are selected
    if uploaded_files:
        # Check if we need to hit the upload API (only if new files are uploaded)
        current_names = [f.name for f in uploaded_files]
        last_uploaded_names = st.session_state.get("last_uploaded_names", [])
        
        if current_names != last_uploaded_names:
            file_payloads = []
            for f in uploaded_files:
                file_payloads.append((f.name, f.getvalue()))
                
            with st.spinner("Uploading and analyzing Excel sheets locally..."):
                response = api_client.upload_files(file_payloads)
                
            if "error" in response:
                st.error(response["error"])
            else:
                st.session_state["files_metadata"] = response.get("files", [])
                st.session_state["last_uploaded_names"] = current_names
                st.success(response.get("message", "Files uploaded successfully!"))
                
    files_metadata = st.session_state.get("files_metadata", [])
    
    if not files_metadata:
        st.info("Please upload one or more Excel files to get started.")
        return

    st.markdown("#### 📂 Uploaded Datasets")
    
    # Tier 1: Horizontal tabs for File Names
    file_names = [meta["filename"] for meta in files_metadata]
    file_tabs = st.tabs(file_names)
    
    for idx, tab in enumerate(file_tabs):
        with tab:
            meta = files_metadata[idx]
            filepath = meta["filepath"]
            sheet_names = meta["sheet_names"]
            file_size_mb = meta["file_size_mb"]
            
            st.markdown(
                f"""
                <div style="font-size:13px; color:#6B7280; margin-bottom: 10px;">
                    <strong>Path:</strong> {filepath} &nbsp;|&nbsp; <strong>Size:</strong> {file_size_mb} MB
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Tier 2: Nested Tabs reflecting individual sheets within that file
            if sheet_names:
                sheet_tabs = st.tabs([f"📄 {sheet}" for sheet in sheet_names])
                for s_idx, s_tab in enumerate(sheet_tabs):
                    with s_tab:
                        sheet_name = sheet_names[s_idx]
                        st.markdown(
                            f"**Active Sheet:** `{sheet_name}` inside file `{meta['filename']}`"
                        )
                        
                        # Helper buttons to set active file/sheet for analytics
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.button("Set as Active Dataset", key=f"set_active_{idx}_{s_idx}"):
                                st.session_state["active_file_path"] = filepath
                                st.session_state["active_file_name"] = meta["filename"]
                                st.session_state["active_sheet_name"] = sheet_name
                                st.success(f"Activated: {meta['filename']} -> {sheet_name}")
                                st.rerun()
                        with col2:
                            st.write("(Click this button to load this sheet into the filtering, pivot, and join sections below)")
            else:
                st.warning("No sheets found in this file.")
