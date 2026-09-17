import streamlit as st

def render_top_nav():
    """
    Render navigasi tab horizontal tepat di bawah header.
    Mengembalikan key menu yang sedang aktif.
    """
    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "screener"

    active_nav = st.session_state["active_nav"]

    # Buat 4 kolom presisi di area utama
    col1, col2, col3, col4, _ = st.columns([1.5, 1.5, 1.5, 1.5, 4])

    with col1:
        if st.button(
            "⚡ Screener",
            key="topnav_screener",
            use_container_width=True,
            type="primary" if active_nav == "screener" else "secondary"
        ):
            st.session_state["active_nav"] = "screener"
            st.rerun()

    with col2:
        if st.button(
            "📈 Markets",
            key="topnav_markets",
            use_container_width=True,
            type="primary" if active_nav == "markets" else "secondary"
        ):
            st.session_state["active_nav"] = "markets"
            st.rerun()

    with col3:
        if st.button(
            "📡 Stream",
            key="topnav_stream",
            use_container_width=True,
            type="primary" if active_nav == "stream" else "secondary"
        ):
            st.session_state["active_nav"] = "stream"
            st.rerun()

    with col4:
        if st.button(
            "🎧 Support",
            key="topnav_support",
            use_container_width=True,
            type="primary" if active_nav == "support" else "secondary"
        ):
            st.session_state["active_nav"] = "support"
            st.rerun()

    return st.session_state["active_nav"]