import os
import sys

# Mendaftarkan Root Directory ke Python path secara eksplisit
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st

# Import modul UI Views
from views.tab_rsi import render_tab_rsi
from views.tab_stoch_psar import render_tab_stoch_psar
from views.tab_trade_planner import render_tab_trade_planner

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="ZIO QUANT - Screener & Trade Planner",
    page_icon="📈",
    layout="wide",
)

# 2. Header Aplikasi
st.title("📈 ZIO QUANT Dashboard")
st.markdown(
    "Aplikasi screening saham berbasis **RSI Divergence**, **Stochastic &"
    " Parabolic SAR**, serta kalkulator **Trade Planner** dengan Scoring System."
)

# 3. Navigasi Tab
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
