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
            progress_bar.progress(completed / total_saham)
            status_text.text(
                f"Progres Screener: {completed} / {total_saham} saham diproses..."
            )

    status_text.success(
        f"Selesai! Berhasil menganalisis {len(results)} saham dari {total_saham} ticker."
    )

    if results:
        df_res = pd.DataFrame(results)
        st.session_state["df_screener_raw"] = df_res


def reset_filters():
    """Fungsi Callback untuk mereset nilai filter."""
    st.session_state["f_strategi"] = "SEMUA STRATEGI"
    st.session_state["f_grade"] = "SEMUA GRADE"
    st.session_state["f_zone"] = "SEMUA POSISI"
    st.session_state["f_rr"] = "SEMUA RASIO"
    st.session_state["f_candle"] = "SEMUA CANDLE"


def render_tab_trade_planner():
    # Header Tanpa Logo / Emoji
    st.header("Smart Execution Screener")
    st.write(
        "Platform pemeringkat saham berbasis **Price Action**, **Risk-to-Reward Ratio**, dan **Skoring Otomatis (0-100)**."
    )

    # Inisialisasi state filter
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

    # 1. PILIHAN MODE SCREENER
    mode_screener = st.radio(
        "Pilih Mode Screener:",
        [
            "1. Single / Custom Ticker",
            "2. Full Batch Screener (Daftar Saham 962 Ticker)",
        ],
        horizontal=True,
    )

    # --- MODE 1: SINGLE / CUSTOM TICKER ---
    if "1. Single" in mode_screener:
        col_input, col_btn = st.columns([3, 1])

        with col_input:
            input_ticker = st.text_input(
                "Masukkan Kode Saham (Pisahkan dengan koma jika lebih dari 1):",
                value="",
                placeholder="Contoh: BBCA, BMRI, TLKM, INCO",
            )

        with col_btn:
            st.write(" ")
            st.write(" ")
            btn_single = st.button(
                "Run Single Ticker", type="primary", use_container_width=True
            )

        if btn_single:
            if not input_ticker.strip():
                st.warning("Silakan masukkan kode saham terlebih dahulu!")
            else:
                list_to_scan = [
                    t.strip().upper()
                    for t in input_ticker.split(",")
                    if t.strip()
                ]
                run_batch_execution(list_to_scan)

    # --- MODE 2: FULL BATCH SCREENER ---
    else:
        all_tickers = load_daftar_saham("daftar_saham.txt")
        if not all_tickers:
            st.error(
                "File 'daftar_saham.txt' tidak ditemukan atau kosong di direktori utama!"
            )
            return

        st.info(f"Memuat **{len(all_tickers)} saham** dari `daftar_saham.txt`.")

        if st.button("Jalankan Batch Screener (962 Saham)", type="primary"):
            run_batch_execution(all_tickers)

    # ---------------------------------------------------------
    # 2. PANEL FILTER & HASIL SCREENER
    # ---------------------------------------------------------
    if "df_screener_raw" in st.session_state:
        df_raw = st.session_state["df_screener_raw"]

        st.markdown("---")

        col_title, col_clear = st.columns([3, 1])
        with col_title:
            st.subheader("Filter & Sortir Hasil Screener")
        with col_clear:
            st.write(" ")
            st.button(
                "Clear / Reset Filter",
                on_click=reset_filters,
                use_container_width=True,
            )

        row1_col1, row1_col2, row1_col3 = st.columns(3)
        with row1_col1:
            f_strategi = st.selectbox(
                "Strategi Trading:",
                ["SEMUA STRATEGI", "Buy On Weakness (BOW)", "Breakout (BOB)"],
                key="f_strategi",
            )
        with row1_col2:
            f_grade = st.selectbox(
                "Kualitas Setup (Grade):",
                [
                    "SEMUA GRADE",
                    "Grade A / A+ Only (High Quality)",
                    "Grade B Kebawah (Moderate/Risk)",
                ],
                key="f_grade",
            )
        with row1_col3:
            f_zone = st.selectbox(
                "Posisi Harga Saat Ini:",
                [
                    "SEMUA POSISI",
                    "In Buy Zone (Siap Eksekusi)",
                    "Near Zone (Dekat Entry)",
                ],
                key="f_zone",
            )

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            f_rr = st.selectbox(
                "Minimal Risk-to-Reward:",
                [
                    "SEMUA RASIO",
                    "Min 1 : 1.5",
                    "Min 1 : 2.0 (Pro Standard)",
                    "Min 1 : 3.0 (High Reward)",
                ],
                key="f_rr",
            )
        with row2_col2:
            f_candle = st.selectbox(
                "Sinyal Candlestick:",
                ["SEMUA CANDLE", "Bullish Signal Only", "Neutral / Doji Only"],
                key="f_candle",
            )

        # --- LOGIKA FILTER ---
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

        st.subheader(
            f"Hasil Screener ({len(df)} dari {len(df_raw)} Saham Lolos Filter)"
        )

        if df.empty:
            st.warning(
                "Tidak ada saham yang cocok dengan kombinasi filter Anda. Coba longgarkan kriteria filter atau tekan tombol 'Clear / Reset Filter'."
            )
        else:
            # TAMPILAN CARD DENGAN ST.CONTAINER (BERSIH, SAFE, DAN INTERAKTIF)
            for idx, row in df.iterrows():
                with st.container(border=True):
                    # Card Header
                    c_h1, c_h2 = st.columns([3, 1])
                    with c_h1:
                        st.markdown(
                            f"### **{row['Saham']}** · {row['Strategi']} | Score: `{row['Score']}` (`{row['Grade']}`)"
                        )
                    with c_h2:
                        st.caption(f"Posisi: **{row['Posisi Zone']}**")

                    # Grid Metric Harga & Planning
                    m1, m2, m3, m4, m5, m6 = st.columns(6)
                    m1.metric("Harga Last", f"Rp {row['Harga Last']:,}")
                    m2.metric("Area Buy", str(row["Area Buy"]))
                    m3.metric(
                        "Stop Loss (SL)",
                        f"{row['Stop Loss (SL)']:,}",
                        delta=row["Risiko SL"],
                        delta_color="inverse",
                    )
                    m4.metric(
                        "TP 1",
                        f"{row['TP 1']:,}",
                        delta=row["Potensi Gain"],
                        delta_color="normal",
                    )
                    m5.metric("TP 2", f"{row['TP 2']:,}")
                    m6.metric("R:R Ratio", str(row["Rasio (R:R)"]))

                    # Footer Info & Warning
                    st.caption(
                        f"**Pola Candle:** {row['Pola Candle']} | **Catatan:** {row['Catatan Analisis & Warning']}"
                    )
