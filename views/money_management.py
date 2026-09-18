import math
from typing import Dict, Any, Tuple, Optional

# views/money_management.py

def render_page_money_management():
    # Isi logika streamlit kamu di sini
    pass
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
    """
    Format ticker saham lokal/IDX.
    Returns: (clean_ticker, full_ticker)
    """
    clean = raw_ticker.upper().replace(".JK", "").strip() or "COCO"
    return clean, f"{clean}.JK"


def sync_trade_plan_data(
    trade_planner_cls: Any,
    full_ticker: str,
    plan_type: str
) -> Optional[Dict[str, float]]:
    """
    Mengambil data Trade Plan dari instance TradePlanner eksternal.
    """
    if not trade_planner_cls:
        return None

    try:
        planner = trade_planner_cls(ticker=full_ticker)
        planner.fetch_and_prepare_data()
        df_plan = planner.generate_trade_plan()

        matched = df_plan[df_plan["Type"] == plan_type]
        if matched.empty:
            matched = df_plan

        row = matched.iloc[0]

        return {
            "entry_price": float(row["Range Buy Min"]),
            "sl_price": float(row["Stop Loss"]),
            "tp1_price": float(row["TP 1"]),
            "tp2_price": float(row["TP 2"]),
        }
    except Exception:
        return None


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
        
        # Konversi Fee Persentase ke Desimal
        self.fee_buy = fee_buy_pct / 100.0
        self.fee_sell = fee_sell_pct / 100.0

        # Ambil Aturan Profil
        self.rule = PROFILE_RULES.get(
            trading_style, PROFILE_RULES["Swing Trading"]
        )

    def validate(self) -> Tuple[bool, str]:
        """Validasi dasar kriteria input."""
        if self.sl_price >= self.entry_price:
            return False, "Stop Loss (SL) harus lebih kecil dari Harga Entry!"
        if self.capital <= 0:
            return False, "Capital harus lebih besar dari 0!"
        return True, ""

    def calculate(self) -> Dict[str, Any]:
        """Menjalankan seluruh logika perhitungan posisi & risiko."""
        is_valid, msg = self.validate()
        if not is_valid:
            raise ValueError(msg)

        # 1. Calculation per Share (With Fee)
        risk_per_share_raw = self.entry_price - self.sl_price
        total_risk_per_share_with_fee = (
            self.entry_price * (1 + self.fee_buy)
        ) - (self.sl_price * (1 - self.fee_sell))

        # 2. Risk-Based Position Sizing
        max_risk_allowed_idr = self.capital * (self.risk_pct / 100.0)
        raw_shares_by_risk = (
            max_risk_allowed_idr / total_risk_per_share_with_fee
        )
        lot_by_risk = math.floor(raw_shares_by_risk / 100.0)

        # 3. Capital-Based Position Sizing (Max Alloc Profile Limit)
        max_alloc_pct = self.rule["max_alloc"]
        max_capital_allowed = self.capital * (max_alloc_pct / 100.0)
        lot_by_cap = math.floor(
            max_capital_allowed / (self.entry_price * 100 * (1 + self.fee_buy))
        )

        # 4. Final Position Sizing Decision
        final_lot = min(lot_by_risk, lot_by_cap)
        final_shares = final_lot * 100
        total_buy_value = final_shares * self.entry_price
        total_cost_with_fee = total_buy_value * (1 + self.fee_buy)

        # 5. Actual Realized Risk Metrics
        if final_lot > 0:
            actual_risk_idr = (
                final_shares * self.entry_price * (1 + self.fee_buy)
            ) - (final_shares * self.sl_price * (1 - self.fee_sell))
        else:
            actual_risk_idr = 0.0

        actual_risk_pct = (
            (actual_risk_idr / self.capital) * 100.0 if self.capital > 0 else 0.0
        )

        # 6. Risk / Reward Ratio (RRR)
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

        # 7. Partial Profit Taking Plan (50% TP1 & 50% TP2)
        lot_tp1 = math.floor(final_lot * 0.5)
        lot_tp2 = final_lot - lot_tp1

        p_tp1 = (lot_tp1 * 100 * self.tp1_price) * (1 - self.fee_sell) - (
            lot_tp1 * 100 * self.entry_price * (1 + self.fee_buy)
        )
        p_tp2 = (lot_tp2 * 100 * self.tp2_price) * (1 - self.fee_sell) - (
            lot_tp2 * 100 * self.entry_price * (1 + self.fee_buy)
        )
        total_potential_profit = p_tp1 + p_tp2

        # 8. Exposure Data
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
# EXAMPLE USAGE / UNIT TEST
# ==============================================================================
if __name__ == "__main__":
    engine = MoneyManagementEngine(
        capital=100_000_000,
        trading_style="Swing Trading",
        risk_pct=1.0,
        entry_price=125.0,
        sl_price=120.0,
        tp1_price=151.0,
        tp2_price=216.0,
        fee_buy_pct=0.15,
        fee_sell_pct=0.25,
    )

    result = engine.calculate()
    print("=== MONEY MANAGEMENT RESULT ===")
    print(f"Recommended Size : {result['final_lot']} Lot ({result['final_shares']} shares)")
    print(f"Total Buy Value  : Rp {result['total_buy_value']:,.0f}")
    print(f"Actual Risk (%)  : {result['actual_risk_pct']:.2f}%")
    print(f"RRR Status       : {result['rrr_status']} (1 : {result['rrr_tp1']:.2f})")
    print(f"TP1 Profit Est.  : Rp {result['partial_tp']['tp1']['estimated_profit']:,.0f}")
    print(f"Total Profit Est.: Rp {result['partial_tp']['total_potential_profit']:,.0f}")
