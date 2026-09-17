import streamlit as st


def render_top_nav():
    """Menampilkan 5 Button Dummy Navigasi ukuran ringkas & rapat di sebelah kiri."""

    # Bungkus dalam container khusus agar styling CSS tidak hilang saat berpindah tab
    with st.container():
        st.markdown(
            '<div class="dummy-nav-wrapper">', unsafe_allow_html=True
        )

        cols = st.columns([0.85, 0.85, 0.85, 0.85, 0.85, 3])

        with cols[0]:
            st.button(
                "🌐 OVERVIEW", key="nav_overview", use_container_width=True
            )

        with cols[1]:
            st.button(
                "💼 PORTFOLIO", key="nav_portfolio", use_container_width=True
            )

        with cols[2]:
            st.button(
                "⭐ WATCHLIST", key="nav_watchlist", use_container_width=True
            )

        with cols[3]:
            st.button(
                "🔄 BACKTEST", key="nav_backtest", use_container_width=True
            )

        with cols[4]:
            st.button(
                "📊 ANALYTICS", key="nav_analytics", use_container_width=True
            )

        st.markdown("</div>", unsafe_allow_html=True)
