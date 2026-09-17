import streamlit as st


def render_sidebar_nav():
    """Sidebar Navigasi Ringkas (Ikon + Teks Vertikal) dengan Fitur Collapse."""

    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "screener"

    active_nav = st.session_state["active_nav"]

    sidebar_css = """
    <style>
    /* Lebar Sidebar Ringkas */
    [data-testid="stSidebar"] {
        min-width: 85px !important;
        max-width: 85px !important;
        background-color: #0D0E12 !important;
        border-right: 1px solid #1E222D !important;
    }

    /* Reset Padding Dalam Sidebar */
    [data-testid="stSidebarUserContent"] {
        padding: 10px 4px !important;
    }

    /* Styling Standar Tombol Navigasi */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent !important;
        border: none !important;
        color: #787B86 !important;
        font-family: sans-serif !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        height: 60px !important;
        width: 100% !important;
        border-radius: 6px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 4px !important;
        white-space: pre-line !important;
        line-height: 1.2 !important;
        box-shadow: none !important;
    }

    /* Hover State */
    [data-testid="stSidebar"] div.stButton > button:hover {
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.05) !important;
    }

    /* Active State via Container Marker */
    .nav-active div.stButton > button {
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.1) !important;
        border-left: 3px solid #00FF66 !important;
        border-radius: 0px 6px 6px 0px !important;
    }
    </style>
    """
    st.markdown(sidebar_css, unsafe_allow_html=True)

    nav_items = [
        ("screener", "⚙️\nScreener"),
        ("markets", "📈\nMarkets"),
        ("stream", "📡\nStream"),
        ("support", "🎧\nSupport"),
    ]

    with st.sidebar:
        for key, label in nav_items:
            # Gunakan st.container dengan class dinamis (Streamlit 1.30+)
            is_active = active_nav == key
            container_class = "nav-active" if is_active else "nav-inactive"

            with st.container(key=f"cont_{key}"):
                # Bungkus CSS marker
                st.markdown(
                    f'<div class="{container_class}">', unsafe_allow_html=True
                )
                if st.button(
                    label, key=f"btn_{key}", use_container_width=True
                ):
                    if st.session_state["active_nav"] != key:
                        st.session_state["active_nav"] = key
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
