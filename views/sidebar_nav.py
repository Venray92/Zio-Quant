import streamlit as st


def render_sidebar_nav():
    """Sidebar Navigasi Standar dan Aman (Tanpa Error)."""

    # Init State dasar
    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "screener"

    active_nav = st.session_state["active_nav"]

    # Render menggunakan st.sidebar bawaan Streamlit secara bersih
    with st.sidebar:
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
            # Berikan indikator visual sederhana untuk menu yang aktif
            button_label = f"👉 {label}" if active_nav == key else label

            if st.button(button_label, key=f"nav_{key}", use_container_width=True):
                if st.session_state["active_nav"] != key:
                    st.session_state["active_nav"] = key
                    st.rerun()
