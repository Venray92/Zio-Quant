import streamlit as st

# Import modul UI Views & Helper
from utils.ui_helpers import inject_custom_css
from views.header import render_header, render_header_divider, render_welcome
from views.top_nav import render_top_nav
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

# 3. Inisialisasi Session State
if "selected_screener" not in st.session_state:
    st.session_state["selected_screener"] = None

# 4. Render Layout Atas (Header -> Top Nav -> Divider)
render_header()
render_top_nav()
render_header_divider()

# 5. Routing Halaman Berdasarkan Screener Terpilih
screener = st.session_state["selected_screener"]

if screener is None:
    render_welcome()
elif screener == "rsi":
    render_tab_rsi()
elif screener == "stoch_psar":
    render_tab_stoch_psar()
elif screener == "trade_plan":
    render_tab_trade_planner()
