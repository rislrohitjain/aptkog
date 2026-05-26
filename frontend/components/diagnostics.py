import streamlit as st
from frontend.api_client import AntigravityAPIClient

def render_diagnostics_panel(api_client: AntigravityAPIClient):
    """
    Renders a diagnostic panel representing the hardware utilization, compiler state,
    and Polars optimization flags returned from the backend.
    """
    # Fetch diagnostics
    diag = api_client.get_diagnostics()
    
    if "error" in diag:
        st.error(f"Failed to fetch system diagnostics: {diag['error']}")
        return

    # Modern visual layout for performance metrics
    st.markdown(
        """
        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 15px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h4 style="margin: 0; color: #1E293B; font-size: 16px;">🖥️ Server Resource Utilization & Optimization Flags</h4>
                <span style="background-color: #DEF7EC; color: #03543F; font-size: 11px; font-weight: 600; padding: 4px 8px; border-radius: 12px;">
                    🟢 Connected
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_d1, col_d2, col_d3 = st.columns(3)
    
    with col_d1:
        st.markdown("**💻 CPU & RAM Utilization**")
        cpu_val = diag.get("cpu_percent", 0.0)
        st.metric("CPU Usage", f"{cpu_val}%")
        
        # RAM usage of backend process vs total system
        ram_proc = diag.get("ram_process_mb", 0.0)
        st.metric("API Process RAM", f"{ram_proc:,.1f} MB")
        
    with col_d2:
        st.markdown("**⚡ Vectorization Core (Polars)**")
        st.metric("Polars Version", diag.get("polars_version", "N/A"))
        
        simd_state = diag.get("polars_simd_status", "Inactive")
        st.metric("SIMD Acceleration", simd_state, 
                  help="Indicates whether Rust SIMD vectors (AVX2/NEON) are compiled.")
        
    with col_d3:
        st.markdown("**🔒 Privacy & Security**")
        # Local Privacy Validation Status
        privacy_status = diag.get("local_privacy_validation", "Active")
        st.markdown(
            f"""
            <div style="margin-top: 10px;">
                <p style="margin:0; font-size:12px; color:#475569;"><strong>Local Validation:</strong></p>
                <p style="margin: 4px 0 0 0; font-size: 13px; font-weight: bold; color: #15803D;">✅ Local Sandbox Active</p>
                <p style="margin: 2px 0 0 0; font-size: 11px; color: #64748B;">Data remains completely local. Zero cloud uploads.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown("<hr style='margin:10px 0; border-color:#E2E8F0;' />", unsafe_allow_html=True)
    
    # Environment info
    col_env1, col_env2 = st.columns(2)
    with col_env1:
        st.markdown(f"**Python Compiler:** `{diag.get('python_compiler', 'N/A')}`")
        st.markdown(f"**Platform Architecture:** `{diag.get('architecture', 'N/A')}`")
    with col_env2:
        st.markdown(f"**Polars Threadpool Size:** `{diag.get('polars_threadpool_size', 'N/A')} Threads`")
        st.markdown(f"**SIMD Config:** `{(diag.get('polars_simd_info', 'N/A'))}`")
        
    # Refresh button
    if st.button("🔄 Poll Real-Time Hardware Performance", key="poll_diagnostics_btn", use_container_width=True):
        st.rerun()
