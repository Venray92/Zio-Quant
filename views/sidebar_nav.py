import streamlit as st


def render_sidebar_nav():
    """Sidebar Navigasi Bergaya TradingView yang Stabil dan Pasti Muncul."""

    # Init State
    if "nav_collapsed" not in st.session_state:
        st.session_state["nav_collapsed"] = True
    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "screener"

    is_collapsed = st.session_state["nav_collapsed"]
    active_nav = st.session_state["active_nav"]

    # Atur lebar berdasarkan state lipat
    sidebar_width = "70px" if is_collapsed else "160px"

    # CSS Aman Tanpa Merusak Elemen Utama
    css = f"""
    <style>
    /* Force Lebar Sidebar dan Styling Dasar */
    [data-testid="stSidebar"] {{
        min-width: {sidebar_width} !important;
        max-width: {sidebar_width} !important;
        background-color: #0D0E12 !important;
        border-right: 2px solid #00FF66 !important;
    }}

    /* Hilangkan padding default agar lebih rapat ke atas */
    [data-testid="stSidebarUserContent"] {{
        padding: 4px 4px !important;
    }}

    /* Style Semua Tombol Navigasi */
    [data-testid="stSidebar"] button {{
        background-color: transparent !important;
        border: none !important;
        color: #787B86 !important;
        height: 60px !important;
        border-radius: 6px !important;
        margin-bottom: 6px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: none !important;
    }}

    [data-testid="stSidebar"] button:hover {{
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }}

    /* CSS Khusus Tombol Toggle Buka/Tutup di Atas */
    [data-testid="stSidebar"] button[key="btn_toggle"] {{
        height: 32px !important;
        border: 1px solid #30363D !important;
        background-color: #161B22 !important;
        color: #00FF66 !important;
        margin-bottom: 10px !important;
        margin-top: 0px !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    nav_items = [
        ("screener", "Screener", "⚙️"),
        ("markets", "Markets", "📈"),
        ("stream", "Stream", "📡"),
        ("support", "Support", "🎧"),
    ]

    with st.sidebar:
        # 1. Tombol Toggle Buka/Tutup di Paling Atas
        toggle_label = "❯" if is_collapsed else "❮"
        if st.button(toggle_label, key="btn_toggle", use_container_width=True):
            st.session_state["nav_collapsed"] = not is_collapsed
            st.rerun()

        # 2. Tombol Navigasi Utama
        for key, label, icon in nav_items:
            is_active = active_nav == key

            button_label = f"{icon}" if is_collapsed else f"{icon}\n{label}"

            if is_active:
                button_label = f"● {icon}" if is_collapsed else f"{icon} {label}"

            if st.button(
                button_label, key=f"nav_btn_{key}", use_container_width=True
            ):
                if st.session_state["active_nav"] != key:
                    st.session_state["active_nav"] = key
                    st.rerun()
