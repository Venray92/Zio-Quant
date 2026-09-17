import os
import pandas as pd
import streamlit as st

# Mengimpor visualisasi helper dengan paket relatif/absolute yang benar
from utils.ui_helpers import (
    render_portfolio_pie_chart,
    render_risk_gauge_chart,
)

try:
    from engines.trade_planner import TradePlanner
except ImportError:
    TradePlanner = None


def _clean_num(val):
    if pd.isna(val) or val is None or val == "" or val == "-":
        return None
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return float(val)
    except Exception:
        return None


def render_page_money_management():
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); padding: 20px; border-radius: 12px; border-left: 6px solid #10B981; margin-bottom: 25px;">
            <h2 style="color: #F8FAFC; margin: 0; font-size: 24px;">⚖️ Advanced Money Management & Position Sizing</h2>
            <p style="color: #94A3B8; margin-top: 5px; font-size: 14px;">
                Hitung alokasi lot presisi, kontrol toleransi risiko modal, dan evaluasi Risk-to-Reward Ratio secara matematis sebelum melakukan eksekusi order.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "mm_buy_price" not in st.session_state:
        st.session_state["mm_buy_price"] = 1000.0
    if "mm_sl_price" not in st.session_state:
        st.session_state["mm_sl_price"] = 950.0
    if "mm_tp1_price" not in st.session_state:
        st.session_state["mm_tp1_price"] = 1100.0
    if "mm_tp2_price" not in st.session_state:
        st.session_state["mm_tp2_price"] = 1200.0
    if "mm_ticker" not in st.session_state:
        st.session_state["mm_ticker"] = "BBCA"

    col_input, col_output = st.columns([1, 1], gap="large")

    with col_input:
        st.markdown("### 📥 Parameter Transaksi")

        ticker = st.text_input(
            "Ticker Saham",
            value=st.session_state["mm_ticker"],
            key="input_mm_ticker",
        ).upper()

        capital = st.number_input(
            "Total Modal Trading (IDR)",
            min_value=100_000,
            value=100_000_000,
            step=1_000_000,
            format="%d",
        )

        st.markdown("---")
        st.markdown("#### 🎯 Profil Risk & Allocation Limit")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            risk_pct = st.number_input(
                "Max Risk Per Trade (%)",
                min_value=0.1,
                max_value=10.0,
                value=2.0,
                step=0.1,
                help="Maksimal toleransi kerugian dari total modal untuk 1 posisi transaksi.",
            )
        with col_r2:
            max_alloc_pct = st.number_input(
                "Max Portfolio Allocation (%)",
                min_value=1.0,
                max_value=100.0,
                value=20.0,
                step=1.0,
                help="Maksimal porsi modal yang dialokasikan untuk 1 saham ini.",
            )

        st.markdown("---")
        st.markdown("#### 📈 Target Harga & Level Risiko")

        c_buy, c_sl = st.columns(2)
        with c_buy:
            buy_price = st.number_input(
                "Harga Beli (Buy Price)",
                min_value=1.0,
                value=float(st.session_state["mm_buy_price"]),
                step=1.0,
            )
        with c_sl:
            sl_price = st.number_input(
                "Stop Loss (SL)",
                min_value=1.0,
                value=float(st.session_state["mm_sl_price"]),
                step=1.0,
            )

        c_tp1, c_tp2 = st.columns(2)
        with c_tp1:
            tp1_price = st.number_input(
                "Target Profit 1 (TP 1)",
                min_value=1.0,
                value=float(st.session_state["mm_tp1_price"]),
                step=1.0,
            )
        with c_tp2:
            tp2_price = st.number_input(
                "Target Profit 2 (TP 2)",
                min_value=1.0,
                value=float(st.session_state["mm_tp2_price"]),
                step=1.0,
            )

        st.markdown("---")
        st.markdown("#### 💸 Transaksi Fee Sekuritas")
        c_fb, c_fs = st.columns(2)
        with c_fb:
            fee_buy_pct = (
                st.number_input(
                    "Fee Beli (%)",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.15,
                    step=0.01,
                )
                / 100.0
            )
        with c_fs:
            fee_sell_pct = (
                st.number_input(
                    "Fee Jual (%)",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.25,
                    step=0.01,
                )
                / 100.0
            )

        st.markdown("---")
        with st.expander("🔄 Import Parameter dari Trade Plan", expanded=False):
            st.caption(
                "Tarik rekomendasi level harga terbaru berdasarkan Trade Planner otomatis."
            )
            col_sp_btn, col_sp_sel = st.columns([1, 1])
            with col_sp_sel:
                sync_period = st.selectbox(
                    "Periode Data",
                    options=["3mo", "6mo", "1y"],
                    key="mm_sync_period",
                )
            with col_sp_btn:
                if st.button(
                    "⚡ Sync Trade Plan", use_container_width=True
                ):
                    if TradePlanner is not None:
                        with st.spinner("Mengambil data Trade Plan..."):
                            try:
                                tp = TradePlanner(
                                    ticker=ticker, period=sync_period
                                )
                                tp.fetch_and_prepare_data()
                                df_plan = tp.generate_trade_plan()
                                if df_plan is not None and not df_plan.empty:
                                    best_plan = df_plan.iloc[0]
                                    buy_val = _clean_num(
                                        best_plan.get(
                                            "Range Buy Max",
                                            best_plan.get("Buy Max", buy_price),
                                        )
                                    )
                                    sl_val = _clean_num(
                                        best_plan.get(
                                            "Stop Loss",
                                            best_plan.get("SL", sl_price),
                                        )
                                    )
                                    tp1_val = _clean_num(
                                        best_plan.get(
                                            "TP 1",
                                            best_plan.get("TP1", tp1_price),
                                        )
                                    )
                                    tp2_val = _clean_num(
                                        best_plan.get(
                                            "TP 2",
                                            best_plan.get("TP2", tp2_price),
                                        )
                                    )

                                    if buy_val:
                                        st.session_state["mm_buy_price"] = (
                                            buy_val
                                        )
                                    if sl_val:
                                        st.session_state["mm_sl_price"] = sl_val
                                    if tp1_val:
                                        st.session_state["mm_tp1_price"] = (
                                            tp1_val
                                        )
                                    if tp2_val:
                                        st.session_state["mm_tp2_price"] = (
                                            tp2_val
                                        )
                                    st.session_state["mm_ticker"] = ticker
                                    st.success(
                                        f"Berhasil mengimpor rekomendasi Trade Plan #{1} ({best_plan.get('Type', 'Plan')})!"
                                    )
                                    st.rerun()
                                else:
                                    st.warning(
                                        "Tidak ada data Trade Plan yang valid."
                                    )
                            except Exception as ex:
                                st.error(f"Gagal memuat Trade Plan: {ex}")
                    else:
                        st.warning("Modul `TradePlanner` tidak tersedia.")

    # LOGIKA MONEY MANAGEMENT
    max_risk_amount = capital * (risk_pct / 100.0)
    max_alloc_amount = capital * (max_alloc_pct / 100.0)

    sl_distance = max(0.0, buy_price - sl_price)
    sl_pct = (sl_distance / buy_price) * 100.0 if buy_price > 0 else 0.0

    if sl_distance > 0:
        shares_by_risk = max_risk_amount / (sl_distance * (1 + fee_buy_pct))
        lot_by_risk = shares_by_risk // 100

        shares_by_alloc = max_alloc_amount / (buy_price * (1 + fee_buy_pct))
        lot_by_alloc = shares_by_alloc // 100

        final_lot = int(max(0, min(lot_by_risk, lot_by_alloc)))
    else:
        final_lot = 0

    total_shares = final_lot * 100
    total_cost_raw = total_shares * buy_price
    total_buy_fee = total_cost_raw * fee_buy_pct
    total_cost_with_fee = total_cost_raw + total_buy_fee

    actual_loss_raw = total_shares * sl_distance
    actual_sell_fee_sl = (total_shares * sl_price) * fee_sell_pct
    actual_risk_amount = actual_loss_raw + total_buy_fee + actual_sell_fee_sl
    actual_risk_pct = (
        (actual_risk_amount / capital) * 100.0 if capital > 0 else 0.0
    )

    tp1_distance = max(0.0, tp1_price - buy_price)
    tp1_gain_raw = total_shares * tp1_distance
    tp1_sell_fee = (total_shares * tp1_price) * fee_sell_pct
    tp1_net_gain = max(0.0, tp1_gain_raw - total_buy_fee - tp1_sell_fee)

    tp2_distance = max(0.0, tp2_price - buy_price)
    tp2_gain_raw = total_shares * tp2_distance
    tp2_sell_fee = (total_shares * tp2_price) * fee_sell_pct
    tp2_net_gain = max(0.0, tp2_gain_raw - total_buy_fee - tp2_sell_fee)

    rr_tp1 = (tp1_distance / sl_distance) if sl_distance > 0 else 0.0
    rr_tp2 = (tp2_distance / sl_distance) if sl_distance > 0 else 0.0

    with col_output:
        st.markdown("### 📊 Rekomendasi Eksekusi & Ringkasan Risk")

        m1 = f"""
        <div style="background: linear-gradient(135deg, #0D1117 0%, #161B22 100%); border: 1px solid #30363D; border-left: 5px solid #00E676; border-radius: 10px; padding: 16px; margin-bottom: 15px;">
            <div style="font-size: 12px; color: #8B949E; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Rekomendasi Posisi Maksimal</div>
            <div style="font-size: 32px; font-weight: 900; color: #00E676; margin-top: 4px;">{final_lot:,} <span style="font-size: 16px; color: #C0C5D0;">LOT</span></div>
            <div style="font-size: 13px; color: #8B949E; margin-top: 4px;">Setara dengan <b>{total_shares:,}</b> lembar saham {ticker}</div>
        </div>
        """

        m2 = f"""
        <div style="background: linear-gradient(135deg, #0D1117 0%, #161B22 100%); border: 1px solid #30363D; border-left: 5px solid #38BDF8; border-radius: 10px; padding: 16px; margin-bottom: 15px;">
            <div style="font-size: 12px; color: #8B949E; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Total Nilai Transaksi (+ Fee Beli)</div>
            <div style="font-size: 26px; font-weight: 900; color: #38BDF8; margin-top: 4px;">Rp {total_cost_with_fee:,.0f}</div>
            <div style="font-size: 13px; color: #8B949E; margin-top: 4px;">Alokasi Modal: <b>{((total_cost_with_fee / capital) * 100):.2f}%</b> dari total portfolio</div>
        </div>
        """

        m3 = f"""
        <div style="background: linear-gradient(135deg, #0D1117 0%, #161B22 100%); border: 1px solid #30363D; border-left: 5px solid #FF5252; border-radius: 10px; padding: 16px; margin-bottom: 20px;">
            <div style="font-size: 12px; color: #8B949E; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Potensi Risiko Riil (Bila Kena Stop Loss)</div>
            <div style="font-size: 26px; font-weight: 900; color: #FF5252; margin-top: 4px;">- Rp {actual_risk_amount:,.0f}</div>
            <div style="font-size: 13px; color: #8B949E; margin-top: 4px;">Risiko Riil Portfolio: <b>{actual_risk_pct:.2f}%</b> (Target limit: {risk_pct:.2f}%)</div>
        </div>
        """

        st.markdown(m1, unsafe_allow_html=True)
        st.markdown(m2, unsafe_allow_html=True)
        st.markdown(m3, unsafe_allow_html=True)

        with st.expander("📌 Rincian Potensi Profit & Rasio Risk/Reward", expanded=True):
            r1, r2 = st.columns(2)
            with r1:
                st.metric(
                    label="Potensi Profit TP 1 (Bersih Fee)",
                    value=f"Rp {tp1_net_gain:,.0f}",
                    delta=f"R:R = 1 : {rr_tp1:.2f}",
                )
            with r2:
                st.metric(
                    label="Potensi Profit TP 2 (Bersih Fee)",
                    value=f"Rp {tp2_net_gain:,.0f}",
                    delta=f"R:R = 1 : {rr_tp2:.2f}",
                )

            st.caption(
                f"Jarak ke Stop Loss: **-{sl_pct:.2f}%** | Jarak ke TP1: **+{((tp1_distance/buy_price)*100):.2f}%** | Jarak ke TP2: **+{((tp2_distance/buy_price)*100):.2f}%**"
            )

        st.markdown("---")
        st.markdown("#### 📈 Visualisasi Profil Risk & Portofolio")

        tab_g1, tab_g2 = st.tabs(["🎯 Risk Gauge Chart", "🥧 Portfolio Allocation"])

        with tab_g1:
            fig_g = render_risk_gauge_chart(actual_risk_pct, risk_pct)
            st.plotly_chart(fig_g, use_container_width=True)

        with tab_g2:
            fig_p = render_portfolio_pie_chart(
                ticker, total_cost_with_fee, capital
            )
            st.plotly_chart(fig_p, use_container_width=True)


if __name__ == "__main__":
    st.set_page_config(page_title="Money Management", layout="wide")
    render_money_management_page()
