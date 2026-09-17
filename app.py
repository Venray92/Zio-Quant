import base64
import os
import streamlit as st


def get_logo_base64(file_path="logo.jpg"):
    """Konversi file logo ke format base64."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None


def render_header():
    """Menampilkan Header Bar, Navigasi Tab Utama, & Popover Menu Screener."""

    # Cek apakah ada query param reset dari klik logo/home
    if st.query_params.get("reset") == "true":
        st.session_state["selected_screener"] = None
        st.query_params.clear()
        st.rerun()

    # Init State navigasi utama jika belum ada
    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "screener"

    logo_b64 = get_logo_base64("logo.jpg")

    # Kolom 1: Logo, Kolom 2: Tab Navigasi Horizontal, Kolom 3: Dropdown Screener
    col_brand, col_nav, col_popover = st.columns(
        [1.5, 4, 1.5], vertical_alignment="center"
    )

    with col_brand:
        if logo_b64:
            logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" class="brand-logo-img" />'
        else:
            logo_html = '<span style="font-size: 32px;">⚡</span>'

        st.markdown(
            f"""
            <div class="brand-container" style="position: relative; z-index: 999999; pointer-events: auto;">
                <a href="/?reset=true" target="_self" class="brand-link" style="display: inline-flex; align-items: center; gap: 12px; text-decoration: none; cursor: pointer;">
                    {logo_html}
                    <span class="brand-title-text" style="cursor: pointer;">Z-QUANT</span>
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_nav:
        # Menampilkan 4 Tab Navigasi di bawah/samping logo
        t1, t2, t3, t4 = st.columns(4)
        active_nav = st.session_state["active_nav"]

        with t1:
            if st.button(
                "⚡ Screener",
                key="top_screener",
                use_container_width=True,
                type="primary" if active_nav == "screener" else "secondary",
            ):
                st.session_state["active_nav"] = "screener"
                st.rerun()

        with t2:
            if st.button(
                "📈 Markets",
                key="top_markets",
                use_container_width=True,
                type="primary" if active_nav == "markets" else "secondary",
            ):
                st.session_state["active_nav"] = "markets"
                st.rerun()

        with t3:
            if st.button(
                "📡 Stream",
                key="top_stream",
                use_container_width=True,
                type="primary" if active_nav == "stream" else "secondary",
            ):
                st.session_state["active_nav"] = "stream"
                st.rerun()

        with t4:
            if st.button(
                "🎧 Support",
                key="top_support",
                use_container_width=True,
                type="primary" if active_nav == "support" else "secondary",
            ):
                st.session_state["active_nav"] = "support"
                st.rerun()

    with col_popover:
        with st.popover("CHOOSE SCREENER", use_container_width=True):
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

    st.markdown(
        "<hr style='margin-top: 15px; margin-bottom: 24px; border: 0; height: 1px; background: linear-gradient(90deg, #00FF66, transparent);'>",
        unsafe_allow_html=True,
    )


def render_welcome():
    """Menampilkan tampilan Welcome Banner saat belum ada screener terpilih."""
    st.markdown(
        """
        <div style="background-color: #242424; border: 1px solid #00FF66; box-shadow: 0 0 20px rgba(0, 255, 102, 0.2); padding: 70px 20px; text-align: center; margin-top: 10px; font-family: 'Share Tech Mono', monospace;">
            <h2 style="color: #00FF66; font-size: 24px; margin-bottom: 8px; text-shadow: 0 0 10px #00FF66; font-weight: 900; letter-spacing: 2px;">
                WELCOME TO Z-QUANT TERMINAL
            </h2>
            <p style="color: #8A8B98; font-size: 13px; max-width: 580px; margin: 0 auto 16px auto; letter-spacing: 1px;">
                Pilih strategi screening saham IHSG di menu <strong style="color:#00FF66;">CHOOSE_SCREENER</strong> di pojok kanan atas untuk memulai analisis.
            </p>
            <div style="display: inline-block; background: rgba(0, 255, 102, 0.05); border: 1px solid #00FF66; color: #8A8B98; padding: 6px 16px; font-size: 11px;">
                STATUS: <span style="color: #00FF66; font-weight: bold; text-shadow: 0 0 5px #00FF66;">[ONLINE]</span> | ENGINE: <span style="color: #00F3FF; font-weight: bold;">[QUANT]</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
