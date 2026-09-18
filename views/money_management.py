import math
import os
import plotly.graph_objects as go
import streamlit as st

# Safe import TradePlanner dari modul backend
try:
    from engines.trade_planner import TradePlanner
except ImportError:
    TradePlanner = None


# ==============================================================================
# 1. CYBERPUNK THEME ENGINE (AGGRESSIVE CSS OVERRIDE)
# ==============================================================================
def inject_cyberpunk_theme():
    """Memaksa seluruh layout Streamlit (Background, Cards, Input, Button, Text)

    menggunakan Tema Cyberpunk Neon secara menyeluruh.
    """
    cyberpunk_css = """
    <style>
    /* 1. OVERRIDE ROOT STREAMLIT THEME */
    :root, [data-testid="stAppViewContainer"], .stApp {
        --background-color: #05070a !important;
        --secondary-background-color: #0d111a !important;
        --primary-color: #00f3ff !important;
        --text-color: #00f3ff !important;
        background-color: #05070a !important;
        color: #00f3ff !important;
        font-family: 'Segoe UI', Roboto, monospace !important;
    }

    /* 2. BACKGROUND GLOBAL APLIKASI */
    .stAppViewContainer, .main, [data-testid="stHeader"] {
        background-color: #05070a !important;
    }

    /* 3. CARD & CONTAINER CUSTOM */
    .cyber-card {
        background: #0c1017 !important;
        border: 1px solid #00f3ff !important;
        border-radius: 6px !important;
        padding: 16px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.2), inset 0 0 10px rgba(0, 243, 255, 0.05) !important;
        position: relative !important;
    }

    .cyber-card-pink {
        background: #140810 !important;
        border: 1px solid #ff0055 !important;
        border-radius: 6px !important;
        padding: 16px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 0 15px rgba(255, 0, 85, 0.2) !important;
    }

    /* 4. TYPOGRAPHY & TEXT OVERRIDES */
    h1, h2, h3, h4, h5, h6, label, .stMarkdown, p, span {
        color: #ffffff !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #00f3ff !important;
        text-shadow: 0 0 8px rgba(0, 243, 255, 0.6) !important;
        letter-spacing: 1.5px !important;
    }
    .cyber-label {
        color: #8d9bb0 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
    }
    .cyber-value {
        font-size: 26px !important;
        font-weight: 900 !important;
        color: #00f3ff !important;
        text-shadow: 0 0 10px rgba(0, 243, 255, 0.8) !important;
        font-family: 'Courier New', monospace !important;
    }

    /* 5. INPUT FIELDS (TEXT, NUMBER, SELECTBOX) */
    div[data-baseweb="input"], div[data-baseweb="select"] > div {
        background-color: #0d111a !important;
        border: 1px solid #00f3ff !important;
        border-radius: 4px !important;
        box-shadow: 0 0 5px rgba(0, 243, 255, 0.3) !important;
    }
    input {
        color: #00f3ff !important;
        background-color: transparent !important;
        font-weight: bold !important;
        font-family: 'Courier New', monospace !important;
    }

    /* 6. BUTTON STYLING (NEON GLOW) */
    div.stButton > button {
        background: #05070a !important;
        color: #00f3ff !important;
        border: 1px solid #00f3ff !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.4) !important;
        font-weight: 800 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:hover {
        background: #00f3ff !important;
        color: #05070a !important;
        box-shadow: 0 0 20px #00f3ff !important;
    }

    /* 7. EXPANDER / ACCORDION */
    div[data-testid="stExpander"] {
        background-color: #080c14 !important;
        border: 1px solid #1e2638 !important;
        border-radius: 6px !important;
    }
    div[data-testid="stExpander"] details summary p {
        color: #00f3ff !important;
        font-weight: 700 !important;
    }

    /* 8. BADGES */
    .cyber-badge {
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    .badge-cyan { background: rgba(0,243,255,0.15); color: #00f3ff; border: 1px solid #00f3ff; }
    .badge-yellow { background: rgba(255,230,0,0.15); color: #ffe600; border: 1px solid #ffe600; }
    .badge-pink { background: rgba(255,0,85,0.15); color: #ff0055; border: 1px solid #ff0055; }
    </style>
    """
    st.markdown(cyberpunk_css, unsafe_allow_html=True)


# ==============================================================================
# 2. STRATEGY RULES CONSTANTS
# ==============================================================================
PROFILE_RULES = {
    "Scalping / Fast Trade": {
        "max_alloc": 10.0,
        "max_pos": 10,
        "cash_buff": 30.0,
        "desc": "High frequency, holding < 1 hari. Strict risk management.",
    },
    "Swing Trading": {
        "max_alloc": 20.0,
        "max_pos": 5,
        "cash_buff": 15.0,
        "desc": "Sweet spot IDX. Holding period 3 hari - 3 minggu.",
    },
    "Trend Following": {
        "max_alloc": 25.0,
        "max_pos": 4,
        "cash_buff": 10.0,
        "desc": "Riding trend berbulan-bulan hingga tren terkonfirmasi patah.",
    },
    "Investing (Value/Growth)": {
        "max_alloc": 33.0,
        "max_pos": 3,
        "cash_buff": 0.0,
        "desc": "Fokus fundamental & akumulasi posisi secara bertahap.",
    },
}


# ==============================================================================
# 3. HELPER FUNCTIONS
# ==============================================================================
def fetch_trade_plan(full_ticker: str, plan_type: str, clean_ticker: str) -> bool:
    """Mengambil data Trade Plan dari TradePlanner engine backend."""
    if not TradePlanner:
        st.error("[SYS_ERR] Modul `TradePlanner` tidak ditemukan.")
        return False

    try:
        with st.spinner(f"[SYNC] Syncing Trade Plan {full_ticker}..."):
            planner = TradePlanner(ticker=full_ticker)
            planner.fetch_and_prepare_data()
            df_plan = planner.generate_trade_plan()

            matched = df_plan[df_plan["Type"] == plan_type]
            if matched.empty:
                matched = df_plan

            row = matched.iloc[0]

            st.session_state["input_entry_price"] = float(row["Range Buy Min"])
            st.session_state["input_sl_price"] = float(row["Stop Loss"])
            st.session_state["input_tp1_price"] = float(row["TP 1"])
            st.session_state["input_tp2_price"] = float(row["TP 2"])
            st.session_state["last_synced_ticker"] = clean_ticker
            st.session_state["last_synced_type"] = plan_type
            return True
    except Exception as e:
        st.error(f"[SYS_ERR] Gagal sinkronisasi {clean_ticker}: {e}")
        return False


# ==============================================================================
# 4. MAIN RENDER FUNCTION
# ==============================================================================
def render_page_money_management():
    """Render utama Halaman Money Management."""
    # Eksekusi Pemaksaan CSS Cyberpunk
    inject_cyberpunk_theme()

    # Header Utama
    st.markdown("<h1>⚡ CYBERPUNK MONEY MANAGEMENT ENGINE</h1>", unsafe_allow_html=True)
    st.caption("System Execution & Position Sizing Analytics for IDX Trading")
    st.markdown("<br>", unsafe_allow_html=True)

    # Grid Utama (Kolom Kiri Control, Kolom Kanan Output Analytics)
    col_input, col_output = st.columns([1.1, 1.9], gap="large")

    # --------------------------------------------------------------------------
    # KOLOM 1: PARAMETER INPUT CONTROL
    # --------------------------------------------------------------------------
    with col_input:
        st.markdown("### ⚙️ SYSTEM CONTROLS")

        with st.expander("👤 CAPITAL & TRADER PROFILE", expanded=True):
            capital = st.number_input(
                "Total Capital (IDR)",
                min_value=1_000_000,
                value=100_000_000,
                step=5_000_000,
                format="%d",
                key="mm_capital_input",
            )
            trading_style = st.selectbox(
                "Trading Strategy Profile",
                list(PROFILE_RULES.keys()),
                index=1,
                key="mm_style_select",
            )
            risk_pct = st.slider(
                "Max Risk Tolerance per Trade (%)",
                min_value=0.25,
                max_value=10.0,
                value=1.0,
                step=0.25,
                key="mm_risk_slider",
            )

            rule = PROFILE_RULES[trading_style]
            st.caption(f"💡 *{rule['desc']}*")

        with st.expander("📊 TRADE EXECUTION SETUP", expanded=True):
            st.session_state.setdefault("input_entry_price", 125.0)
            st.session_state.setdefault("input_sl_price", 120.0)
            st.session_state.setdefault("input_tp1_price", 151.0)
            st.session_state.setdefault("input_tp2_price", 216.0)

            raw_ticker_default = (
                st.session_state.get("mm_ticker", "COCO").upper().replace(".JK", "")
            )
            ticker_input = st.text_input(
                "Ticker Code",
                value=raw_ticker_default,
                key="mm_raw_ticker_input",
            ).strip()

            clean_ticker = ticker_input.upper().replace(".JK", "").strip() or "COCO"
            full_ticker = f"{clean_ticker}.JK"

            plan_type = st.radio(
                "Trade Strategy Type",
                ["BOW", "BOB"],
                horizontal=True,
                key="mm_plan_type_radio",
            )

            if st.button("🔄 Sync with Trade Planner", use_container_width=True):
                if fetch_trade_plan(full_ticker, plan_type, clean_ticker):
                    st.rerun()

            c_entry, c_sl = st.columns(2)
            with c_entry:
                entry_price = st.number_input(
                    "Entry Price", min_value=1.0, step=1.0, key="input_entry_price"
                )
            with c_sl:
                sl_price = st.number_input(
                    "Stop Loss (SL)", min_value=1.0, step=1.0, key="input_sl_price"
                )

            c_tp1, c_tp2 = st.columns(2)
            with c_tp1:
                tp1_price = st.number_input(
                    "Target Price 1", min_value=1.0, step=1.0, key="input_tp1_price"
                )
            with c_tp2:
                tp2_price = st.number_input(
                    "Target Price 2", min_value=1.0, step=1.0, key="input_tp2_price"
                )

        with st.expander("🛠️ BROKERAGE FEES", expanded=False):
            fee_buy = (
                st.number_input(
                    "Buy Fee (%)", min_value=0.0, value=0.15, step=0.01, key="mm_fee_buy"
                )
                / 100
            )
            fee_sell = (
                st.number_input(
                    "Sell Fee (%)", min_value=0.0, value=0.25, step=0.01, key="mm_fee_sell"
                )
                / 100
            )

    # --------------------------------------------------------------------------
    # KOLOM 2: ANALYTICS OUTPUT
    # --------------------------------------------------------------------------
    with col_output:
        st.markdown("### 🎯 POSITION SIZING ANALYTICS")

        # Validasi Input Logic
        if sl_price >= entry_price:
            st.error("❌ [LOGIC ERROR] Stop Loss (SL) harus LEBIH KECIL dari Harga Entry!")
            return

        # Core Calculation Engine
        max_risk_allowed_idr = capital * (risk_pct / 100)
        risk_per_share_raw = entry_price - sl_price
        total_risk_per_share_with_fee = (entry_price * (1 + fee_buy)) - (
            sl_price * (1 - fee_sell)
        )

        raw_shares_by_risk = max_risk_allowed_idr / total_risk_per_share_with_fee
        lot_by_risk = math.floor(raw_shares_by_risk / 100)

        max_alloc_pct = rule["max_alloc"]
        max_capital_allowed = capital * (max_alloc_pct / 100)
        lot_by_cap = math.floor(
            max_capital_allowed / (entry_price * 100 * (1 + fee_buy))
        )

        final_lot = min(lot_by_risk, lot_by_cap)
        final_shares = final_lot * 100
        total_buy_value = final_shares * entry_price
        total_cost_with_fee = total_buy_value * (1 + fee_buy)

        actual_risk_idr = (
            (final_shares * entry_price * (1 + fee_buy))
            - (final_shares * sl_price * (1 - fee_sell))
            if final_lot > 0
            else 0.0
        )
        actual_risk_pct = (actual_risk_idr / capital) * 100 if capital > 0 else 0.0

        reward_tp1 = tp1_price - entry_price
        rrr_tp1 = reward_tp1 / risk_per_share_raw if risk_per_share_raw > 0 else 0
        is_capped = (lot_by_cap < lot_by_risk) and (lot_by_risk > 0)

        # 3 Card Neon Display
        m1, m2, m3 = st.columns(3)

        with m1:
            st.markdown(
                f"""
                <div class="cyber-card">
                    <div class="cyber-label">RECOMMENDED SIZE</div>
                    <div class="cyber-value">{final_lot:,} LOT</div>
                    <div style="font-size: 11px; color: #8d9bb0;">({final_shares:,} Lembar)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m2:
            st.markdown(
                f"""
                <div class="cyber-card">
                    <div class="cyber-label">TOTAL BUY VALUE</div>
                    <div class="cyber-value" style="color:#ffffff;">Rp {total_buy_value:,.0f}</div>
                    <div style="font-size: 11px; color: #8d9bb0;">Alloc: {(total_buy_value/capital)*100:.1f}% Modal</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m3:
            if rrr_tp1 >= 2.0:
                rrr_badge = '<span class="cyber-badge badge-cyan">EXCELLENT</span>'
            elif rrr_tp1 >= 1.5:
                rrr_badge = '<span class="cyber-badge badge-yellow">ACCEPTABLE</span>'
            else:
                rrr_badge = '<span class="cyber-badge badge-pink">POOR RISK</span>'

            st.markdown(
                f"""
                <div class="cyber-card">
                    <div class="cyber-label">RISK / REWARD</div>
                    <div class="cyber-value" style="color:#ffe600;">1 : {rrr_tp1:.2f}</div>
                    <div>{rrr_badge}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if is_capped:
            st.warning(
                f"⚠️ **CAP ALERT:** Toleransi risk mengizinkan **{lot_by_risk:,} Lot**, "
                f"namun dibatasi max **{final_lot:,} Lot** sesuai profil {trading_style} ({max_alloc_pct}%)."
            )

        # Partial Profit Taking Execution Plan
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### ✂️ PARTIAL PROFIT TAKING PLAN")

        lot_tp1 = math.floor(final_lot * 0.5)
        lot_tp2 = final_lot - lot_tp1

        p_tp1 = (lot_tp1 * 100 * tp1_price) * (1 - fee_sell) - (
            lot_tp1 * 100 * entry_price * (1 + fee_buy)
        )
        p_tp2 = (lot_tp2 * 100 * tp2_price) * (1 - fee_sell) - (
            lot_tp2 * 100 * entry_price * (1 + fee_buy)
        )
        total_potential_profit = p_tp1 + p_tp2

        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(
                f"""
                <div class="cyber-card">
                    <h4 style="margin:0; color:#00f3ff; font-size:14px;">TAHAP 1: SELL 50% @ TP1</h4>
                    <p style="margin:6px 0; font-size:13px; color:#ffffff;">Jual <b>{lot_tp1:,} Lot</b> @ <b>Rp {tp1_price:,.0f}</b></p>
                    <p style="margin:0; font-size:12px; color:#8d9bb0;">Est. Profit: <b style="color:#00ff66;">+Rp {p_tp1:,.0f}</b></p>
                    <hr style="margin:10px 0; border-color:#1e2638;">
                    <span style="font-size:11px; color:#ffe600;">📌 Action: Set Break-Even SL @ Rp {entry_price:,.0f}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with sc2:
            st.markdown(
                f"""
                <div class="cyber-card">
                    <h4 style="margin:0; color:#00f3ff; font-size:14px;">TAHAP 2: SELL 50% @ TP2</h4>
                    <p style="margin:6px 0; font-size:13px; color:#ffffff;">Jual <b>{lot_tp2:,} Lot</b> @ <b>Rp {tp2_price:,.0f}</b></p>
                    <p style="margin:0; font-size:12px; color:#8d9bb0;">Est. Profit: <b style="color:#00ff66;">+Rp {p_tp2:,.0f}</b></p>
                    <hr style="margin:10px 0; border-color:#1e2638;">
                    <span style="font-size:11px; color:#00f3ff;">💰 Total Potential: <b style="color:#00ff66;">+Rp {total_potential_profit:,.0f}</b></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Plotly Visualizers
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📈 RISK VISUALIZER & EXPOSURE")

        v1, v2 = st.columns(2)

        with v1:
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=actual_risk_pct,
                    number={"suffix": "%", "font": {"color": "#00f3ff"}},
                    domain={"x": [0, 1], "y": [0, 1]},
                    gauge={
                        "axis": {"range": [0, max(10.0, risk_pct * 1.5)]},
                        "bar": {
                            "color": "#00f3ff" if actual_risk_pct <= risk_pct else "#ff0055"
                        },
                        "steps": [
                            {"range": [0, risk_pct], "color": "#0d111a"},
                            {"range": [risk_pct, 10.0], "color": "#1c0812"},
                        ],
                    },
                )
            )
            fig_gauge.update_layout(
                height=180,
                margin=dict(l=20, r=20, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#ffffff"},
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        with v2:
            cash_left = max(0.0, capital - total_cost_with_fee)
            fig_donut = go.Figure(
                data=[
                    go.Pie(
                        labels=[f"Posisi {clean_ticker}", "Cash"],
                        values=[total_cost_with_fee, cash_left],
                        hole=0.6,
                        marker_colors=["#00f3ff", "#1e2638"],
                    )
                ]
            )
            fig_donut.update_layout(
                height=180,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#ffffff"},
                showlegend=False,
            )
            st.plotly_chart(fig_donut, use_container_width=True)
