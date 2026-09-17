import streamlit as st


def render_top_nav():
    # Inject CSS untuk mengatur posisi tombol dan style ikon SVG
    st.markdown(
        """
        <style>
        /* Mendorong seluruh baris tombol ke bawah mendekati garis border */
        div[data-testid="stHorizontalBlock"]:has(button[key*="nav_"]) {
            align-items: flex-end !important;
            transform: translateY(25px) !important;
            margin-bottom: 0px !important;
        }

        /* Hilangkan margin bawaan tombol agar menempel dasar */
        button[key*="nav_"] {
            margin-bottom: 0px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 8px !important;
        }

        /* Utility style untuk SVG icon agar rapi di dalam button */
        .nav-icon {
            width: 16px;
            height: 16px;
            vertical-align: middle;
            display: inline-block;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Disesuaikan menjadi 4 kolom tombol + 1 kolom spacer kanan
    cols = st.columns([1, 1, 1.2, 1, 2.5])

    # 1. HOME (Dengan fitur Back to Default)
    with cols[0]:
        btn_home = st.button(
            "🏠 Home", key="nav_home", use_container_width=True
        )
        if btn_home:
            # Reset state menu/screener ke kondisi awal jika ada
            if "screener_mode" in st.session_state:
                st.session_state["screener_mode"] = "single"
            if "selected_page" in st.session_state:
                st.session_state["selected_page"] = "home"
            st.rerun()

    # 2. WATCHLIST
    with cols[1]:
        btn_watchlist = st.button(
            "📌 Watchlist", key="nav_watchlist", use_container_width=True
        )
        if btn_watchlist:
            # Siap dihubungkan ke file/logic watchlist baru
            st.session_state["selected_page"] = "watchlist"

    # 3. MONEY MANAGEMENT
    with cols[2]:
        btn_mm = st.button(
            "🛡️ Money Management", key="nav_mm", use_container_width=True
        )
        if btn_mm:
            # Siap dihubungkan ke file/logic money management baru
            st.session_state["selected_page"] = "money_management"

    # 4. HOW TO
    with cols[3]:
        btn_howto = st.button(
            "💡 How To", key="nav_howto", use_container_width=True
        )
        if btn_howto:
            # Siap dihubungkan ke file/logic panduan/tutorial baru
            st.session_state["selected_page"] = "how_to"
