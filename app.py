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
from views.money_management import render_page_money_management

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Z-QUANT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Inject Custom CSS dari assets/styleupdate.css
inject_custom_css()

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
