import streamlit as st


def render_sidebar_nav():
    """Sidebar Navigasi Vertikal Ringkas (Ikon + Teks) - Tanpa Error Multiline."""

    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "screener"

    active_nav = st.session_state["active_nav"]

    # Definisi menu navigasi
    nav_items = [
        ("screener", "Screener", "⚙️"),
        ("markets", "Markets", "📈"),
        ("stream", "Stream", "📡"),
        ("support", "Support", "🎧"),
    ]

    # CSS untuk menyusun Ikon & Teks secara vertikal tanpa menggunakan \n
    sidebar_css = """
    <style>
    /* Paksa tombol menyusun konten di dalamnya secara vertikal */
    [data-testid="stSidebar"] button {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #C9D1D9 !important;
        height: 60px !important;
        border-radius: 6px !important;
        margin-bottom: 6px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }

    [data-testid="stSidebar"] button p {
        font-size: 11px !important;
        font-weight: 600 !important;
        line-height: 1.3 !important;
        text-align: center !important;
        margin: 0 !important;
    }

    /* Styling saat hover */
    [data-testid="stSidebar"] button:hover {
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }
    </style>
    """
    st.markdown(sidebar_css, unsafe_allow_html=True)

    # Render di Sidebar
    with st.sidebar:
        for key, label, icon in nav_items:
            is_active = active_nav == key

            # Gabungkan ikon dan label dengan spasi biasa (bukan \n)
            button_label = f"{icon} {label}" if not is_active else f"► {icon} {label}"

            if st.button(button_label, key=f"nav_{key}", use_container_width=True):
                if st.session_state["active_nav"] != key:
                    st.session_state["active_nav"] = key
                    st.rerun()
