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
        f"Berhasil menganalisis {len(results)} dari {total_saham} saham!",
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
    # 🎨 INJEKSI CSS CUSTOM PREMIUM DASHBOARD
    st.markdown(
        """
        <style>
        /* Header Title Gradient */
        .main-header {
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
            letter-spacing: -0.5px;
        }
        .sub-header {
            color: #94A3B8;
            font-size: 0.95rem;
            margin-bottom: 25px;
        }

        /* Container Card styling */
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] > div[data-testid="stBlock"] {
            border-radius: 12px;
        }
        
        /* Input Field Styling */
        div[data-baseweb="input"] {
            border-radius: 8px !important;
            border: 1px solid #334155 !important;
            background-color: #0F172A !important;
        }
        div[data-baseweb="input"]:focus-within {
            border-color: #38BDF8 !important;
            box-shadow: 0 0 0 1px #38BDF8 !important;
        }

        /* Custom Button Styling */
        div.stButton > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease-in-out !important;
            border: none !important;
        }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
            color: #FFFFFF !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.5) !important;
            transform: translateY(-1px);
        }

        /* Radio Group Styling */
        div[role="radiogroup"] {
            gap: 20px;
            background: #0F172A;
            padding: 10px 16px;
            border-radius: 10px;
            border: 1px solid #1E293B;
        }

        /* Metric Box Custom */
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.7) 100%);
            border: 1px solid #334155;
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        div[data-testid="stMetricLabel"] {
            color: #94A3B8 !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
        }
        div[data-testid="stMetricValue"] {
            color: #F8FAFC !important;
            font-weight: 700 !important;
            font-size: 1.5rem !important;
        }

        /* Expander / Filter Box */
        div[data-testid="stExpander"] {
            background-color: #0F172A !important;
            border: 1px solid #1E293B !important;
            border-radius: 12px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- HEADER ---
    st.markdown('<p class="main-header">⚡ Smart Execution Screener</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Platform pemeringkat saham cerdas berbasis <b>Price Action</b>, <b>Risk-to-Reward Ratio</b>, & <b>Skoring Otomatis</b>.</p>', unsafe_allow_html=True)

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

    # --- 1. PANEL CONTROLLER / MODE ---
    with st.container(border=True):
        st.markdown("<span style='font-weight:600; color:#E2E8F0; font-size: 0.95rem;'>🎯 Pilih Mode Screener</span>", unsafe_allow_html=True)
        st.write("")
        mode_screener = st.radio(
            "Pilih Mode Screener:",
            [
                "⚡ Single / Custom Ticker",
                "🚀 Full Batch Screener (Daftar Saham 962 Ticker)",
            ],
            horizontal=True,
            label_visibility="collapsed"
        )
        st.write("")

        # MODE 1: SINGLE / CUSTOM TICKER
        if "⚡ Single" in mode_screener:
            col_input, col_btn = st.columns([3.5, 1], vertical_alignment="bottom")

            with col_input:
                input_ticker = st.text_input(
                    "Masukkan Kode Saham:",
                    value="",
                    placeholder="Contoh: BBCA, BMRI, TLKM, INCO (pisahkan koma)",
                )

            with col_btn:
                btn_single = st.button(
                    "🔍 Analisis Sekarang", type="primary", use_container_width=True
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
                st.error("❌ File `daftar_saham.txt` tidak ditemukan di folder utama!")
                return

            col_info, col_batch_btn = st.columns([3, 1], vertical_alignment="center")
            with col_info:
                st.info(f"📁 Siap memindai **{len(all_tickers)} saham** sekaligus dari database `daftar_saham.txt`.")
            with col_batch_btn:
                if st.button("🚀 Jalankan Batch Screener", type="primary", use_container_width=True):
                    run_batch_execution(all_tickers)

    # --- 2. STATS KPI DASHBOARD & PANEL FILTER ---
    if "df_screener_raw" in st.session_state:
        df_raw = st.session_state["df_screener_raw"]

        st.write("")

        # KPI Metrics Cards
        c1, c2, c3, c4 = st.columns(4)
        total_scanned = len(df_raw)
        in_buy_zone = len(df_raw[df_raw["Posisi Zone"] == "In Buy Zone"])
        high_grade = len(df_raw[df_raw["Score"] >= 70])
        avg_score = round(df_raw["Score"].mean(), 1) if not df_raw.empty else 0

        c1.metric("TOTAL SAHAM", f"{total_scanned}")
        c2.metric("IN BUY ZONE", f"{in_buy_zone}", delta=f"{(in_buy_zone/total_scanned*100):.1f}%" if total_scanned else None)
        c3.metric("GRADE A / A+", f"{high_grade}")
        c4.metric("AVG SCORE", f"{avg_score} / 100")

        st.write("")

        # Panel Filter
        with st.expander("🎛️ **Filter & Custom Screener Result**", expanded=True):
            r1c1, r1c2, r1c3 = st.columns(3)
            with r1c1:
                f_strategi = st.selectbox(
                    "🎯 Strategi Trading",
                    ["SEMUA STRATEGI", "Buy On Weakness (BOW)", "Breakout (BOB)"],
                    key="f_strategi",
                )
            with r1c2:
                f_grade = st.selectbox(
                    "🏆 Kualitas Setup",
                    [
                        "SEMUA GRADE",
                        "Grade A / A+ Only (High Quality)",
                        "Grade B Kebawah (Moderate/Risk)",
                    ],
                    key="f_grade",
                )
            with r1c3:
                f_zone = st.selectbox(
                    "📍 Posisi Harga",
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
                    "⚖️ Minimal Risk-to-Reward",
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
                    "🕯️ Sinyal Candlestick",
                    ["SEMUA CANDLE", "Bullish Signal Only", "Neutral / Doji Only"],
                    key="f_candle",
                )
            with r2c3:
                st.button("🔄 Reset Filter", on_click=reset_filters, use_container_width=True)

        # Logika Filtering Data
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

        # Sort berdasarkan Score tertinggi
        df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

        st.write("")

        # Header Hasil + Download CSV
        h_left, h_right = st.columns([3, 1], vertical_alignment="center")
        with h_left:
            st.markdown(f"### 📋 Hasil Screener <span style='font-size:1rem; color:#38BDF8;'>({len(df)} Lolos Filter)</span>", unsafe_allow_html=True)
        with h_right:
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
            st.warning("⚠️ Tidak ada saham yang sesuai dengan kombinasi filter Anda. Silakan longgarkan kriteria filter.")
        else:
            # Dataframe Modern & Interactive
            st.dataframe(
                df,
                column_config={
                    "Saham": st.column_config.TextColumn("Saham"),
                    "Score": st.column_config.ProgressColumn(
                        "Score (0-100)",
                        help="Skor Kualitas Setup Saham",
                        format="%d pts",
                        min_value=0,
                        max_value=100,
                    ),
                    "Grade": st.column_config.TextColumn("Grade"),
                    "Strategi": st.column_config.TextColumn("Strategi"),
                    "Harga Last": st.column_config.NumberColumn("Harga Last", format="Rp %d"),
                    "Posisi Zone": st.column_config.TextColumn("Posisi Price"),
                    "Area Buy": st.column_config.TextColumn("Area Buy (Entry)"),
                    "Stop Loss (SL)": st.column_config.NumberColumn("SL", format="%d"),
                    "TP 1": st.column_config.NumberColumn("TP 1", format="%d"),
                    "TP 2": st.column_config.NumberColumn("TP 2", format="%d"),
                    "Potensi Gain": st.column_config.TextColumn("Gain TP1"),
                    "Risiko SL": st.column_config.TextColumn("Risk SL"),
                    "Rasio (R:R)": st.column_config.TextColumn("R:R Ratio"),
                    "RR_Val": None,
                    "Pola Candle": st.column_config.TextColumn("Candle Signal"),
                    "Catatan Analisis & Warning": st.column_config.TextColumn("Analisis & Warning", width="large"),
                },
                hide_index=True,
                use_container_width=True,
            )
