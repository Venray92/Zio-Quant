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
    """Menampilkan Header Bar & Popover Menu Screener."""
    logo_b64 = get_logo_base64("logo.jpg")

    col_brand, col_popover = st.columns([3, 1], vertical_alignment="center")

    with col_brand:
        if logo_b64:
            logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" class="brand-logo-img" style="vertical-align: middle; margin-right: 8px;" />'
        else:
            logo_html = '<span style="font-size: 24px; vertical-align: middle; margin-right: 8px;">⚡</span>'

        # Label kombinasi Logo + Teks Brand
        button_label = f"{logo_html}<span class='brand-title-text' style='vertical-align: middle;'>Z-QUANT</span>"

        # Tombol Home Native Streamlit (Aman dari bug click & mereset state screener ke Home)
        if st.button(
            button_label,
            key="btn_home_brand",
            type="tertiary",
            use_container_width=False,
        ):
            st.session_state["selected_screener"] = None
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
