import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & INJECT CUSTOM CSS UI REAL-REACT LOOK
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="IDX Technical Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Dark Theme Core Overlay */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0c0e12 !important;
        color: #e1e7ec !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    /* Minimize Margins & Padding */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }

    /* Hide Streamlit Header & Footer elements */
    header, footer, #MainMenu { visibility: hidden !important; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #080a0d !important;
        border-right: 1px solid #1a212b !important;
    }
    
    /* Custom Card Style for Watchlist */
    .stock-card {
        background-color: #11161d;
        border: 1px solid #1a212b;
        border-radius: 6px;
        padding: 8px 12px;
        margin-bottom: 6px;
    }
    .stock-card:hover {
        background-color: #161d26;
        border-color: #263345;
    }
    .stock-card-active {
        background-color: #192433 !important;
        border-left: 4px solid #00c076 !important;
    }
    
    /* Custom Badges */
    .badge-gc {
        background-color: #1d4ed8;
        color: #ffffff;
        font-size: 10px;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 3px;
    }
    .badge-dc {
        background-color: #ef4444;
        color: #ffffff;
        font-size: 10px;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 3px;
    }
    .badge-lq45 {
        background-color: #1e293b;
        color: #94a3b8;
        font-size: 9px;
        padding: 1px 4px;
        border-radius: 2px;
    }
    
    /* Input & Button Modifications */
    .stTextInput input {
        background-color: #11161d !important;
        color: #ffffff !important;
        border: 1px solid #1c2430 !important;
        border-radius: 4px !important;
    }
    
    .stButton button {
        background-color: #141c26 !important;
        color: #8ea5be !important;
        border: 1px solid #273546 !important;
        border-radius: 4px !important;
        font-size: 12px !important;
        padding: 2px 8px !important;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background-color: #00c076 !important;
        color: #000000 !important;
        border-color: #00c076 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. STATE MANAGEMENT & DUMMY DATA UNIVERSE
# -----------------------------------------------------------------------------
@st.cache_data
def load_universe():
    return [
        {"symbol": "IHSG", "name": "Indeks Harga Saham Gabungan", "price": 6541.38, "change": 12.4, "changePercent": 0.19, "isLQ45": False, "stochK": 45.2, "stochD": 40.1, "stochCrossDays": 1, "isDeadCross": False, "deadCrossDays": None, "psarBullish": True, "score": 2},
        {"symbol": "ANTM", "name": "Aneka Tambang Tbk", "price": 1545.0, "change": 35.0, "changePercent": 2.32, "isLQ45": True, "stochK": 78.4, "stochD": 65.2, "stochCrossDays": 0, "isDeadCross": False, "deadCrossDays": None, "psarBullish": True, "score": 5},
        {"symbol": "BBCA", "name": "Bank Central Asia Tbk", "price": 9800.0, "change": -50.0, "changePercent": -0.51, "isLQ45": True, "stochK": 32.1, "stochD": 45.0, "stochCrossDays": None, "isDeadCross": True, "deadCrossDays": 0, "psarBullish": False, "score": -3},
        {"symbol": "BBRI", "name": "Bank Rakyat Indonesia Tbk", "price": 5250.0, "change": 75.0, "changePercent": 1.45, "isLQ45": True, "stochK": 60.5, "stochD": 55.2, "stochCrossDays": 2, "isDeadCross": False, "deadCrossDays": None, "psarBullish": True, "score": 3},
        {"symbol": "TLKM", "name": "Telkom Indonesia Tbk", "price": 3820.0, "change": -20.0, "changePercent": -0.52, "isLQ45": True, "stochK": 25.0, "stochD": 38.4, "stochCrossDays": None, "isDeadCross": True, "deadCrossDays": 1, "psarBullish": False, "score": -2},
        {"symbol": "UNTR", "name": "United Tractors Tbk", "price": 24500.0, "change": 250.0, "changePercent": 1.03, "isLQ45": True, "stochK": 82.0, "stochD": 79.1, "stochCrossDays": 0, "isDeadCross": False, "deadCrossDays": None, "psarBullish": True, "score": 4},
    ]

stocks_data = load_universe()

if "selected_screener" not in st.session_state:
    st.session_state.selected_screener = "1. Stoch - Psar"
if "active_stock" not in st.session_state:
    st.session_state.active_stock = stocks_data[0]
if "screener_filter" not in st.session_state:
    st.session_state.screener_filter = "all_signals"

# -----------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color: #00c076; text-align: center;'>🟢 IDX SCREENER</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.radio("Menu Navigation", ["Screener", "Markets", "Stream", "Settings"], label_visibility="collapsed")
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("Engine: Streamlit Live v2.4")

# -----------------------------------------------------------------------------
# 4. MAIN LAYOUT (WATCHLIST PANEL & CHART)
# -----------------------------------------------------------------------------
col_left, col_right = st.columns([1.1, 3])

# --- LEFT COLUMN: WATCHLIST PANEL ---
with col_left:
    st.markdown(
        f"""
        <div style='display:flex; justify-between; align-items:center; padding-bottom:8px;'>
            <span style='background:#0d3324; color:#00c076; border:1px solid #00c076; font-size:11px; font-weight:bold; padding:2px 8px; border-radius:10px;'>
                ● {st.session_state.selected_screener}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    search_input = st.text_input("Search", placeholder="Cari kode/nama...", label_visibility="collapsed")
    
    # Filter Tabs
    f1, f2, f3 = st.columns(3)
    if f1.button("★ GC", use_container_width=True): st.session_state.screener_filter = "gc_only"
    if f2.button("⚠ DC", use_container_width=True): st.session_state.screener_filter = "dc_only"
    if f3.button("Semua", use_container_width=True): st.session_state.screener_filter = "all_signals"

    # Filter logic
    display_stocks = []
    for s in stocks_data:
        if search_input and not (search_input.lower() in s["symbol"].lower() or search_input.lower() in s["name"].lower()):
            continue
        if st.session_state.screener_filter == "gc_only" and s["symbol"] != "IHSG" and (s.get("stochCrossDays") is None or s["stochCrossDays"] > 2):
            continue
        if st.session_state.screener_filter == "dc_only" and s["symbol"] != "IHSG" and s.get("deadCrossDays") != 0:
            continue
        display_stocks.append(s)

    # Stock List Render
    for stock in display_stocks:
        is_sel = stock["symbol"] == st.session_state.active_stock["symbol"]
        card_class = "stock-card stock-card-active" if is_sel else "stock-card"
        
        badge_html = ""
        if stock.get("deadCrossDays") == 0:
            badge_html = '<span class="badge-dc">⚠ PAS DC</span>'
        elif stock.get("stochCrossDays") == 0:
            badge_html = '<span class="badge-gc">★ BARU GC</span>'
        elif stock.get("stochCrossDays") is not None and stock["stochCrossDays"] <= 2:
            badge_html = f'<span class="badge-gc">GC +{stock["stochCrossDays"]}h</span>'
            
        lq_html = '<span class="badge-lq45">LQ45</span>' if stock["isLQ45"] else ''
        p_color = "#00c076" if stock["change"] >= 0 else "#eb5757"
        
        st.markdown(
            f"""
            <div class="{card_class}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="color:#fff; font-size:13px;">{stock['symbol']}</strong> {lq_html} {badge_html}
                        <div style="color:#8b98a5; font-size:11px; max-width:110px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{stock['name']}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#fff; font-weight:bold; font-size:13px;">{stock['price']:,.0f}</div>
                        <div style="color:{p_color}; font-size:11px; font-weight:600;">{stock['changePercent']:+.2f}%</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Pilih {stock['symbol']}", key=f"sel_{stock['symbol']}", use_container_width=True):
            st.session_state.active_stock = stock
            st.rerun()

# --- RIGHT COLUMN: MAIN DASHBOARD & CHART ---
with col_right:
    curr = st.session_state.active_stock
    
    # Header Info
    h1, h2 = st.columns([2, 1])
    with h1:
        st.markdown(f"<h1 style='margin:0; padding:0; font-size:24px;'>{curr['symbol']} <span style='color:#8b98a5; font-size:14px;'>{curr['name']}</span></h1>", unsafe_allow_html=True)
    with h2:
        st.selectbox("Choose Screener", ["1. Stoch - Psar", "2. Golden Cross Only", "3. Breakout Volume"], key="selected_screener")

    # Interactive Plotly Chart
    np.random.seed(10)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=50, freq="B")
    prices = curr["price"] * np.exp(np.cumsum(np.random.normal(0.0005, 0.012, size=50)))
    
    df_chart = pd.DataFrame({
        "Date": dates,
        "Open": prices * (1 + np.random.uniform(-0.003, 0.003, 50)),
        "High": prices * (1 + np.random.uniform(0.001, 0.008, 50)),
        "Low": prices * (1 - np.random.uniform(0.001, 0.008, 50)),
        "Close": prices,
        "Stoch_K": np.random.uniform(20, 80, 50),
        "Stoch_D": np.random.uniform(20, 80, 50),
    })

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
    
    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df_chart["Date"], open=df_chart["Open"], high=df_chart["High"],
        low=df_chart["Low"], close=df_chart["Close"],
        increasing_line_color="#00c076", decreasing_line_color="#eb5757", name="OHLC"
    ), row=1, col=1)
    
    # Indicator %K & %D
    fig.add_trace(go.Scatter(x=df_chart["Date"], y=df_chart["Stoch_K"], line=dict(color="#00c076", width=1.5), name="%K"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_chart["Date"], y=df_chart["Stoch_D"], line=dict(color="#2563eb", width=1.5), name="%D"), row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#11161d",
        plot_bgcolor="#11161d",
        margin=dict(l=10, r=10, t=10, b=10),
        height=420,
        xaxis_rangeslider_visible=False,
        showlegend=False
    )
    fig.update_xaxes(showgrid=True, gridcolor="#1a212b")
    fig.update_yaxes(showgrid=True, gridcolor="#1a212b")

    st.plotly_chart(fig, use_container_width=True)

    # Technical Details Metric Panel
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Harga Terakhir", f"{curr['price']:,.0f}", delta=f"{curr['changePercent']:+.2f}%")
    m2.metric("Stochastic %K / %D", f"{curr.get('stochK', 0):.1f} / {curr.get('stochD', 0):.1f}")
    m3.metric("Parabolic SAR", "HOLD" if curr.get("psarBullish") else "BUANG")
    m4.metric("Score Signals", f"{curr.get('score', 0)}")
