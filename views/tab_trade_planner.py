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
    # 🎨 OVERHAUL CSS: INJEKSI UI MODERN SESUAI DESAIN GAMBAR
    st.markdown(
        """
        <style>
        /* Modern Clean Header Styling */
        .header-title-container {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 4px;
        }
        .header-icon-box {
            background-color: #6366F1;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
        }
        .header-text {
            color: #FFFFFF;
            font-size: 1.6rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.3px;
        }
        .pill-badge {
            background-color: rgba(168, 85, 247, 0.2);
            color: #C084FC;
            border: 1px solid rgba(168, 85, 247, 0.4);
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 8px;
        }
        .header-subtitle {
            color: #94A3B8;
            font-size: 0.9rem;
            margin-bottom: 20px;
            margin-left: 2px;
        }

        /* Container Card - Sesuai gaya Gambar */
        div[data-testid="stForm"], div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] > div[data-testid="stBlock"] {
            border-radius: 14px;
        }
        
        /* Dark Card Container Custom Class */
        .zio-card {
            background-color: #0B101D;
            border: 1px solid #1E293B;
            border-radius: 14px;
            padding: 18px 22px;
            margin-bottom: 16px;
        }
        .zio-card-title {
            color: #FFFFFF;
            font-weight: 700;
            font-size: 1rem;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Inputs & Selectboxes - Dark Navy Solid */
        div[data-baseweb="input"], div[data-baseweb="select"] > div {
            background-color: #080C14 !important;
            border: 1px solid #1E293B !important;
            border-radius: 10px !important;
            color: #F8FAFC !important;
        }
        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
            border-color: #6366F1 !important;
            box-shadow: 0 0 0 1px #6366F1 !important;
        }

        /* Streamlit Button - Custom Dark Solid with Glow */
        div.stButton > button {
            background-color: #111827 !important;
            color: #F8FAFC !important;
            border: 1px solid #374151 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 8px 16px !important;
            transition: all 0.2s ease !important;
        }
        div.stButton > button:hover {
            background-color: #1F2937 !important;
            border-color: #6366F1 !important;
            color: #FFFFFF !important;
            box-shadow: 0 0 12px rgba(99, 102, 241, 0.3) !important;
        }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%) !important;
            border: none !important;
            color: #FFFFFF !important;
            box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4) !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #4338CA 0%, #2563EB 100%) !important;
            box-shadow: 0 6px 18px rgba(79, 70, 229, 0.6) !important;
        }

        /* Radio Selector Box Modern Dark */
        div[role="radiogroup"] {
            background-color: #080C14;
            border: 1px solid #1E293B;
            border-radius: 10px;
            padding: 10px 16px;
            gap: 20px;
        }

        /* Metric KPI Custom Cards */
        .kpi-card {
            background-color: #0B101D;
            border: 1px solid #1E293B;
            border-radius: 12px;
            padding: 14px 18px;
        }
        .kpi-label {
            color: #94A3B8;
            font-size: 0.8rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .kpi-value {
            font-size: 1.4rem;
            font-weight: 700;
            margin-top: 4px;
        }
        .kpi-sub {
            font-size: 0.75rem;
            color: #64748B;
            margin-top: 2px;
        }

        /* Expander Filter Styling */
        div[data-testid="stExpander"] {
            background-color: #0B101D !important;
            border: 1px solid #1E293B !important;
            border-radius: 12px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- HEADER MODEL GAMBAR SUPPORT ZIO ---
    st.markdown(
        """
        <div class="header-title-container">
            <div class="header-icon-box">📊</div>
            <div class="header-text">
                Smart Execution Screener
                <span class="pill-badge">v2.4 Pro</span>
            </div>
        </div>
        <p class="header-subtitle">Platform pemeringkat & rekomendasi saham berbasis Price Action, Risk-to-Reward Ratio, dan Skoring Otomatis.</p>
        """,
        unsafe_allow_html=True,
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

    # --- 1. PANEL CONTROLLER / MODE ---
    with st.container(border=True):
        st.markdown('<div class="zio-card-title"><span style="color:#A855F7;">🎯</span> Pilih Mode Screener</div>', unsafe_allow_html=True)
        mode_screener = st.radio(
            "Pilih Mode Screener:",
            [
                "⚡ Single / Custom Ticker",
                "🚀 Full Batch Screener (Daftar Saham 962 Ticker)",
            ],
            horizontal=True,
            label_visibility="collapsed",
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
                st.error("❌ File `daftar_saham.txt` tidak ditemukan di direktori utama!")
                return

            col_info, col_batch_btn = st.columns([3, 1], vertical_alignment="center")
            with col_info:
                st.info(f"📁 Siap menganalisis **{len(all_tickers)} saham** sekaligus dari `daftar_saham.txt`.")
            with col_batch_btn:
                if st.button("🚀 Jalankan Batch", type="primary", use_container_width=True):
                    run_batch_execution(all_tickers)

    # --- 2. METRICS STATS CARDS & PANEL FILTER ---
    if "df_screener_raw" in st.session_state:
        df_raw = st.session_state["df_screener_raw"]

        st.write("")

        # 3 CARD KPI PERSIS MODEL DOKUMENTASI / STATUS SISTEM
        c1, c2, c3 = st.columns(3)
        total_scanned = len(df_raw)
        in_buy_zone = len(df_raw[df_raw["Posisi Zone"] == "In Buy Zone"])
        high_grade = len(df_raw[df_raw["Score"] >= 70])

        with c1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label"><span style="color:#00E676;">⏱</span> Total Saham Scanned</div>
                    <div class="kpi-value" style="color:#FFFFFF;">{total_scanned} Saham</div>
                    <div class="kpi-sub">Hasil analisis screener aktif</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label"><span style="color:#00E676;">🛡</span> Status Zone</div>
                    <div class="kpi-value" style="color:#00E676;">{in_buy_zone} In Buy Zone</div>
                    <div class="kpi-sub">Siap dieksekusi berdasarkan plan</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label"><span style="color:#F59E0B;">📖</span> Setup Quality</div>
                    <div class="kpi-value" style="color:#F59E0B;">{high_grade} Grade A/A+</div>
                    <div class="kpi-sub">Score di atas 70 poin</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")

        # Expandable Filter Form (Mirip Form Pertanyaan)
        with st.expander("❓ **Kirim Filter / Custom Screener Parameter**", expanded=True):
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
                st.button("🔄 Reset Filter", on_click=reset_filters, use_container_width=True)

        # Logika Filter Data
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

        # Urutkan berdasarkan Score
        df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

        st.write("")

        # Header Hasil + Download CSV Button
        h_left, h_right = st.columns([3, 1], vertical_alignment="center")
        with h_left:
            st.markdown(f"### 📋 Hasil Screener <span style='font-size:0.9rem; color:#A855F7;'>({len(df)} Lolos Filter)</span>", unsafe_allow_html=True)
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
            st.warning("⚠️ Tidak ada saham yang sesuai dengan filter Anda.")
        else:
            # Dataframe Display
            st.dataframe(
                df,
                column_config={
                    "Saham": st.column_config.TextColumn("Saham"),
                    "Score": st.column_config.ProgressColumn(
                        "Score (0-100)",
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

        # FOOTER SESUAI GAMBAR REFERENSI
        st.markdown(
            """
            <br>
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #1E293B; padding-top: 12px; color: #64748B; font-size: 0.8rem;">
                <div>Official Screener Module • Melayani trader saham seluruh Indonesia</div>
                <div style="color: #A855F7; font-weight: 600; cursor: pointer;">System Active</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
