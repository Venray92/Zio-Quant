import streamlit as st


def render_top_nav():
    # Inject CSS langsung menyasar tombol navigasi
    st.markdown(
        """
        <style>
        /* Dorong container kolom tempat tombol berada ke bawah */
        div[data-testid="stHorizontalBlock"]:has(button[key*="nav_"]) {
            align-items: flex-end !important;
            transform: translateY(18px) !important; /* Mendorong seluruh baris tombol ke bawah */
            margin-bottom: 0px !important;
        }

        /* Hilangkan margin/padding bawaan tombol agar menempel dasar */
        button[key*="nav_"] {
            margin-bottom: 0px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns([0.85, 0.85, 0.85, 0.85, 0.85, 3])

    with cols[0]:
        st.button("🌐 OVERVIEW", key="nav_overview", use_container_width=True)
    with cols[1]:
        st.button("💼 PORTFOLIO", key="nav_portfolio", use_container_width=True)
    with cols[2]:
        st.button("⭐ WATCHLIST", key="nav_watchlist", use_container_width=True)
    with cols[3]:
        st.button("🔄 BACKTEST", key="nav_backtest", use_container_width=True)
    with cols[4]:
        st.button("📊 ANALYTICS", key="nav_analytics", use_container_width=True)
