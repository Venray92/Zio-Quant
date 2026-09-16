import os
import sys

# Mendaftarkan direktori utama ke Python Path secara eksplisit
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# Import modul UI Views
from views.tab_rsi import render_tab_rsi
from views.tab_stoch_psar import render_tab_stoch_psar
from views.tab_trade_planner import render_tab_trade_planner

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="ZIO QUANT - Screener & Trade Planner",
    page_icon="📈",
    layout="wide",
)

# Header Aplikasi
st.title("📈 ZIO QUANT Dashboard")
st.markdown(
    "Aplikasi screening saham berbasis **RSI Divergence**, **Stochastic &"
    " Parabolic SAR**, serta kalkulator **Trade Planner** dengan Scoring System."
)

# Navigasi Tab
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
