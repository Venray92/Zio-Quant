import concurrent.futures
import pandas as pd
import streamlit as st

from trade_planner import TradePlanner


def process_single_ticker(ticker_code: str):
    """Proses tunggal screener per ticker saham."""
    symbol = ticker_code.strip().upper()
    if not symbol.endswith(".JK"):
        symbol += ".JK"

    try:
        planner = TradePlanner(symbol, period="6mo")
        planner.fetch_and_prepare_data()

        df_dir = planner.get_direction()
        df_plan = planner.generate_trade_plan()

        if df_dir.empty or df_plan.empty:
            return None

        curr_close = int(df_dir.iloc[0]["Last Close Market"])
        direction_rec = df_dir.iloc[0]["Direction"]

        # Ambil plan yang direkomendasikan
        selected_plan = df_plan[df_plan["Type"] == direction_rec]
        if selected_plan.empty:
            selected_plan = df_plan.iloc[[0]]

        p = selected_plan.iloc[0]

        # Calculation % Gain & % Risk
        entry_mid = (p["Range Buy Min"] + p["Range Buy Max"]) / 2.0
        pot_gain = (
            round(((p["TP 1"] - entry_mid) / entry_mid) * 100, 1)
            if entry_mid > 0
            else 0
        )
        pot_risk = (
            round(((entry_mid - p["Stop Loss"]) / entry_mid) * 100, 1)
            if entry_mid > 0
            else 0
        )

        return {
            "Saham": symbol.replace(".JK", ""),
            "Score": p["Score"],
            "Grade": p["Grade"],
            "Strategi": p["Type"],
            "Harga Last": curr_close,
            "Posisi Zone": p["Posisi Harga"],
            "Area Buy": p["Area Buy"],
            "Stop Loss (SL)": int(p["Stop Loss"]),
            "TP 1": int(p["TP 1"]),
            "TP 2": int(p["TP 2"]),
            "Potensi Gain": f"+{pot_gain}%",
            "Risiko SL": f"-{pot_risk}%",
            "Rasio (R:R)": p["Rasio (R:R)"],
            "RR_Val": p["RR_Val"],
            "Pola Candle": p["Pola Candle"],
            "Catatan Analisis & Warning": p["Warning"],
        }
    except Exception:
        return None


def render_tab_trade_planner(ticker_list=None):
    st.header("📊 Smart Execution Screener")
    st.write(
        "Platform pemeringkat saham berbasis **Price Action**, **Risk-to-Reward Ratio**, dan **Skoring Otomatis (0-100)**."
    )

    if not ticker_list:
        ticker_list = [
            "AADI",
            "ABBA",
            "AALI",
            "ACES",
            "ABMM",
            "ABDA",
            "ADCP",
            "ACST",
            "ACRO",
            "ADES",
            "BBCA",
            "BMRI",
            "TLKM",
            "ANTM",
            "INCO",
        ]

    # --- PANEL FILTER LENGKAP & PRESISI ---
    st.subheader("🔍 Filter & Parameter Screener")

    row1_col1, row1_col2, row1_col3 = st.columns(3)
    with row1_col1:
        f_strategi = st.selectbox(
            "🎯 Strategi Trading:",
            [
                "SEMUA STRATEGI",
                "Buy On Weakness (BOW)",
                "Breakout (BOB)",
            ],
        )
    with row1_col2:
        f_grade = st.selectbox(
            "🏆 Tingkat Kualitas (Grade):",
            [
                "SEMUA GRADE",
                "Grade A / A+ Only (High Quality)",
                "Grade B Kebawah (Moderate/Risk)",
            ],
        )
    with row1_col3:
        f_zone = st.selectbox(
            "📍 Posisi Harga Saat Ini:",
            [
                "SEMUA POSISI",
                "🎯 In Buy Zone (Siap Eksekusi)",
                "⏳ Near Zone (Dekat Entry)",
            ],
        )

    row2_col1, row2_col2, row2_col3 = st.columns(3)
    with row2_col1:
        f_rr = st.selectbox(
            "⚖️ Minimal Risk-to-Reward:",
            [
                "SEMUA RASIO",
                "Min 1 : 1.5",
                "Min 1 : 2.0 (Pro Standard)",
                "Min 1 : 3.0 (High Reward)",
            ],
        )
    with row2_col2:
        f_candle = st.selectbox(
            "🕯️ Sinyal Candlestick:",
            [
                "SEMUA CANDLE",
                "Bullish Signal Only",
                "Neutral / Doji Only",
            ],
        )
    with row2_col3:
        selected_tickers = st.multiselect(
            "📋 Pilih List Saham:", options=ticker_list, default=ticker_list
        )

    if st.button("🚀 Jalankan Batch Screener", type="primary"):
        if not selected_tickers:
            st.warning("Pilih minimal satu kode saham!")
            return

        with st.spinner("Memproses analisis teknikal & kalkulasi skor..."):
            results = []
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=10
            ) as executor:
                futures = [
                    executor.submit(process_single_ticker, t)
                    for t in selected_tickers
                ]
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    if res:
                        results.append(res)

            if not results:
                st.error("Gagal memuat data saham.")
                return

            df = pd.DataFrame(results)

            # --- ESEKUSI FILTERING ---
            if f_strategi == "Buy On Weakness (BOW)":
                df = df[df["Strategi"] == "BOW"]
            elif f_strategi == "Breakout (BOB)":
                df = df[df["Strategi"] == "BOB"]

            if f_grade == "Grade A / A+ Only (High Quality)":
                df = df[df["Score"] >= 70]
            elif f_grade == "Grade B Kebawah (Moderate/Risk)":
                df = df[df["Score"] < 70]

            if f_zone == "🎯 In Buy Zone (Siap Eksekusi)":
                df = df[df["Posisi Zone"] == "In Buy Zone"]
            elif f_zone == "⏳ Near Zone (Dekat Entry)":
                df = df[df["Posisi Zone"] == "Near Zone"]

            if f_rr == "Min 1 : 1.5":
                df = df[df["RR_Val"] >= 1.5]
            elif f_rr == "Min 1 : 2.0 (Pro Standard)":
                df = df[df["RR_Val"] >= 2.0]
            elif f_rr == "Min 1 : 3.0 (High Reward)":
                df = df[df["RR_Val"] >= 3.0]

            if f_candle == "Bullish Signal Only":
                df = df[
                    df["Pola Candle"].str.contains(
                        "Engulfing|Morning|Soldiers|Marubozu|Hammer|Dragonfly",
                        case=False,
                        na=False,
                    )
                ]
            elif f_candle == "Neutral / Doji Only":
                df = df[
                    df["Pola Candle"].str.contains(
                        "Doji|Spinning|Standard", case=False, na=False
                    )
                ]

            # Urutkan berdasarkan Score tertinggi
            df = df.sort_values(by="Score", ascending=False).reset_index(
                drop=True
            )

            st.subheader(f"📋 Hasil Batch Screener ({len(df)} Saham Terpilih)")

            # Tampilkan Tabel
            st.dataframe(
                df,
                column_config={
                    "Saham": st.column_config.TextColumn("Saham"),
                    "Score": st.column_config.NumberColumn(
                        "Score (0-100)", format="%d pts"
                    ),
                    "Grade": st.column_config.TextColumn("Kualitas Setup"),
                    "Harga Last": st.column_config.NumberColumn(
                        "Harga Last", format="Rp %d"
                    ),
                    "Area Buy": st.column_config.TextColumn("Area Buy (Entry)"),
                    "Stop Loss (SL)": st.column_config.NumberColumn(
                        "SL", format="%d"
                    ),
                    "TP 1": st.column_config.NumberColumn("TP 1", format="%d"),
                    "TP 2": st.column_config.NumberColumn("TP 2", format="%d"),
                    "Potensi Gain": st.column_config.TextColumn("Gain TP1"),
                    "Risiko SL": st.column_config.TextColumn("Risk SL"),
                    "Catatan Analisis & Warning": st.column_config.TextColumn(
                        "Rekomendasi & Warning", width="large"
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )
