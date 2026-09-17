import math
import streamlit as st
from ui_helpers import (
    render_metric_card,
    render_portfolio_pie_chart,
    render_risk_gauge_chart,
    render_scaling_card,
)

try:
    from engines.trade_planner import TradePlanner
except ImportError:
    TradePlanner = None

# --- CONFIG PROFIL TRADING ---
PROFILE_RULES = {
    "Scalping / Fast Trade": {
        "max_alloc": 10.0,
        "desc": "Frekuensi tinggi, tahan posisi < 1 hari. Risiko ketat.",
    },
    "Swing Trading": {
        "max_alloc": 20.0,
        "desc": "Sweet spot IDX. Holding period 3 hari - 3 minggu.",
    },
    "Trend Following": {
        "max_alloc": 25.0,
        "desc": "Riding trend berbulan-bulan sampai tren patah.",
    },
    "Investing (Value/Growth)": {
        "max_alloc": 33.0,
        "desc": "Fokus fundamental, akumulasi bertahap.",
    },
}


def sync_trade_plan(full_ticker: str, plan_type: str) -> bool:
    """Helper untuk menyinkronkan data dari TradePlanner ke Session State."""
    if not TradePlanner:
        st.error("Modul `TradePlanner` tidak dapat dimuat.")
        return False
    try:
        with st.spinner(f"Mengambil data Trade Plan {full_ticker}..."):
            planner = TradePlanner(ticker=full_ticker)
            if hasattr(planner, "fetch_and_prepare_data"):
                planner.fetch_and_prepare_data()

            df_plan = (
                planner.generate_trade_plan()
                if hasattr(planner, "generate_trade_plan")
                else None
            )
            if df_plan is not None and not df_plan.empty:
                matched = df_plan[df_plan["Type"] == plan_type]
                row = matched.iloc[0] if not matched.empty else df_plan.iloc[0]

                st.session_state["input_entry_price"] = float(
                    row.get("Range Buy Min", row.get("Buy Min", 100.0))
                )
                st.session_state["input_sl_price"] = float(
                    row.get("Stop Loss", row.get("SL", 95.0))
                )
                st.session_state["input_tp1_price"] = float(
                    row.get("TP 1", row.get("TP1", 110.0))
                )
                st.session_state["input_tp2_price"] = float(
                    row.get("TP 2", row.get("TP2", 120.0))
                )
                return True
            st.warning(f"Trade Plan {full_ticker} tidak ditemukan.")
    except Exception as e:
        st.error(f"Gagal mengambil Trade Plan: {e}")
    return False


def render_page_money_management():
    st.title("🛡️ Position Sizing & Money Management")
    st.caption(
        "Kelola risiko transaksi dan alokasi modal IDX secara presisi berdasarkan profil Anda."
    )

    col_input, col_output = st.columns([1.1, 1.9], gap="large")

    # === LEFT COLUMN: INPUT PARAMETERS ===
    with col_input:
        st.subheader("⚙️ Parameter Setup")

        with st.expander("👤 Modal & Profil Trader", expanded=True):
            capital = st.number_input(
                "Total Modal (Rp)",
                min_value=1_000_000,
                value=100_000_000,
                step=5_000_000,
                format="%d",
                key="mm_capital_input",
            )
            trading_style = st.selectbox(
                "Tipe / Profil Trading",
                list(PROFILE_RULES.keys()),
                index=1,
                key="mm_style_select",
            )
            risk_pct = st.slider(
                "Batas Toleransi Risiko per Trade (%)",
                min_value=0.25,
                max_value=10.0,
                value=1.0,
                step=0.25,
                key="mm_risk_slider",
            )
            rule = PROFILE_RULES[trading_style]
            st.caption(f"ℹ️ *{rule['desc']}*")

        with st.expander("📊 Parameter Transaksi Saham", expanded=True):
            for k, v in [
                ("input_entry_price", 125.0),
                ("input_sl_price", 120.0),
                ("input_tp1_price", 151.0),
                ("input_tp2_price", 216.0),
            ]:
                if k not in st.session_state:
                    st.session_state[k] = v

            raw_ticker = (
                st.session_state.get("mm_ticker", "COCO")
                .upper()
                .replace(".JK", "")
            )
            ticker_input = st.text_input(
                "Ticker Saham (Tanpa .JK)",
                value=raw_ticker,
                key="mm_raw_ticker_input",
            ).strip()
            clean_ticker = (
                ticker_input.upper().replace(".JK", "").strip() or "COCO"
            )
            full_ticker = f"{clean_ticker}.JK"

            plan_type = st.radio(
                "Tipe Trade Plan",
                ["BOW", "BOB"],
                horizontal=True,
                key="mm_plan_type_radio",
            )

            if st.button("🔄 Sync Trade Plan", use_container_width=True):
                if sync_trade_plan(full_ticker, plan_type):
                    st.rerun()

            c_entry, c_sl = st.columns(2)
            with c_entry:
                entry_price = st.number_input(
                    "Harga Beli (Entry)",
                    min_value=1.0,
                    step=1.0,
                    key="input_entry_price",
                )
            with c_sl:
                sl_price = st.number_input(
                    "Harga Cut Loss (SL)",
                    min_value=1.0,
                    step=1.0,
                    key="input_sl_price",
                )

            c_tp1, c_tp2 = st.columns(2)
            with c_tp1:
                tp1_price = st.number_input(
                    "Target Price 1 (TP1)",
                    min_value=1.0,
                    step=1.0,
                    key="input_tp1_price",
                )
            with c_tp2:
                tp2_price = st.number_input(
                    "Target Price 2 (TP2)",
                    min_value=1.0,
                    step=1.0,
                    key="input_tp2_price",
                )

        with st.expander("🛠️ Custom Fee Sekuritas", expanded=False):
            fee_buy = (
                st.number_input(
                    "Fee Beli (%)",
                    min_value=0.0,
                    value=0.15,
                    step=0.01,
                    key="mm_fee_buy",
                )
                / 100
            )
            fee_sell = (
                st.number_input(
                    "Fee Jual (%)",
                    min_value=0.0,
                    value=0.25,
                    step=0.01,
                    key="mm_fee_sell",
                )
                / 100
            )

    # === RIGHT COLUMN: OUTPUT & CALCULATIONS ===
    with col_output:
        st.subheader("🎯 Hasil Logika & Position Sizing")

        if sl_price >= entry_price:
            st.error(
                "❌ Error Logika: Harga Stop Loss (SL) harus LEBIH KECIL dari harga Beli."
            )
            return

        # Core Mathematical Calculations
        max_risk_allowed = capital * (risk_pct / 100)
        total_risk_per_share = (entry_price * (1 + fee_buy)) - (
            sl_price * (1 - fee_sell)
        )
        lot_by_risk = math.floor(
            (max_risk_allowed / total_risk_per_share) / 100
        )

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

        risk_per_share_raw = entry_price - sl_price
        rrr_tp1 = (
            (tp1_price - entry_price) / risk_per_share_raw
            if risk_per_share_raw > 0
            else 0
        )

        # 1. Metric Cards Row
        m1, m2, m3 = st.columns(3)
        with m1:
            render_metric_card(
                "Rekomendasi Size",
                f"{final_lot:,} LOT",
                f"({final_shares:,} Lembar)",
                val_color="#00E676",
            )
        with m2:
            render_metric_card(
                "Total Nilai Pembelian",
                f"Rp {total_buy_value:,.0f}",
                f"Porsi: {(total_buy_value/capital)*100:.1f}% Modal",
            )
        with m3:
            badge_type = (
                "green"
                if rrr_tp1 >= 2.0
                else ("yellow" if rrr_tp1 >= 1.5 else "red")
            )
            badge_text = (
                "EXCELLENT"
                if rrr_tp1 >= 2.0
                else ("ACCEPTABLE" if rrr_tp1 >= 1.5 else "POOR")
            )
            render_metric_card(
                "Risk to Reward (TP1)",
                f"1 : {rrr_tp1:.2f}",
                badge_text=badge_text,
                badge_type=badge_type,
            )

        if (lot_by_cap < lot_by_risk) and (lot_by_risk > 0):
            st.warning(
                f"⚠️ **Jumlah Lot Dibatasi Profil!** Batas risiko ({risk_pct}%) membolehkan **{lot_by_risk:,} Lot**, "
                f"namun dibatasi **{final_lot:,} Lot** agar tidak melebih alokasi max {max_alloc_pct}% ({trading_style})."
            )

        # 2. Scaling Out Section
        st.markdown("---")
        st.subheader("✂️ Rencana Partial Profit Taking (Scaling Out)")

        lot_tp1 = math.floor(final_lot * 0.5)
        lot_tp2 = final_lot - lot_tp1
        p_tp1 = (lot_tp1 * 100 * tp1_price) * (1 - fee_sell) - (
            lot_tp1 * 100 * entry_price * (1 + fee_buy)
        )
        p_tp2 = (lot_tp2 * 100 * tp2_price) * (1 - fee_sell) - (
            lot_tp2 * 100 * entry_price * (1 + fee_buy)
        )

        sc1, sc2 = st.columns(2)
        with sc1:
            render_scaling_card(
                "Tahap 1: Sell 50% Lot @ TP1",
                lot_tp1,
                tp1_price,
                p_tp1,
                f"📌 Action: Geser SL sisa lot ke harga BEP (Rp {entry_price:,.0f})",
                "yellow",
            )
        with sc2:
            render_scaling_card(
                "Tahap 2: Sell 50% Lot @ TP2",
                lot_tp2,
                tp2_price,
                p_tp2,
                f"💰 Total Potensi Profit: +Rp {p_tp1 + p_tp2:,.0f}",
                "green",
            )

        # 3. Charts Section
        st.markdown("---")
        st.subheader("📈 Visualisasi Risiko & Alokasi Portfolio")
        v1, v2 = st.columns(2)
        with v1:
            st.plotly_chart(
                render_risk_gauge_chart(actual_risk_pct, risk_pct),
                use_container_width=True,
            )
        with v2:
            st.plotly_chart(
                render_portfolio_pie_chart(
                    clean_ticker, total_cost_with_fee, capital
                ),
                use_container_width=True,
            )
