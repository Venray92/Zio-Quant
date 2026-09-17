import streamlit as st

# Import modul UI Views & Helper
from utils.ui_helpers import inject_custom_css
from views.header import render_header, render_welcome
from views.tab_rsi import render_tab_rsi
from views.tab_stoch_psar import render_tab_stoch_psar
from views.tab_trade_planner import render_tab_trade_planner

# 1. Konfigurasi Halaman Streamlit (Ubah initial_sidebar_state ke "expanded")
st.set_page_config(
    page_title="Z-QUANT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",  # <-- WAJIB EXPANDED AGAR SIDEBAR NAVIGASI KELIHATAN
)

# 2. Inject Custom CSS
inject_custom_css()

# 3. Inisialisasi Session State
if "selected_screener" not in st.session_state:
    st.session_state["selected_screener"] = None

if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "screener"

# 4. Render Header UI & Navigation Menu (Secara otomatis merender sidebar navigasi kiri)
render_header()

# 5. Routing Halaman Utama Berdasarkan Navigation & Screener
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
