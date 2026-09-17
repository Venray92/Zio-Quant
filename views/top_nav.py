import streamlit as st


def render_top_nav():
    # Inject CSS untuk tata letak tombol dan animasi hover
    st.markdown(
        """
        <style>
        /* Mengatur kontainer tombol agar posisi rata bawah mendekati garis */
        div[data-testid="stHorizontalBlock"]:has(button[key*="nav_"]) {
            align-items: flex-end !important;
            transform: translateY(25px) !important;
            margin-bottom: 0px !important;
        }

        /* Styling dasar untuk tombol navigasi */
        button[key*="nav_"] {
            margin-bottom: 0px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 8px !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Inisialisasi state halaman jika belum ada
    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = "home"

    cols = st.columns([1, 1, 1.2, 1, 2.5])

    # 1. HOME (Back to Default)
    with cols[0]:
        btn_home = st.button("🏠 Home", key="nav_home", use_container_width=True)
        if btn_home:
            # Reset Halaman & Filter
            st.session_state["selected_page"] = "home"
            st.session_state["screener_mode"] = "single"
            st.session_state.pop("df_screener_single", None)
            st.session_state.pop("df_screener_batch", None)
            st.rerun()

    # 2. WATCHLIST
    with cols[1]:
        btn_watchlist = st.button("📌 Watchlist", key="nav_watchlist", use_container_width=True)
        if btn_watchlist:
            st.session_state["selected_page"] = "watchlist"
            st.rerun()

    # 3. MONEY MANAGEMENT
    with cols[2]:
        btn_mm = st.button("🛡️ Money Mgmt", key="nav_mm", use_container_width=True)
        if btn_mm:
            st.session_state["selected_page"] = "money_management"
            st.rerun()

    # 4. HOW TO
    with cols[3]:
        btn_howto = st.button("💡 How To", key="nav_howto", use_container_width=True)
        if btn_howto:
            st.session_state["selected_page"] = "how_to"
            st.rerun()
