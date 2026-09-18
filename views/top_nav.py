import streamlit as st


def render_top_nav():
    # Inject CSS untuk mengatur posisi tombol dan margin bawah
    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"]:has(button[key*="nav_"]) {
            align-items: flex-end !important;
            transform: translateY(22px) !important;
            margin-bottom: 0px !important;
        }

        button[key*="nav_"] {
            margin-bottom: 0px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 8px !important;
            font-weight: 600 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns([1, 1, 1.2, 1, 2.5])

    # 1. HOME (Reset Total Tampilan Kembali ke Welcome Screen)
    with cols[0]:
        if st.button("Home", key="nav_home", use_container_width=True):
            st.session_state["selected_page"] = "home"
            st.session_state["selected_screener"] = None
            st.rerun()

    # 2. WATCHLIST (Reset screener agar status active hilang)
    with cols[1]:
        if st.button("Watchlist", key="nav_watchlist", use_container_width=True):
            st.session_state["selected_page"] = "watchlist"
            st.session_state["selected_screener"] = None  # <-- RESET SCREENER
            st.rerun()

    # 3. MONEY MANAGEMENT (Reset screener agar status active hilang)
    with cols[2]:
        if st.button("Money Management", key="nav_mm", use_container_width=True):
            st.session_state["selected_page"] = "money_management"
            st.session_state["selected_screener"] = None  # <-- RESET SCREENER
            st.rerun()

    # 4. HOW TO (Reset screener agar status active hilang)
    with cols[3]:
        if st.button("How To", key="nav_howto", use_container_width=True):
            st.session_state["selected_page"] = "how_to"
            st.session_state["selected_screener"] = None  # <-- RESET SCREENER
            st.rerun()
