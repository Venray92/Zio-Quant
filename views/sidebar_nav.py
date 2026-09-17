import streamlit as st


def render_sidebar_nav():
    """Menampilkan 4 Navigasi Vertikal Ramping di Sisi Kiri Utama."""
    active_nav = st.session_state.get("active_nav", "screener")

    # CSS Khusus Navigasi Kiri Ramping
    nav_css = """
    <style>
    .left-nav-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        align-items: center;
        background-color: #0D0E12;
        border-right: 1px solid #21262D;
        padding: 12px 6px;
        border-radius: 8px;
        margin-top: 5px;
    }

    .left-nav-btn-box {
        width: 100%;
        display: flex;
        justify-content: center;
    }

    /* Style Tombol Navigation */
    div.left-nav-btn-box button {
        background: transparent !important;
        border: 1px solid #21262D !important;
        color: #8A8B98 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        height: 48px !important;
        width: 100% !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* Hover State */
    div.left-nav-btn-box button:hover {
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.2) !important;
    }

    /* Active State (Glow Neon Green) */
    .left-nav-btn-box.active-nav button {
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.15) !important;
        border: 1.5px solid #00FF66 !important;
        box-shadow: 0 0 12px rgba(0, 255, 102, 0.4) !important;
        text-shadow: 0 0 8px #00FF66 !important;
    }
    </style>
    """
    st.markdown(nav_css, unsafe_allow_html=True)

    nav_items = [
        ("screener", "Screener"),
        ("markets", "Markets"),
        ("stream", "Stream"),
        ("support", "Support"),
    ]

    st.markdown('<div class="left-nav-container">', unsafe_allow_html=True)
    for key, label in nav_items:
        is_active = "active-nav" if active_nav == key else ""

        st.markdown(
            f'<div class="left-nav-btn-box {is_active}">',
            unsafe_allow_html=True,
        )
        if st.button(
            label,
            key=f"nav_btn_{key}",
            use_container_width=True,
        ):
            st.session_state["active_nav"] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)