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


def render_sidebar_nav():
    """Menampilkan 4 Navigasi Vertikal di Sidebar Kiri."""
    active_nav = st.session_state.get("active_nav", "screener")

    # SVG Icons Modern Outline
    svg_screener = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>'
    svg_markets = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'
    svg_stream = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9"></path><path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5"></path><circle cx="12" cy="12" r="2"></circle><path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5"></path><path d="M19.1 4.9c3.9 3.9 3.9 10.2 0 14.1"></path></svg>'
    svg_support = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 18v-6a9 9 0 0 1 18 0v6"></path><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"></path></svg>'

    nav_items = [
        ("screener", "Screener", svg_screener),
        ("markets", "Markets", svg_markets),
        ("stream", "Stream", svg_stream),
        ("support", "Support", svg_support),
    ]

    with st.sidebar:
        st.markdown('<div class="sidebar-wrapper">', unsafe_allow_html=True)
        for key, label, svg in nav_items:
            is_active = "active-nav" if active_nav == key else ""
            btn_label = f"{svg}<span>{label}</span>"

            st.markdown(f'<div class="nav-btn-box {is_active}">', unsafe_allow_html=True)
            if st.button(
                f"{label}",
                key=f"nav_btn_{key}",
                use_container_width=True,
            ):
                st.session_state["active_nav"] = key
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_header():
    """Menampilkan Header Bar & Popover Menu Screener."""

    # Render Sidebar Navigasi Kiri
    render_sidebar_nav()

    # Cek apakah ada query param reset dari klik logo/home
    if st.query_params.get("reset") == "true":
        st.session_state["selected_screener"] = None
        st.query_params.clear()
        st.rerun()

    logo_b64 = get_logo_base64("logo.jpg")

    col_brand, col_popover = st.columns([3, 1], vertical_alignment="center")

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
    """Menampilkan tampilan Welcome Banner saat belum mepilih screener."""
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
