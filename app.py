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

# 3. Custom CSS Cyberpunk Neon Glow
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

    .stApp {
        background-color: #030407 !important;
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
       🎛️ POPOVER BUTTON MAIN (CHOOSE_SCREENER)
       Targeting semua kemungkinan kelas & elemen tombol popover
       ========================================================= */
    div[data-testid="stPopover"] > button,
    div[data-testid="stPopover"] button,
    div[data-testid="stPopover"] > button[aria-expanded] {
        background-color: #080a12 !important;
        border: 2px solid #00F3FF !important;
        color: #00F3FF !important;
        border-radius: 6px !important;
        padding: 6px 16px !important;
        font-weight: 800 !important;
        font-family: 'Share Tech Mono', monospace !important;
        height: 48px !important;
        /* Forced Neon Glow Cyan */
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.8), inset 0 0 10px rgba(0, 243, 255, 0.3) !important;
        text-shadow: 0 0 8px rgba(0, 243, 255, 0.9) !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        transition: all 0.25s ease-in-out !important;
    }

    /* Memastikan teks/icon di dalam tombol popover juga berwarna cyan */
    div[data-testid="stPopover"] button * {
        color: #00F3FF !important;
    }

    div[data-testid="stPopover"] > button:hover {
        background-color: #00F3FF !important;
        color: #000000 !important;
        border-color: #00F3FF !important;
        box-shadow: 0 0 25px #00F3FF, 0 0 12px #00F3FF !important;
        text-shadow: none !important;
    }

    div[data-testid="stPopover"] > button:hover * {
        color: #000000 !important;
    }

    /* Container Popover Dropdown */
    div[data-testid="stPopoverContent"] {
        background-color: #080A10 !important;
        border: 1.5px solid #00F3FF !important;
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.5) !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }

    div[data-testid="stPopoverContent"] [data-testid="stVerticalBlock"] {
        gap: 8px !important;
    }
    div[data-testid="stPopoverContent"] [data-testid="stVerticalBlockBorderWrapper"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stPopoverContent"] div.stButton {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* =========================================================
       ITEM BUTTONS INSIDE DROPDOWN (RSI, STOCH, TRADE PLAN)
       ========================================================= */
    div[data-testid="stPopoverContent"] div.stButton > button {
        width: 100% !important;
        text-align: left !important;
        padding: 8px 14px !important;
        min-height: 0px !important;
        height: 42px !important;
        border-radius: 6px !important;
        background-color: #0D101D !important;
        border: 1.5px solid #00F3FF !important;
        color: #00F3FF !important;
        font-size: 13px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-weight: 700 !important;
        margin: 0 !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.3) !important;
        text-shadow: 0 0 6px rgba(0, 243, 255, 0.7) !important;
        transition: all 0.2s ease-in-out !important;
    }

    div[data-testid="stPopoverContent"] div.stButton > button * {
        color: #00F3FF !important;
    }

    div[data-testid="stPopoverContent"] div.stButton > button:hover {
        border-color: #00F3FF !important;
        color: #000000 !important;
        background-color: #00F3FF !important;
        box-shadow: 0 0 18px #00F3FF !important;
        text-shadow: none !important;
    }

    div[data-testid="stPopoverContent"] div.stButton > button:hover * {
        color: #000000 !important;
    }

    /* Status Active (Screener Terpilih) */
    div.btn-active div.stButton > button {
        background-color: rgba(0, 243, 255, 0.2) !important;
        border: 2px solid #00F3FF !important;
        color: #00F3FF !important;
        font-weight: 800 !important;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.7), inset 0 0 10px rgba(0, 243, 255, 0.3) !important;
        text-shadow: 0 0 10px #00F3FF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 4. Header Bar (Logo + Z-QUANT berupa Tag Anchor <a>)
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
    with st.popover("🎛️ CHOOSE_SCREENER", use_container_width=True):
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 0 2px; font-family: 'Share Tech Mono', monospace;">
                <span style="color: #00F3FF; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; text-shadow: 0 0 5px #00F3FF;">PRESET_SCREENER</span>
                <span style="color: #00E676; font-size: 11px; font-weight: 800; text-shadow: 0 0 5px #00E676;">3 AVAILABLE</span>
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
            f"1. RSI - Divergence{badge_rsi}",
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
            f"2. Stoch - Psar{badge_stoch}",
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
            f"3. Trade Plan - Batch Filter{badge_tp}",
            key="btn_tp",
            use_container_width=True,
        ):
            st.session_state["selected_screener"] = "trade_plan"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    "<hr style='margin-top: 15px; margin-bottom: 24px; border: 0; height: 1px; background: linear-gradient(90deg, #00F3FF, transparent);'>",
    unsafe_allow_html=True,
)

# 5. Home View / Render Screener Terpilih
if st.session_state["selected_screener"] is None:
    st.markdown(
        """
        <div style="background-color: #080A12; border: 1px solid #00F3FF; box-shadow: 0 0 20px rgba(0, 243, 255, 0.15); padding: 70px 20px; text-align: center; margin-top: 10px; font-family: 'Share Tech Mono', monospace;">
            <h2 style="color: #00F3FF; font-size: 24px; margin-bottom: 8px; text-shadow: 0 0 8px #00F3FF; font-weight: 900; letter-spacing: 2px;">
                WELCOME TO Z-QUANT TERMINAL
            </h2>
            <p style="color: #8A8B98; font-size: 13px; max-width: 580px; margin: 0 auto 16px auto; letter-spacing: 1px;">
                Pilih strategi screening saham IHSG di menu <strong>🎛️ CHOOSE_SCREENER</strong> di pojok kanan atas untuk memulai analisis.
            </p>
            <div style="display: inline-block; background: rgba(0, 243, 255, 0.05); border: 1px solid #00F3FF; color: #8A8B98; padding: 6px 16px; font-size: 11px;">
                STATUS: <span style="color: #00E676; font-weight: bold;">[ONLINE]</span> | ENGINE: <span style="color: #00F3FF; font-weight: bold;">[QUANT_v2.0]</span>
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
