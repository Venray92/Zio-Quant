import streamlit as st

# Import modul UI Views & Helper
from utils.ui_helpers import inject_custom_css
from views.header import render_header, render_welcome
from views.sidebar_nav import render_sidebar_nav  # <-- MODUL BARU KITA
from views.tab_rsi import render_tab_rsi
from views.tab_stoch_psar import render_tab_stoch_psar
from views.tab_trade_planner import render_tab_trade_planner

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Z-QUANT",
    page_icon="⚡",
    layout="wide",
)

# 2. Inject Custom CSS Global
inject_custom_css()

# 3. Inisialisasi Session State
if "selected_screener" not in st.session_state:
    st.session_state["selected_screener"] = None

if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "screener"

# 4. Render Header Atas (Logo & Choose Screener Popover)
render_header()

# 5. TATA LETAK UTAMA: Navigasi Kiri (1) vs Konten Utama (15)
col_nav, col_main = st.columns([1, 15])

with col_nav:
    render_sidebar_nav()  # <-- CUKUP PANGGIL DI SINI

with col_main:
    nav = st.session_state.get("active_nav", "screener")
    screener = st.session_state.get("selected_screener")

    if nav == "screener":
        if screener is None:
            render_welcome()
        elif screener == "rsi":
            render_tab_rsi()
        elif screener == "stoch_psar":
            render_tab_stoch_psar()
        elif screener == "trade_plan":
            render_tab_trade_planner()

    elif nav == "markets":
        st.title("📈 MARKETS OVERVIEW")
        st.info("Halaman analisis pasar IHSG & Indeks Sektoral.")

    elif nav == "stream":
        st.title("📡 LIVE RADAR STREAM")
        st.info("Real-time signal feed & divergence alert.")

    elif nav == "support":
        st.title("🎧 SYSTEM SUPPORT")
        st.info("Panduan penggunaan Z-QUANT Terminal & Helpdesk.")
