import math
from typing import Dict, Any, Tuple
import streamlit as st


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
# 2. CORE CALCULATION ENGINE
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
            "capital_alloc_pct": (total_buy_value / self.capital) * 100.0 if self.capital > 0 else 0.0,
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
# 3. STREAMLIT UI RENDER FUNCTION
# ==============================================================================
def render_page_money_management():
    st.markdown("## 💰 MONEY MANAGEMENT ENGINE")
    st.caption("System Execution & Position Sizing Analytics for IDX Trading")

    col_input, col_output = st.columns([1.1, 1.9], gap="large")

    with col_input:
        st.subheader("⚙️ CONTROL PARAMETERS")

        capital = st.number_input(
            "Total Capital (IDR)",
            min_value=1_000_000,
            value=100_000_000,
            step=5_000_000,
            key="mm_cap",
        )
        trading_style = st.selectbox(
            "Trading Strategy Profile",
            list(PROFILE_RULES.keys()),
            index=1,
            key="mm_style",
        )
        risk_pct = st.slider(
            "Max Risk Tolerance per Trade (%)",
            min_value=0.25,
            max_value=10.0,
            value=1.0,
            step=0.25,
            key="mm_risk",
        )

        st.markdown("---")
        st.subheader("🎯 TRADE SETUP")

        c_entry, c_sl = st.columns(2)
        with c_entry:
            entry_price = st.number_input("Entry Price", min_value=1.0, value=125.0, key="mm_entry")
        with c_sl:
            sl_price = st.number_input("Stop Loss (SL)", min_value=1.0, value=120.0, key="mm_sl")

        c_tp1, c_tp2 = st.columns(2)
        with c_tp1:
            tp1_price = st.number_input("Target Price 1", min_value=1.0, value=151.0, key="mm_tp1")
        with c_tp2:
            tp2_price = st.number_input("Target Price 2", min_value=1.0, value=216.0, key="mm_tp2")

        fee_buy_pct = 0.15
        fee_sell_pct = 0.25

    with col_output:
        st.subheader("📊 POSITION SIZING RESULT")

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

        m1, m2, m3 = st.columns(3)
        m1.metric("RECOMMENDED SIZE", f"{res['final_lot']:,} LOT", f"{res['final_shares']:,} Lembar")
        m2.metric("TOTAL BUY VALUE", f"Rp {res['total_buy_value']:,.0f}", f"Alloc: {res['capital_alloc_pct']:.1f}% Modal")
        m3.metric("RISK / REWARD", f"1 : {res['rrr_tp1']:.2f}", res["rrr_status"])

        if res["is_capped"]:
            st.info(
                f"ℹ️ Toleransi risk mengizinkan **{res['lot_by_risk']:,} Lot**, "
                f"namun dibatasi maksimal **{res['final_lot']:,} Lot** sesuai batas profil {trading_style} ({res['max_alloc_pct']}%)."
            )

        st.markdown("---")
        st.subheader("🎯 PARTIAL PROFIT TAKING PLAN")
        sc1, sc2 = st.columns(2)
        tp1_data = res["partial_tp"]["tp1"]
        tp2_data = res["partial_tp"]["tp2"]

        with sc1:
            st.markdown("##### TAHAP 1: SELL 50% @ TP1")
            st.write(f"• Size: **{tp1_data['lot']:,} Lot** @ **Rp {tp1_data['target_price']:,.0f}**")
            st.write(f"• Est. Profit: **+Rp {tp1_data['estimated_profit']:,.0f}**")

        with sc2:
            st.markdown("##### TAHAP 2: SELL 50% @ TP2")
            st.write(f"• Size: **{tp2_data['lot']:,} Lot** @ **Rp {tp2_data['target_price']:,.0f}**")
            st.write(f"• Est. Profit: **+Rp {tp2_data['estimated_profit']:,.0f}**")
            st.write(f"• Total Profit Est: **+Rp {res['partial_tp']['total_potential_profit']:,.0f}**")
