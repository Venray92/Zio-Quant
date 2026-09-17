import math
import plotly.graph_objects as go
import streamlit as st

# Import TradePlanner dari file backend kamu
try:
    from engines.trade_planner import TradePlanner
except ImportError:
    TradePlanner = None


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
        "Kelola risiko transaksi dan alokasi modal IDX secara presisi berdasarkan profil trading Anda."
    )

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
                key="mm_capital_input",
            )
            trading_style = st.selectbox(
                "Tipe / Profil Trading",
                list(PROFILE_RULES.keys()),
                index=1,
                key="mm_style_select",
            )

            # Max risk dinaikkan hingga 10%
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

        # Section 2: Trade Plan Parameters
        with st.expander("📊 Parameter Transaksi Saham", expanded=True):
            if "input_entry_price" not in st.session_state:
                st.session_state["input_entry_price"] = 125.0
            if "input_sl_price" not in st.session_state:
                st.session_state["input_sl_price"] = 120.0
            if "input_tp1_price" not in st.session_state:
                st.session_state["input_tp1_price"] = 151.0
            if "input_tp2_price" not in st.session_state:
                st.session_state["input_tp2_price"] = 216.0

            raw_ticker_default = (
                st.session_state.get("mm_ticker", "COCO")
                .upper()
                .replace(".JK", "")
            )
            ticker_input = st.text_input(
                "Ticker Saham (Tanpa .JK)",
                value=raw_ticker_default,
                key="mm_raw_ticker_input",
            ).strip()

            clean_ticker_code = (
                ticker_input.upper().replace(".JK", "").strip() or "COCO"
            )
            full_ticker = f"{clean_ticker_code}.JK"

            plan_type = st.radio(
                "Tipe Trade Plan",
                ["BOW", "BOB"],
                horizontal=True,
                key="mm_plan_type_radio",
            )

            def fetch_trade_plan_values():
                if not TradePlanner:
                    st.error("Modul `TradePlanner` tidak dapat dimuat.")
                    return False
                try:
                    with st.spinner(
                        f"Mengambil data Trade Plan {full_ticker}..."
                    ):
                        planner = TradePlanner(ticker=full_ticker)
                        planner.fetch_and_prepare_data()
                        df_plan = planner.generate_trade_plan()

                        matched = df_plan[df_plan["Type"] == plan_type]
                        if matched.empty:
                            matched = df_plan

                        row = matched.iloc[0]

                        st.session_state["input_entry_price"] = float(
                            row["Range Buy Min"]
                        )
                        st.session_state["input_sl_price"] = float(
                            row["Stop Loss"]
                        )
                        st.session_state["input_tp1_price"] = float(row["TP 1"])
                        st.session_state["input_tp2_price"] = float(row["TP 2"])

                        st.session_state["last_synced_ticker"] = (
                            clean_ticker_code
                        )
                        st.session_state["last_synced_type"] = plan_type
                        return True
                except Exception as e:
                    st.error(
                        f"Gagal mengambil Trade Plan {clean_ticker_code}: {e}"
                    )
                    return False

            c_btn1, c_btn2 = st.columns([1.5, 1])
            with c_btn1:
                if st.button("🔄 Sync Trade Plan", use_container_width=True):
                    if fetch_trade_plan_values():
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

        # Section 3: Fee Sekuritas
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

    # --- PROSES KALKULASI MONEY MANAGEMENT & RE-LINK DATA ---
    with col_output:
        st.subheader("🎯 Hasil Logika & Position Sizing")

        if sl_price >= entry_price:
            st.error(
                "❌ Error Logika: Harga Stop Loss (SL) harus LEBIH KECIL dari harga Beli (Entry)."
            )
            return

        if tp1_price <= entry_price:
            st.warning(
                "⚠️ Catatan: Target Price 1 sebaiknya lebih besar dari harga Entry."
            )

        # 1. Batas Risiko Maksimal Nominal
        max_risk_allowed_idr = capital * (risk_pct / 100)

        # 2. Perhitungan Risiko per Lembar
        risk_per_share_raw = entry_price - sl_price
        total_risk_per_share_with_fee = (entry_price * (1 + fee_buy)) - (
            sl_price * (1 - fee_sell)
        )

        # 3. Lot Berdasarkan Toleransi Risiko
        raw_shares_by_risk = max_risk_allowed_idr / total_risk_per_share_with_fee
        lot_by_risk = math.floor(raw_shares_by_risk / 100)

        # 4. Lot Berdasarkan Alokasi Profil
        max_alloc_pct = rule["max_alloc"]
        max_capital_allowed = capital * (max_alloc_pct / 100)
        lot_by_cap = math.floor(
            max_capital_allowed / (entry_price * 100 * (1 + fee_buy))
        )

        # Final Selected Lot
        final_lot = min(lot_by_risk, lot_by_cap)
        final_shares = final_lot * 100
        total_buy_value = final_shares * entry_price
        total_cost_with_fee = total_buy_value * (1 + fee_buy)

        # Dynamic Realized Risk berdasarkan Lot yang terbentuk
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
        rrr_tp1 = reward_tp1 / risk_per_share_raw if risk_per_share_raw > 0 else 0

        reward_tp2 = tp2_price - entry_price
        rrr_tp2 = reward_tp2 / risk_per_share_raw if risk_per_share_raw > 0 else 0

        is_capped = (lot_by_cap < lot_by_risk) and (lot_by_risk > 0)

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

        if is_capped:
            st.warning(
                f"⚠️ **Jumlah Lot Dibatasi Profil!** Berdasarkan toleransi risiko ({risk_pct}%) Anda bisa membeli **{lot_by_risk:,} Lot**, "
                f"namun dibatasi menjadi **{final_lot:,} Lot** agar tidak melebihi alokasi max {max_alloc_pct}% modal ({trading_style})."
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
                <p style="margin:5px 0; font-size:14px;"><b>Jual {lot_tp1:,} Lot</b> di harga <b>Rp {tp1_price:,.0f}</b></p>
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
                <p style="margin:5px 0; font-size:14px;"><b>Jual {lot_tp2:,} Lot</b> di harga <b>Rp {tp2_price:,.0f}</b></p>
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
            # Gauge sekarang memantau Risiko Realistis vs Toleransi Slider Risiko
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=actual_risk_pct,
                    number={"suffix": "%", "valueformat": ".2f"},
                    delta={
                        "reference": risk_pct,
                        "relative": False,
                        "position": "top",
                    },
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={
                        "text": f"Risiko Posisi Saat Ini vs Target ({risk_pct}%)<br><span style='font-size:12px;color:#8E94A0;'>Nominal Risk: Rp {actual_risk_idr:,.0f}</span>"
                    },
                    gauge={
                        "axis": {
                            "range": [0, max(10.0, risk_pct * 1.2)],
                            "tickwidth": 1,
                        },
                        "bar": {
                            "color": (
                                "#26a69a"
                                if actual_risk_pct <= risk_pct
                                else "#ef5350"
                            )
                        },
                        "steps": [
                            {
                                "range": [0, risk_pct],
                                "color": "rgba(38, 166, 154, 0.2)",
                            },
                            {
                                "range": [risk_pct, 10.0],
                                "color": "rgba(239, 83, 80, 0.2)",
                            },
                        ],
                        "threshold": {
                            "line": {"color": "gold", "width": 4},
                            "thickness": 0.75,
                            "value": risk_pct,
                        },
                    },
                )
            )
            fig_gauge.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=50, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        with v2:
            cash_left = max(0.0, capital - total_cost_with_fee)
            fig_donut = go.Figure(
                data=[
                    go.Pie(
                        labels=[
                            f"Posisi {clean_ticker_code}",
                            "Sisa Cash Modal",
                        ],
                        values=[total_cost_with_fee, cash_left],
                        hole=0.6,
                        marker_colors=["#26a69a", "#2A2E39"],
                    )
                ]
            )
            fig_donut.update_layout(
                title_text="Simulasi Capital Exposure (Inc. Fee)",
                height=260,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
                showlegend=True,
            )
            st.plotly_chart(fig_donut, use_container_width=True)
