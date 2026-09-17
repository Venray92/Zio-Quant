import streamlit as st


def render_sidebar_nav():
    """Menampilkan Navigasi Vertikal dengan Tombol Toggle Presisi di Tengah Garis Pembatas Kanan."""

    if "nav_collapsed" not in st.session_state:
        st.session_state["nav_collapsed"] = False

    is_collapsed = st.session_state["nav_collapsed"]
    active_nav = st.session_state.get("active_nav", "screener")

    # Lebar sidebar menyesuaikan status buka/tutup
    sidebar_width = "72px" if is_collapsed else "165px"

    nav_css = f"""
    <style>
    /* Kontainer utama sidebar dengan garis pembatas di sebelah kanan */
    .block-sidebar {{
        position: relative;
        background-color: #0D0E12;
        border-right: 2px solid #21262D;
        border-radius: 8px;
        padding: 16px 8px;
        width: {sidebar_width};
        min-height: 520px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        transition: width 0.25s ease-in-out;
    }}

    /* Styling Tombol Navigasi Utama (Ukuran pas, teks tidak terpotong) */
    .block-sidebar div.stButton > button {{
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
    }}

    .block-sidebar div.stButton > button:hover {{
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }}

    /* State Aktif (Glow Neon Green) */
    .btn-active div.stButton > button {{
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.15) !important;
        border: 1.5px solid #00FF66 !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.3) !important;
    }}

    /* TOMBOL TOGGLE: Mengambang tepat di tengah secara vertikal pada garis batas kanan */
    .sidebar-toggle-container {{
        position: absolute;
        top: 50%;
        right: -12px;
        transform: translateY(-50%);
        z-index: 999;
    }}

    .sidebar-toggle-container div.stButton > button {{
        background-color: #161B22 !important;
        border: 2px solid #30363D !important;
        color: #00FF66 !important;
        font-size: 15px !important;
        font-weight: 900 !important;
        height: 48px !important;
        width: 22px !important;
        min-width: 22px !important;
        padding: 0 !important;
        border-radius: 4px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.7) !important;
        transition: all 0.2s ease-in-out !important;
    }}

    .sidebar-toggle-container div.stButton > button:hover {{
        background-color: #00FF66 !important;
        color: #000000 !important;
        border-color: #00FF66 !important;
        box-shadow: 0 0 14px #00FF66 !important;
    }}
    </style>
    """
    st.markdown(nav_css, unsafe_allow_html=True)

    nav_items = [
        ("screener", "⚡ Screener"),
        ("markets", "📈 Markets"),
        ("stream", "📡 Stream"),
        ("support", "🎧 Support"),
    ]

    # Buka Kontainer Sidebar
    st.markdown('<div class="block-sidebar">', unsafe_allow_html=True)

    # Render Tombol Menu
    for key, label in nav_items:
        display_text = label[:2] if is_collapsed else label
        active_class = "btn-active" if active_nav == key else ""

        st.markdown(f'<div class="{active_class}">', unsafe_allow_html=True)
        if st.button(
            display_text, key=f"nav_btn_{key}", use_container_width=True
        ):
            st.session_state["active_nav"] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Tombol Toggle di Tengah Garis Pembatas
    toggle_icon = "›" if is_collapsed else "‹"
    st.markdown(
        '<div class="sidebar-toggle-container">', unsafe_allow_html=True
    )
    if st.button(
        toggle_icon, key="btn_sidebar_toggle", use_container_width=False
    ):
        st.session_state["nav_collapsed"] = not is_collapsed
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
