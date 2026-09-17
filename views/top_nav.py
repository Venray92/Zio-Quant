import streamlit as st


def render_top_nav():
    """Menampilkan 5 Button Dummy Navigasi di bawah header, tepat di atas garis pembatas."""

    cols = st.columns(5)

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
