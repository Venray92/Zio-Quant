import streamlit as st


def render_sidebar_nav():
    """Menampilkan Navigasi Vertikal Ramping dengan Tombol Toggle Melayang di Garis Pembatas."""

    if "nav_collapsed" not in st.session_state:
        st.session_state["nav_collapsed"] = False

    is_collapsed = st.session_state["nav_collapsed"]
    active_nav = st.session_state.get("active_nav", "screener")

    # Dynamic CSS
    nav_css = """
    <style>
    /* Hilangkan background default & border kaku tombol Streamlit di sidebar nav */
    div[data-testid="stColumn"] div.stButton > button {
        background-color: transparent !important;
        border: 1px solid #21262D !important;
        color: #8A8B98 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        height: 50px !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: none !important;
    }

    /* Hover State Navigation Buttons */
    div[data-testid="stColumn"] div.stButton > button:hover {
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.2) !important;
    }

    /* Tombol Toggle Collapse khusus (Tombol Panah Ramping) */
    div.toggle-container div.stButton > button {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #00FF66 !important;
        font-size: 14px !important;
        font-weight: 900 !important;
        height: 40px !important;
        padding: 0 !important;
        border-radius: 4px !important;
        margin-top: 10px !important;
    }

    div.toggle-container div.stButton > button:hover {
        background-color: #00FF66 !important;
        color: #000000 !important;
        box-shadow: 0 0 10px #00FF66 !important;
    }

    /* Styling Container Utama Navigasi */
    .sidebar-inner-box {
        background-color: #0D0E12;
        border-right: 1px solid #21262D;
        padding: 10px 4px;
        border-radius: 8px;
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

    # Bagi kontainer navigasi kiri menjadi 2 sub-kolom: Menu Navigasi & Tombol Toggle
    col_menu, col_toggle = st.columns([4, 1])

    with col_menu:
        st.markdown('<div class="sidebar-inner-box">', unsafe_allow_html=True)
        for key, label in nav_items:
            # Jika dalam keadaan collapsed, tampilkan label singkat/ikon saja
            display_label = label[0] if is_collapsed else label
            is_active_badge = " ▪" if active_nav == key else ""

            if st.button(
                f"{display_label}{is_active_badge}",
                key=f"nav_btn_{key}",
                use_container_width=True,
            ):
                st.session_state["active_nav"] = key
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_toggle:
        st.markdown('<div class="toggle-container">', unsafe_allow_html=True)
        toggle_icon = "›" if is_collapsed else "‹"
        if st.button(
            toggle_icon, key="btn_nav_toggle", use_container_width=True
        ):
            st.session_state["nav_collapsed"] = not is_collapsed
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
