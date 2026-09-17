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
    """Menampilkan Header Bar (Logo di kiri, CHOOSE SCREENER di kanan)."""

    # Cek query param reset dari logo
    if st.query_params.get("reset") == "true":
        st.session_state["selected_screener"] = None
        st.session_state["selected_page"] = "home"
        st.query_params.clear()
        st.rerun()

    logo_b64 = get_logo_base64("logo.jpg")

    if logo_b64:
        logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" class="brand-logo-img" />'
    else:
        logo_html = '<span style="font-size: 32px;">⚡</span>'

    # Layout Header: Logo (Kiri) & Popover (Kanan)
    col_brand, col_popover = st.columns([3, 1])

    with col_brand:
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
        with st.popover("CHOOSE SCREENER ▾", use_container_width=True):
            st.markdown(
                """
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 0 2px; font-family: 'Share Tech Mono', monospace;">
                    <span style="color: #00F3FF; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; text-shadow: 0 0 8px #00F3FF;">PRESET_SCREENER</span>
                    <span style="color: #00F3FF; font-size: 11px; font-weight: 800; text-shadow: 0 0 8px #00F3FF;">3 AVAILABLE</span>
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
                st.session_state["selected_page"] = "home"  # FORCE KE HOME PAGE
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
                st.session_state["selected_page"] = "home"  # FORCE KE HOME PAGE
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
                st.session_state["selected_page"] = "home"  # FORCE KE HOME PAGE
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def render_header_divider():
    """Menampilkan garis pembatas hijau neon di bawah top navigation."""
    st.markdown(
        "<hr style='margin-top: 8px; margin-bottom: 24px; border: 0; height: 1px; background: linear-gradient(90deg, #00F3FF, transparent);'>",
        unsafe_allow_html=True,
    )


def render_welcome():
    """Menampilkan tampilan Welcome Banner saat belum ada screener terpilih."""
    st.markdown(
        """
        <div style="background-color: #242424; border: 1px solid #00F3FF; box-shadow: 0 0 20px rgba(0, 243, 255, 0.2); padding: 70px 20px; text-align: center; margin-top: 10px; font-family: 'Share Tech Mono', monospace;">
            <h2 style="color: #00F3FF; font-size: 24px; margin-bottom: 8px; text-shadow: 0 0 10px #00F3FF; font-weight: 900; letter-spacing: 2px;">
                WELCOME TO Z-QUANT TERMINAL
            </h2>
            <p style="color: #8A8B98; font-size: 13px; max-width: 580px; margin: 0 auto 16px auto; letter-spacing: 1px;">
                Pilih strategi screening saham IHSG di menu <strong style="color:#00F3FF;">CHOOSE_SCREENER</strong> di pojok kanan atas untuk memulai analisis.
            </p>
            <div style="display: inline-block; background: rgba(0, 243, 255, 0.05); border: 1px solid #00F3FF; color: #8A8B98; padding: 6px 16px; font-size: 11px;">
                STATUS: <span style="color: #00F3FF; font-weight: bold; text-shadow: 0 0 5px #00F3FF;">[ONLINE]</span> | ENGINE: <span style="color: #00F3FF; font-weight: bold;">[QUANT]</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
