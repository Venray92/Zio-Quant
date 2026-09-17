import streamlit as st


def render_sidebar_nav():
    """Sidebar Navigasi Ringkas Vertikal (Ikon di atas, teks di bawah) - Garansi Muncul."""

    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "screener"

    active_nav = st.session_state["active_nav"]

    # Definisi menu navigasi (Key, Label, Icon)
    nav_items = [
        ("screener", "Screener", "⚙️"),
        ("markets", "Markets", "📈"),
        ("stream", "Stream", "📡"),
        ("support", "Support", "🎧"),
    ]

    # CSS Global khusus Sidebar
    sidebar_css = """
    <style>
    /* Lebar Sidebar Ramping */
    [data-testid="stSidebar"] {
        min-width: 90px !important;
        max-width: 90px !important;
        background-color: #0D0E12 !important;
        border-right: 1px solid #1E222D !important;
    }

    /* Container tombol di sidebar */
    [data-testid="stSidebarUserContent"] {
        padding: 12px 6px !important;
    }

    /* Styling Universal Semua Tombol Sidebar */
    [data-testid="stSidebar"] button {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        color: #787B86 !important;
        font-family: sans-serif !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        height: 60px !important;
        width: 100% !important;
        border-radius: 6px !important;
        padding: 4px 0 !important;
        box-shadow: none !important;
    }

    /* Target isi teks di dalam tombol agar bertumpuk (Ikon atas, Teks bawah) */
    [data-testid="stSidebar"] button p {
        font-size: 11px !important;
        line-height: 1.2 !important;
        white-space: pre-line !important;
        text-align: center !important;
    }

    /* Hover State */
    [data-testid="stSidebar"] button:hover {
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.05) !important;
    }
    </style>
    """
    st.markdown(sidebar_css, unsafe_allow_html=True)

    # Render Tombol Langsung di Sidebar
    with st.sidebar:
        for key, label, icon in nav_items:
            is_active = active_nav == key

            # Format gabungan Ikon & Teks dengan Enter (\n)
            button_text = f"{icon}\n{label}"

            # Jika menu ini aktif, tampilkan penanda visual (misal diberi indikator penanda)
            if is_active:
                # Menggunakan simbol indicator aktif jika sedang terpilih
                button_text = f"{icon}\n● {label}"

            if st.button(button_text, key=f"nav_{key}", use_container_width=True):
                if st.session_state["active_nav"] != key:
                    st.session_state["active_nav"] = key
                    st.rerun()
