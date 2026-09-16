import streamlit as st

# Import modul UI Views & Helper
from utils.ui_helpers import inject_custom_css
from views.tab_rsi import render_tab_rsi
from views.tab_stoch_psar import render_tab_stoch_psar
from views.tab_trade_planner import render_tab_trade_planner

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Zio - Screener & Quant Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Inject Custom CSS (Dark Trading Theme)
inject_custom_css()

# 3. Header Aplikasi Pro (TradingView / Stockbit Style)
st.markdown(
    """
    <div class="zio-header-container">
        <div class="zio-brand">
            <span>📈</span>
            <span>Zio - Screener</span>
            <span class="badge-green" style="font-size: 11px; padding: 2px 8px; margin-left: 10px;">PRO QUANT</span>
        </div>
        <div style="display: flex; align-items: center; gap: 15px;">
            <span class="badge-info">⚡ RSI • STOCH • PSAR • TRADE PLANNER</span>
            <span class="badge-green">● IDX LIVE</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 4. Navigasi Tab Utama
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
