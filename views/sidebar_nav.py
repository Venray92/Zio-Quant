import streamlit as st


def render_sidebar_nav():
    """Menampilkan Navigasi Vertikal dalam Kontainer Garis Pembatas dengan Toggle di Tengah."""

    if "nav_collapsed" not in st.session_state:
        st.session_state["nav_collapsed"] = False

    is_collapsed = st.session_state["nav_collapsed"]
    active_nav = st.session_state.get("active_nav", "screener")

    # Lebar sidebar berdasarkan status collapse
    sidebar_width = "64px" if is_collapsed else "160px"

    # CSS & HTML Layout kustom agar tombol toggle pas di tengah garis pembatas
    nav_css = f"""
    <style>
    .custom-sidebar-container {{
        position: relative;
        width: {sidebar_width};
        background-color: #0D0E12;
        border-right: 2px solid #21262D;
        border-radius: 8px;
        padding: 16px 8px;
        min-height: 600px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        transition: width 0.25s ease-in-out;
    }

    /* Style Tombol Menu Navigasi */
    div.stButton > button.nav-menu-btn {{
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #C9D1D9 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        height: 50px !important;
        width: 100% !important;
        border-radius: 6px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        padding-left: 14px !important;
        transition: all 0.2s ease-in-out !important;
    }}

    div.stButton > button.nav-menu-btn:hover {{
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }}

    /* Active State */
    div.stButton > button.nav-active-btn {{
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.15) !important;
        border: 1.5px solid #00FF66 !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.3) !important;
    }}

    /* Tombol Toggle Presisi di Tengah Garis Pembatas Kanan */
    .toggle-wrapper-center {{
        position: absolute;
        top: 50%;
        right: -13px;
        transform: translateY(-50%);
        z-index: 99;
    }}

    div.stButton > button.toggle-arrow-btn {{
        background-color: #161B22 !important;
        border: 2px solid #30363D !important;
        color: #00FF66 !important;
        font-size: 14px !important;
        font-weight: 900 !important;
        height: 48px !important;
        width: 24px !important;
        min-width: 24px !important;
        padding: 0 !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
        transition: all 0.2s ease-in-out !important;
    }}

    div.stButton > button.toggle-arrow-btn:hover {{
        background-color: #00FF66 !important;
        color: #000000 !important;
        border-color: #00FF66 !important;
        box-shadow: 0 0 12px #00FF66 !important;
    }}
    </style>
    """
    st.markdown(nav_css, unsafe_allow_html=True)

    nav_items = [
        ("screener", "⚡ Screener"),
        ("markets", "📈 Markets"),
        ("stream", "📡 Stream"),
        ("support", "🎧 Support"),
    ]

    # Wrapper kontainer utama sidebar
    st.markdown('<div class="custom-sidebar-container">', unsafe_allow_html=True)

    # Render Menu Item
    for key, label in nav_items:
        # Jika collapsed, tampilkan ikon/huruf pertamanya saja agar tidak patah
        display_text = label[:2] if is_collapsed else label
        is_active_class = "nav-active-btn" if active_nav == key else "nav-menu-btn"

        if st.button(
            display_text, key=f"nav_btn_{key}", use_container_width=True
        ):
            st.session_state["active_nav"] = key
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Tombol Toggle Tepat di Tengah Garis Pembatas (Menggunakan absolut positioning CSS)
    toggle_icon = "›" if is_collapsed else "‹"
    st.markdown('<div class="toggle-wrapper-center">', unsafe_allow_html=True)
    if st.button(toggle_icon, key="btn_nav_toggle", use_container_width=False):
        st.session_state["nav_collapsed"] = not is_collapsed
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
