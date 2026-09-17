import streamlit as st


def render_sidebar_nav():
    """Sidebar Navigasi Ringkas (Ikon + Teks Vertikal) dengan Fitur Collapse."""

    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "screener"

    active_nav = st.session_state["active_nav"]

    sidebar_css = """
    <style>
    /* 1. Atur Lebar Sidebar agar Ringkas Mirip TradingView */
    [data-testid="stSidebar"] {
        min-width: 85px !important;
        max-width: 85px !important;
        background-color: #0D0E12 !important;
        border-right: 1px solid #1E222D !important;
    }

    /* Padding Kontainer Dalam Sidebar */
    [data-testid="stSidebarUserContent"] {
        padding: 10px 6px !important;
    }

    /* 2. Style Dasar Semua Tombol Navigasi */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent !important;
        border: none !important;
        color: #787B86 !important;
        font-family: 'Share Tech Mono', monospace, sans-serif !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        height: 65px !important;
        width: 100% !important;
        border-radius: 6px !important;
        
        /* Layout Vertikal: Ikon di Atas, Teks di Bawah */
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 4px !important;
        padding: 4px 0px !important;
        white-space: pre-line !important; /* Agar \n membuat baris baru */
        line-height: 1.2 !important;
        box-shadow: none !important;
    }

    /* Hover Effect */
    [data-testid="stSidebar"] div.stButton > button:hover {
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.05) !important;
    }

    /* 3. Style Khusus untuk Tombol yang Sedang Aktif */
    /* Targetkan tombol berdasarkan key yang aktif */
    </style>
    """

    # Buat CSS Dinamis untuk Menandai Menu Aktif dengan Indikator Hijau
    active_css = f"""
    <style>
    [data-testid="stSidebar"] div.stButton > button[key="nav_btn_{active_nav}"] {{
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.1) !important;
        border-left: 3px solid #00FF66 !important;
        border-radius: 0px 6px 6px 0px !important;
    }}
    </style>
    """

    st.markdown(sidebar_css + active_css, unsafe_allow_html=True)

    # Item Navigasi: format label menggunakan '\n' agar Ikon di Atas & Teks di Bawah
    nav_items = [
        ("screener", "⚙️\nScreener"),
        ("markets", "📈\nMarkets"),
        ("stream", "📡\nStream"),
        ("support", "🎧\nSupport"),
    ]

    # Render Komponen Langsung di Dalam Sidebar
    with st.sidebar:
        for key, label in nav_items:
            if st.button(
                label,
                key=f"nav_btn_{key}",
                use_container_width=True,
            ):
                if st.session_state["active_nav"] != key:
                    st.session_state["active_nav"] = key
                    st.rerun()
