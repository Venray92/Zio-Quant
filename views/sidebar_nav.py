import streamlit as st


def render_sidebar_nav():
    """Menampilkan Navigasi Vertikal dengan Tombol Toggle Tepat di Tengah Garis Kanan."""

    if "nav_collapsed" not in st.session_state:
        st.session_state["nav_collapsed"] = False

    is_collapsed = st.session_state["nav_collapsed"]
    active_nav = st.session_state.get("active_nav", "screener")

    # CSS Khusus untuk merapikan ukuran tombol & posisi tombol toggle di tengah garis
    nav_css = """
    <style>
    /* Hilangkan padding default kolom agar rapat */
    div[data-testid="stColumn"] {
        padding: 0px !important;
    }

    /* Style Tombol Navigasi Utama */
    div.nav-main-col div.stButton > button {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #C9D1D9 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        height: 52px !important;
        width: 100% !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: none !important;
    }

    /* Hover & Active State Navigasi */
    div.nav-main-col div.stButton > button:hover {
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }

    /* Tombol Toggle persis di tengah garis pembatas */
    div.nav-toggle-col {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        height: 100%;
        min-height: 280px; /* Menyesuaikan tinggi agar pas di tengah vertikal */
    }

    div.nav-toggle-col div.stButton > button {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-left: none !important;
        color: #00FF66 !important;
        font-size: 14px !important;
        font-weight: 900 !important;
        height: 55px !important;
        width: 16px !important;
        min-width: 16px !important;
        padding: 0 !important;
        border-radius: 0px 6px 6px 0px !important;
        transition: all 0.2s ease-in-out !important;
    }

    div.nav-toggle-col div.stButton > button:hover {
        background-color: #00FF66 !important;
        color: #000000 !important;
        border-color: #00FF66 !important;
        box-shadow: 2px 0 10px rgba(0, 255, 102, 0.4) !important;
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

    # Menggunakan rasio kolom yang pas agar teks tidak kepotong
    # Kolom kiri untuk tombol menu, kolom kanan sangat kecil khusus untuk tombol toggle melayang di garis
    col_menu, col_toggle = st.columns([5, 1], gap="small")

    with col_menu:
        st.markdown('<div class="nav-main-col">', unsafe_allow_html=True)
        for key, label in nav_items:
            # Jika state collapsed, singkat hurufnya agar rapi
            display_label = label[:1] if is_collapsed else label
            is_active_indicator = " •" if active_nav == key else ""

            if st.button(
                f"{display_label}{is_active_indicator}",
                key=f"nav_btn_{key}",
                use_container_width=True,
            ):
                st.session_state["active_nav"] = key
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_toggle:
        st.markdown('<div class="nav-toggle-col">', unsafe_allow_html=True)
        toggle_icon = "›" if is_collapsed else "‹"
        if st.button(
            toggle_icon, key="btn_nav_toggle", use_container_width=True
        ):
            st.session_state["nav_collapsed"] = not is_collapsed
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
