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
        with st.spinner("Analyzing columns..."):
            res = api_client.filter_dataset(filepath, sheet_name, [])
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
        with st.spinner("Applying universal filter and updating views..."):
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
            st.markdown(f"*Showing first 500 matching records out of {filtered:,}*")
            st.dataframe(df_table, use_container_width=True)
        else:
            st.info("No records matched the filter criteria.")
            
    with view_tab2:
        graph_rows = filter_res.get("graph_data", [])
        if graph_rows:
            df_graph = pd.DataFrame(graph_rows)
            
            st.markdown("##### Plotly Graph Configurator")
            g_cols = list(df_graph.columns)
            
            col_g1, col_g2, col_g3, col_g4 = st.columns(4)
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
                    "Chart Type", ["Scatter", "Bar", "Line", "Histogram"],
                    help="Select visual representation type."
                )
                
            color_param = None if color_by == "None" else color_by
            
            fig = None
            if chart_type == "Scatter" and x_axis and y_axis:
                fig = px.scatter(df_graph, x=x_axis, y=y_axis, color=color_param, title=f"Scatter Plot: {y_axis} vs {x_axis}")
            elif chart_type == "Bar" and x_axis and y_axis:
                fig = px.bar(df_graph, x=x_axis, y=y_axis, color=color_param, title=f"Bar Chart: {y_axis} vs {x_axis}")
            elif chart_type == "Line" and x_axis and y_axis:
                fig = px.line(df_graph, x=x_axis, y=y_axis, color=color_param, title=f"Line Chart: {y_axis} vs {x_axis}")
            elif chart_type == "Histogram" and x_axis:
                fig = px.histogram(df_graph, x=x_axis, color=color_param, title=f"Distribution of {x_axis}")
                
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
            
            with st.expander("📄 View JSON Schema hierarchy"):
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
            with st.spinner("LangChain analyzing dataset schema and metadata..."):
                chat_res = api_client.ask_analyst(filepath, sheet_name, chat_question)
                
            if "error" in chat_res:
                st.error(chat_res["error"])
            else:
                response_txt = chat_res.get("response", "No answer received.")
                st.session_state["chat_history"].append((chat_question, response_txt))
                st.rerun()
