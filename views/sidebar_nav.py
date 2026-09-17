import streamlit as st


def render_sidebar_nav():
    """Sidebar Navigasi di Kiri Luar Layar (Fixed Positioning) dengan Garis Border di Kanan."""

    if "nav_collapsed" not in st.session_state:
        st.session_state["nav_collapsed"] = False

    is_collapsed = st.session_state["nav_collapsed"]
    active_nav = st.session_state.get("active_nav", "screener")

    # Lebar sidebar saat terbuka vs tertutup
    sidebar_width = "70px" if is_collapsed else "180px"

    # CSS Fixed Positioning agar sidebar benar-benar berada di luar kontainer utama (di kiri layar)
    nav_css = f"""
    <style>
    /* Kontainer Sidebar Fixed di Kiri Mentok Luar */
    .fixed-left-sidebar {{
        position: fixed;
        top: 80px; /* Jarak dari atas (di bawah header/logo) */
        left: 20px; /* Jarak dari sisi paling kiri layar */
        width: {sidebar_width};
        background-color: #0D0E12;
        border-right: 3px solid #00FF66 !important; /* Garis border jelas di kanan */
        border-radius: 8px;
        padding: 14px 8px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        z-index: 99999;
        box-shadow: 5px 0 20px rgba(0, 0, 0, 0.6);
        transition: width 0.2s ease-in-out;
    }}

    /* Styling Tombol Menu Navigasi */
    .fixed-left-sidebar div.stButton > button {{
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

    .fixed-left-sidebar div.stButton > button:hover {{
        color: #00FF66 !important;
        border-color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.08) !important;
    }}

    /* State Aktif (Glow Neon Green) */
    .btn-active-menu div.stButton > button {{
        color: #00FF66 !important;
        background-color: rgba(0, 255, 102, 0.15) !important;
        border: 1.5px solid #00FF66 !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.3) !important;
    }}

    /* Tombol Toggle persis di tengah garis border kanan */
    .fixed-toggle-btn {{
        position: absolute;
        top: 50%;
        right: -17px;
        transform: translateY(-50%);
        z-index: 100000;
    }}

    .fixed-toggle-btn div.stButton > button {{
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

    .fixed-toggle-btn div.stButton > button:hover {{
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

    # Render kontainer utama sidebar di luar aliran normal layout
    st.markdown('<div class="fixed-left-sidebar">', unsafe_allow_html=True)

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
    st.markdown('<div class="fixed-toggle-btn">', unsafe_allow_html=True)
    if st.button(
        toggle_icon, key="btn_sidebar_toggle", use_container_width=False
    ):
        st.session_state["nav_collapsed"] = not is_collapsed
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
