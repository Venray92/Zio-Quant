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
# 1. CYBERPUNK THEME ENGINE (CSS & STYLING INJECTION)
# ==============================================================================
def inject_cyberpunk_theme():
    """Menerapkan styling CSS bertema Cyberpunk / High-Tech Trading Dashboard

    secara menyeluruh ke komponen kustom dan elemen bawaan Streamlit.
    """
    cyberpunk_css = """
    <style>
    /* Global Cyberpunk Palette Variables */
    :root {
        --cyber-bg-dark: #0a0b10;
        --cyber-card-bg: #12151e;
        --cyber-card-border: #1e2638;
        --cyber-cyan: #00f3ff;
        --cyber-pink: #ff0055;
        --cyber-yellow: #ffe600;
        --cyber-green: #00ff66;
        --cyber-text-muted: #8d9bb0;
        --cyber-glow-cyan: rgba(0, 243, 255, 0.3);
        --cyber-glow-pink: rgba(255, 0, 85, 0.3);
    }

    /* Container Card Style */
    .cyber-card {
        background-color: var(--cyber-card-bg) !important;
        border: 1px solid var(--cyber-card-border) !important;
        border-radius: 8px !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .cyber-card::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important; left: 0 !important; right: 0 !important;
        height: 2px !important;
        background: linear-gradient(90deg, transparent, var(--cyber-cyan), transparent) !important;
    }

    /* Dynamic Badges */
    .cyber-badge {
        padding: 4px 12px !important;
        border-radius: 4px !important;
        font-weight: 800 !important;
        font-size: 11px !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        display: inline-block !important;
    }
    .cyber-badge-cyan {
        background-color: rgba(0, 243, 255, 0.1) !important;
        color: var(--cyber-cyan) !important;
        border: 1px solid var(--cyber-cyan) !important;
        box-shadow: 0 0 10px var(--cyber-glow-cyan) !important;
    }
    .cyber-badge-pink {
        background-color: rgba(255, 0, 85, 0.1) !important;
        color: var(--cyber-pink) !important;
        border: 1px solid var(--cyber-pink) !important;
        box-shadow: 0 0 10px var(--cyber-glow-pink) !important;
    }
    .cyber-badge-yellow {
        background-color: rgba(255, 230, 0, 0.1) !important;
        color: var(--cyber-yellow) !important;
        border: 1px solid var(--cyber-yellow) !important;
    }

    /* Typography Overrides */
    .cyber-label {
        color: var(--cyber-text-muted) !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        margin-bottom: 4px !important;
    }
    .cyber-value {
        font-size: 24px !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        font-family: 'Courier New', Courier, monospace !important;
    }

    /* Custom Titles */
    .cyber-header {
        font-size: 14px !important;
        font-weight: 800 !important;
        color: var(--cyber-cyan) !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        text-align: center !important;
        margin-bottom: 2px !important;
    }
    .cyber-subheader {
        font-size: 11px !important;
        color: var(--cyber-text-muted) !important;
        text-align: center !important;
        margin-bottom: 12px !important;
    }

    /* ==========================================================================
       STREAMLIT NATIVE COMPONENTS OVERRIDES
       ========================================================================== */
    /* Input Fields (Text & Number) */
    div[data-baseweb="input"] > div {
        background-color: #12151e !important;
        border: 1px solid var(--cyber-card-border) !important;
        color: var(--cyber-cyan) !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="input"] input {
        color: var(--cyber-cyan) !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-weight: 700 !important;
    }
    
    /* Selectbox / Dropdown */
    div[data-baseweb="select"] > div {
        background-color: #12151e !important;
        border: 1px solid var(--cyber-card-border) !important;
        color: #ffffff !important;
        border-radius: 6px !important;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #12151e !important;
        color: var(--cyber-cyan) !important;
        border: 1px solid var(--cyber-cyan) !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        border-radius: 6px !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        background-color: var(--cyber-cyan) !important;
        color: #000000 !important;
        box-shadow: 0 0 15px var(--cyber-cyan) !important;
    }

    /* Expander Container & Header */
    .stExpander {
        background-color: #0d0f17 !important;
        border: 1px solid var(--cyber-card-border) !important;
        border-radius: 8px !important;
        margin-bottom: 10px !important;
    }
    .stExpander > details > summary {
        color: var(--cyber-cyan) !important;
        font-weight: 700 !important;
    }

    /* Radio Buttons & Labels */
    div[role="radiogroup"] label p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    </style>
    """
    st.markdown(cyberpunk_css, unsafe_allow_html=True)


# ==============================================================================
# 2. DATA CONSTANTS & TRADING RULES
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
    """Mengambil data Trade Plan dari TradePlanner engine backend

    dan menyimpan nilai ke dalam Streamlit session_state.
    """
    if not TradePlanner:
        st.error("[SYS_ERR] Modul `TradePlanner` tidak dapat dimuat.")
        return False

    try:
        with st.spinner(f"[SYNCING] Mengambil Trade Plan {full_ticker}..."):
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
    """Halaman utama kalkulator Position Sizing & Money Management."""
    # Inject styling Cyberpunk ke halaman
    inject_cyberpunk_theme()

    # Header Halaman
    st.title("⚡ Cyberpunk Money Management Engine")
    st.caption(
        "Kalkulasi alokasi posisi & manajemen risiko transaksi IDX berbasis kustom presisi tinggi."
    )

    # Layout Utama: 2 Kolom (Input Parameters vs Calculator Output)
    col_input, col_output = st.columns([1.1, 1.9], gap="large")

    # --------------------------------------------------------------------------
    # KOLOM 1: PARAMETER INPUT
    # --------------------------------------------------------------------------
    with col_input:
        st.subheader("⚙️ System Control Parameters")

        # Section 1: Capital & Profile
        with st.expander("👤 Capital & Trader Profile", expanded=True):
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

        # Section 2: Trade Plan Parameters
        with st.expander("📊 Trade Execution Setup", expanded=True):
            # Inisialisasi default session_state jika belum ada
            st.session_state.setdefault("input_entry_price", 125.0)
            st.session_state.setdefault("input_sl_price", 120.0)
            st.session_state.setdefault("input_tp1_price", 151.0)
            st.session_state.setdefault("input_tp2_price", 216.0)

            raw_ticker_default = (
                st.session_state.get("mm_ticker", "COCO")
                .upper()
                .replace(".JK", "")
            )
            ticker_input = st.text_input(
                "Ticker Code (Tanpa .JK)",
                value=raw_ticker_default,
                key="mm_raw_ticker_input",
            ).strip()

            clean_ticker = (
                ticker_input.upper().replace(".JK", "").strip() or "COCO"
            )
            full_ticker = f"{clean_ticker}.JK"

            plan_type = st.radio(
                "Trade Strategy Type",
                ["BOW", "BOB"],
                horizontal=True,
                key="mm_plan_type_radio",
            )

            # Button Sync
            if st.button("🔄 Sync with Trade Planner", use_container_width=True):
                if fetch_trade_plan(full_ticker, plan_type, clean_ticker):
                    st.rerun()

            # Entry & SL Inputs
            c_entry, c_sl = st.columns(2)
            with c_entry:
                entry_price = st.number_input(
                    "Entry Price",
                    min_value=1.0,
                    step=1.0,
                    key="input_entry_price",
                )
            with c_sl:
                sl_price = st.number_input(
                    "Stop Loss (SL)",
                    min_value=1.0,
                    step=1.0,
                    key="input_sl_price",
                )

            # TP1 & TP2 Inputs
            c_tp1, c_tp2 = st.columns(2)
            with c_tp1:
                tp1_price = st.number_input(
                    "Target Price 1",
                    min_value=1.0,
                    step=1.0,
                    key="input_tp1_price",
                )
            with c_tp2:
                tp2_price = st.number_input(
                    "Target Price 2",
                    min_value=1.0,
                    step=1.0,
                    key="input_tp2_price",
                )

        # Section 3: Fees Sekuritas
        with st.expander("🛠️ Brokerage Fee Structure", expanded=False):
            fee_buy = (
                st.number_input(
                    "Buy Fee (%)",
                    min_value=0.0,
                    value=0.15,
                    step=0.01,
                    key="mm_fee_buy",
                )
                / 100
            )
            fee_sell = (
                st.number_input(
                    "Sell Fee (%)",
                    min_value=0.0,
                    value=0.25,
                    step=0.01,
                    key="mm_fee_sell",
                )
                / 100
            )

    # --------------------------------------------------------------------------
    # KOLOM 2: HASIL KALKULASI LOGIKA POSITION SIZING
    # --------------------------------------------------------------------------
    with col_output:
        st.subheader("🎯 Position Sizing Analytics Output")

        # Proteksi Logika Input
        if sl_price >= entry_price:
            st.error(
                "❌ [LOGIC ERROR] Stop Loss (SL) harus LEBIH KECIL dari Entry Price."
            )
            return

        if tp1_price <= entry_price:
            st.warning(
                "⚠️ [WARN] Target Price 1 sebaiknya lebih besar dari harga Entry."
            )

        # ----------------------------------------------------------------------
        # HITUNG RISK & SIZING (ENGINE CORE)
        # ----------------------------------------------------------------------
        max_risk_allowed_idr = capital * (risk_pct / 100)
        risk_per_share_raw = entry_price - sl_price
        total_risk_per_share_with_fee = (entry_price * (1 + fee_buy)) - (
            sl_price * (1 - fee_sell)
        )

        # Sizing berdasarkan Batas Risk
        raw_shares_by_risk = (
            max_risk_allowed_idr / total_risk_per_share_with_fee
        )
        lot_by_risk = math.floor(raw_shares_by_risk / 100)

        # Sizing berdasarkan Max Alokasi Modal Profil
        max_alloc_pct = rule["max_alloc"]
        max_capital_allowed = capital * (max_alloc_pct / 100)
        lot_by_cap = math.floor(
            max_capital_allowed / (entry_price * 100 * (1 + fee_buy))
        )

        # Keputusan Final Lot
        final_lot = min(lot_by_risk, lot_by_cap)
        final_shares = final_lot * 100
        total_buy_value = final_shares * entry_price
        total_cost_with_fee = total_buy_value * (1 + fee_buy)

        # Realized Risk
        actual_risk_idr = (
            (final_shares * entry_price * (1 + fee_buy))
            - (final_shares * sl_price * (1 - fee_sell))
            if final_lot > 0
            else 0.0
        )
        actual_risk_pct = (
            (actual_risk_idr / capital) * 100 if capital > 0 else 0.0
        )

        # Risk Reward Ratio (RRR)
        reward_tp1 = tp1_price - entry_price
        rrr_tp1 = (
            reward_tp1 / risk_per_share_raw if risk_per_share_raw > 0 else 0
        )

        is_capped = (lot_by_cap < lot_by_risk) and (lot_by_risk > 0)

        # ----------------------------------------------------------------------
        # METRIC CARDS DISPLAY (CYBERPUNK THEME)
        # ----------------------------------------------------------------------
        m1, m2, m3 = st.columns(3)

        with m1:
            st.markdown(
                f"""
                <div class="cyber-card">
                    <div class="cyber-label">Recommended Size</div>
                    <div class="cyber-value" style="color:var(--cyber-cyan);">{final_lot:,} LOT</div>
                    <div style="font-size: 11px; color: var(--cyber-text-muted);">({final_shares:,} Lembar)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m2:
            st.markdown(
                f"""
                <div class="cyber-card">
                    <div class="cyber-label">Total Buy Value</div>
                    <div class="cyber-value">Rp {total_buy_value:,.0f}</div>
                    <div style="font-size: 11px; color: var(--cyber-text-muted);">Allocation: {(total_buy_value/capital)*100:.1f}% Modal</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m3:
            if rrr_tp1 >= 2.0:
                rrr_badge_class = "cyber-badge-cyan"
                rrr_status = "EXCELLENT"
            elif rrr_tp1 >= 1.5:
                rrr_badge_class = "cyber-badge-yellow"
                rrr_status = "ACCEPTABLE"
            else:
                rrr_badge_class = "cyber-badge-pink"
                rrr_status = "POOR RISK"

            st.markdown(
                f"""
                <div class="cyber-card">
                    <div class="cyber-label">Risk/Reward (TP1)</div>
                    <div class="cyber-value">1 : {rrr_tp1:.2f}</div>
                    <span class="cyber-badge {rrr_badge_class}">{rrr_status}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Warning jika jumlah lot terkena Cap Profil Trading
        if is_capped:
            st.warning(
                f"⚠️ **[CAP ALERT] Size Dibatasi Strategy Profile!** Toleransi risk mengizinkan **{lot_by_risk:,} Lot**, "
                f"tetapi dibatasi menjadi **{final_lot:,} Lot** agar tidak melewati alokasi max {max_alloc_pct}% ({trading_style})."
            )

        # ----------------------------------------------------------------------
        # SCALING OUT / PARTIAL PROFIT TAKING PLANNER
        # ----------------------------------------------------------------------
        st.markdown("---")
        st.subheader("✂️ Partial Profit Taking Execution Plan")

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
                    <h4 style="margin:0; color:var(--cyber-cyan); font-size:15px;">Tahap 1: Sell 50% Lot @ TP1</h4>
                    <p style="margin:6px 0; font-size:13px;">Jual <b>{lot_tp1:,} Lot</b> @ <b>Rp {tp1_price:,.0f}</b></p>
                    <p style="margin:0; font-size:12px; color:var(--cyber-text-muted);">Estimated Profit: <b style="color:var(--cyber-green);">+Rp {p_tp1:,.0f}</b></p>
                    <hr style="margin:10px 0; border-color:var(--cyber-card-border);">
                    <span style="font-size:11px; color:var(--cyber-yellow);">📌 Action: Geser SL sisa lot ke Break Even (Rp {entry_price:,.0f})</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with sc2:
            st.markdown(
                f"""
                <div class="cyber-card">
                    <h4 style="margin:0; color:var(--cyber-cyan); font-size:15px;">Tahap 2: Sell 50% Lot @ TP2</h4>
                    <p style="margin:6px 0; font-size:13px;">Jual <b>{lot_tp2:,} Lot</b> @ <b>Rp {tp2_price:,.0f}</b></p>
                    <p style="margin:0; font-size:12px; color:var(--cyber-text-muted);">Estimated Profit: <b style="color:var(--cyber-green);">+Rp {p_tp2:,.0f}</b></p>
                    <hr style="margin:10px 0; border-color:var(--cyber-card-border);">
                    <span style="font-size:11px; color:var(--cyber-cyan);">💰 Max Potential Return: <b style="color:var(--cyber-green);">+Rp {total_potential_profit:,.0f}</b></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------------------------
        # PLOTLY CYBERPUNK CHARTS VISUALIZATION
        # ----------------------------------------------------------------------
        st.markdown("---")
        st.subheader("📈 Risk Visualizer & Capital Exposure")

        v1, v2 = st.columns(2)

        # Plot 1: Gauge Risk Tracker
        with v1:
            st.markdown(
                f'<div class="cyber-header">Risk Exposure Ratio ({risk_pct}%)</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="cyber-subheader">Actual Risk IDR: Rp {actual_risk_idr:,.0f}</div>',
                unsafe_allow_html=True,
            )

            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=actual_risk_pct,
                    number={
                        "suffix": "%",
                        "valueformat": ".2f",
                        "font": {
                            "color": "#00f3ff",
                            "family": "Courier New",
                        },
                    },
                    delta={
                        "reference": risk_pct,
                        "relative": False,
                        "position": "top",
                    },
                    domain={"x": [0, 1], "y": [0, 1]},
                    gauge={
                        "axis": {
                            "range": [0, max(10.0, risk_pct * 1.2)],
                            "tickwidth": 1,
                            "tickcolor": "#8d9bb0",
                        },
                        "bar": {
                            "color": (
                                "#00f3ff"
                                if actual_risk_pct <= risk_pct
                                else "#ff0055"
                            )
                        },
                        "steps": [
                            {
                                "range": [0, risk_pct],
                                "color": "rgba(0, 243, 255, 0.15)",
                            },
                            {
                                "range": [risk_pct, 10.0],
                                "color": "rgba(255, 0, 85, 0.15)",
                            },
                        ],
                        "threshold": {
                            "line": {"color": "#ffe600", "width": 4},
                            "thickness": 0.75,
                            "value": risk_pct,
                        },
                    },
                )
            )
            fig_gauge.update_layout(
                height=220,
                margin=dict(l=20, r=20, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#ffffff"},
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        # Plot 2: Donut Capital Exposure Chart
        with v2:
            st.markdown(
                '<div class="cyber-header">Capital Allocation Exposure</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="cyber-subheader">Position Value vs Available Liquidity</div>',
                unsafe_allow_html=True,
            )

            cash_left = max(0.0, capital - total_cost_with_fee)
            fig_donut = go.Figure(
                data=[
                    go.Pie(
                        labels=[
                            f"Posisi {clean_ticker}",
                            "Unallocated Liquidity",
                        ],
                        values=[total_cost_with_fee, cash_left],
                        hole=0.6,
                        marker_colors=["#00f3ff", "#1e2638"],
                        hoverinfo="label+value+percent",
                        textinfo="percent",
                    )
                ]
            )
            fig_donut.update_layout(
                height=220,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#ffffff"},
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5,
                ),
            )
            st.plotly_chart(fig_donut, use_container_width=True)
