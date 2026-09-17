import streamlit as st


def render_top_nav():
    # Inject CSS khusus untuk menurunkan tombol dan merapatkannya ke garis bawah
    st.markdown(
        """
        <style>
        /* Mengatur wrapper agar konten di dalamnya sejajar ke bawah */
        .dummy-nav-wrapper {
            margin-bottom: -15px; /* Narik seluruh wrapper ke bawah */
        }
        
        /* Memaksa elemen kolom Streamlit di dalam wrapper agar rata bawah */
        div[data-testid="stHorizontalBlock"]:has(button[key*="nav_"]) {
            align-items: flex-end !important;
            margin-bottom: -10px !important;
        }

        /* Mengurangi padding internal tombol agar posisi fisiknya turun mendekati garis */
        button[key*="nav_"] {
            margin-top: 15px !important; /* Dorong tombol dari atas ke bawah */
            margin-bottom: 0px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="dummy-nav-wrapper">', unsafe_allow_html=True)
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

    st.markdown("</div>", unsafe_allow_html=True)
