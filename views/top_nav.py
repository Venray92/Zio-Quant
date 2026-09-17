import streamlit as st


def render_top_nav():
    """Menampilkan 5 Button Dummy Navigasi ukuran ringkas & rapat di sebelah kiri."""

    # 5 kolom pertama untuk tombol dummy (lebar disesuaikan), 1 kolom sisa kosong
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
