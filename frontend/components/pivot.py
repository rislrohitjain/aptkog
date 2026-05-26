import streamlit as st
import pandas as pd
from typing import List
from frontend.api_client import AntigravityAPIClient

def render_pivot_container(api_client: AntigravityAPIClient):
    """
    Renders the Dynamic Pivot Engine UI block, letting users select
    row indices, column groupings, aggregation functions, and values.
    """
    st.markdown(
        """
        <div style="margin-bottom: 15px;">
            <h3 style="margin:0; color:#5B21B6; font-size:20px;">📊 Dynamic Pivot Engine</h3>
            <p style="margin: 2px 0 10px 0; color:#6B7280; font-size:14px;">Simulate drag-and-drop multidimensional analysis by grouping rows and columns.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Validate active dataset
    filepath = st.session_state.get("active_file_path")
    sheet_name = st.session_state.get("active_sheet_name")
    filename = st.session_state.get("active_file_name")

    if not filepath or not sheet_name:
        st.warning("⚠️ No active dataset selected. Please set an active dataset in the Ingestion Panel.")
        return

    st.markdown(f"**Target Dataset:** `{sheet_name}` in `{filename}`")

    # Retrieve columns from filter response schema
    filter_res = st.session_state.get("filter_response", {})
    schema = filter_res.get("schema", {})
    columns = list(schema.keys())

    if not columns:
        st.info("No columns available. Verify dataset upload.")
        return

    # Render Pivot Matrix layout using a grid
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        row_indices = st.multiselect(
            "🗂️ Row Indices (Rows)", 
            options=columns, 
            default=[columns[0]] if columns else [],
            help="Select columns to stack vertically as row groups."
        )
        
        column_groupings = st.multiselect(
            "📂 Column Groupings (Columns)",
            options=[c for c in columns if c not in row_indices],
            default=[columns[1]] if len(columns) > 1 else [],
            help="Select columns to expand horizontally. (Uses first selected column in Polars)."
        )
        
    with col_p2:
        val_column = st.selectbox(
            "🔢 Metric Value (Values)",
            options=columns,
            index=min(2, len(columns) - 1) if columns else 0,
            help="Select the column containing the data values to aggregate."
        )
        
        agg_op = st.selectbox(
            "📈 Aggregation Function",
            options=["Sum", "Mean", "Count", "Max", "Min"],
            index=0,
            help="Select the operation to compute values."
        )

    # Pivot Execution Button
    if st.button("📊 Execute Pivot Aggregation", type="primary", use_container_width=True):
        if not row_indices:
            st.error("Please select at least one Row Index column.")
        elif not column_groupings:
            st.error("Please select at least one Column Grouping column.")
        elif not val_column:
            st.error("Please select a Metric Value column.")
        else:
            with st.spinner("Processing multi-threaded Polars pivot on backend..."):
                # Call Pivot API
                res = api_client.execute_pivot(
                    filepath=filepath,
                    sheet_name=sheet_name,
                    index=row_indices,
                    columns=column_groupings,
                    values=val_column,
                    agg=agg_op
                )
                
            if "error" in res:
                st.error(res["error"])
            else:
                st.session_state["pivot_result"] = res
                st.success(f"Pivot executed! Result shape: {res.get('shape', [0,0])}")

    # Display Pivot Table
    pivot_res = st.session_state.get("pivot_result")
    if pivot_res and "data" in pivot_res:
        st.markdown("##### 🏁 Aggregated Pivot Table")
        
        # Convert records to Pandas DataFrame for presentation
        df_pivot = pd.DataFrame(pivot_res["data"])
        
        # Ensure row indexes are set as the dataframe index for index-like display
        # We can detect if index columns are in dataframe columns
        cols_present = [c for c in row_indices if c in df_pivot.columns]
        if cols_present:
            df_pivot_styled = df_pivot.set_index(cols_present)
        else:
            df_pivot_styled = df_pivot
            
        st.dataframe(df_pivot_styled, use_container_width=True)
        
        # Add Excel Download for Pivot
        # Let's save pivoted dataframe back using openpyxl in streamlit locally
        try:
            import io
            bio = io.BytesIO()
            with pd.ExcelWriter(bio, engine="openpyxl") as writer:
                df_pivot.to_excel(writer, index=False, sheet_name="PivotTable")
            excel_data = bio.getvalue()
            
            st.download_button(
                label="📥 Download Pivot Table as Excel",
                data=excel_data,
                file_name="pivot_table_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.warning(f"Excel generation not available: {e}")
