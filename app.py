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

# 3. Header Bar dengan Dropdown Pilih Screener di Kanan Atas
col_brand, col_select = st.columns([2, 1], vertical_alignment="center")

with col_brand:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; padding: 5px 0;">
            <span style="font-size: 24px;">📈</span>
            <span style="color: #FFFFFF; font-size: 20px; font-weight: 700;">Zio - Screener</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_select:
    selected_screener = st.selectbox(
        "Choose Screener",
        options=[
            "1. RSI - Divergence",
            "2. Stoch - Psar",
            "3. Trade Plan - Batch Filter",
        ],
        index=0,
        key="screener_dropdown",
    )

st.markdown(
    "<hr style='margin-top: 5px; margin-bottom: 20px; border-color: #21262D;'>",
    unsafe_allow_html=True,
)

# 4. Render View Sesuai Pilihan Dropdown
if selected_screener == "1. RSI - Divergence":
    render_tab_rsi()
elif selected_screener == "2. Stoch - Psar":
    render_tab_stoch_psar()
elif selected_screener == "3. Trade Plan - Batch Filter":
    render_tab_trade_planner()
