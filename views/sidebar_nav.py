import streamlit as st


def render_sidebar_nav():
    """Menampilkan Navigasi Vertikal Ramping dengan Tombol Toggle Melayang di Garis Pembatas."""

    if "nav_collapsed" not in st.session_state:
        st.session_state["nav_collapsed"] = False

    is_collapsed = st.session_state["nav_collapsed"]
    active_nav = st.session_state.get("active_nav", "screener")

    # CSS khusus agar tombol toggle berada persis di tengah garis pembatas kanan
    nav_css = """
    <style>
    .nav-sidebar-outer {
        position: relative;
        width: 100%;
        background-color: #0D0E12;
        border-right: 1px solid #21262D;
        padding: 16px 6px 20px 6px;
        min-height: 500px;
        border-radius: 4px;
    }

    .nav-sidebar-inner {
        display: flex;
        flex-direction: column;
        gap: 16px;
        align-items: center;
    }

    /* Style Item Navigasi */
    .nav-item-wrapper {
        width: 100%;
    }

    div.nav-item-wrapper button {
        background: transparent !important;
        border: none !important;
        color: #8A8B98 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 10px !important;
        font-weight: 700 !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 54px !important;
        width: 100% !important;
        padding: 6px 2px !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: none !important;
    }

    div.nav-item-wrapper button:hover {
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }

    /* Active State (Glow Neon Green) */
    .nav-item-wrapper.active-nav button {
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.12) !important;
        border-right: 3px solid #00FF66 !important;
        box-shadow: inset -2px 0 8px rgba(0, 255, 102, 0.3) !important;
        text-shadow: 0 0 8px #00FF66 !important;
    }

    /* Tombol Toggle Collapse Floating di Garis Pembatas Kanan */
    div.floating-toggle-btn {
        margin-top: 40px;
        margin-bottom: 15px;
        display: flex;
        justify-content: center;
    }

    div.floating-toggle-btn button {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #8A8B98 !important;
        font-size: 11px !important;
        font-weight: 900 !important;
        height: 38px !important;
        width: 22px !important;
        min-width: 22px !important;
        padding: 0 !important;
        border-radius: 4px 0px 0px 4px !important;
        transition: all 0.2s ease-in-out !important;
        margin-left: auto !important;
    }

    div.floating-toggle-btn button:hover {
        background-color: #00FF66 !important;
        color: #000000 !important;
        border-color: #00FF66 !important;
        box-shadow: 0 0 8px #00FF66 !important;
    }
    </style>
    """
    st.markdown(nav_css, unsafe_allow_html=True)

    # SVG Outline Icons
    svg_screener = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>'
    svg_markets = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'
    svg_stream = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9"></path><path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5"></path><circle cx="12" cy="12" r="2"></circle><path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5"></path><path d="M19.1 4.9c3.9 3.9 3.9 10.2 0 14.1"></path></svg>'
    svg_support = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 18v-6a9 9 0 0 1 18 0v6"></path><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"></path></svg>'

    nav_items = [
        ("screener", "Screener", svg_screener),
        ("markets", "Markets", svg_markets),
        ("stream", "Stream", svg_stream),
        ("support", "Support", svg_support),
    ]

    st.markdown('<div class="nav-sidebar-outer">', unsafe_allow_html=True)

    # 1. Navigasi Items List
    st.markdown('<div class="nav-sidebar-inner">', unsafe_allow_html=True)
    for key, label, svg in nav_items:
        is_active = "active-nav" if active_nav == key else ""

        st.markdown(
            f'<div class="nav-item-wrapper {is_active}">',
            unsafe_allow_html=True,
        )
        if st.button(
            label if is_collapsed else f"{label}",
            key=f"nav_btn_{key}",
            use_container_width=True,
        ):
            st.session_state["active_nav"] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # 2. Tombol Toggle Menempel di Garis Pembatas Kanan
    toggle_icon = "›" if is_collapsed else "‹"
    st.markdown('<div class="floating-toggle-btn">', unsafe_allow_html=True)
    if st.button(toggle_icon, key="btn_nav_toggle", use_container_width=True):
        st.session_state["nav_collapsed"] = not is_collapsed
        st.rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)
