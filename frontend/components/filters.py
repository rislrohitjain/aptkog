import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
from frontend.api_client import AntigravityAPIClient

def flatten_tree(node: Dict[str, Any], parent_id: str = "") -> tuple:
    """
    Flattens hierarchical tree JSON into lists for Plotly Treemap rendering.
    """
    ids = []
    labels = []
    parents = []
    values = []
    
    name = node.get("name", "Root")
    val = node.get("value", 0)
    current_id = f"{parent_id}/{name}" if parent_id else name
    
    ids.append(current_id)
    labels.append(name)
    parents.append(parent_id)
    values.append(val)
    
    for child in node.get("children", []):
        c_ids, c_labels, c_parents, c_values = flatten_tree(child, current_id)
        ids.extend(c_ids)
        labels.extend(c_labels)
        parents.extend(c_parents)
        values.extend(c_values)
        
    return ids, labels, parents, values

def render_filters_container(api_client: AntigravityAPIClient):
    """
    Renders the Universal Filter Engine and the Tri-View Layout (Table, Graph, Tree).
    Also embeds Scikit-Learn K-Means clustering controls and LangChain Chat Dialogue.
    """
    st.markdown(
        """
        <div style="margin-bottom: 15px;">
            <h3 style="margin:0; color:#6366F1; font-size:20px;">🔍 Universal Filter & Tri-View Engine</h3>
            <p style="margin: 2px 0 10px 0; color:#94A3B8; font-size:14px;">Define query parameters to screen data records, perform unsupervised clustering, and visualize customer segments.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Check if active file is set
    filepath = st.session_state.get("active_file_path")
    sheet_name = st.session_state.get("active_sheet_name")
    filename = st.session_state.get("active_file_name")

    if not filepath or not sheet_name:
        st.warning("⚠️ No active dataset selected. Please go to the Ingestion Panel and click 'Set as Active Dataset'.")
        return

    st.markdown(f"**Loaded Sheet:** `{sheet_name}` in `{filename}`")

    # Fetch schema details from session state if available, or fetch it via filter
    if "filter_response" not in st.session_state or st.session_state.get("last_filtered_sheet") != (filepath, sheet_name):
        from frontend.components.skeleton import render_skeleton
        loader_placeholder = st.empty()
        with loader_placeholder.container():
            render_skeleton("table", message="⏳ Analyzing columns...")
        res = api_client.filter_dataset(filepath, sheet_name, [])
        loader_placeholder.empty()
        if "error" not in res:
            st.session_state["filter_response"] = res
            st.session_state["last_filtered_sheet"] = (filepath, sheet_name)
        else:
            st.error(res["error"])
            return

    filter_res = st.session_state.get("filter_response", {})
    schema = filter_res.get("schema", {})
    columns = list(schema.keys())

    # Initialize filters list
    if "filters_list" not in st.session_state:
        st.session_state["filters_list"] = []

    # Dynamic Filter Builder Controls
    st.markdown("##### ➕ Define Query Filters")
    
    # Operators selection
    operators = [
        "=", "!=", "Like", "Contains", "Starts With", "Ends With", 
        "reg_expr", "Wildcards", ">", "<", ">=", "<=", "Is Null", 
        "Is Not Null", "In", "Not In"
    ]

    new_filters_list = []
    
    # Render existing filters
    for i, filt in enumerate(st.session_state["filters_list"]):
        col1, col2, col3, col4 = st.columns([3, 2, 3, 1])
        with col1:
            col_sel = st.selectbox(
                f"Column", columns, 
                index=columns.index(filt["column"]) if filt["column"] in columns else 0,
                key=f"col_{i}",
                help="Select the column to apply the filter rule on (e.g. amount, credit_score)."
            )
        with col2:
            op_sel = st.selectbox(
                f"Operator", operators, 
                index=operators.index(filt["operator"]) if filt["operator"] in operators else 0,
                key=f"op_{i}",
                help="Choose the comparison operator (e.g. '>' for greater than, '=' for exact match)."
            )
        with col3:
            # Disable value input for Null checks
            disable_val = op_sel in ["Is Null", "Is Not Null"]
            val_input = st.text_input(
                f"Value", 
                value=str(filt["value"]) if filt["value"] is not None else "",
                disabled=disable_val,
                key=f"val_{i}",
                placeholder="Comma separate for In/Not In",
                help="Enter the value to compare against. Use comma separation for 'In' or 'Not In'."
            )
        with col4:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            remove_clicked = st.button("❌", key=f"del_{i}", help="Click to delete this filter rule.")
            
        if not remove_clicked:
            new_filters_list.append({
                "column": col_sel,
                "operator": op_sel,
                "value": None if disable_val else val_input
            })

    st.session_state["filters_list"] = new_filters_list

    c_btn1, c_btn2, c_btn3 = st.columns([1.5, 1.5, 4])
    with c_btn1:
        if st.button("➕ Add Condition", use_container_width=True, help="Add a new filter condition block to refine the query."):
            st.session_state["filters_list"].append({
                "column": columns[0] if columns else "",
                "operator": "=",
                "value": ""
            })
            st.rerun()
    with c_btn2:
        if st.button("🧹 Clear Filters", use_container_width=True, help="Remove all query conditions and reset the view."):
            st.session_state["filters_list"] = []
            st.rerun()

    # Advanced Machine Learning / Clustering controls
    st.markdown("<hr style='margin:15px 0; border-color:#334155;' />", unsafe_allow_html=True)
    st.markdown("##### 🧠 Unsupervised Clustering (Scikit-Learn)")
    
    numeric_cols = [c for c, dtype in schema.items() if "int" in dtype.lower() or "float" in dtype.lower()]
    
    col_c1, col_c2 = st.columns([3, 1])
    with col_c1:
        selected_cluster_cols = st.multiselect(
            "Select Numeric Columns for K-Means Clustering",
            options=numeric_cols,
            help="Select numeric variables (e.g. amount, credit_score, income) to segment accounts using K-Means clustering."
        )
    with col_c2:
        cluster_cnt = st.number_input(
            "Cluster Count (K)", min_value=2, max_value=10, value=3,
            help="Number of target segment clusters to divide the dataset into."
        )

    # Anchor columns to select for Tree hierarchy
    st.markdown("<hr style='margin:15px 0; border-color:#334155;' />", unsafe_allow_html=True)
    st.markdown("##### 🌳 Hierarchical Tree Settings")
    string_cols = [c for c, dtype in schema.items() if "str" in dtype.lower() or "utf8" in dtype.lower()]
    
    selected_tree_cols = st.multiselect(
        "Select Categorical Columns to group Hierarchically",
        options=string_cols,
        default=string_cols[:2] if len(string_cols) >= 2 else string_cols,
        help="Select categorical variables (e.g. type, status, region) to create a nested breakdown tree."
    )

    # Filter Execution Button
    if st.button(
        "🚀 Apply Filters & Process Views", 
        type="primary", 
        use_container_width=True,
        help="Click to execute the query conditions, K-Means clustering, and hierarchical calculations."
    ):
        from frontend.components.skeleton import render_skeleton
        loader_placeholder = st.empty()
        with loader_placeholder.container():
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                render_skeleton("table", message="⏳ Processing Table View...")
            with col_l2:
                render_skeleton("graph", message="⏳ Processing Graph View...")
        res = api_client.filter_dataset(
            filepath=filepath,
            sheet_name=sheet_name,
            filters=st.session_state["filters_list"],
            tree_group_cols=selected_tree_cols,
            cluster_cols=selected_cluster_cols,
            cluster_count=cluster_cnt
        )
        loader_placeholder.empty()
        if "error" not in res:
            st.session_state["filter_response"] = res
            st.success("Analysis views updated successfully!")
        else:
            st.error(res["error"])

    # Load updated filter response
    filter_res = st.session_state.get("filter_response", {})
    metrics = filter_res.get("metrics", {"total_records": 0, "filtered_records": 0, "columns_count": 0})
    
    total = metrics.get("total_records", 0)
    filtered = metrics.get("filtered_records", 0)
    
    # Continuous Metric Bar
    st.markdown("##### 📊 Record Metrics Summary")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Total Records Loaded", f"{total:,}", help="Total number of database records loaded in memory.")
    with col_m2:
        st.metric("Filtered Records Matching", f"{filtered:,}", help="Number of records matching the current query criteria.")
    with col_m3:
        percentage = (filtered / total * 100) if total > 0 else 0
        st.metric("Data Selection ratio", f"{percentage:.1f}%", help="Percentage of base records matching the filter.")
        
    st.progress(percentage / 100 if total > 0 else 0)

    # 3-Tier Tri-View Tabs
    st.markdown("<br>", unsafe_allow_html=True)
    view_tab1, view_tab2, view_tab3 = st.tabs(["📝 Table View", "📈 Visual Graph View", "🌿 Tree Hierarchy View"])
    
    with view_tab1:
        table_rows = filter_res.get("table_data", [])
        if table_rows:
            df_table = pd.DataFrame(table_rows)
            st.markdown(
                """
                <div style="background-color: #1E293B; border-radius: 6px; padding: 10px; border-left: 4px solid #3B82F6; margin-bottom: 15px;">
                    <p style="margin: 0; font-size: 13px; color: #94A3B8;">
                        💡 <b>Pro-Tip:</b> You can double-click cells to edit them, or copy/paste multiple cells directly using <b>Ctrl+C</b> / <b>Ctrl+V</b> from external sheets like Excel!
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(f"*Showing first 500 matching records out of {filtered:,}*")
            
            # Ensure Remarks column is in the dataframe
            if "Remarks" not in df_table.columns:
                df_table.insert(0, "Remarks", "")
                
            # Config column_config and disabled lists dynamically based on actual columns present
            col_config = {}
            disabled_cols = []
            if "row_index" in df_table.columns:
                col_config["row_index"] = None
                disabled_cols.append("row_index")
                
            # Render editable dataframe
            edited_df = st.data_editor(
                df_table,
                use_container_width=True,
                column_config=col_config,
                disabled=disabled_cols if disabled_cols else None,
                key="table_editor"
            )
            
            # Check for changes in session state
            if "table_editor" in st.session_state:
                edited_rows = st.session_state["table_editor"].get("edited_rows", {})
                if edited_rows:
                    updates = []
                    for idx_str, changes in edited_rows.items():
                        idx = int(idx_str)
                        if "row_index" in df_table.columns:
                            row_index_val = int(df_table.iloc[idx]["row_index"])
                            for col_name, new_val in changes.items():
                                updates.append({
                                    "row_index": row_index_val,
                                    "column": col_name,
                                    "value": new_val
                                })
                        else:
                            st.error("Error: Cannot save edits. 'row_index' column is missing from this dataset.")
                            break
                    
                    if updates:
                        # Call API to save to server
                        with st.spinner("💾 Saving remarks to server..."):
                            save_res = api_client.update_remarks(filepath, sheet_name, updates)
                        if "error" in save_res:
                            st.error(save_res["error"])
                        else:
                            st.toast("📝 Remarks saved successfully to the server file!", icon="✅")
                            # Clear the edit queue from state to prevent infinite loop/re-saves
                            st.session_state["table_editor"]["edited_rows"] = {}
                            
                            # Refetch filtered data with new remarks
                            res = api_client.filter_dataset(
                                filepath=filepath,
                                sheet_name=sheet_name,
                                filters=st.session_state["filters_list"],
                                tree_group_cols=selected_tree_cols,
                                cluster_cols=selected_cluster_cols,
                                cluster_count=cluster_cnt
                            )
                            if "error" not in res:
                                st.session_state["filter_response"] = res
                            st.rerun()
            
            # Bulk Autofill Section
            with st.expander("⚡ Bulk Autofill Utility", expanded=False):
                col_fill1, col_fill2, col_fill3 = st.columns([2, 2, 2])
                with col_fill1:
                    col_to_fill = st.selectbox(
                        "Column to Fill", 
                        options=[c for c in df_table.columns if c != "row_index"],
                        help="Select the column you want to autofill."
                    )
                with col_fill2:
                    fill_value = st.text_input(
                        "Fill Value", 
                        placeholder="Type value to fill...",
                        help="Enter the value to populate the chosen column."
                    )
                with col_fill3:
                    fill_mode = st.radio(
                        "Fill Mode", 
                        ["Empty Cells Only", "All Rows"],
                        help="Choose whether to fill only empty cells or overwrite all cells in the column."
                    )
                
                if st.button("🚀 Apply Autofill & Save", use_container_width=True):
                    if "row_index" not in df_table.columns:
                        st.error("Error: 'row_index' column is missing from this dataset. Cannot apply bulk autofill.")
                    else:
                        fill_updates = []
                        for i in range(len(df_table)):
                            orig_row_idx = int(df_table.iloc[i]["row_index"])
                            curr_val = df_table.iloc[i][col_to_fill]
                            
                            # Determine if we should fill this cell
                            should_fill = False
                            if fill_mode == "All Rows":
                                should_fill = True
                            else:
                                # Empty Cells Only (check for None, NaN, empty string)
                                should_fill = pd.isna(curr_val) or str(curr_val).strip() == ""
                                
                            if should_fill:
                                fill_updates.append({
                                    "row_index": orig_row_idx,
                                    "column": col_to_fill,
                                    "value": fill_value
                                })
                                
                        if fill_updates:
                            with st.spinner("💾 Applying bulk autofill to server..."):
                                save_res = api_client.update_remarks(filepath, sheet_name, fill_updates)
                            if "error" in save_res:
                                st.error(save_res["error"])
                            else:
                                st.toast(f"Successfully autofilled {len(fill_updates)} cells!", icon="✅")
                                # Refetch filtered data
                                res = api_client.filter_dataset(
                                    filepath=filepath,
                                    sheet_name=sheet_name,
                                    filters=st.session_state["filters_list"],
                                    tree_group_cols=selected_tree_cols,
                                    cluster_cols=selected_cluster_cols,
                                    cluster_count=cluster_cnt
                                )
                                if "error" not in res:
                                    st.session_state["filter_response"] = res
                                st.rerun()
                        else:
                            st.info("No cells matched the autofill criteria.")
            
            # Utility Actions Section
            st.markdown("---")
            col_act1, col_act2 = st.columns(2)
            
            with col_act1:
                try:
                    with open(filepath, "rb") as f:
                        file_bytes = f.read()
                    st.download_button(
                        label="📥 Download Updated Dataset (Excel/CSV)",
                        data=file_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if filename.lower().endswith(".xlsx") else "text/csv",
                        use_container_width=True,
                        help="Download the updated file from the server containing your remarks."
                    )
                except Exception as e:
                    st.error(f"Error loading file for download: {e}")
                    
            with col_act2:
                if st.button("🔄 Restart Work with Updated Remarks", use_container_width=True, help="Clear filters and reload the updated dataset to start fresh."):
                    st.session_state["filters_list"] = []
                    if "filter_response" in st.session_state:
                        del st.session_state["filter_response"]
                    if "last_filtered_sheet" in st.session_state:
                        del st.session_state["last_filtered_sheet"]
                    st.toast("Workspace reset with updated remarks!", icon="🔄")
                    st.rerun()
        else:
            st.info("No records matched the filter criteria.")
            
    with view_tab2:
        graph_rows = filter_res.get("graph_data", [])
        if graph_rows:
            df_graph = pd.DataFrame(graph_rows)
            
            st.markdown("##### Plotly Graph Configurator")
            g_cols = list(df_graph.columns)
            
            col_g1, col_g2, col_g3, col_g4, col_g5 = st.columns(5)
            with col_g1:
                x_axis = st.selectbox(
                    "X-Axis Column", g_cols, index=0 if g_cols else None,
                    help="Select variable for the horizontal X-axis."
                )
            with col_g2:
                y_options = [c for c in g_cols if c in numeric_cols]
                if not y_options:
                    y_options = g_cols
                y_axis = st.selectbox(
                    "Y-Axis Column (Numeric)", y_options, index=0 if y_options else None,
                    help="Select numeric variable for the vertical Y-axis."
                )
            with col_g3:
                color_options = ["None"] + [c for c in g_cols if c in string_cols or "Cluster" in c]
                color_by = st.selectbox(
                    "Group/Color By", color_options,
                    help="Group and color coordinate points based on categorical values (e.g. status or cluster label)."
                )
            with col_g4:
                chart_type = st.selectbox(
                    "Chart Type", ["Scatter", "Bar", "Line", "Histogram", "Pie", "Donut", "Area"],
                    help="Select visual representation type."
                )
            with col_g5:
                agg_type = st.selectbox(
                    "Aggregation / Group By", ["None (Raw Records)", "Count of Records", "Sum", "Mean", "Min", "Max"],
                    help="Aggregate values or counts by X-axis and Group/Color categories."
                )
                
            color_param = None if color_by == "None" else color_by
            df_plot = df_graph.copy()
            y_axis_col = y_axis
            
            # Apply aggregation if specified
            if agg_type != "None (Raw Records)" and x_axis:
                group_keys = [x_axis]
                if color_param:
                    group_keys.append(color_param)
                
                if agg_type == "Count of Records":
                    df_plot = df_plot.groupby(group_keys).size().reset_index(name="Record Count")
                    y_axis_col = "Record Count"
                elif y_axis:
                    agg_map = {
                        "Sum": "sum",
                        "Mean": "mean",
                        "Min": "min",
                        "Max": "max"
                    }
                    try:
                        df_plot[y_axis] = pd.to_numeric(df_plot[y_axis], errors='coerce')
                    except Exception:
                        pass
                    df_plot = df_plot.groupby(group_keys)[y_axis].agg(agg_map[agg_type]).reset_index()
            
            fig = None
            if chart_type == "Scatter" and x_axis and y_axis_col:
                fig = px.scatter(df_plot, x=x_axis, y=y_axis_col, color=color_param, title=f"Scatter Plot: {y_axis_col} vs {x_axis}")
            elif chart_type == "Bar" and x_axis and y_axis_col:
                fig = px.bar(df_plot, x=x_axis, y=y_axis_col, color=color_param, title=f"Bar Chart: {y_axis_col} vs {x_axis}", barmode="group")
            elif chart_type == "Line" and x_axis and y_axis_col:
                fig = px.line(df_plot, x=x_axis, y=y_axis_col, color=color_param, title=f"Line Chart: {y_axis_col} vs {x_axis}")
            elif chart_type == "Histogram" and x_axis:
                fig = px.histogram(df_plot, x=x_axis, y=y_axis_col if agg_type != "None (Raw Records)" else None, color=color_param, title=f"Distribution of {x_axis}")
            elif chart_type == "Pie" and x_axis:
                if agg_type == "None (Raw Records)":
                    df_pie = df_plot.groupby(x_axis).size().reset_index(name="Record Count")
                    fig = px.pie(df_pie, names=x_axis, values="Record Count", title=f"Pie Chart: Record Count by {x_axis}")
                elif y_axis_col:
                    fig = px.pie(df_plot, names=x_axis, values=y_axis_col, title=f"Pie Chart: {y_axis_col} by {x_axis}")
            elif chart_type == "Donut" and x_axis:
                if agg_type == "None (Raw Records)":
                    df_pie = df_plot.groupby(x_axis).size().reset_index(name="Record Count")
                    fig = px.pie(df_pie, names=x_axis, values="Record Count", hole=0.4, title=f"Donut Chart: Record Count by {x_axis}")
                elif y_axis_col:
                    fig = px.pie(df_plot, names=x_axis, values=y_axis_col, hole=0.4, title=f"Donut Chart: {y_axis_col} by {x_axis}")
            elif chart_type == "Area" and x_axis and y_axis_col:
                fig = px.area(df_plot, x=x_axis, y=y_axis_col, color=color_param, title=f"Area Chart: {y_axis_col} vs {x_axis}")
                
            if fig:
                # Dark template integration for Plotly Graph
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#1E293B",
                    plot_bgcolor="#1E293B"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for plotting.")
            
    with view_tab3:
        tree_node = filter_res.get("tree_data", {})
        if tree_node and tree_node.get("children"):
            st.markdown("##### Plotly Interactive Treemap")
            ids, labels, parents, values = flatten_tree(tree_node)
            
            fig_tree = go.Figure(go.Treemap(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values,
                branchvalues="total",
                textinfo="label+value+percent parent",
                hovertemplate='<b>%{label} </b><br>Records: %{value}<br>Percent of Parent: %{percentParent:.2%}',
            ))
            fig_tree.update_layout(
                margin=dict(t=10, l=10, r=10, b=10),
                template="plotly_dark",
                paper_bgcolor="#1E293B",
                plot_bgcolor="#1E293B"
            )
            st.plotly_chart(fig_tree, use_container_width=True)
            show_json = st.checkbox("📄 View JSON Schema hierarchy", value=False, help="Toggle to view the raw JSON tree breakdown.")
            if show_json:
                st.json(tree_node)
        else:
            st.info("Configure 'Hierarchical Tree Settings' above and click Apply to generate a tree hierarchy.")

    # LangChain Chat Dialogue Assistant
    st.markdown("<hr style='margin:20px 0; border-color:#334155;' />", unsafe_allow_html=True)
    st.markdown("##### 💬 Semantic AI Data Assistant (LangChain)")
    
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
        
    for q, ans in st.session_state["chat_history"]:
        st.markdown(f"**👤 You:** {q}")
        st.markdown(f"**🤖 Analyst:** {ans}")
        st.markdown("<hr style='margin:10px 0; border-style:dashed; border-color:#334155;' />", unsafe_allow_html=True)
        
    chat_question = st.text_input(
        "Ask a question about this sheet (e.g., 'Describe the columns', 'Which columns have null values?')", 
        key="chat_question_input",
        help="Type a question about the active dataset. Processing is offline and secure."
    )
    if st.button(
        "Send Query", 
        key="send_chat_query",
        help="Click to submit the query to the offline LangChain AI data analyst."
    ):
        if chat_question.strip():
            from frontend.components.skeleton import render_skeleton
            loader_placeholder = st.empty()
            with loader_placeholder.container():
                render_skeleton("text", message="🤖 Analyst is thinking...")
            chat_res = api_client.ask_analyst(filepath, sheet_name, chat_question)
            loader_placeholder.empty()
                
            if "error" in chat_res:
                st.error(chat_res["error"])
            else:
                response_txt = chat_res.get("response", "No answer received.")
                st.session_state["chat_history"].append((chat_question, response_txt))
                st.rerun()
