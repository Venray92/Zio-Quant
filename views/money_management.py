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
# CYBERPUNK COLOR INJECTION (Cyan untuk System Controls, Magenta untuk Analytics)
# ==============================================================================
def inject_custom_theme():
    st.markdown(
        """
        <style>
            /* 1. Warna Cyan untuk System Controls (Sebelah Kiri) */
            h3:has(+ div [data-testid="stExpander"]),
            .stExpander summary span,
            .stExpander p,
            label.st-bp,
            div[data-baseweb="form-control"] label,
            .stTextInput label,
            .stNumberInput label,
            .stSelectbox label,
            .stSlider label {
                color: #00FFFF !important;
            }
            
            .stExpander {
                border: 1px solid #00FFFF !important;
                border-radius: 4px;
            }
            
            div[data-baseweb="input"] > div, 
            div[data-baseweb="select"] > div, 
            div[data-baseweb="base-input"] {
                border-color: #00FFFF !important;
            }
            
            .stButton > button {
                border: 1px solid #00FFFF !important;
                color: #00FFFF !important;
            }

            /* 2. Warna Magenta untuk Sisi Kanan (Position Sizing Analytics & Kontainer Hasil) */
            div[data-testid="column"]:nth-of-type(2) h2,
            div[data-testid="column"]:nth-of-type(2) h3,
            div[data-testid="column"]:nth-of-type(2) h5,
            div[data-testid="column"]:nth-of-type(2) p,
            div[data-testid="column"]:nth-of-type(2) span,
            div[data-testid="column"]:nth-of-type(2) label {
                color: #FF00FF !important;
            }

            Mengubah Kotak Metrik di Sebelah Kanan menjadi Border Magenta 
            div[data-testid="column"]:nth-of-type(2) div[data-testid="stMetric"] {
                border: 1px solid #FF00FF !important;
                padding: 10px;
                border-radius: 5px;
            }

            /* Mengubah Kotak Warning/Peringatan yang tadinya Kuning menjadi Magenta */
            div[data-testid="stAlert"] {
                background-color: rgba(255, 0, 255, 0.1) !important;
                border: 1px solid #FF00FF !important;
                color: #FF00FF !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ==============================================================================
# 1. STRATEGY RULES CONSTANTS
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
# 2. HELPER FUNCTIONS
# ==============================================================================
def fetch_trade_plan(full_ticker: str, plan_type: str, clean_ticker: str) -> bool:
    """Mengambil data Trade Plan dari TradePlanner engine backend."""
    if not TradePlanner:
        st.error("Modul `TradePlanner` tidak ditemukan.")
        return False

    try:
        with st.spinner(f"Syncing Trade Plan {full_ticker}..."):
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
        st.error(f"Gagal sinkronisasi {clean_ticker}: {e}")
        return False


def clear_ticker_callback():
    """Callback untuk mengosongkan input ticker dan session state terkait."""
    st.session_state["mm_raw_ticker_input"] = ""
    st.session_state["selected_watchlist_ticker"] = ""


def toggle_bow():
    """Memastikan hanya salah satu checkbox (BOW/BOB) yang aktif."""
    if st.session_state.get("chk_strat_bow", False):
        st.session_state["chk_strat_bob"] = False

def toggle_bob():
    """Memastikan hanya salah satu checkbox (BOW/BOB) yang aktif."""
    if st.session_state.get("chk_strat_bob", False):
        st.session_state["chk_strat_bow"] = False


# ==============================================================================
# 3. MAIN RENDER FUNCTION
# ==============================================================================
def render_page_money_management():
    """Render utama Halaman Money Management."""
    inject_custom_theme()

    st.title("Money Management Engine")
    st.caption("System Execution & Position Sizing Analytics for IDX Trading")
    st.markdown("---")

    # Grid Utama
    col_input, col_output = st.columns([1.1, 1.9], gap="large")

    # --------------------------------------------------------------------------
    # KOLOM 1: PARAMETER INPUT CONTROL
    # --------------------------------------------------------------------------
    with col_input:
        st.subheader("System Controls")

        with st.expander("Capital & Trader Profile", expanded=True):
            # Menggunakan text_input agar bebas tanpa titik, koma, atau IDR
            raw_capital_str = st.text_input(
                "Total Capital (IDR)",
                value="100000000",
                key="mm_capital_text_input"
            )
            try:
                capital = float(raw_capital_str.replace(".", "").replace(",", "").strip())
            except ValueError:
                capital = 100000000.0

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
            st.info(f"{rule['desc']}")

        with st.expander("Trade Execution Setup", expanded=True):
            st.session_state.setdefault("input_entry_price", 125.0)
            st.session_state.setdefault("input_sl_price", 120.0)
            st.session_state.setdefault("input_tp1_price", 151.0)
            st.session_state.setdefault("input_tp2_price", 216.0)

            # Fitur Pilih dari Watchlist
            watchlist_items = st.session_state.get("watchlist_data", [])
            if watchlist_items:
                wl_tickers = ["-- Pilih dari Watchlist --"] + [
                    x.get("Ticker", "").replace(".JK", "") for x in watchlist_items if isinstance(x, dict)
                ]
                selected_from_wl = st.selectbox(
                    "Ambil dari Watchlist",
                    wl_tickers,
                    key="mm_select_from_watchlist"
                )
                if selected_from_wl != "-- Pilih dari Watchlist --":
                    st.session_state["mm_raw_ticker_input"] = selected_from_wl

            # Kolom Ticker Input berdampingan dengan Tombol Clear
            col_tinput, col_tclear = st.columns([3, 1], vertical_alignment="bottom")

            with col_tinput:
                default_ticker_val = st.session_state.get("mm_raw_ticker_input", "")
                ticker_input = st.text_input(
                    "Ticker Code",
                    value=default_ticker_val,
                    key="mm_raw_ticker_input",
                    placeholder="COCO / BBCA",
                ).strip()

            with col_tclear:
                st.button("Clear", key="btn_clear_ticker", on_click=clear_ticker_callback, use_container_width=True)

            clean_ticker = (
                ticker_input.upper().replace(".JK", "").strip() or "COCO"
            )
            full_ticker = f"{clean_ticker}.JK"

            st.write("Trade Strategy Type (Checklist)")
            c_chk1, c_chk2 = st.columns(2)
            with c_chk1:
                chk_bow = st.checkbox("BOW (Buy on Weakness)", value=True, key="chk_strat_bow", on_change=toggle_bow)
            with c_chk2:
                chk_bob = st.checkbox("BOB (Buy on Breakout)", value=False, key="chk_strat_bob", on_change=toggle_bob)

            active_plan_type = "BOW" if chk_bow else ("BOB" if chk_bob else "BOW")

            if st.button("Sync with Trade Planner", use_container_width=True):
                if fetch_trade_plan(full_ticker, active_plan_type, clean_ticker):
                    st.rerun()

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

        with st.expander("Brokerage Fees", expanded=False):
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
    # KOLOM 2: ANALYTICS OUTPUT
    # --------------------------------------------------------------------------
    with col_output:
        st.subheader("Position Sizing Analytics")

        # Validasi Input Logic
        if sl_price >= entry_price:
            st.error("Stop Loss (SL) harus LEBIH KECIL dari Harga Entry!")
            return

        # Core Calculation Engine
        max_risk_allowed_idr = capital * (risk_pct / 100)
        risk_per_share_raw = entry_price - sl_price
        total_risk_per_share_with_fee = (entry_price * (1 + fee_buy)) - (
            sl_price * (1 - fee_sell)
        )

        raw_shares_by_risk = (
            max_risk_allowed_idr / total_risk_per_share_with_fee
        )
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
        actual_risk_pct = (
            (actual_risk_idr / capital) * 100 if capital > 0 else 0.0
        )

        reward_tp1 = tp1_price - entry_price
        rrr_tp1 = (
            reward_tp1 / risk_per_share_raw if risk_per_share_raw > 0 else 0
        )
        is_capped = (lot_by_cap < lot_by_risk) and (lot_by_risk > 0)

        # 3 Metrics Display
        m1, m2, m3 = st.columns(3)
        m1.metric("Recommended Size", f"{final_lot:,} Lot", f"{final_shares:,} Lembar")
        m2.metric("Total Buy Value", f"Rp {total_buy_value:,.0f}", f"Alloc: {(total_buy_value/capital)*100:.1f}%")
        
        if rrr_tp1 >= 2.0:
            rrr_status = "EXCELLENT"
        elif rrr_tp1 >= 1.5:
            rrr_status = "ACCEPTABLE"
        else:
            rrr_status = "POOR RISK"
        
        m3.metric("Risk / Reward", f"1 : {rrr_tp1:.2f}", rrr_status)

        if is_capped:
            st.markdown(
                f"""
                <div style="background: rgba(0, 243, 255, 0.08); border: 1px solid #00F3FF; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; color: #00F3FF; font-family: 'Share Tech Mono', monospace; font-size: 13px; box-shadow: 0 0 10px rgba(0, 243, 255, 0.2);">
                    ⚡ Toleransi risk mengizinkan <strong>{lot_by_risk:,} Lot</strong>, namun dibatasi max <strong>{final_lot:,} Lot</strong> sesuai profil {trading_style} ({max_alloc_pct}%).
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")

        st.markdown("---")
        st.subheader("Partial Profit Taking Plan")

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
            st.markdown("##### TAHAP 1: SELL 50% @ TP1")
            st.write(f"- Size: **{lot_tp1:,} Lot** @ **Rp {tp1_price:,.0f}**")
            st.write(f"- Est. Profit: **+Rp {p_tp1:,.0f}**")
            st.caption(f"Action: Set Break-Even SL @ Rp {entry_price:,.0f}")

        with sc2:
            st.markdown("##### TAHAP 2: SELL 50% @ TP2")
            st.write(f"- Size: **{lot_tp2:,} Lot** @ **Rp {tp2_price:,.0f}**")
            st.write(f"- Est. Profit: **+Rp {p_tp2:,.0f}**")
            st.write(f"- Total Potential Profit: **+Rp {total_potential_profit:,.0f}**")

        # Plotly Visualizers
        st.markdown("---")
        st.subheader("Risk Visualizer & Exposure")

        v1, v2 = st.columns(2)

        with v1:
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=actual_risk_pct,
                    number={"suffix": "%"},
                    domain={"x": [0, 1], "y": [0, 1]},
                    gauge={
                        "axis": {"range": [0, max(10.0, risk_pct * 1.5)]},
                    },
                )
            )
            fig_gauge.update_layout(
                height=180,
                margin=dict(l=20, r=20, t=10, b=10),
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
                    )
                ]
            )
            fig_donut.update_layout(
                height=180,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=True,
            )
            st.plotly_chart(fig_donut, use_container_width=True)
