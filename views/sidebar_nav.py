import streamlit as st


def render_sidebar_nav():
    """Menampilkan Navigasi Vertikal dalam Kontainer dengan Toggle di Tengah Garis Pembatas."""

    if "nav_collapsed" not in st.session_state:
        st.session_state["nav_collapsed"] = False

    is_collapsed = st.session_state["nav_collapsed"]
    active_nav = st.session_state.get("active_nav", "screener")

    # Styling CSS penuh untuk kontainer, tombol utama, dan toggle di tengah garis
    nav_css = """
    <style>
    /* Kontainer pembungkus sidebar kustom */
    .sidebar-wrapper {
        background-color: #0D0E12;
        border-right: 2px solid #21262D;
        border-radius: 8px;
        padding: 14px 8px;
        position: relative;
    }

    /* Memperbesar tombol navigasi utama agar tidak kekecilan dan teks tidak terpotong */
    div.nav-main-area div.stButton > button {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #C9D1D9 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        height: 52px !important;
        width: 100% !important;
        border-radius: 6px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        padding-left: 14px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: none !important;
    }

    div.nav-main-area div.stButton > button:hover {
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }

    /* Active State (Glow Hijau) */
    .nav-item-active div.stButton > button {
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.12) !important;
        border: 1.5px solid #00FF66 !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.25) !important;
    }

    /* Posisi tombol toggle agar tepat di tengah secara vertikal pada kolom kanan */
    .nav-toggle-area {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        min-height: 260px;
    }

    div.nav-toggle-area div.stButton > button {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-left: none !important;
        color: #00FF66 !important;
        font-size: 15px !important;
        font-weight: 900 !important;
        height: 60px !important;
        width: 18px !important;
        min-width: 18px !important;
        padding: 0 !important;
        border-radius: 0px 6px 6px 0px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 2px 0 8px rgba(0,0,0,0.4) !important;
    }

    div.nav-toggle-area div.stButton > button:hover {
        background-color: #00FF66 !important;
        color: #000000 !important;
        border-color: #00FF66 !important;
        box-shadow: 0 0 12px #00FF66 !important;
    }
    </style>
    """
    st.markdown(nav_css, unsafe_allow_html=True)

    nav_items = [
        ("screener", "⚡ Screener"),
        ("markets", "📈 Markets"),
        ("stream", "📡 Stream"),
        ("support", "🎧 Support"),
    ]

    # Bungkus dalam kontainer utama bergaris pembatas
    st.markdown('<div class="sidebar-wrapper">', unsafe_allow_html=True)

    # Menggunakan rasio kolom agar tombol menu utama luas dan tombol toggle pas di garis kanan
    col_menu, col_toggle = st.columns([6, 1], gap="small")

    with col_menu:
        st.markdown('<div class="nav-main-area">', unsafe_allow_html=True)
        for key, label in nav_items:
            display_label = label[:2] if is_collapsed else label
            is_active = (
                "nav-item-active" if active_nav == key else "nav-item-normal"
            )

            st.markdown(f'<div class="{is_active}">', unsafe_allow_html=True)
            if st.button(
                display_label, key=f"nav_btn_{key}", use_container_width=True
            ):
                st.session_state["active_nav"] = key
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_toggle:
        st.markdown('<div class="nav-toggle-area">', unsafe_allow_html=True)
        toggle_icon = "›" if is_collapsed else "‹"
        if st.button(
            toggle_icon, key="btn_nav_toggle", use_container_width=True
        ):
            st.session_state["nav_collapsed"] = not is_collapsed
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
