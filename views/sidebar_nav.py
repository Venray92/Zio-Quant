import streamlit as st


def render_sidebar_nav():
    """Sidebar Navigasi di Luar Kontainer Utama, Nempel di Paling Kiri Layar."""

    if "nav_collapsed" not in st.session_state:
        st.session_state["nav_collapsed"] = False

    is_collapsed = st.session_state["nav_collapsed"]
    active_nav = st.session_state.get("active_nav", "screener")

    # Lebar sidebar saat terbuka vs tertutup
    sidebar_width = "70px" if is_collapsed else "175px"

    # CSS Fixed di sisi paling kiri luar layar (left: 10px) dengan garis border jelas di kanan
    nav_css = f"""
    <style>
    /* Sembunyikan elemen kolom pembawa lama jika ada, fokus ke sidebar fixed luar */
    .st-emotion-cache-12w0qpk, .st-emotion-cache-1r6slb0 {{
        gap: 0rem !important;
    }}

    /* Kontainer Sidebar Fixed Paling Kiri Luar */
    .outer-left-sidebar {{
        position: fixed !important;
        top: 85px !important;
        left: 12px !important;
        width: {sidebar_width} !important;
        background-color: #0D0E12 !important;
        border-right: 3px solid #00FF66 !important; /* Garis border hijau jelas di kanan */
        border-radius: 8px !important;
        padding: 14px 8px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 10px !important;
        z-index: 999999 !important;
        box-shadow: 6px 0 25px rgba(0, 0, 0, 0.8) !important;
        transition: width 0.2s ease-in-out !important;
    }}

    /* Styling Tombol Menu Navigasi */
    .outer-left-sidebar div.stButton > button {{
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #C9D1D9 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        height: 50px !important;
        width: 100% !important;
        border-radius: 6px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        padding-left: 12px !important;
        box-shadow: none !important;
        transition: all 0.2s ease-in-out !important;
    }}

    .outer-left-sidebar div.stButton > button:hover {{
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }}

    /* State Aktif (Glow Hijau) */
    .btn-active-menu div.stButton > button {{
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.15) !important;
        border: 1.5px solid #00FF66 !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.3) !important;
    }}

    /* Tombol Toggle persis di tengah garis border kanan */
    .outer-toggle-btn {{
        position: absolute !important;
        top: 50% !important;
        right: -17px !important;
        transform: translateY(-50%) !important;
        z-index: 1000000 !important;
    }}

    .outer-toggle-btn div.stButton > button {{
        background-color: #161B22 !important;
        border: 2px solid #00FF66 !important;
        color: #00FF66 !important;
        font-size: 14px !important;
        font-weight: 900 !important;
        height: 44px !important;
        width: 22px !important;
        min-width: 22px !important;
        padding: 0 !important;
        border-radius: 4px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.6) !important;
    }}

    .outer-toggle-btn div.stButton > button:hover {{
        background-color: #00FF66 !important;
        color: #000000 !important;
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

    # Render Sidebar di luar kontainer utama (Paling Kiri Layar)
    st.markdown('<div class="outer-left-sidebar">', unsafe_allow_html=True)

    for key, label in nav_items:
        display_text = label[:2] if is_collapsed else label
        active_class = "btn-active-menu" if active_nav == key else ""

        st.markdown(f'<div class="{active_class}">', unsafe_allow_html=True)
        if st.button(
            display_text, key=f"nav_btn_{key}", use_container_width=True
        ):
            st.session_state["active_nav"] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Tombol Toggle di tengah garis border kanan
    toggle_icon = "›" if is_collapsed else "‹"
    st.markdown('<div class="outer-toggle-btn">', unsafe_allow_html=True)
    if st.button(
        toggle_icon, key="btn_sidebar_toggle", use_container_width=False
    ):
        st.session_state["nav_collapsed"] = not is_collapsed
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
