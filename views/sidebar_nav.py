import streamlit as st


def render_sidebar_nav():
    """Navigasi Sidebar Vertikal dengan Kontainer Rapi dan Toggle di Tengah Garis."""

    if "nav_collapsed" not in st.session_state:
        st.session_state["nav_collapsed"] = False

    is_collapsed = st.session_state["nav_collapsed"]
    active_nav = st.session_state.get("active_nav", "screener")

    # CSS Global Bersih: Hilangkan margin/padding aneh & atur ukuran tombol besar
    nav_css = """
    <style>
    /* Styling Tombol Menu Navigasi Utama */
    div.nav-column div.stButton > button {
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
        box-shadow: none !important;
        transition: all 0.2s ease-in-out !important;
    }

    div.nav-column div.stButton > button:hover {
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }

    /* State Aktif (Glow Neon Green) */
    div.nav-column div.stButton.btn-active-state > button {
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.15) !important;
        border: 1.5px solid #00FF66 !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.3) !important;
    }

    /* Styling Tombol Toggle di Kolom Kanan Agar Tepat di Tengah Vertikal */
    div.toggle-column {
        display: flex;
        align-items: center;
        height: 100%;
        min-height: 250px;
    }

    div.toggle-column div.stButton > button {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-left: none !important;
        color: #00FF66 !important;
        font-size: 14px !important;
        font-weight: 900 !important;
        height: 50px !important;
        width: 18px !important;
        min-width: 18px !important;
        padding: 0 !important;
        border-radius: 0px 6px 6px 0px !important;
        box-shadow: 2px 0 8px rgba(0,0,0,0.5) !important;
        transition: all 0.2s ease-in-out !important;
    }

    div.toggle-column div.stButton > button:hover {
        background-color: #00FF66 !important;
        color: #000000 !important;
        border-color: #00FF66 !important;
        box-shadow: 0 0 12px #00FF66 !important;
    }

    /* Kontainer Garis Pembatas Sidebar */
    .sidebar-container-box {
        background-color: #0D0E12;
        border-right: 2px solid #21262D;
        border-radius: 8px;
        padding: 12px 6px;
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

    # Layout menggunakan 2 kolom berdampingan murni tanpa elemen melayang yang bug
    col_menu, col_toggle = st.columns([5, 1], gap="small")

    with col_menu:
        st.markdown('<div class="sidebar-container-box">', unsafe_allow_html=True)
        for key, label in nav_items:
            display_text = label[:2] if is_collapsed else label
            is_active = active_nav == key

            # Bungkus tombol dengan class khusus untuk styling aktif
            wrapper_class = "nav-column btn-active-state" if is_active else "nav-column"
            st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
            
            if st.button(
                display_text, key=f"nav_btn_{key}", use_container_width=True
            ):
                st.session_state["active_nav"] = key
                st.rerun()
                
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_toggle:
        st.markdown('<div class="toggle-column">', unsafe_allow_html=True)
        toggle_icon = "›" if is_collapsed else "‹"
        if st.button(
            toggle_icon, key="btn_sidebar_toggle", use_container_width=True
        ):
            st.session_state["nav_collapsed"] = not is_collapsed
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
