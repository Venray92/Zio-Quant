import streamlit as st

# Import modul UI Views & Helper
from utils.ui_helpers import inject_custom_css
from views.tab_rsi import render_tab_rsi
from views.tab_stoch_psar import render_tab_stoch_psar
from views.tab_trade_planner import render_tab_trade_planner

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Z - QUANT // SCREENER",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Inject Custom CSS
inject_custom_css()

# Inisialisasi session state (Default None = Home View)
if "selected_screener" not in st.session_state:
    st.session_state["selected_screener"] = None

# Custom CSS: Cyberpunk Aesthetic (Neon Cyan & Pink/Magenta)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

    .stApp {
        background-color: #030407 !important;
        color: #C0C5D0 !important;
        font-family: 'Share Tech Mono', monospace !important;
    }

    /* 1. Sembunyikan Top Bar Streamlit & Rapatkan Padding Atas */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    /* 2. Style Khusus Button Home (Logo + Brand) */
    div.btn-home-container div.stButton > button {
        background-color: #090B10 !important;
        border: 2px solid #FF0055 !important;
        border-radius: 0px !important;
        padding: 8px 16px !important;
        box-shadow: 0 0 15px rgba(255, 0, 85, 0.35) !important;
        height: auto !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.btn-home-container div.stButton > button:hover {
        border-color: #00F3FF !important;
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.5) !important;
        background-color: #0D101D !important;
    }

    /* 3. Trigger Popover Button */
    div[data-testid="stPopover"] > button {
        background-color: #090C15 !important;
        border: 1.5px solid #00F3FF !important;
        color: #00F3FF !important;
        border-radius: 0px !important;
        padding: 4px 14px !important;
        font-weight: 700 !important;
        font-family: 'Share Tech Mono', monospace !important;
        height: 48px !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.2) !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        transition: all 0.2s ease-in-out !important;
    }
    div[data-testid="stPopover"] > button:hover {
        background-color: #00F3FF !important;
        color: #000000 !important;
        border-color: #00F3FF !important;
        box-shadow: 0 0 18px #00F3FF !important;
    }

    /* 4. Popover Menu Content Styling */
    div[data-testid="stPopoverContent"] {
        background-color: #080A10 !important;
        border: 1px solid #FF0055 !important;
        box-shadow: 0 0 15px rgba(255, 0, 85, 0.3) !important;
        border-radius: 0px !important;
    }

    div[data-testid="stPopoverContent"] [data-testid="stVerticalBlock"] {
        gap: 4px !important;
    }
    div[data-testid="stPopoverContent"] [data-testid="stVerticalBlockBorderWrapper"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stPopoverContent"] div.stButton {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Button Item di Popover */
    div[data-testid="stPopoverContent"] div.stButton > button {
        width: 100% !important;
        text-align: left !important;
        padding: 6px 12px !important;
        min-height: 0px !important;
        height: 38px !important;
        border-radius: 0px !important;
        background-color: #0D101D !important;
        border: 1px solid #1E2338 !important;
        color: #C0C5D0 !important;
        font-size: 13px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-weight: 600 !important;
        margin: 0 !important;
        transition: all 0.15s ease-in-out !important;
    }

    div[data-testid="stPopoverContent"] div.stButton > button:hover {
        border-color: #00F3FF !important;
        color: #00F3FF !important;
        background-color: rgba(0, 243, 255, 0.1) !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.2) !important;
    }

    /* Status Active ketika button dipilih */
    div.btn-active div.stButton > button {
        background-color: rgba(255, 0, 85, 0.15) !important;
        border: 1.5px solid #FF0055 !important;
        color: #FF0055 !important;
        font-weight: 700 !important;
        box-shadow: 0 0 10px rgba(255, 0, 85, 0.3) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. Header Bar & Popover Menu di Kanan Atas
col_brand, col_popover = st.columns([2.5, 1], vertical_alignment="center")

with col_brand:
    st.markdown('<div class="btn-home-container">', unsafe_allow_html=True)
    if st.button("⚡ Z - QUANT // SCREENER", key="btn_go_home"):
        st.session_state["selected_screener"] = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with col_popover:
    with st.popover("🎛️ CHOOSE_SCREENER", use_container_width=True):
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 0 2px; font-family: 'Share Tech Mono', monospace;">
                <span style="color: #FF0055; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;">PRESET_SCREENER</span>
                <span style="color: #00F3FF; font-size: 10px; font-weight: 700;">3 AVAILABLE</span>
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
    "<hr style='margin-top: 10px; margin-bottom: 24px; border: 0; height: 1px; background: linear-gradient(90deg, #FF0055, #00F3FF, transparent);'>",
    unsafe_allow_html=True,
)

# 4. State Default Clean (Home) / Render Screener Terpilih
if st.session_state["selected_screener"] is None:
    st.markdown(
        """
        <div style="background-color: #080A12; border: 1px solid #00F3FF; box-shadow: 0 0 20px rgba(0, 243, 255, 0.15); padding: 70px 20px; text-align: center; margin-top: 10px; font-family: 'Share Tech Mono', monospace;">
            <div style="font-size: 3rem; margin-bottom: 10px; text-shadow: 0 0 10px #00F3FF;">⚡</div>
            <h2 style="color: #00F3FF; font-size: 24px; margin-bottom: 8px; text-shadow: 0 0 8px #00F3FF; font-weight: 900; letter-spacing: 2px;">
                WELCOME TO Z - QUANT TERMINAL
            </h2>
            <p style="color: #FF0055; font-size: 13px; max-width: 580px; margin: 0 auto 16px auto; letter-spacing: 1px;">
                // SYSTEM_READY: Select algorithmic screening strategy from <strong>🎛️ CHOOSE_SCREENER</strong> menu on the top-right corner.
            </p>
            <div style="display: inline-block; background: rgba(0, 243, 255, 0.05); border: 1px solid #00F3FF; color: #8A8B98; padding: 6px 16px; font-size: 11px;">
                STATUS: <span style="color: #00F3FF; font-weight: bold;">[ONLINE]</span> | ENGINE: <span style="color: #FF0055; font-weight: bold;">[QUANT_v2.0]</span>
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
