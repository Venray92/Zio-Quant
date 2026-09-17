import streamlit as st


def render_sidebar_nav():
    """Sidebar Navigasi Bersih dengan 4 Tombol Normal Tanpa Kotak Hitam di Atas."""

    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "screener"

    active_nav = st.session_state["active_nav"]

    sidebar_css = """
    <style>
    /* HILANGKAN KOTAK HITAM / TOMBOL BAWAAN DI BAGIAN ATAS SIDEBAR */
    section[data-testid="stSidebar"] [data-testid="stBaseButton-header"],
    section[data-testid="stSidebar"] button[kind="header"],
    [data-testid="collapsedControl"],
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* Rapikan padding atas sidebar agar tombol langsung mepet ke atas */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem !important;
    }

    .clean-sidebar-box {
        background-color: #0D0E12;
        border-right: 2px solid #00FF66;
        border-radius: 6px;
        padding: 12px 8px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .clean-sidebar-box div.stButton > button {
        background-color: #161B22 !important;
        border: 1.5px solid #30363D !important;
        color: #C9D1D9 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        height: 48px !important;
        width: 100% !important;
        border-radius: 6px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        padding-left: 12px !important;
        box-shadow: none !important;
    }

    .clean-sidebar-box div.stButton > button:hover {
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }
    </style>
    """
    st.markdown(sidebar_css, unsafe_allow_html=True)

    nav_items = [
        ("screener", "⚡ Screener"),
        ("markets", "📈 Markets"),
        ("stream", "📡 Stream"),
        ("support", "🎧 Support"),
    ]

    # Jika lo menggunakan st.sidebar, bungkus kodenya di sini:
    with st.sidebar:
        st.markdown('<div class="clean-sidebar-box">', unsafe_allow_html=True)

        for key, label in nav_items:
            if st.button(
                label, key=f"clean_btn_{key}", use_container_width=True
            ):
                st.session_state["active_nav"] = key
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
