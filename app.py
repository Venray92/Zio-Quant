import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as gg
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# 1. SETUP HALAMAN & STYLESHEET (STRICT CSS INJECTION)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="IDX Technical Screener Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS untuk mengesampingkan styling default Streamlit agar mirip 100% UI React
st.markdown(
    """
    <style>
    /* Reset main margins */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }
    
    /* Background global */
    .stApp {
        background-color: #0c0e12;
        color: #e1e7ec;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Container border & styling */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.3rem !important;
    }

    /* Badge & Tag Styling */
    .badge-active {
        background-color: #0d3324;
        border: 1px solid #00c076;
        color: #00c076;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
        display: inline-block;
    }
    .badge-gc {
        background-color: #1d4ed8;
        border: 1px solid #3b82f6;
        color: #ffffff;
        padding: 1px 4px;
        border-radius: 3px;
        font-size: 9px;
        font-weight: bold;
    }
    .badge-dc {
        background-color: #ef4444;
        border: 1px solid #f87171;
        color: #ffffff;
        padding: 1px 4px;
        border-radius: 3px;
        font-size: 9px;
        font-weight: bold;
    }
    .badge-lq45 {
        background-color: #1e293b;
        color: #94a3b8;
        padding: 1px 3px;
        border-radius: 2px;
        font-size: 9px;
        font-weight: 600;
    }
    
    /* Table / Card List item styling */
    .stock-card {
        background-color: #11161d;
        border-bottom: 1px solid #1a212b;
        padding: 8px 10px;
        border-radius: 4px;
        margin-bottom: 4px;
        cursor: pointer;
    }
    .stock-card:hover {
        background-color: #151c26;
    }
    .stock-card-selected {
        background-color: #192433;
        border-left: 3px solid #00c076;
    }

    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. MOCK DATA UNIVERSE (Sama seperti STOCKS_UNIVERSE)
# -----------------------------------------------------------------------------
@st.cache_data
def get_mock_stocks():
    return [
        {"symbol": "IHSG", "name": "Indeks Harga Saham Gabungan", "price": 6541.38, "change": 12.4, "changePercent": 0.19, "isLQ45": False, "stochK": 45.2, "stochD": 40.1, "stochCrossDays": 1, "isDeadCross": False, "deadCrossDays": None, "psar": 6500.0, "psarBullish": True, "apiData": {"Score": 2}},
        {"symbol": "ANTM", "name": "Aneka Tambang Tbk", "price": 1545.0, "change": 35.0, "changePercent": 2.32, "isLQ45": True, "stochK": 78.4, "stochD": 65.2, "stochCrossDays": 0, "isDeadCross": False, "deadCrossDays": None, "psar": 1480.0, "psarBullish": True, "apiData": {"Score": 5, "Action": "BELI"}},
        {"symbol": "BBCA", "name": "Bank Central Asia Tbk", "price": 9800.0, "change": -50.0, "changePercent": -0.51, "isLQ45": True, "stochK": 32.1, "stochD": 45.0, "stochCrossDays": None, "isDeadCross": True, "deadCrossDays": 0, "psar": 9950.0, "psarBullish": False, "apiData": {"Score": -3, "Action": "JUAL"}},
        {"symbol": "BBRI", "name": "Bank Rakyat Indonesia Tbk", "price": 5250.0, "change": 75.0, "changePercent": 1.45, "isLQ45": True, "stochK": 60.5, "stochD": 55.2, "stochCrossDays": 2, "isDeadCross": False, "deadCrossDays": None, "psar": 5100.0, "psarBullish": True, "apiData": {"Score": 3, "Action": "BELI"}},
        {"symbol": "TLKM", "name": "Telkom Indonesia Tbk", "price": 3820.0, "change": -20.0, "changePercent": -0.52, "isLQ45": True, "stochK": 25.0, "stochD": 38.4, "stochCrossDays": None, "isDeadCross": True, "deadCrossDays": 1, "psar": 3900.0, "psarBullish": False, "apiData": {"Score": -2}},
        {"symbol": "UNTR", "name": "United Tractors Tbk", "price": 24500.0, "change": 250.0, "changePercent": 1.03, "isLQ45": True, "stochK": 82.0, "stochD": 79.1, "stochCrossDays": 0, "isDeadCross": False, "deadCrossDays": None, "psar": 23900.0, "psarBullish": True, "apiData": {"Score": 4, "Action": "BELI"}},
    ]

stocks_data = get_mock_stocks()

# Init State
if "selected_screener" not in st_session := st.session_state:
    st.session_state.selected_screener = "1. Stoch - Psar"
if "active_stock" not in st.session_state:
    st.session_state.active_stock = stocks_data[0]
if "screener_filter" not in st.session_state:
    st.session_state.screener_filter = "all_signals"

# -----------------------------------------------------------------------------
# 3. SIDEBAR NAVIGASI PINGGIR (60px minimalized feel)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h3 style='text-align: center; color: #00c076;'>🟢 IDX</h3>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio(
        "Menu",
        ["Screener", "Markets", "Stream", "Support", "Settings"],
        label_visibility="collapsed"
    )
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.caption("v2.4.0 • Live")

# -----------------------------------------------------------------------------
# 4. TATA LETAK UTAMA (WATCHLIST & DASHBOARD AREA)
# -----------------------------------------------------------------------------
col_watchlist, col_main = st.columns([1, 3.5])

# --- PANE KIRI: WATCHLIST PANEL ---
with col_watchlist:
    # Header Control Watchlist
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0px;">
            <span class="badge-active">● {st.session_state.selected_screener}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Input Cari
    search_q = st.text_input("Search", placeholder="Cari kode atau nama...", label_visibility="collapsed")

    # Screener Filter Tabs (GC 0-2h | Pas DC | Semua)
    f_col1, f_col2, f_col3 = st.columns(3)
    if f_col1.button("★ GC", use_container_width=True):
        st.session_state.screener_filter = "gc_only"
    if f_col2.button("⚠ DC", use_container_width=True):
        st.session_state.screener_filter = "dc_only"
    if f_col3.button("Semua", use_container_width=True):
        st.session_state.screener_filter = "all_signals"

    # Filter Logic Saham
    filtered_stocks = []
    for s in stocks_data:
        # Search match
        if search_q and not (search_q.lower() in s["symbol"].lower() or search_q.lower() in s["name"].lower()):
            continue
        
        # Screener filter match
        if st.session_state.screener_filter == "gc_only":
            if s["symbol"] == "IHSG" or (s.get("stochCrossDays") is not None and s["stochCrossDays"] <= 2):
                filtered_stocks.append(s)
        elif st.session_state.screener_filter == "dc_only":
            if s["symbol"] == "IHSG" or s.get("deadCrossDays") == 0:
                filtered_stocks.append(s)
        else:
            filtered_stocks.append(s)

    # Render List Saham
    st.markdown("<div style='height: 400px; overflow-y: auto;'>", unsafe_allow_html=True)
    for stock in filtered_stocks:
        is_active = stock["symbol"] == st.session_state.active_stock["symbol"]
        card_class = "stock-card stock-card-selected" if is_active else "stock-card"
        
        # Badge status logic
        status_badge = ""
        if stock.get("deadCrossDays") == 0:
            status_badge = '<span class="badge-dc">⚠ PAS DC</span>'
        elif stock.get("stochCrossDays") == 0:
            status_badge = '<span class="badge-gc">★ BARU GC</span>'
        elif stock.get("stochCrossDays") is not None and stock["stochCrossDays"] <= 2:
            status_badge = f'<span class="badge-gc">GC +{stock["stochCrossDays"]}h</span>'

        lq45_badge = '<span class="badge-lq45">LQ45</span>' if stock["isLQ45"] else ''
        chg_color = "#00c076" if stock["change"] >= 0 else "#eb5757"
        chg_sign = "+" if stock["change"] > 0 else ""

        # Layout HTML Kartu
        card_html = f"""
        <div class="{card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="font-size: 13px; color: #fff;">{stock['symbol']}</strong> {lq45_badge} {status_badge}
                    <div style="font-size: 11px; color: #8292a4; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 120px;">{stock['name']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 13px; font-weight: bold; color: #f0f4f8;">{stock['price']:,.2f}</div>
                    <div style="font-size: 11px; font-weight: 500; color: {chg_color};">{chg_sign}{stock['changePercent']:.2f}%</div>
                </div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        if st.button(f"Pilih {stock['symbol']}", key=f"btn_{stock['symbol']}", use_container_width=True):
            st.session_state.active_stock = stock
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption(f"Total: {len(filtered_stocks)} | IDX LIVE")

# --- PANE KANAN: DASHBOARD UTAMA & CHART ---
with col_main:
    curr_stock = st.session_state.active_stock

    # Top Bar Info Saham Terpilih
    head_c1, head_c2, head_c3 = st.columns([2, 1, 1])
    with head_c1:
        st.markdown(f"## {curr_stock['symbol']} - <span style='font-size: 16px; color: #8b98a5;'>{curr_stock['name']}</span>", unsafe_allow_html=True)
    with head_c2:
        chg_color = "#00c076" if curr_stock["change"] >= 0 else "#eb5757"
        st.markdown(
            f"""
            <div style="text-align: right;">
                <h3 style="margin: 0; color: #fff;">{curr_stock['price']:,.2f}</h3>
                <span style="color: {chg_color}; font-weight: bold;">{curr_stock['change']:+.2f} ({curr_stock['changePercent']:+.2f}%)</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with head_c3:
        st.selectbox("Choose Screener", ["1. Stoch - Psar", "2. Golden Cross Only", "3. Breakout Volume"], key="selected_screener")

    st.markdown("---")

    # Generate Dummy Candlestick & Indicator Data
    dates = pd.date_range(end=pd.Timestamp.now(), periods=60, freq="B")
    np.random.seed(42)
    base_price = curr_stock["price"]
    returns = np.random.normal(0.001, 0.015, size=len(dates))
    price_path = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        "Date": dates,
        "Open": price_path * (1 + np.random.uniform(-0.005, 0.005, size=len(dates))),
        "High": price_path * (1 + np.random.uniform(0.001, 0.012, size=len(dates))),
        "Low": price_path * (1 - np.random.uniform(0.001, 0.012, size=len(dates))),
        "Close": price_path,
        "Stoch_K": np.random.uniform(20, 80, size=len(dates)),
        "Stoch_D": np.random.uniform(20, 80, size=len(dates)),
    })

    # Render Chart (Candlestick + Stochastic Oscillator Subplot)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    
    # Candlestick
    fig.add_trace(
        gg.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            increasing_line_color="#00c076",
            decreasing_line_color="#eb5757",
            name="Harga"
        ),
        row=1, col=1
    )
    
    # Stochastic Subplot
    fig.add_trace(gg.Scatter(x=df["Date"], y=df["Stoch_K"], line=dict(color="#00c076", width=1), name="%K"), row=2, col=1)
    fig.add_trace(gg.Scatter(x=df["Date"], y=df["Stoch_D"], line=dict(color="#2563eb", width=1), name="%D"), row=2, col=1)
    
    # Chart Layout Customization
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#11161d",
        plot_bgcolor="#11161d",
        margin=dict(l=10, r=10, t=10, b=10),
        height=450,
        xaxis_rangeslider_visible=False,
        showlegend=False
    )
    fig.update_xaxes(showgrid=True, gridcolor="#1a212b")
    fig.update_yaxes(showgrid=True, gridcolor="#1a212b")

    st.plotly_chart(fig, use_container_width=True)

    # Technical Details Metric Panel
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Stochastic %K", f"{curr_stock.get('stochK', 0):.1f}", delta="Bullish Cross" if curr_stock.get("stochK", 0) > curr_stock.get("stochD", 0) else "Bearish")
    m2.metric("Stochastic %D", f"{curr_stock.get('stochD', 0):.1f}")
    m3.metric("Parabolic SAR", f"{curr_stock.get('psar', 0):,.2f}", delta="HOLD" if curr_stock.get("psarBullish") else "BUANG")
    m4.metric("Score Sinyal", f"{curr_stock['apiData'].get('Score', 0)}")