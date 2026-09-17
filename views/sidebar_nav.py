import streamlit as st


def render_sidebar_nav():
    """Sidebar Navigasi Standar dengan Kontainer Berborder Merah."""

    # CSS khusus untuk mengubah border kontainer di sidebar menjadi warna merah
    st.markdown(
        """
        <style>
        /* Styling kontainer di sidebar agar border berwarna merah */
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #FF0000 !important;
            border-radius: 8px !important;
            padding: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Init State dasar
    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "screener"

    active_nav = st.session_state["active_nav"]

    # Render menggunakan st.sidebar
    with st.sidebar:
        # Membungkus elemen navigasi ke dalam container ber-border
        with st.container(border=True):
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
