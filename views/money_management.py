import math
from typing import Dict, Any, Tuple, Optional
import streamlit as st
import plotly.graph_objects as go

# Safe import TradePlanner dari modul backend
try:
    from engines.trade_planner import TradePlanner
except ImportError:
    TradePlanner = None


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
# 2. HELPER & SYNC LOGIC
# ==============================================================================
def format_ticker_symbol(raw_ticker: str) -> Tuple[str, str]:
    clean = raw_ticker.upper().replace(".JK", "").strip() or "COCO"
    return clean, f"{clean}.JK"


def fetch_trade_plan(full_ticker: str, plan_type: str, clean_ticker: str) -> bool:
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


def clear_ticker_callback():
    st.session_state["mm_raw_ticker_input"] = ""
    st.session_state["selected_watchlist_ticker"] = ""


# ==============================================================================
# 3. CORE CALCULATION ENGINE
# ==============================================================================
class MoneyManagementEngine:
    def __init__(
        self,
        capital: float,
        trading_style: str,
        risk_pct: float,
        entry_price: float,
        sl_price: float,
        tp1_price: float,
        tp2_price: float,
        fee_buy_pct: float = 0.15,
        fee_sell_pct: float = 0.25,
    ):
        self.capital = capital
        self.trading_style = trading_style
        self.risk_pct = risk_pct
        self.entry_price = entry_price
        self.sl_price = sl_price
        self.tp1_price = tp1_price
        self.tp2_price = tp2_price

        self.fee_buy = fee_buy_pct / 100.0
        self.fee_sell = fee_sell_pct / 100.0

        self.rule = PROFILE_RULES.get(
            trading_style, PROFILE_RULES["Swing Trading"]
        )

    def validate(self) -> Tuple[bool, str]:
        if self.sl_price >= self.entry_price:
            return False, "Stop Loss (SL) harus lebih kecil dari Harga Entry!"
        if self.capital <= 0:
            return False, "Capital harus lebih besar dari 0!"
        return True, ""

    def calculate(self) -> Dict[str, Any]:
        is_valid, msg = self.validate()
        if not is_valid:
            raise ValueError(msg)

        risk_per_share_raw = self.entry_price - self.sl_price
        total_risk_per_share_with_fee = (
            self.entry_price * (1 + self.fee_buy)
        ) - (self.sl_price * (1 - self.fee_sell))

        max_risk_allowed_idr = self.capital * (self.risk_pct / 100.0)
        raw_shares_by_risk = (
            max_risk_allowed_idr / total_risk_per_share_with_fee
            if total_risk_per_share_with_fee > 0 else 0
        )
        lot_by_risk = math.floor(raw_shares_by_risk / 100.0)

        max_alloc_pct = self.rule["max_alloc"]
        max_capital_allowed = self.capital * (max_alloc_pct / 100.0)
        lot_by_cap = math.floor(
            max_capital_allowed / (self.entry_price * 100 * (1 + self.fee_buy))
        )

        final_lot = max(0, min(lot_by_risk, lot_by_cap))
        final_shares = final_lot * 100
        total_buy_value = final_shares * self.entry_price
        total_cost_with_fee = total_buy_value * (1 + self.fee_buy)

        if final_lot > 0:
            actual_risk_idr = (
                final_shares * self.entry_price * (1 + self.fee_buy)
            ) - (final_shares * self.sl_price * (1 - self.fee_sell))
        else:
            actual_risk_idr = 0.0

        actual_risk_pct = (
            (actual_risk_idr / self.capital) * 100.0 if self.capital > 0 else 0.0
        )

        reward_tp1 = self.tp1_price - self.entry_price
        rrr_tp1 = (
            reward_tp1 / risk_per_share_raw if risk_per_share_raw > 0 else 0.0
        )

        if rrr_tp1 >= 2.0:
            rrr_status = "EXCELLENT"
        elif rrr_tp1 >= 1.5:
            rrr_status = "ACCEPTABLE"
        else:
            rrr_status = "POOR RISK"

        is_capped = (lot_by_cap < lot_by_risk) and (lot_by_risk > 0)

        lot_tp1 = math.floor(final_lot * 0.5)
        lot_tp2 = final_lot - lot_tp1

        p_tp1 = (lot_tp1 * 100 * self.tp1_price) * (1 - self.fee_sell) - (
            lot_tp1 * 100 * self.entry_price * (1 + self.fee_buy)
        )
        p_tp2 = (lot_tp2 * 100 * self.tp2_price) * (1 - self.fee_sell) - (
            lot_tp2 * 100 * self.entry_price * (1 + self.fee_buy)
        )
        total_potential_profit = p_tp1 + p_tp2

        cash_left = max(0.0, self.capital - total_cost_with_fee)

        return {
            "final_lot": final_lot,
            "final_shares": final_shares,
            "total_buy_value": total_buy_value,
            "total_cost_with_fee": total_cost_with_fee,
            "capital_alloc_pct": (total_buy_value / self.capital) * 100.0,
            "actual_risk_idr": actual_risk_idr,
            "actual_risk_pct": actual_risk_pct,
            "rrr_tp1": rrr_tp1,
            "rrr_status": rrr_status,
            "is_capped": is_capped,
            "lot_by_risk": lot_by_risk,
            "lot_by_cap": lot_by_cap,
            "max_alloc_pct": max_alloc_pct,
            "partial_tp": {
                "tp1": {
                    "lot": lot_tp1,
                    "target_price": self.tp1_price,
                    "estimated_profit": p_tp1,
                    "action": f"Set Break-Even SL @ Rp {self.entry_price:,.0f}",
                },
                "tp2": {
                    "lot": lot_tp2,
                    "target_price": self.tp2_price,
                    "estimated_profit": p_tp2,
                },
                "total_potential_profit": total_potential_profit,
            },
            "exposure": {
                "used_capital": total_cost_with_fee,
                "cash_remaining": cash_left,
            },
        }


# ==============================================================================
# 4. STREAMLIT UI RENDER FUNCTION
# ==============================================================================
def render_page_money_management():
    """Render utama Halaman Money Management."""
    st.title("MONEY MANAGEMENT ENGINE")
    st.caption("System Execution & Position Sizing Analytics for IDX Trading")

    # Set Session State Defaults
    st.session_state.setdefault("input_entry_price", 125.0)
    st.session_state.setdefault("input_sl_price", 120.0)
    st.session_state.setdefault("input_tp1_price", 151.0)
    st.session_state.setdefault("input_tp2_price", 216.0)

    # Layout Grid Utama
    col_input, col_output = st.columns([1.1, 1.9], gap="large")

    # --------------------------------------------------------------------------
    # KOLOM 1: CONTROL PARAMETERS
    # --------------------------------------------------------------------------
    with col_input:
        st.header("SYSTEM CONTROLS")

        with st.expander("CAPITAL & TRADER PROFILE", expanded=True):
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
            st.caption(f"*{rule['desc']}*")

        with st.expander("TRADE EXECUTION SETUP", expanded=True):
            # Watchlist Dropdown Sync
            watchlist_items = st.session_state.get("watchlist_data", [])
            if watchlist_items:
                wl_tickers = ["-- Pilih dari Watchlist --"] + [
                    x.get("Ticker", "").replace(".JK", "")
                    for x in watchlist_items
                    if isinstance(x, dict)
                ]
                selected_from_wl = st.selectbox(
                    "Ambil dari Watchlist",
                    wl_tickers,
                    key="mm_select_from_watchlist",
                )
                if selected_from_wl != "-- Pilih dari Watchlist --":
                    st.session_state["mm_raw_ticker_input"] = selected_from_wl

            # Input Ticker & Clear Button
            col_tinput, col_tclear = st.columns([3, 1], vertical_alignment="bottom")
            with col_tinput:
                default_ticker = st.session_state.get("mm_raw_ticker_input", "COCO")
                ticker_input = st.text_input(
                    "Ticker Code",
                    value=default_ticker,
                    key="mm_raw_ticker_input",
                    placeholder="COCO / BBCA",
                ).strip()

            with col_tclear:
                st.button(
                    "Clear",
                    key="btn_clear_ticker",
                    on_click=clear_ticker_callback,
                    use_container_width=True,
                )

            clean_ticker, full_ticker = format_ticker_symbol(ticker_input)

            # Strategy Checklist
            st.caption("Trade Strategy Type")
            c_chk1, c_chk2 = st.columns(2)
            with c_chk1:
                chk_bow = st.checkbox("BOW (Buy on Weakness)", value=True, key="chk_strat_bow")
            with c_chk2:
                chk_bob = st.checkbox("BOB (Buy on Breakout)", value=False, key="chk_strat_bob")

            active_plan_type = "BOW" if chk_bow else ("BOB" if chk_bob else "BOW")

            if st.button("Sync with Trade Planner", use_container_width=True):
                if fetch_trade_plan(full_ticker, active_plan_type, clean_ticker):
                    st.rerun()

            # Entry, SL, TP Inputs
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

        with st.expander("BROKERAGE FEES", expanded=False):
            fee_buy_pct = st.number_input(
                "Buy Fee (%)",
                min_value=0.0,
                value=0.15,
                step=0.01,
                key="mm_fee_buy",
            )
            fee_sell_pct = st.number_input(
                "Sell Fee (%)",
                min_value=0.0,
                value=0.25,
                step=0.01,
                key="mm_fee_sell",
            )

    # --------------------------------------------------------------------------
    # KOLOM 2: ANALYTICS OUTPUT
    # --------------------------------------------------------------------------
    with col_output:
        st.header("POSITION SIZING ANALYTICS")

        # Inisialisasi Engine & Eksekusi Kalkulasi
        engine = MoneyManagementEngine(
            capital=capital,
            trading_style=trading_style,
            risk_pct=risk_pct,
            entry_price=entry_price,
            sl_price=sl_price,
            tp1_price=tp1_price,
            tp2_price=tp2_price,
            fee_buy_pct=fee_buy_pct,
            fee_sell_pct=fee_sell_pct,
        )

        is_valid, err_msg = engine.validate()
        if not is_valid:
            st.warning(f"⚠️ {err_msg}")
            return

        res = engine.calculate()

        # Display Metrik Utama
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(
                label="RECOMMENDED SIZE",
                value=f"{res['final_lot']:,} LOT",
                delta=f"{res['final_shares']:,} Lembar",
                delta_color="off",
            )
        with m2:
            st.metric(
                label="TOTAL BUY VALUE",
                value=f"Rp {res['total_buy_value']:,.0f}",
                delta=f"Alloc: {res['capital_alloc_pct']:.1f}% Modal",
                delta_color="off",
            )
        with m3:
            st.metric(
                label="RISK / REWARD",
                value=f"1 : {res['rrr_tp1']:.2f}",
                delta=res["rrr_status"],
                delta_color="normal" if res["rrr_tp1"] >= 1.5 else "inverse",
            )

        if res["is_capped"]:
            st.warning(
                f"Toleransi risk mengizinkan {res['lot_by_risk']:,} Lot, "
                f"namun dibatasi max {res['final_lot']:,} Lot sesuai profil {trading_style} ({res['max_alloc_pct']}%)."
            )

        # Rencana Partial Profit Taking
        st.subheader("PARTIAL PROFIT TAKING PLAN")
        sc1, sc2 = st.columns(2)
        tp1_data = res["partial_tp"]["tp1"]
        tp2_data = res["partial_tp"]["tp2"]

        with sc1:
            st.markdown("### TAHAP 1: SELL 50% @ TP1")
            st.write(f"Jual **{tp1_data['lot']:,} Lot** @ **Rp {tp1_data['target_price']:,.0f}**")
            st.write(f"Est. Profit: **+Rp {tp1_data['estimated_profit']:,.0f}**")
            st.caption(f"Action: {tp1_data['action']}")

        with sc2:
            st.markdown("### TAHAP 2: SELL 50% @ TP2")
            st.write(f"Jual **{tp2_data['lot']:,} Lot** @ **Rp {tp2_data['target_price']:,.0f}**")
            st.write(f"Est. Profit: **+Rp {tp2_data['estimated_profit']:,.0f}**")
            st.write(f"Total Potential: **+Rp {res['partial_tp']['total_potential_profit']:,.0f}**")

        # Plotly Visualizers
        st.subheader("RISK VISUALIZER & EXPOSURE")
        v1, v2 = st.columns(2)

        with v1:
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=res["actual_risk_pct"],
                    number={"suffix": "%"},
                    domain={"x": [0, 1], "y": [0, 1]},
                    gauge={
                        "axis": {"range": [0, max(10.0, risk_pct * 1.5)]},
                        "steps": [
                            {"range": [0, risk_pct]},
                            {"range": [risk_pct, 10.0]},
                        ],
                    },
                )
            )
            fig_gauge.update_layout(
                height=180,
                margin=dict(l=20, r=20, t=10, b=10),
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        with v2:
            fig_donut = go.Figure(
                data=[
                    go.Pie(
                        labels=[f"Posisi {clean_ticker}", "Cash"],
                        values=[
                            res["exposure"]["used_capital"],
                            res["exposure"]["cash_remaining"],
                        ],
                        hole=0.6,
                    )
                ]
            )
            fig_donut.update_layout(
                height=180,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig_donut, use_container_width=True)


# Untuk testing lokal/langsung
if __name__ == "__main__":
    render_page_money_management()
