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

# Inisialisasi session state untuk screener aktif
if "selected_screener" not in st.session_state:
    st.session_state["selected_screener"] = "stoch_psar"

# Styling khusus untuk Custom Dropdown Popover ala TradingView/Stockbit
st.markdown(
    """
    <style>
    /* Styling tombol trigger popover di pojok kanan */
    div[data-testid="stPopover"] > button {
        background-color: #0E1117 !important;
        border: 1.5px solid #00E676 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        padding: 6px 16px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stPopover"] > button:hover {
        background-color: #0D2B1D !important;
        box-shadow: 0 0 10px rgba(0, 230, 118, 0.2) !important;
    }
    
    /* Styling Card di dalam Menu Popover */
    .screener-card {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        border: 1px solid #21262D;
        background-color: #161B22;
    }
    .screener-card-active {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        border: 1.5px solid #00E676;
        background-color: #0D2B1D;
    }
    .badge-active {
        background-color: #00E676;
        color: #0E1117;
        font-size: 10px;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. Header Bar & Popover Menu di Kanan Atas
col_brand, col_popover = st.columns([2.5, 1], vertical_alignment="center")

with col_brand:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 24px;">📈</span>
            <span style="color: #FFFFFF; font-size: 20px; font-weight: 700;">Zio - Screener</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_popover:
    # Popover Custom Menu pengganti selectbox biasa
    with st.popover("⚙️ Choose Screener", use_container_width=True):
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="color: #8B949E; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;">PRESET SCREENER</span>
                <span style="color: #00E676; font-size: 11px; font-weight: 700;">3 AVAILABLE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        curr = st.session_state["selected_screener"]

        # Option 1: Stoch - Psar
        card_class = "screener-card-active" if curr == "stoch_psar" else "screener-card"
        active_badge = '<span class="badge-active">Active</span>' if curr == "stoch_psar" else ""
        check_icon = " ✔️" if curr == "stoch_psar" else ""

        st.markdown(
            f"""
            <div class="{card_class}">
                <div style="font-weight: 700; color: #FFFFFF; font-size: 14px;">
                    📈 1. Stoch – Psar {active_badge} <span style="float: right; color: #00E676;">{check_icon}</span>
                </div>
                <div style="color: #8B949E; font-size: 11px; margin-top: 4px;">
                    Stoch (10,5,5) GC (0–2 Hari) & Psar Dead Cross (0 Hari)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Pilih Stoch - Psar", key="btn_sel_stoch", use_container_width=True):
            st.session_state["selected_screener"] = "stoch_psar"
            st.rerun()

        st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)

        # Option 2: RSI + Pattern
        card_class = "screener-card-active" if curr == "rsi" else "screener-card"
        active_badge = '<span class="badge-active">Active</span>' if curr == "rsi" else ""
        check_icon = " ✔️" if curr == "rsi" else ""

        st.markdown(
            f"""
            <div class="{card_class}">
                <div style="font-weight: 700; color: #FFFFFF; font-size: 14px;">
                    📈 2. RSI + Pattern {active_badge} <span style="float: right; color: #00E676;">{check_icon}</span>
                </div>
                <div style="color: #8B949E; font-size: 11px; margin-top: 4px;">
                    RSI Divergence & Chart Pattern Breakout / Reversal
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Pilih RSI + Pattern", key="btn_sel_rsi", use_container_width=True):
            st.session_state["selected_screener"] = "rsi"
            st.rerun()

        st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)

        # Option 3: Trade Planner & Batch Screener
        card_class = "screener-card-active" if curr == "trade_plan" else "screener-card"
        active_badge = '<span class="badge-active">Active</span>' if curr == "trade_plan" else ""
        check_icon = " ✔️" if curr == "trade_plan" else ""

        st.markdown(
            f"""
            <div class="{card_class}">
                <div style="font-weight: 700; color: #FFFFFF; font-size: 14px;">
                    🎯 3. Trade Plan Filter {active_badge} <span style="float: right; color: #00E676;">{check_icon}</span>
                </div>
                <div style="color: #8B949E; font-size: 11px; margin-top: 4px;">
                    Batch Screening & Dynamic Support / Resistance Scoring
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Pilih Trade Planner", key="btn_sel_tp", use_container_width=True):
            st.session_state["selected_screener"] = "trade_plan"
            st.rerun()

st.markdown(
    "<hr style='margin-top: 5px; margin-bottom: 20px; border-color: #21262D;'>",
    unsafe_allow_html=True,
)

# 4. Render View Sesuai Pilihan
if st.session_state["selected_screener"] == "stoch_psar":
    render_tab_stoch_psar()
elif st.session_state["selected_screener"] == "rsi":
    render_tab_rsi()
elif st.session_state["selected_screener"] == "trade_plan":
    render_tab_trade_planner()
