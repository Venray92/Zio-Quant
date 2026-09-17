import base64
import os
import streamlit as st

# Import modul UI Views & Helper
from utils.ui_helpers import inject_custom_css
from views.tab_rsi import render_tab_rsi
from views.tab_stoch_psar import render_tab_stoch_psar
from views.tab_trade_planner import render_tab_trade_planner

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Z-QUANT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Inject Custom CSS
inject_custom_css()

# Inisialisasi session state
if "selected_screener" not in st.session_state:
    st.session_state["selected_screener"] = None


# Helper untuk konversi logo.jpg ke Base64
def get_logo_base64(file_path="logo.jpg"):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None


logo_b64 = get_logo_base64("logo.jpg")

# 3. Custom CSS (Background Abu Gelap #1A1A1A + Cyberpunk Neon Green #00FF66)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

    /* BACKGROUND UTAMA APLIKASI (ABU GELAP) */
    .stApp {
        background-color: #1A1A1A !important;
        color: #C0C5D0 !important;
        font-family: 'Share Tech Mono', monospace !important;
    }

    /* Sembunyikan Top Bar Streamlit */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    /* Link Brand (Logo + Teks) */
    .brand-link {
        display: inline-flex;
        align-items: center;
        gap: 14px;
        text-decoration: none !important;
        cursor: pointer;
        transition: opacity 0.2s ease-in-out;
    }
    .brand-link:hover {
        opacity: 0.8;
    }

    .brand-logo-img {
        width: 55px;
        height: 55px;
        border-radius: 8px;
        object-fit: cover;
        border: 1.5px solid #00F3FF;
        box-shadow: 0 0 12px rgba(0, 243, 255, 0.4);
    }

    .brand-title-text {
        color: #00F3FF;
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 1px;
        text-shadow: 0 0 10px rgba(0, 243, 255, 0.6);
        font-family: 'Share Tech Mono', monospace;
    }

    /* =========================================================
       🟢 MAIN POPOVER BUTTON (CHOOSE_SCREENER)
       ========================================================= */
    div[data-testid="stPopover"] > button {
        background-color: #242424 !important;
        border: 2px solid #00FF66 !important;
        border-radius: 8px !important;
        padding: 6px 16px !important;
        height: 48px !important;
        box-shadow: 0 0 15px #00FF66, inset 0 0 8px rgba(0, 255, 102, 0.4) !important;
        transition: all 0.2s ease-in-out !important;
    }

    div[data-testid="stPopover"] > button *,
    div[data-testid="stPopover"] > button p {
        color: #00FF66 !important;
        font-weight: 900 !important;
        font-family: 'Share Tech Mono', monospace !important;
        text-shadow: 0 0 8px #00FF66 !important;
        letter-spacing: 1px !important;
    }

    div[data-testid="stPopover"] > button:hover {
        background-color: #00FF66 !important;
        box-shadow: 0 0 25px #00FF66 !important;
    }

    div[data-testid="stPopover"] > button:hover *,
    div[data-testid="stPopover"] > button:hover p {
        color: #000000 !important;
        text-shadow: none !important;
    }

    /* Container Popover Dropdown */
    div[data-testid="stPopoverContent"] {
        background-color: #242424 !important;
        border: 2px solid #00FF66 !important;
        box-shadow: 0 0 25px rgba(0, 255, 102, 0.5) !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }

    /* =========================================================
       🟢 TOMBOL ITEM 1, 2, 3 DI DALAM DROPDOWN (FORCED BORDER & GLOW)
       ========================================================= */
    div[data-testid="stPopoverContent"] button {
        background-color: #1E1E1E !important;
        border: 1.5px solid #00FF66 !important;
        border-radius: 6px !important;
        margin: 4px 0 !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.4), inset 0 0 5px rgba(0, 255, 102, 0.2) !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* Paksa teks di dalam tombol 1-3 berwarna Hijau Neon */
    div[data-testid="stPopoverContent"] button *,
    div[data-testid="stPopoverContent"] button p,
    div[data-testid="stPopoverContent"] button span {
        color: #00FF66 !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-weight: 800 !important;
        text-shadow: 0 0 6px #00FF66 !important;
    }

    /* Hover Effect Tombol 1-3 */
    div[data-testid="stPopoverContent"] button:hover {
        background-color: #00FF66 !important;
        border-color: #00FF66 !important;
        box-shadow: 0 0 20px #00FF66 !important;
    }

    div[data-testid="stPopoverContent"] button:hover *,
    div[data-testid="stPopoverContent"] button:hover p,
    div[data-testid="stPopoverContent"] button:hover span {
        color: #000000 !important;
        text-shadow: none !important;
    }

    /* State Aktif (Tombol Terpilih) */
    div.btn-active button {
        background-color: rgba(0, 255, 102, 0.25) !important;
        border: 2px solid #00FF66 !important;
        box-shadow: 0 0 18px #00FF66, inset 0 0 8px rgba(0, 255, 102, 0.6) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 4. Header Bar (Logo + Z-QUANT)
col_brand, col_popover = st.columns([3, 1], vertical_alignment="center")

with col_brand:
    if logo_b64:
        logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" class="brand-logo-img" />'
    else:
        logo_html = '<span style="font-size: 32px;">⚡</span>'

    st.markdown(
        f"""
        <a href="/" target="_self" class="brand-link">
            {logo_html}
            <span class="brand-title-text">Z-QUANT</span>
        </a>
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

        curr = st.session_state["selected_screener"]

        # Button 1: RSI - Divergence
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

        # Button 2: Stoch - Psar
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

        # Button 3: Trade Plan - Batch Filter
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

# 5. Home View / Render Screener Terpilih
if st.session_state["selected_screener"] is None:
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
elif st.session_state["selected_screener"] == "rsi":
    render_tab_rsi()
elif st.session_state["selected_screener"] == "stoch_psar":
    render_tab_stoch_psar()
elif st.session_state["selected_screener"] == "trade_plan":
    render_tab_trade_planner()
