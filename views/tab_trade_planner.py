import concurrent.futures
import os
import pandas as pd
import streamlit as st

from trade_planner import TradePlanner


def load_daftar_saham(filename="daftar_saham.txt"):
    """Membaca file daftar_saham.txt."""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r") as f:
            lines = f.readlines()
        tickers = [
            line.strip().upper()
            for line in lines
            if line.strip() and not line.startswith("#")
        ]
        return tickers
    except Exception:
        return []


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
            "Score": int(p["Score"]),
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
            "RR_Val": float(p["RR_Val"]) if "RR_Val" in p else 0.0,
            "Pola Candle": p["Pola Candle"],
            "Catatan Analisis & Warning": p["Warning"],
        }
    except Exception:
        return None


def run_batch_execution(ticker_list):
    """Fungsi runner eksekusi multi-threading."""
    total_saham = len(ticker_list)
    progress_bar = st.progress(0)
    status_text = st.empty()

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_ticker = {
            executor.submit(process_single_ticker, t): t for t in ticker_list
        }

        completed = 0
        for future in concurrent.futures.as_completed(future_to_ticker):
            res = future.result()
            if res:
                results.append(res)

            completed += 1
            percent = completed / total_saham
            progress_bar.progress(percent)
            status_text.markdown(
                f"⏳ **Progres Screener:** `{completed}/{total_saham}` saham diproses ({int(percent * 100)}%)"
            )

    progress_bar.empty()
    status_text.empty()
    st.toast(
        f"✅ Selesai! Berhasil menganalisis {len(results)} dari {total_saham} saham.",
        icon="🚀",
    )

    if results:
        df_res = pd.DataFrame(results)
        st.session_state["df_screener_raw"] = df_res


def reset_filters():
    """Fungsi Callback untuk mereset nilai filter ke pilihan pertama (SEMUA)."""
    st.session_state["f_strategi"] = "SEMUA STRATEGI"
    st.session_state["f_grade"] = "SEMUA GRADE"
    st.session_state["f_zone"] = "SEMUA POSISI"
    st.session_state["f_rr"] = "SEMUA RASIO"
    st.session_state["f_candle"] = "SEMUA CANDLE"


def render_tab_trade_planner():
    # Style Custom CSS untuk mempercantik tampilan UI
    st.markdown(
        """
        <style>
        .stMetric {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 12px 18px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .screener-header {
            font-size: 1.6rem;
            font-weight: 700;
            background: linear-gradient(90deg, #4A90E2, #50E3C2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<p class="screener-header">📊 Smart Execution Screener</p>', unsafe_allow_html=True)
    st.caption(
        "Platform pemeringkat & rekomendasi saham berbasis **Price Action**, **Risk-to-Reward Ratio**, dan **Skoring Otomatis (0-100)**."
    )

    # Inisialisasi state filter jika belum ada
    if "f_strategi" not in st.session_state:
        st.session_state["f_strategi"] = "SEMUA STRATEGI"
    if "f_grade" not in st.session_state:
        st.session_state["f_grade"] = "SEMUA GRADE"
    if "f_zone" not in st.session_state:
        st.session_state["f_zone"] = "SEMUA POSISI"
    if "f_rr" not in st.session_state:
        st.session_state["f_rr"] = "SEMUA RASIO"
    if "f_candle" not in st.session_state:
        st.session_state["f_candle"] = "SEMUA CANDLE"

    # --- 1. PILIHAN MODE SCREENER ---
    with st.container(border=True):
        mode_screener = st.radio(
            "🎯 Pilih Mode Screener:",
            [
                "⚡ Single / Custom Ticker",
                "🚀 Full Batch Screener (Daftar Saham 962 Ticker)",
            ],
            horizontal=True,
        )

        # MODE 1: SINGLE / CUSTOM TICKER
        if "⚡ Single" in mode_screener:
            col_input, col_btn = st.columns([3, 1], vertical_alignment="bottom")

            with col_input:
                input_ticker = st.text_input(
                    "Masukkan Kode Saham (Pisahkan koma jika > 1):",
                    value="",
                    placeholder="Contoh: BBCA, BMRI, TLKM, INCO",
                )

            with col_btn:
                btn_single = st.button(
                    "🔍 Analisis Ticker", type="primary", use_container_width=True
                )

            if btn_single:
                if not input_ticker.strip():
                    st.warning("⚠️ Silakan masukkan kode saham terlebih dahulu!")
                else:
                    list_to_scan = [
                        t.strip().upper()
                        for t in input_ticker.split(",")
                        if t.strip()
                    ]
                    run_batch_execution(list_to_scan)

        # MODE 2: FULL BATCH SCREENER
        else:
            all_tickers = load_daftar_saham("daftar_saham.txt")
            if not all_tickers:
                st.error(
                    "❌ File `daftar_saham.txt` tidak ditemukan atau kosong di direktori utama!"
                )
                return

            col_info, col_batch_btn = st.columns([3, 1], vertical_alignment="center")
            with col_info:
                st.info(
                    f"📁 Siap menganalisis **{len(all_tickers)} saham** yang terdaftar di `daftar_saham.txt`."
                )
            with col_batch_btn:
                if st.button("🚀 Jalankan Batch Screener", type="primary", use_container_width=True):
                    run_batch_execution(all_tickers)

    # --- 2. TAMPILAN DASHBOARD & PANEL FILTER ---
    if "df_screener_raw" in st.session_state:
        df_raw = st.session_state["df_screener_raw"]

        st.write("")

        # Metrics KPI Dashboard Ringkas
        c1, c2, c3, c4 = st.columns(4)
        total_scanned = len(df_raw)
        in_buy_zone = len(df_raw[df_raw["Posisi Zone"] == "In Buy Zone"])
        high_grade = len(df_raw[df_raw["Score"] >= 70])
        avg_score = round(df_raw["Score"].mean(), 1) if not df_raw.empty else 0

        c1.metric("Total Saham Menganalisis", f"{total_scanned} Saham")
        c2.metric("In Buy Zone (Siap Eksekusi)", f"{in_buy_zone}", delta=f"{(in_buy_zone/total_scanned*100):.1f}%" if total_scanned else None)
        c3.metric("Setup High Quality (Grade A/A+)", f"{high_grade}")
        c4.metric("Rata-Rata Skoring Market", f"{avg_score} / 100")

        st.markdown("---")

        # Container Panel Filter
        with st.expander("🛠️ **Panel Filter & Parameter Pencarian**", expanded=True):
            r1c1, r1c2, r1c3 = st.columns(3)
            with r1c1:
                f_strategi = st.selectbox(
                    "🎯 Strategi Trading:",
                    ["SEMUA STRATEGI", "Buy On Weakness (BOW)", "Breakout (BOB)"],
                    key="f_strategi",
                )
            with r1c2:
                f_grade = st.selectbox(
                    "🏆 Kualitas Setup (Grade):",
                    [
                        "SEMUA GRADE",
                        "Grade A / A+ Only (High Quality)",
                        "Grade B Kebawah (Moderate/Risk)",
                    ],
                    key="f_grade",
                )
            with r1c3:
                f_zone = st.selectbox(
                    "📍 Posisi Harga Saat Ini:",
                    [
                        "SEMUA POSISI",
                        "In Buy Zone (Siap Eksekusi)",
                        "Near Zone (Dekat Entry)",
                    ],
                    key="f_zone",
                )

            r2c1, r2c2, r2c3 = st.columns([1.5, 1.5, 1], vertical_alignment="bottom")
            with r2c1:
                f_rr = st.selectbox(
                    "⚖️ Minimal Risk-to-Reward:",
                    [
                        "SEMUA RASIO",
                        "Min 1 : 1.5",
                        "Min 1 : 2.0 (Pro Standard)",
                        "Min 1 : 3.0 (High Reward)",
                    ],
                    key="f_rr",
                )
            with r2c2:
                f_candle = st.selectbox(
                    "🕯️ Sinyal Candlestick:",
                    ["SEMUA CANDLE", "Bullish Signal Only", "Neutral / Doji Only"],
                    key="f_candle",
                )
            with r2c3:
                st.button(
                    "🔄 Reset Filter",
                    on_click=reset_filters,
                    use_container_width=True,
                )

        # --- LOGIKA FILTERING ---
        df = df_raw.copy()

        if f_strategi == "Buy On Weakness (BOW)":
            df = df[df["Strategi"] == "BOW"]
        elif f_strategi == "Breakout (BOB)":
            df = df[df["Strategi"] == "BOB"]

        if f_grade == "Grade A / A+ Only (High Quality)":
            df = df[df["Score"] >= 70]
        elif f_grade == "Grade B Kebawah (Moderate/Risk)":
            df = df[df["Score"] < 70]

        if f_zone == "In Buy Zone (Siap Eksekusi)":
            df = df[df["Posisi Zone"] == "In Buy Zone"]
        elif f_zone == "Near Zone (Dekat Entry)":
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
        df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

        # --- HEADER HASIL SCREENER ---
        header_col, download_col = st.columns([3, 1], vertical_alignment="center")
        with header_col:
            st.subheader(
                f"📋 Hasil Screener ({len(df)} dari {len(df_raw)} Saham Lolos Filter)"
            )
        with download_col:
            if not df.empty:
                csv_data = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Export CSV",
                    data=csv_data,
                    file_name="screener_trade_planner.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        if df.empty:
            st.warning(
                "⚠️ Tidak ada saham yang cocok dengan kombinasi filter Anda. Coba longgarkan kriteria filter atau tekan tombol 'Reset Filter'."
            )
        else:
            # --- TAMPILAN DATAFRAME YANG ELEGAN & COLORFUL ---
            st.dataframe(
                df,
                column_config={
                    "Saham": st.column_config.TextColumn("Saham", help="Kode Ticker Saham"),
                    "Score": st.column_config.ProgressColumn(
                        "Score Setup",
                        help="Skor Kualitas Setup (0-100)",
                        format="%d pts",
                        min_value=0,
                        max_value=100,
                    ),
                    "Grade": st.column_config.TextColumn("Grade", help="Grade Kualitas Setup"),
                    "Strategi": st.column_config.TextColumn("Strategi"),
                    "Harga Last": st.column_config.NumberColumn(
                        "Harga Last", format="Rp %d"
                    ),
                    "Posisi Zone": st.column_config.TextColumn("Posisi Price"),
                    "Area Buy": st.column_config.TextColumn("Area Buy (Entry)"),
                    "Stop Loss (SL)": st.column_config.NumberColumn(
                        "SL", format="%d"
                    ),
                    "TP 1": st.column_config.NumberColumn("TP 1", format="%d"),
                    "TP 2": st.column_config.NumberColumn("TP 2", format="%d"),
                    "Potensi Gain": st.column_config.TextColumn("Gain TP1"),
                    "Risiko SL": st.column_config.TextColumn("Risk SL"),
                    "Rasio (R:R)": st.column_config.TextColumn("R:R Ratio"),
                    "RR_Val": None,  # Sembunyikan kolom numerik pembantu dari tampilan
                    "Pola Candle": st.column_config.TextColumn("Candle Signal"),
                    "Catatan Analisis & Warning": st.column_config.TextColumn(
                        "Rekomendasi & Warning", width="large"
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )
