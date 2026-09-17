import streamlit as st


def render_top_nav():
    """Menampilkan Top Navigation Bar dengan 5 Dummy Buttons dan Popover Screener di Kanan."""

    # Kolom layout: 5 kolom dummy di kiri, 1 kolom popover screener di kanan
    col1, col2, col3, col4, col5, col_popover = st.columns(
        [1.2, 1.1, 1.1, 1.1, 1.1, 1.8]
    )

    with col1:
        st.button("🌐 OVERVIEW", key="nav_overview", use_container_width=True)

    with col2:
        st.button("💼 PORTFOLIO", key="nav_portfolio", use_container_width=True)

    with col3:
        st.button("⭐ WATCHLIST", key="nav_watchlist", use_container_width=True)

    with col4:
        st.button("🔄 BACKTEST", key="nav_backtest", use_container_width=True)

    with col5:
        st.button("📊 ANALYTICS", key="nav_analytics", use_container_width=True)

    with col_popover:
        with st.popover("CHOOSE SCREENER ▾", use_container_width=True):
            st.markdown(
                """
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 0 2px; font-family: 'Share Tech Mono', monospace;">
                    <span style="color: #00FF66; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; text-shadow: 0 0 8px #00FF66;">PRESET_SCREENER</span>
                    <span style="color: #00FF66; font-size: 11px; font-weight: 800; text-shadow: 0 0 8px #00FF66;">3 AVAILABLE</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            curr = st.session_state.get("selected_screener")

            # 1. RSI Matrix
            cls_rsi = "btn-active" if curr == "rsi" else ""
            badge_rsi = " [ACTIVE] ✔" if curr == "rsi" else ""
            st.markdown(f'<div class="{cls_rsi}">', unsafe_allow_html=True)
            if st.button(
                f"1. RSI MATRIX{badge_rsi}",
                key="btn_rsi",
                use_container_width=True,
            ):
                st.session_state["selected_screener"] = "rsi"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            # 2. Stoch Radar
            cls_stoch = "btn-active" if curr == "stoch_psar" else ""
            badge_stoch = " [ACTIVE] ✔" if curr == "stoch_psar" else ""
            st.markdown(f'<div class="{cls_stoch}">', unsafe_allow_html=True)
            if st.button(
                f"2. STOCH-TREND RADAR{badge_stoch}",
                key="btn_stoch",
                use_container_width=True,
            ):
                st.session_state["selected_screener"] = "stoch_psar"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            # 3. Trade Plan Entry
            cls_tp = "btn-active" if curr == "trade_plan" else ""
            badge_tp = " [ACTIVE] ✔" if curr == "trade_plan" else ""
            st.markdown(f'<div class="{cls_tp}">', unsafe_allow_html=True)
            if st.button(
                f"3. TRADE PLAN ENTRY{badge_tp}",
                key="btn_tp",
                use_container_width=True,
            ):
                st.session_state["selected_screener"] = "trade_plan"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
