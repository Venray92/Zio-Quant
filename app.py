import streamlit as st

# Import modul UI Views & Helper
from utils.ui_helpers import inject_custom_css
from views.header import render_header, render_header_divider, render_welcome
from views.top_nav import render_top_nav
from views.tab_rsi import render_tab_rsi
from views.tab_stoch_psar import render_tab_stoch_psar
from views.tab_trade_planner import render_tab_trade_planner

# Import modul halaman baru
from views.watchlist import render_page_watchlist
from views.money_management import (
    render_page_money_management,
)

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Z-QUANT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Inject Custom CSS bawaan
inject_custom_css()

# --- TAMBAHKAN CSS GLOBAL CYBERPUNK DI SINI AGAR KELIHATAN ---
st.markdown(
    """
    <style>
    /* 1. Styling Universal untuk Tombol di Horizontal Block (Home, Watchlist, dll) */
    div[data-testid="stHorizontalBlock"] .stButton button,
    .stButton button {
        background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%) !important;
        border: 1.5px solid #00F3FF !important;
        color: #00F3FF !important;
        border-radius: 8px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-weight: 700 !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stHorizontalBlock"] .stButton button:hover,
    .stButton button:hover {
        background: rgba(0, 243, 255, 0.2) !important;
        color: #ffffff !important;
        border-color: #FF007F !important;
        box-shadow: 0 0 18px rgba(255, 0, 127, 0.6) !important;
        transform: translateY(-1px) !important;
    }

    /* 2. Styling untuk Kotak Tombol CHOOSE SCREENER di Kanan Atas (Popover) */
    [data-testid="stPopover"] > button {
        background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%) !important;
        border: 1.5px solid #00F3FF !important;
        color: #00F3FF !important;
        border-radius: 8px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-weight: 700 !important;
        box-shadow: 0 0 12px rgba(0, 243, 255, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stPopover"] > button:hover {
        background: rgba(0, 243, 255, 0.2) !important;
        color: #ffffff !important;
        border-color: #FF007F !important;
        box-shadow: 0 0 20px rgba(255, 0, 127, 0.7) !important;
    }

    /* 3. Memastikan teks di dalam popover tombol screener tetap kontras */
    [data-testid="stPopoverBody"] .stButton button {
        background: #161B22 !important;
        border: 1px solid #00F3FF !important;
        color: #00F3FF !important;
    }
    [data-testid="stPopoverBody"] .stButton button:hover {
        border-color: #FF007F !important;
        color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# -------------------------------------------------------------

# 3. Inisialisasi Session State
if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "home"

if "selected_screener" not in st.session_state:
    st.session_state["selected_screener"] = None

if "active_screener_name" not in st.session_state:
    st.session_state["active_screener_name"] = "Screener"

# 4. Render Layout Atas (Header -> Top Nav -> Divider)
render_header()
render_top_nav()
render_header_divider()

# 5. Routing Utama Berdasarkan `selected_page`
page = st.session_state["selected_page"]

if page == "home":
    screener = st.session_state.get("selected_screener", None)

    if screener is None:
        render_welcome()
    elif screener == "rsi":
        st.session_state["active_screener_name"] = "RSI Screener"
        render_tab_rsi()
    elif screener == "stoch_psar":
        st.session_state["active_screener_name"] = "Stoch-Trend Radar"
        render_tab_stoch_psar()
    elif screener == "trade_plan":
        st.session_state["active_screener_name"] = "Trade Planner"
        render_tab_trade_planner()

elif page == "watchlist":
    render_page_watchlist()

elif page == "money_management":
    render_page_money_management()

elif page == "how_to":
    st.title("💡 How To")
    st.info("Halaman Panduan / Tutorial siap dihubungkan ke file baru.")
