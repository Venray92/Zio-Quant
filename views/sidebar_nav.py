import streamlit as st


def render_sidebar_nav():
    """Sidebar Navigasi Standar dengan Kontainer Berborder Merah."""

    # Init State dasar
    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "screener"

    active_nav = st.session_state["active_nav"]

    with st.sidebar:
        # CSS disuntikkan langsung di dalam sidebar menggunakan selector key 'sidebar_box'
        st.markdown(
            """
            <style>
            div[data-element-link-key="sidebar_box"],
            div[element-id="sidebar_box"],
            div:has(> div[data-testid="stVerticalBlock"] .element-container) {
                border: 2px solid #FF0000 !important;
                border-radius: 8px !important;
                padding: 15px !important;
                box-shadow: 0 0 10px rgba(255, 0, 0, 0.3) !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Kontainer khusus di sidebar
        with st.container(border=True, key="sidebar_box"):
            st.markdown("### 🧭 Navigation")
            st.markdown("---")

            # Daftar 4 menu utama
            nav_items = [
                ("screener", "⚡ Screener"),
                ("markets", "📈 Markets"),
                ("stream", "📡 Stream"),
                ("support", "🎧 Support"),
            ]

            for key, label in nav_items:
                # Indikator visual sederhana untuk menu yang aktif
                button_label = f"👉 {label}" if active_nav == key else label

                if st.button(
                    button_label, key=f"nav_{key}", use_container_width=True
                ):
                    if st.session_state["active_nav"] != key:
                        st.session_state["active_nav"] = key
                        st.rerun()
