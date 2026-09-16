import streamlit as st

# Import modul UI Views & Helper
from utils.ui_helpers import inject_custom_css
from views.tab_rsi import render_tab_rsi
from views.tab_stoch_psar import render_tab_stoch_psar
from views.tab_trade_planner import render_tab_trade_planner

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Zio - Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Inject Custom CSS
inject_custom_css()

# 3. Header Clean & Minimalis
st.markdown(
    """
    <div class="zio-header-container">
        <div class="zio-brand">
            <span style="font-size: 22px;">📈</span>
            <span style="color: #FFFFFF; font-size: 20px; font-weight: 700;">Zio - Screener</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 4. Navigasi Tab
tab1, tab2, tab3 = st.tabs([
    "🔄 RSI Divergence",
    "⚡ Stochastic & Parabolic SAR",
    "🎯 Trade Planner & Batch Screener",
])

with tab1:
    render_tab_rsi()

with tab2:
    render_tab_stoch_psar()

with tab3:
    render_tab_trade_planner()
