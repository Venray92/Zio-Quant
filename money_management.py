import math
import plotly.graph_objects as go
import streamlit as st


def render_page_money_management():
    # --- INJECT CUSTOM CSS FOR MODERN CARDS & METRICS ---
    st.markdown(
        """
        <style>
        .mm-card {
            background-color: #1E222D;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #2A2E39;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
        }
        .mm-badge-green {
            background-color: rgba(38, 166, 154, 0.2);
            color: #26a69a;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 14px;
            border: 1px solid #26a69a;
        }
        .mm-badge-red {
            background-color: rgba(239, 83, 80, 0.2);
            color: #ef5350;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 14px;
            border: 1px solid #ef5350;
        }
        .mm-badge-yellow {
            background-color: rgba(255, 179, 0, 0.2);
            color: #ffb300;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 14px;
            border: 1px solid #ffb300;
        }
        .metric-label {
            color: #8E94A0;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .metric-value {
            font-size: 24px;
            font-weight: 800;
            color: #FFFFFF;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🛡️ Position Sizing & Money Management")
    st.caption(
        "Kelola risiko transaksi dan alokasi modal IDX 962 Saham secara presisi berdasarkan profil trading Anda."
    )

    # --- AMBIL DATA ATAU DEFAULT DARI SESSION STATE ---
    # Jika dipanggil dari Trade Planner / Screener, data otomatis terpakai
    default_ticker = st.session_state.get("mm_ticker", "BBCA.JK")
    default_entry = float(st.session_state.get("mm_entry", 10000.0))
    default_sl = float(st.session_state.get("mm_sl", 9600.0))
    default_tp1 = float(st.session_state.get("mm_tp1", 10800.0))
    default_tp2 = float(st.session_state.get("mm_tp2", 11600.0))

    # --- CONFIG PROFIL TRADING ---
    PROFILE_RULES = {
        "Scalping / Fast Trade": {
            "max_alloc": 10.0,
            "max_pos": 10,
            "cash_buff": 30.0,
            "desc": "Frekuensi tinggi, tahan posisi < 1 hari. Risiko ketat.",
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
            "desc": "Riding trend berbulan-bulan sampai tren patah.",
        },
        "Investing (Value/Growth)": {
            "max_alloc": 33.0,
            "max_pos": 3,
            "cash_buff": 0.0,
            "desc": "Fokus fundamental, akumulasi bertahap.",
        },
    }

    # --- TWO COLUMN LAYOUT (INPUT vs CALCULATOR ENGINE) ---
    col_input, col_output = st.columns([1.1, 1.9], gap="large")

    with col_input:
        st.subheader("⚙️ Parameter Setup")

        # Section 1: Profil & Capital
        with st.expander("👤 Modal & Profil Trader", expanded=True):
            capital = st.number_input(
                "Total Modal (Rp)",
                min_value=1_000_000,
                value=100_000_000,
                step=5_000_000,
                format="%d",
            )
            trading_style = st.selectbox(
                "Tipe / Profil Trading", list(PROFILE_RULES.keys()), index=1
            )
            risk_pct = st.slider(
                "Batas Toleransi Risiko per Trade (%)",
                min_value=0.25,
                max_value=3.0,
                value=1.0,
                step=0.25,
            )

            # Info profil otomatis
            rule = PROFILE_RULES[trading_style]
            st.caption(f"ℹ️ *{rule['desc']}*")

        # Section 2: Trade Plan Parameters
        with st.expander("📊 Parameter Transaksi Saham", expanded=True):
            ticker = st.text_input("Ticker Saham", value=default_ticker).upper()
            c_entry, c_sl = st.columns(2)
            with c_entry:
                entry_price = st.number_input(
                    "Harga Beli (Entry)",
                    min_value=50.0,
                    value=default_entry,
                    step=10.0,
                )
            with c_sl:
                sl_price = st.number_input(
                    "Harga Cut Loss (SL)",
                    min_value=1.0,
                    value=default_sl,
                    step=10.0,
                )

            c_tp1, c_tp2 = st.columns(2)
            with c_tp1:
                tp1_price = st.number_input(
                    "Target Price 1 (TP1)",
                    min_value=50.0,
                    value=default_tp1,
                    step=10.0,
                )
            with c_tp2:
                tp2_price = st.number_input(
                    "Target Price 2 (TP2)",
                    min_value=50.0,
                    value=default_tp2,
                    step=10.0,
                )

        # Fee Broker IDX
        with st.expander("🛠️ Custom Fee Sekuritas", expanded=False):
            fee_buy = (
                st.number_input(
                    "Fee Beli (%)", min_value=0.0, value=0.15, step=0.01
                )
                / 100
            )
            fee_sell = (
                st.number_input(
                    "Fee Jual (%)", min_value=0.0, value=0.25, step=0.01
                )
                / 100
            )

    # --- PROSES KALKULASI MONEY MANAGEMENT ---
    with col_output:
        st.subheader("🎯 Hasil Logika & Position Sizing")

        # Validasi Input
        if sl_price >= entry_price:
            st.error(
                "❌ Error Logika: Harga Stop Loss (SL) harus LEBIH KECIL dari harga Beli (Entry)."
            )
            return

        if tp1_price <= entry_price:
            st.warning(
                "⚠️ Catatan: Target Price 1 sebaiknya lebih besar dari harga Entry."
            )

        # 1. Jarak Risiko
        risk_per_share = entry_price - sl_price
        risk_pct_trade = (risk_per_share / entry_price) * 100
        max_risk_idr = capital * (risk_pct / 100)

        # 2. Raw Position Size (Lembar & Lot)
        raw_shares = max_risk_idr / risk_per_share
        lot_by_risk = math.floor(raw_shares / 100)

        # 3. Cap Alokasi Berdasarkan Profil
        max_alloc_pct = rule["max_alloc"]
        max_capital_allowed = capital * (max_alloc_pct / 100)
        lot_by_cap = math.floor(max_capital_allowed / (entry_price * 100))

        # Final Recommended Lot
        final_lot = min(lot_by_risk, lot_by_cap)
        final_shares = final_lot * 100
        total_buy_value = final_shares * entry_price
        total_cost_with_fee = total_buy_value * (1 + fee_buy)
        actual_risk_idr = (total_cost_with_fee) - (
            (final_shares * sl_price) * (1 - fee_sell)
        )
        actual_risk_pct_capital = (actual_risk_idr / capital) * 100

        # Risk Reward Ratio (RRR)
        reward_tp1 = tp1_price - entry_price
        rrr_tp1 = reward_tp1 / risk_per_share if risk_per_share > 0 else 0

        reward_tp2 = tp2_price - entry_price
        rrr_tp2 = reward_tp2 / risk_per_share if risk_per_share > 0 else 0

        # Cek Capping Alert
        is_capped = lot_by_cap < lot_by_risk

        # --- DISPLAY RESULTS IN METRIC CARDS ---
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                f"""
            <div class="mm-card">
                <div class="metric-label">Rekomendasi Size</div>
                <div class="metric-value" style="color:#26a69a;">{final_lot:,} LOT</div>
                <div style="font-size: 12px; color: #8E94A0;">({final_shares:,} Lembar)</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with m2:
            st.markdown(
                f"""
            <div class="mm-card">
                <div class="metric-label">Total Nilai Pembelian</div>
                <div class="metric-value">Rp {total_buy_value:,.0f}</div>
                <div style="font-size: 12px; color: #8E94A0;">Porsi: { (total_buy_value/capital)*100:.1f}% Modal</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with m3:
            rrr_badge = (
                "mm-badge-green"
                if rrr_tp1 >= 2.0
                else ("mm-badge-yellow" if rrr_tp1 >= 1.5 else "mm-badge-red")
            )
            st.markdown(
                f"""
            <div class="mm-card">
                <div class="metric-label">Risk to Reward (TP1)</div>
                <div class="metric-value">1 : {rrr_tp1:.2f}</div>
                <span class="{rrr_badge}">{"EXCELLENT" if rrr_tp1>=2 else ("ACCEPTABLE" if rrr_tp1>=1.5 else "POOR")}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Alert Capping jika Lot dipotong aturan profil
        if is_capped:
            st.warning(
                f"⚠️ **Jumlah Lot Dibatasi!** Berdasarkan toleransi risiko Anda bisa membeli **{lot_by_risk} Lot**, namun dibatasi menjadi **{final_lot} Lot** agar tidak melebihi alokasi max {max_alloc_pct}% modal ({trading_style})."
            )

        # --- SCALING OUT / PARTIAL PROFIT TAKING PLANNER ---
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
        total_potential_profit = p_tp1 + p_tp2

        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(
                f"""
            <div class="mm-card">
                <h4 style="margin:0; color:#26a69a;">Tahap 1: Sell 50% Lot @ TP1</h4>
                <p style="margin:5px 0; font-size:14px;"><b>Jual {lot_tp1} Lot</b> di harga <b>Rp {tp1_price:,.0f}</b></p>
                <p style="margin:0; font-size:13px; color:#8E94A0;">Profit Diamankan: <b style="color:#26a69a;">+Rp {p_tp1:,.0f}</b></p>
                <hr style="margin:10px 0; border-color:#2A2E39;">
                <span style="font-size:12px; color:#ffb300;">📌 Action: Geser SL sisa lot ke harga BEP (Rp {entry_price:,.0f})</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with sc2:
            st.markdown(
                f"""
            <div class="mm-card">
                <h4 style="margin:0; color:#26a69a;">Tahap 2: Sell 50% Lot @ TP2</h4>
                <p style="margin:5px 0; font-size:14px;"><b>Jual {lot_tp2} Lot</b> di harga <b>Rp {tp2_price:,.0f}</b></p>
                <p style="margin:0; font-size:13px; color:#8E94A0;">Profit Diamankan: <b style="color:#26a69a;">+Rp {p_tp2:,.0f}</b></p>
                <hr style="margin:10px 0; border-color:#2A2E39;">
                <span style="font-size:12px; color:#26a69a;">💰 Total Potensi Profit Maksimal: <b>+Rp {total_potential_profit:,.0f}</b></span>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # --- VISUALIZATIONS: GAUGE & PORTFOLIO ALLOCATION ---
        st.markdown("---")
        st.subheader("📈 Visualisasi Risiko & Alokasi Portfolio")

        v1, v2 = st.columns(2)

        with v1:
            # Gauge Chart untuk RRR TP1
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=rrr_tp1,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Risk/Reward Gauge (TP1)"},
                    gauge={
                        "axis": {"range": [0, 4]},
                        "bar": {"color": "#26a69a"},
                        "steps": [
                            {"range": [0, 1.5], "color": "rgba(239, 83, 80, 0.3)"},
                            {"range": [1.5, 2.0], "color": "rgba(255, 179, 0, 0.3)"},
                            {"range": [2.0, 4.0], "color": "rgba(38, 166, 154, 0.3)"},
                        ],
                        "threshold": {
                            "line": {"color": "white", "width": 4},
                            "thickness": 0.75,
                            "value": rrr_tp1,
                        },
                    },
                )
            )
            fig_gauge.update_layout(
                height=250,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        with v2:
            # Donut Chart untuk Portfolio Exposure
            cash_left = capital - total_buy_value
            fig_donut = go.Figure(
                data=[
                    go.Pie(
                        labels=[f"Posisi {ticker}", "Sisa Cash Modal"],
                        values=[total_buy_value, cash_left],
                        hole=0.6,
                        marker_colors=["#26a69a", "#2A2E39"],
                    )
                ]
            )
            fig_donut.update_layout(
                title_text="Simulasi Capital Exposure",
                height=250,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
                showlegend=True,
            )
            st.plotly_chart(fig_donut, use_container_width=True)