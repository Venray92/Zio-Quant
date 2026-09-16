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

        selected_plan = df_plan[df_plan["Type"] == direction_rec]
        if selected_plan.empty:
            selected_plan = df_plan.iloc[[0]]

        p = selected_plan.iloc[0]

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
    # 🎨 OVERHAUL CSS: STYLING CARD BUTTON MODERN
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #07090E !important;
        }

        /* Header Style Zio */
        .zio-header-wrapper {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: #0D111A;
            border: 1px solid #1E2638;
            border-radius: 14px;
            padding: 18px 24px;
            margin-bottom: 20px;
        }
        .zio-header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .zio-icon-square {
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
            width: 44px;
            height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 15px rgba(139, 92, 246, 0.3);
        }
        .zio-title-text {
            color: #FFFFFF;
            font-size: 1.35rem;
            font-weight: 700;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .zio-badge-pill {
            background-color: rgba(168, 85, 247, 0.15);
            color: #C084FC;
            border: 1px solid rgba(168, 85, 247, 0.3);
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 600;
        }
        .zio-subtitle-text {
            color: #64748B;
            font-size: 0.85rem;
            margin-top: 2px;
        }

        /* Main Container Box */
        .zio-card-container {
            background-color: #0D111A;
            border: 1px solid #1E2638;
            border-radius: 14px;
            padding: 22px;
            margin-bottom: 20px;
        }

        /* Status Cards 3 Kolom */
        .zio-status-card {
            background-color: #0D111A;
            border: 1px solid #1E2638;
            border-radius: 14px;
            padding: 18px 20px;
            height: 100%;
        }
        .zio-status-title {
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }
        .zio-status-value {
            font-size: 1.25rem;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 4px;
        }
        .zio-status-desc {
            font-size: 0.78rem;
            color: #64748B;
            line-height: 1.3;
        }

        /* Form Titles */
        .zio-form-header {
            color: #FFFFFF;
            font-size: 1.05rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
        }
        .zio-label {
            color: #94A3B8;
            font-size: 0.82rem;
            font-weight: 600;
            margin-bottom: 6px;
            display: block;
        }

        /* Input Custom */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
            background-color: #07090E !important;
            border: 1px solid #1E2638 !important;
            border-radius: 8px !important;
            color: #F8FAFC !important;
        }
        div[data-baseweb="input"]:focus-within > div, div[data-baseweb="select"]:focus-within > div {
            border-color: #8B5CF6 !important;
            box-shadow: 0 0 0 1px #8B5CF6 !important;
        }

        /* Custom Button Styling */
        div.stButton > button {
            background-color: #111625 !important;
            color: #94A3B8 !important;
            border: 1px solid #1E2638 !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            padding: 12px 18px !important;
            transition: all 0.2s ease-in-out !important;
            height: auto !important;
        }
        div.stButton > button:hover {
            border-color: #8B5CF6 !important;
            color: #FFFFFF !important;
            box-shadow: 0 0 12px rgba(139, 92, 246, 0.3) !important;
        }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            box-shadow: 0 4px 16px rgba(139, 92, 246, 0.4) !important;
        }
        div.stButton > button[kind="primary"]:hover {
            box-shadow: 0 6px 22px rgba(139, 92, 246, 0.6) !important;
        }

        /* Expander */
        div[data-testid="stExpander"] {
            background-color: #0D111A !important;
            border: 1px solid #1E2638 !important;
            border-radius: 12px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- HEADER MODEL ZIO ---
    st.markdown(
        """
        <div class="zio-header-wrapper">
            <div class="zio-header-left">
                <div class="zio-icon-square">📊</div>
                <div>
                    <div class="zio-title-text">
                        Smart Execution Screener
                        <span class="zio-badge-pill">Screener Engine v3.0</span>
                    </div>
                    <div class="zio-subtitle-text">Platform pemeringkat & rekomendasi saham berbasis Price Action, Risk-to-Reward Ratio, dan Skoring Otomatis.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Inisialisasi State Filter & Mode Screener
    if "screener_mode" not in st.session_state:
        st.session_state["screener_mode"] = "single"
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

    # --- 1. CARD CONTAINER: MODE SCREENER (MODERN CARD SELECTOR) ---
    st.markdown('<div class="zio-card-container">', unsafe_allow_html=True)
    st.markdown(
        '<div class="zio-form-header"><span style="color:#A855F7;">🎯</span> Pilih Mode Eksekusi Screener</div>',
        unsafe_allow_html=True,
    )

    # Modern Card Selector (Tanpa Radio / Checkbox)
    mode_col1, mode_col2 = st.columns(2)
    current_mode = st.session_state["screener_mode"]

    with mode_col1:
        is_single = current_mode == "single"
        btn_type_single = "primary" if is_single else "secondary"
        if st.button(
            "⚡ Single / Custom Ticker\n\nAnalisis 1 atau beberapa kode saham tertentu",
            use_container_width=True,
            type=btn_type_single,
            key="btn_card_single",
        ):
            st.session_state["screener_mode"] = "single"
            st.rerun()

    with mode_col2:
        is_batch = current_mode == "batch"
        btn_type_batch = "primary" if is_batch else "secondary"
        if st.button(
            "🚀 Full Batch Screener\n\nScan otomatis 962+ saham dari database",
            use_container_width=True,
            type=btn_type_batch,
            key="btn_card_batch",
        ):
            st.session_state["screener_mode"] = "batch"
            st.rerun()

    st.write("")

    # Form Aksi berdasarkan Card yang Dipilih
    if st.session_state["screener_mode"] == "single":
        col_input, col_btn = st.columns([3.5, 1], vertical_alignment="bottom")
        with col_input:
            st.markdown(
                '<span class="zio-label">Masukkan Kode Saham:</span>',
                unsafe_allow_html=True,
            )
            input_ticker = st.text_input(
                "Kode Saham",
                value="",
                placeholder="Contoh: BBCA, BMRI, TLKM, INCO (pisahkan koma)",
                label_visibility="collapsed",
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

    else:
        all_tickers = load_daftar_saham("daftar_saham.txt")
        if not all_tickers:
            st.error("❌ File `daftar_saham.txt` tidak ditemukan di folder utama!")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        col_info, col_batch_btn = st.columns([3, 1], vertical_alignment="center")
        with col_info:
            st.info(f"📁 Siap menganalisis **{len(all_tickers)} saham** dari database `daftar_saham.txt`.")
        with col_batch_btn:
            if st.button("🚀 Jalankan Batch", type="primary", use_container_width=True):
                run_batch_execution(all_tickers)

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 2. STATS CARD 3 KOLOM + FILTER PANEL ---
    if "df_screener_raw" in st.session_state:
        df_raw = st.session_state["df_screener_raw"]

        c1, c2, c3 = st.columns(3)
        total_scanned = len(df_raw)
        in_buy_zone = len(df_raw[df_raw["Posisi Zone"] == "In Buy Zone"])
        high_grade = len(df_raw[df_raw["Score"] >= 70])

        with c1:
            st.markdown(
                f"""
                <div class="zio-status-card">
                    <div class="zio-status-title" style="color: #00E676;">
                        <span>🕒</span> Total Saham Scanned
                    </div>
                    <div class="zio-status-value">{total_scanned} Saham</div>
                    <div class="zio-status-desc">Hasil pemindaian algoritma aktif</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                f"""
                <div class="zio-status-card">
                    <div class="zio-status-title" style="color: #00E676;">
                        <span>🛡️</span> In Buy Zone
                    </div>
                    <div class="zio-status-value" style="color: #00E676;">{in_buy_zone} Saham</div>
                    <div class="zio-status-desc">Siap dieksekusi masuk area entry</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                f"""
                <div class="zio-status-card">
                    <div class="zio-status-title" style="color: #F59E0B;">
                        <span>📖</span> High Quality Setup
                    </div>
                    <div class="zio-status-value" style="color: #F59E0B;">{high_grade} Grade A/A+</div>
                    <div class="zio-status-desc">Score analisis &gt;= 70 poin</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")

        # Panel Filter Custom
        with st.expander("🛠️ **Parameter & Custom Filter Result**", expanded=True):
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

        # Logika Filter
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

        df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

        st.write("")

        # Table Header
        h_left, h_right = st.columns([3, 1], vertical_alignment="center")
        with h_left:
            st.markdown(
                f"### 📋 Hasil Screener <span style='font-size:0.9rem; color:#A855F7;'>({len(df)} Lolos Filter)</span>",
                unsafe_allow_html=True,
            )
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
            st.warning("⚠️ Tidak ada saham yang sesuai dengan kombinasi filter Anda.")
        else:
            st.dataframe(
                df,
                column_config={
                    "Saham": st.column_config.TextColumn("Saham"),
                    "Score": st.column_config.ProgressColumn(
                        "Score",
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

    # Footer
    st.markdown(
        """
        <br>
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #1E2638; padding-top: 12px; color: #475569; font-size: 0.8rem;">
            <div>Official Trade Planner Screener • Melayani trader saham seluruh Indonesia</div>
            <div style="color: #A855F7; font-weight: 600; cursor: pointer;">System Active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
