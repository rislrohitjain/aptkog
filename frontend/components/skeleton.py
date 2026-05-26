import streamlit as st

def render_skeleton(skeleton_type: str = "table", message: str = ""):
    """
    Renders a CSS placeholder skeleton loader with a modern pulse animation.
    Supported types: 'table', 'graph', 'text'
    """
    message_html = f'<div style="color: #818CF8; font-weight: 600; font-size: 15px; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">{message}</div>' if message else ''
    
    if skeleton_type == "table":
        st.markdown(
            f"""
            <style>
            @keyframes pulse {{
                0%, 100% {{ opacity: 0.4; }}
                50% {{ opacity: 0.85; }}
            }}
            .skeleton-container {{
                animation: pulse 1.5s infinite ease-in-out;
                background-color: #1E293B;
                border-radius: 8px;
                padding: 20px;
                border: 1px solid #334155;
                margin-top: 15px;
                margin-bottom: 15px;
            }}
            .skeleton-header {{
                display: flex;
                gap: 15px;
                border-bottom: 2px solid #334155;
                padding-bottom: 12px;
                margin-bottom: 15px;
            }}
            .skeleton-header-cell {{
                height: 22px;
                background-color: #475569;
                border-radius: 4px;
                flex: 1;
            }}
            .skeleton-row {{
                display: flex;
                gap: 15px;
                margin-bottom: 12px;
            }}
            .skeleton-cell {{
                height: 16px;
                background-color: #334155;
                border-radius: 4px;
                flex: 1;
            }}
            </style>
            <div class="skeleton-container">
                {message_html}
                <div class="skeleton-header">
                    <div class="skeleton-header-cell" style="flex: 0.5;"></div>
                    <div class="skeleton-header-cell"></div>
                    <div class="skeleton-header-cell" style="flex: 1.5;"></div>
                    <div class="skeleton-header-cell"></div>
                </div>
                <div class="skeleton-row">
                    <div class="skeleton-cell" style="flex: 0.5;"></div>
                    <div class="skeleton-cell"></div>
                    <div class="skeleton-cell" style="flex: 1.5;"></div>
                    <div class="skeleton-cell"></div>
                </div>
                <div class="skeleton-row">
                    <div class="skeleton-cell" style="flex: 0.5;"></div>
                    <div class="skeleton-cell" style="width: 80%;"></div>
                    <div class="skeleton-cell" style="flex: 1.5; width: 90%;"></div>
                    <div class="skeleton-cell"></div>
                </div>
                <div class="skeleton-row">
                    <div class="skeleton-cell" style="flex: 0.5;"></div>
                    <div class="skeleton-cell"></div>
                    <div class="skeleton-cell" style="flex: 1.5;"></div>
                    <div class="skeleton-cell" style="width: 85%;"></div>
                </div>
                <div class="skeleton-row" style="margin-bottom: 0;">
                    <div class="skeleton-cell" style="flex: 0.5; width: 70%;"></div>
                    <div class="skeleton-cell" style="width: 90%;"></div>
                    <div class="skeleton-cell" style="flex: 1.5; width: 60%;"></div>
                    <div class="skeleton-cell"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif skeleton_type == "graph":
        st.markdown(
            f"""
            <style>
            @keyframes pulse {{
                0%, 100% {{ opacity: 0.4; }}
                50% {{ opacity: 0.85; }}
            }}
            .skeleton-graph {{
                animation: pulse 1.5s infinite ease-in-out;
                background-color: #1E293B;
                border-radius: 8px;
                padding: 20px;
                border: 1px solid #334155;
                height: 380px;
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
                margin-top: 15px;
                margin-bottom: 15px;
            }}
            .skeleton-graph-title {{
                height: 22px;
                width: 25%;
                background-color: #475569;
                border-radius: 4px;
                align-self: flex-start;
                margin-bottom: 30px;
            }}
            .skeleton-bars {{
                display: flex;
                align-items: flex-end;
                justify-content: space-around;
                height: 280px;
                padding: 0 15px;
                border-left: 2px solid #334155;
                border-bottom: 2px solid #334155;
            }}
            .skeleton-bar {{
                width: 10%;
                background-color: #334155;
                border-radius: 6px 6px 0 0;
            }}
            </style>
            <div class="skeleton-graph">
                {message_html}
                <div class="skeleton-graph-title"></div>
                <div class="skeleton-bars">
                    <div class="skeleton-bar" style="height: 25%;"></div>
                    <div class="skeleton-bar" style="height: 60%;"></div>
                    <div class="skeleton-bar" style="height: 40%;"></div>
                    <div class="skeleton-bar" style="height: 85%;"></div>
                    <div class="skeleton-bar" style="height: 50%;"></div>
                    <div class="skeleton-bar" style="height: 75%;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif skeleton_type == "text":
        st.markdown(
            f"""
            <style>
            @keyframes pulse {{
                0%, 100% {{ opacity: 0.4; }}
                50% {{ opacity: 0.85; }}
            }}
            .skeleton-text-container {{
                animation: pulse 1.5s infinite ease-in-out;
                background-color: #1E293B;
                border-radius: 8px;
                padding: 22px;
                border: 1px solid #334155;
                margin-top: 15px;
                margin-bottom: 15px;
            }}
            .skeleton-text-title {{
                height: 18px;
                width: 20%;
                background-color: #475569;
                border-radius: 4px;
                margin-bottom: 15px;
            }}
            .skeleton-text-line {{
                height: 12px;
                background-color: #334155;
                border-radius: 4px;
                margin-bottom: 10px;
            }}
            </style>
            <div class="skeleton-text-container">
                {message_html}
                <div class="skeleton-text-title"></div>
                <div class="skeleton-text-line" style="width: 95%;"></div>
                <div class="skeleton-text-line" style="width: 100%;"></div>
                <div class="skeleton-text-line" style="width: 90%;"></div>
                <div class="skeleton-text-line" style="width: 40%; margin-bottom: 0;"></div>
            </div>
            """,
            unsafe_allow_html=True
        )
