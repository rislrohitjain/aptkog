import streamlit as st
from typing import List, Dict, Any
from frontend.api_client import AntigravityAPIClient

def render_join_container(api_client: AntigravityAPIClient):
    """
    Renders the Dataset Builder (Join / VLOOKUP Simulator) Container.
    Allows users to merge files via key matching and download the output.
    Optimized for bank loan internal department employees.
    """
    st.markdown(
        """
        <div style="margin-bottom: 15px;">
            <h3 style="margin:0; color:#6366F1; font-size:20px;">🔗 Vectorized Dataset Builder (VLOOKUP & Join Simulator)</h3>
            <p style="margin: 2px 0 10px 0; color:#94A3B8; font-size:14px;">Simulate complex bank database lookups (VLOOKUP, INDEX-MATCH) by joining columns from two sheets on a common key.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    files_metadata = st.session_state.get("files_metadata", [])
    if len(files_metadata) < 2:
        st.warning("⚠️ Relational joins require at least two uploaded files (e.g. Applicant Profiles and Credit Scores). Please upload more files in the Ingestion Panel.")
        return

    # Create file mapping
    file_options = {meta["filename"]: meta for meta in files_metadata}
    file_list = list(file_options.keys())

    # Layout for Source A and Source B
    col_j1, col_j2 = st.columns(2)
    
    with col_j1:
        st.markdown("**📁 Source Table A (Primary Base Dataset)**")
        file_a_name = st.selectbox(
            "Select File A", 
            options=file_list, 
            key="join_file_a",
            help="Select the base data file containing primary application records (e.g. customer_profiles.xlsx)"
        )
        meta_a = file_options[file_a_name]
        sheet_a = st.selectbox(
            "Select Sheet in A", 
            options=meta_a["sheet_names"], 
            key="join_sheet_a",
            help="Select the specific sheet in File A containing the data"
        )
        
    with col_j2:
        st.markdown("**📁 Source Table B (Lookup Database)**")
        b_default_idx = 1 if len(file_list) > 1 else 0
        file_b_name = st.selectbox(
            "Select File B", 
            options=file_list, 
            index=b_default_idx, 
            key="join_file_b",
            help="Select the secondary file containing auxiliary data to append (e.g. credit_bureau_scores.csv)"
        )
        meta_b = file_options[file_b_name]
        sheet_b = st.selectbox(
            "Select Sheet in B", 
            options=meta_b["sheet_names"], 
            key="join_sheet_b",
            help="Select the specific sheet in File B containing the lookup data"
        )

    # Fetch columns for File A and File B dynamically if changed
    cache_key_a = (meta_a["filepath"], sheet_a)
    cache_key_b = (meta_b["filepath"], sheet_b)

    if st.session_state.get("join_cache_key_a") != cache_key_a:
        with st.spinner(f"Reading columns for {file_a_name}..."):
            res = api_client.filter_dataset(meta_a["filepath"], sheet_a, [])
            if "error" not in res:
                st.session_state["join_cols_a"] = list(res.get("schema", {}).keys())
                st.session_state["join_cache_key_a"] = cache_key_a
            else:
                st.error(f"Failed to read File A columns: {res['error']}")
                return

    if st.session_state.get("join_cache_key_b") != cache_key_b:
        with st.spinner(f"Reading columns for {file_b_name}..."):
            res = api_client.filter_dataset(meta_b["filepath"], sheet_b, [])
            if "error" not in res:
                st.session_state["join_cols_b"] = list(res.get("schema", {}).keys())
                st.session_state["join_cache_key_b"] = cache_key_b
            else:
                st.error(f"Failed to read File B columns: {res['error']}")
                return

    cols_a = st.session_state.get("join_cols_a", [])
    cols_b = st.session_state.get("join_cols_b", [])

    st.markdown("<hr style='margin:15px 0; border-color:#334155;' />", unsafe_allow_html=True)
    st.markdown("##### 🔑 Join Parameters & Matching Keys")

    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        join_key_a = st.selectbox(
            "Join Key Column in File A", 
            options=cols_a,
            help="Select the primary column in File A to match rows (e.g. customer_id, loan_number)"
        )
    with col_p2:
        b_default_key_idx = cols_b.index(join_key_a) if join_key_a in cols_b else 0
        join_key_b = st.selectbox(
            "Join Key Column in File B", 
            options=cols_b, 
            index=b_default_key_idx,
            help="Select the matching lookup column in File B (e.g. customer_id, applicant_no)"
        )
    with col_p3:
        join_type = st.selectbox(
            "Join Method", 
            options=["Left", "Inner", "Outer"], 
            help="Left Join is standard VLOOKUP (keeps all applicants from Table A and appends data from Table B where matches exist)."
        )

    # Column Selection block for File A & File B
    st.markdown("<hr style='margin:15px 0; border-color:#334155;' />", unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("##### 📁 File A Columns to Keep")
        select_all_a = st.checkbox(
            "Select All Columns from File A", 
            value=True, 
            key="select_all_cols_a",
            help="Include all columns from File A in the final output sheet"
        )
        if select_all_a:
            select_columns_a = cols_a
            st.info("ℹ️ All columns from File A will be included in the output.")
        else:
            select_columns_a = st.multiselect(
                "Choose specific columns to keep from File A",
                options=cols_a,
                default=[c for c in cols_a if c == join_key_a] or ([cols_a[0]] if cols_a else []),
                help="Select only the specific fields you need to retain from File A"
            )

    with col_c2:
        st.markdown("##### 📁 File B Columns to Extract & Append")
        cols_b_to_select = [c for c in cols_b if c != join_key_b]
        select_all_b = st.checkbox(
            "Select All Columns from File B", 
            value=False, 
            key="select_all_cols_b",
            help="Append all available columns from File B (excluding join key) to the output"
        )
        if select_all_b:
            select_columns_b = cols_b_to_select
            st.info("ℹ️ All columns from File B will be appended to the output.")
        else:
            select_columns_b = st.multiselect(
                "Choose specific columns to append from File B",
                options=cols_b_to_select,
                default=cols_b_to_select[:3] if cols_b_to_select else [],
                help="Select only the specific fields you need to lookup/extract from File B"
            )

    # Execution button which returns downloadable Excel stream
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(
        "🔗 Run Vectorized Join & Consolidate Excel", 
        type="primary", 
        use_container_width=True,
        help="Click to execute the relational join locally. This compiles and adds 'joined_output.xlsx' to your workspace."
    ):
        if not select_columns_a:
            st.warning("Please select at least one column to keep from File A.")
        elif not select_columns_b:
            st.warning("Please select at least one column to copy from File B.")
        else:
            with st.spinner("Executing relational merge and generating output Excel file..."):
                joined_res = api_client.execute_join(
                    filepath_a=meta_a["filepath"],
                    sheet_name_a=sheet_a,
                    filepath_b=meta_b["filepath"],
                    sheet_name_b=sheet_b,
                    join_key_a=join_key_a,
                    join_key_b=join_key_b,
                    join_type=join_type,
                    select_columns_a=select_columns_a,
                    select_columns_b=select_columns_b
                )
                
            if isinstance(joined_res, dict) and "error" in joined_res:
                st.error(joined_res["error"])
            else:
                joined_bytes = joined_res["content"]
                joined_filepath = joined_res["joined_filepath"]
                
                st.session_state["join_binary_result"] = joined_bytes
                
                # Automatically append the merged file to the file tabs listing
                new_meta = {
                    "filename": "joined_output.xlsx",
                    "filepath": joined_filepath,
                    "sheet_names": ["ConsolidatedData"],
                    "file_size_mb": round(len(joined_bytes) / (1024 * 1024), 2)
                }
                
                meta_list = st.session_state.get("files_metadata", [])
                meta_list = [m for m in meta_list if m["filename"] != "joined_output.xlsx"]
                meta_list.append(new_meta)
                st.session_state["files_metadata"] = meta_list
                
                st.success("Dataset consolidation complete! The merged file 'joined_output.xlsx' has been automatically added to your tabs in the Ingestion Container.")
                st.rerun()

    binary_data = st.session_state.get("join_binary_result")
    if binary_data:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="💾 Click here to download consolidated Excel file",
            data=binary_data,
            file_name="aptkog_consolidated_dataset.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="Download the consolidated joined dataset to your local device"
        )
