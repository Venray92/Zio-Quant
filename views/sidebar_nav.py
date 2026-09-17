import streamlit as st


def render_sidebar_nav():
    """Sidebar Navigasi Ringkas Vertikal - Tanpa Memaksa Lebar CSS yang Merusak DOM."""

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

    # Style CSS murni untuk komponen di dalam sidebar
    sidebar_css = """
    <style>
    /* Ubah tampilan tombol di sidebar agar ikon & teks vertikal */
    [data-testid="stSidebar"] button {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #C9D1D9 !important;
        height: 60px !important;
        border-radius: 6px !important;
        margin-bottom: 4px !important;
    }

    /* Format teks dalam tombol agar bertumpuk */
    [data-testid="stSidebar"] button p {
        font-size: 12px !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
        white-space: pre-line !important;
        text-align: center !important;
    }

    /* Hover State */
    [data-testid="stSidebar"] button:hover {
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }
    </style>
    """
    st.markdown(sidebar_css, unsafe_allow_html=True)

    # Render Tombol di Sidebar
    with st.sidebar:
        st.caption("NAVIGASI")
        for key, label, icon in nav_items:
            is_active = active_nav == key

            # Jika aktif, tambahkan penanda visual dan ubah format teks
            button_text = f"{icon}\n{label}"
            if is_active:
                button_text = f"► {icon}\n{label}"

            if st.button(button_text, key=f"nav_{key}", use_container_width=True):
                if st.session_state["active_nav"] != key:
                    st.session_state["active_nav"] = key
                    st.rerun()
