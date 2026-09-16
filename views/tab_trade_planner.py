import concurrent.futures
import os
import pandas as pd
import streamlit as st

from trade_planner import TradePlanner


def load_daftar_saham(filename="daftar_saham.txt"):
    """Reads ticker list from file."""
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
    """Single ticker execution processor."""
    symbol = ticker_code.strip().upper()
    if not symbol.endswith(".JK"):
        symbol += ".JK"

    try:
        planner = TradePlanner(symbol, period="6mo")
        planner.fetch_and_prepare_data()

        df_dir = planner.get_direction()
        df_plan = planner.generate_trade_plan()

        if df_dir is None or df_plan is None or df_dir.empty or df_plan.empty:
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
            "Symbol": symbol.replace(".JK", ""),
            "Score": int(p["Score"]) if pd.notnull(p["Score"]) else 0,
            "Grade": str(p["Grade"]),
            "Strategy": str(p["Type"]),
            "Last Price": curr_close,
            "Zone Position": str(p["Posisi Harga"]),
            "Buy Range": str(p["Area Buy"]),
            "Stop Loss (SL)": int(p["Stop Loss"]) if pd.notnull(p["Stop Loss"]) else 0,
            "TP 1": int(p["TP 1"]) if pd.notnull(p["TP 1"]) else 0,
            "TP 2": int(p["TP 2"]) if pd.notnull(p["TP 2"]) else 0,
            "Potential Gain": f"+{pot_gain}%",
            "SL Risk": f"-{pot_risk}%",
            "Risk-Reward Ratio": str(p["Rasio (R:R)"]),
            "RR_Val": float(p["RR_Val"]) if "RR_Val" in p and pd.notnull(p["RR_Val"]) else 0.0,
            "Candlestick Pattern": str(p["Pola Candle"]),
            "Analysis & Risk Warning": str(p["Warning"]),
        }
    except Exception:
        return None


def run_batch_execution(ticker_list, cache_key):
    """Multi-threaded execution runner."""
    total_saham = len(ticker_list)
    if total_saham == 0:
        st.warning("⚠️ Daftar saham kosong!")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    results = []
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ticker = {
            executor.submit(process_single_ticker, t): t for t in ticker_list
        }

        for future in concurrent.futures.as_completed(future_to_ticker):
            res = future.result()
            if res:
                results.append(res)

            completed += 1
            percent = completed / total_saham
            progress_bar.progress(percent)
            status_text.markdown(
                f"⏳ <span style='color:#00ff66; font-family: monospace;'>Memproses:</span> `{completed}/{total_saham}` saham ({int(percent * 100)}%)",
                unsafe_allow_html=True,
            )

    progress_bar.empty()
    status_text.empty()
    st.toast(
        f"Analisis selesai: {len(results)} dari {total_saham} saham diproses!",
        icon="⚡",
    )

    if results:
        df_res = pd.DataFrame(results)
        st.session_state[cache_key] = df_res


def reset_filters():
    """Reset filter pilihan ke default."""
    st.session_state["f_strategi"] = "Semua Strategi"
    st.session_state["f_grade"] = "Semua Grade"
    st.session_state["f_zone"] = "Semua Posisi"
    st.session_state["f_rr"] = "Semua Rasio"
    st.session_state["f_candle"] = "Semua Candlestick"


def clear_cache(cache_key):
    """Hapus cache data."""
    st.session_state.pop(cache_key, None)
    st.toast("Data berhasil dihapus!", icon="🧹")


def draw_card(title, value, subtext, badge_text="", variant="cyan", value_color="cyan"):
    """Komponen Card Cyberpunk Clean."""
    badge_html = (
        f'<span class="cp-badge badge-{variant}">{badge_text}</span>'
        if badge_text
        else ""
    )

    card_html = f"""
    <div class="cp-card cp-card-{variant}">
        <div class="cp-card-header">
            <span class="cp-card-title title-{variant}">{title}</span>
            {badge_html}
        </div>
        <div class="cp-card-value val-{value_color}">{value}</div>
        <p class="cp-card-subtext">{subtext}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_trade_plan_cards(df_data, is_title_needed=True):
    """Render Trade Plan Cards dengan gaya Cyberpunk Cyan & Green."""
    if is_title_needed:
        st.markdown(
            f"<h3 style='color:#00f3ff; font-family: sans-serif; font-weight: 700;'>Rencana Trading <span style='font-size:0.9rem; color:#00ff66;'>({len(df_data)} Saham)</span></h3>",
            unsafe_allow_html=True,
        )

    for idx, row in df_data.iterrows():
        st.markdown(
            f"""
            <div style="background: #091018; border: 1px solid #00f3ff; box-shadow: 0 0 10px rgba(0, 243, 255, 0.15); padding: 16px 20px; border-radius: 4px; margin-top: 20px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                    <span style="font-size: 1.5rem; font-weight: 800; color: #00ff66; text-shadow: 0 0 6px rgba(0, 255, 102, 0.4); letter-spacing: 1px;">{row['Symbol']}</span>
                    <span style="background: rgba(0, 243, 255, 0.1); color: #00f3ff; border: 1px solid #00f3ff; padding: 3px 10px; font-size: 0.8rem; font-weight: 600;">Strategi: {row['Strategy']}</span>
                    <span style="background: rgba(0, 255, 102, 0.1); color: #00ff66; border: 1px solid #00ff66; padding: 3px 10px; font-size: 0.8rem; font-weight: 600;">Grade: {row['Grade']}</span>
                    <span style="background: rgba(0, 243, 255, 0.1); color: #00f3ff; border: 1px solid #00f3ff; padding: 3px 10px; font-size: 0.8rem; font-weight: 600;">Skor: {row['Score']}/100</span>
                </div>
                <div style="color: #90a4ae; font-size: 0.9rem;">
                    Harga Terakhir: <strong style="color: #00f3ff; font-size: 1.2rem;">Rp {row['Last Price']:,}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            draw_card(
                title="Area Beli (Entry)",
                value=str(row["Buy Range"]),
                subtext=f"Status: {row['Zone Position']}",
                badge_text=str(row["Zone Position"]),
                variant="cyan",
                value_color="cyan",
            )
            draw_card(
                title="Target Harga 1 (TP 1)",
                value=f"Rp {row['TP 1']:,}",
                subtext="Target keuntungan pertama.",
                badge_text=str(row["Potential Gain"]),
                variant="green",
                value_color="green",
            )

        with col2:
            draw_card(
                title="Stop Loss (SL)",
                value=f"Rp {row['Stop Loss (SL)']:,}",
                subtext="Batas toleransi risiko.",
                badge_text=str(row["SL Risk"]),
                variant="cyan",
                value_color="cyan",
            )
            draw_card(
                title="Target Harga 2 (TP 2)",
                value=f"Rp {row['TP 2']:,}",
                subtext="Target keuntungan utama.",
                badge_text=f"R:R {row['Risk-Reward Ratio']}",
                variant="green",
                value_color="green",
            )

        st.markdown(
            f"""
            <div style="background: #050a10; border: 1px solid #142834; padding: 14px 18px; margin-bottom: 28px; border-radius: 4px; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
                <div>
                    <span style="font-size: 0.75rem; color: #607d8b; display: block;">Risk to Reward</span>
                    <span style="font-size: 0.95rem; color: #00f3ff; font-weight: 600;">1 : {row['Risk-Reward Ratio']}</span>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #607d8b; display: block;">Pola Candlestick</span>
                    <span style="font-size: 0.95rem; color: #00ff66; font-weight: 600;">{row['Candlestick Pattern']}</span>
                </div>
                <div style="grid-column: span 2;">
                    <span style="font-size: 0.75rem; color: #607d8b; display: block;">Analisis & Catatan Risiko</span>
                    <span style="font-size: 0.88rem; color: #b0bec5; font-weight: 500;">{row['Analysis & Risk Warning']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_tab_trade_planner():
    # 🎨 CYBERPUNK CYAN & NEON GREEN STYLING (NO RED / NO AGGRESSIVE GLITCH)
    st.markdown(
        """
        <style>
        /* Base Background */
        .stApp {
            background-color: #04080e !important;
            color: #c0cecf !important;
        }

        /* Clean Cyber Header */
        .cp-header-wrapper {
            display: flex;
            align-items: center;
            background: #08101a;
            border: 1px solid #00f3ff;
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.2);
            padding: 16px 20px;
            margin-bottom: 24px;
            border-radius: 4px;
        }
        .cp-title-text {
            color: #00f3ff;
            font-size: 1.4rem;
            font-weight: 700;
            letter-spacing: 1px;
        }

        /* Inputs Styling */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
            background-color: #070d16 !important;
            border: 1px solid #00f3ff !important;
            color: #00f3ff !important;
            border-radius: 4px !important;
        }
        div[data-baseweb="input"]:focus-within > div, div[data-baseweb="select"]:focus-within > div {
            border-color: #00ff66 !important;
            box-shadow: 0 0 8px rgba(0, 255, 102, 0.4) !important;
        }

        /* Cyber Buttons (Cyan & Neon Green) */
        div.stButton > button {
            background: #08121e !important;
            color: #00f3ff !important;
            border: 1px solid #00f3ff !important;
            border-radius: 4px !important;
            font-weight: 600 !important;
            padding: 10px 16px !important;
            transition: all 0.2s ease-in-out !important;
        }
        div.stButton > button:hover {
            background: #00f3ff !important;
            color: #04080e !important;
            box-shadow: 0 0 12px #00f3ff !important;
        }
        div.stButton > button[kind="primary"] {
            background: #00ff66 !important;
            color: #04080e !important;
            border: 1px solid #00ff66 !important;
            font-weight: 700 !important;
            box-shadow: 0 0 10px rgba(0, 255, 102, 0.3) !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background: #33ff88 !important;
            box-shadow: 0 0 16px #00ff66 !important;
        }

        /* Expander */
        div[data-testid="stExpander"] {
            background-color: #060c14 !important;
            border: 1px solid #00f3ff !important;
            border-radius: 4px !important;
        }

        /* Cards */
        .cp-card {
            background-color: #070e17;
            padding: 16px 18px;
            margin-bottom: 14px;
            border-radius: 4px;
            position: relative;
        }
        .cp-card-cyan { border: 1px solid #00f3ff; box-shadow: 0 0 8px rgba(0, 243, 255, 0.1); }
        .cp-card-green { border: 1px solid #00ff66; box-shadow: 0 0 8px rgba(0, 255, 102, 0.1); }

        .cp-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .cp-card-title {
            font-size: 0.82rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .title-cyan { color: #00f3ff; }
        .title-green { color: #00ff66; }

        .cp-badge {
            font-size: 0.72rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 3px;
        }
        .badge-cyan { background: rgba(0, 243, 255, 0.1); color: #00f3ff; border: 1px solid #00f3ff; }
        .badge-green { background: rgba(0, 255, 102, 0.1); color: #00ff66; border: 1px solid #00ff66; }

        .cp-card-value {
            font-size: 1.35rem;
            font-weight: 800;
            margin-bottom: 4px;
            line-height: 1.2;
        }
        .val-cyan { color: #00f3ff; }
        .val-green { color: #00ff66; }

        .cp-card-subtext {
            font-size: 0.78rem;
            color: #78909c;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- HEADER ---
    st.markdown(
        """
        <div class="cp-header-wrapper">
            <div class="cp-title-text">⚡ Trade Planner & Stock Screener</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "screener_mode" not in st.session_state:
        st.session_state["screener_mode"] = "single"
    if "f_strategi" not in st.session_state:
        st.session_state["f_strategi"] = "Semua Strategi"
    if "f_grade" not in st.session_state:
        st.session_state["f_grade"] = "Semua Grade"
    if "f_zone" not in st.session_state:
        st.session_state["f_zone"] = "Semua Posisi"
    if "f_rr" not in st.session_state:
        st.session_state["f_rr"] = "Semua Rasio"
    if "f_candle" not in st.session_state:
        st.session_state["f_candle"] = "Semua Candlestick"

    st.markdown(
        '<div style="color:#00ff66; font-weight:600; margin-bottom:8px;">Pilih Mode Analisis:</div>',
        unsafe_allow_html=True,
    )

    mode_col1, mode_col2 = st.columns(2)
    current_mode = st.session_state["screener_mode"]

    with mode_col1:
        is_single = current_mode == "single"
        btn_type_single = "primary" if is_single else "secondary"
        if st.button(
            "🔍 Analisis Saham Pilihan\nCek ticker saham tertentu",
            use_container_width=True,
            type=btn_type_single,
            key="btn_card_single",
        ):
            if st.session_state["screener_mode"] != "single":
                st.session_state["screener_mode"] = "single"
            st.rerun()

    with mode_col2:
        is_batch = current_mode == "batch"
        btn_type_batch = "primary" if is_batch else "secondary"
        if st.button(
            "🚀 Scan Semua Saham\nAnalisis seluruh daftar saham",
            use_container_width=True,
            type=btn_type_batch,
            key="btn_card_batch",
        ):
            if st.session_state["screener_mode"] != "batch":
                st.session_state["screener_mode"] = "batch"
            st.rerun()

    st.write("")

    if st.session_state["screener_mode"] == "single":
        col_input, col_btn = st.columns([3.5, 1], vertical_alignment="bottom")
        with col_input:
            st.markdown(
                '<span style="color:#00f3ff; font-size:0.85rem;">Masukkan Kode Saham:</span>',
                unsafe_allow_html=True,
            )
            input_ticker = st.text_input(
                "Kode Saham",
                value="",
                placeholder="BBCA, BMRI, TLKM, INCO...",
                label_visibility="collapsed",
            )
        with col_btn:
            btn_single = st.button(
                "🔍 Mulai Analisis", type="primary", use_container_width=True
            )

        if btn_single:
            if not input_ticker.strip():
                st.warning("⚠️ Kode saham belum diisi!")
            else:
                list_to_scan = [
                    t.strip().upper()
                    for t in input_ticker.split(",")
                    if t.strip()
                ]
                run_batch_execution(list_to_scan, cache_key="df_screener_single")

        active_cache_key = "df_screener_single"

        if active_cache_key in st.session_state:
            df_single_res = st.session_state[active_cache_key]

            st.write("")
            h_left, h_right = st.columns([3, 1], vertical_alignment="center")
            with h_left:
                st.markdown(
                    f"<h3 style='color:#00f3ff;'>Hasil Analisis <span style='font-size:0.9rem; color:#00ff66;'>({len(df_single_res)} Saham)</span></h3>",
                    unsafe_allow_html=True,
                )
            with h_right:
                if st.button("🗑️ Hapus Hasil", use_container_width=True, key="btn_clear_single"):
                    clear_cache(active_cache_key)
                    st.rerun()

            if df_single_res.empty:
                st.warning("⚠️ Tidak ada data yang ditemukan.")
            else:
                render_trade_plan_cards(df_single_res, is_title_needed=False)

    else:
        all_tickers = load_daftar_saham("daftar_saham.txt")
        if not all_tickers:
            st.error("❌ File `daftar_saham.txt` tidak ditemukan!")
            return

        col_info, col_batch_btn = st.columns([3, 1], vertical_alignment="center")
        with col_info:
            st.info(f"📁 Siap menganalisis **{len(all_tickers)} saham** dari file `daftar_saham.txt`.")
        with col_batch_btn:
            if st.button("🚀 Jalankan Scan", type="primary", use_container_width=True):
                run_batch_execution(all_tickers, cache_key="df_screener_batch")

        active_cache_key = "df_screener_batch"

        if active_cache_key in st.session_state:
            df_raw = st.session_state[active_cache_key]

            st.write("")
            with st.expander("🛠️ **Filter Hasil Analisis**", expanded=True):
                r1c1, r1c2, r1c3 = st.columns(3)
                with r1c1:
                    f_strategi = st.selectbox(
                        "Strategi:",
                        ["Semua Strategi", "Buy On Weakness (BOW)", "Breakout (BOB)"],
                        key="f_strategi",
                    )
                with r1c2:
                    f_grade = st.selectbox(
                        "Grade Setup:",
                        [
                            "Semua Grade",
                            "Grade A / A+ (Kualitas Tinggi)",
                            "Grade B atau Lebih Rendah",
                        ],
                        key="f_grade",
                    )
                with r1c3:
                    f_zone = st.selectbox(
                        "Posisi Harga:",
                        [
                            "Semua Posisi",
                            "Dalam Area Beli (Siap Eksekusi)",
                            "Mendekati Area Beli",
                        ],
                        key="f_zone",
                    )

                r2c1, r2c2, r2c3 = st.columns([1.5, 1.5, 1], vertical_alignment="bottom")
                with r2c1:
                    f_rr = st.selectbox(
                        "Minimal Risk to Reward:",
                        [
                            "Semua Rasio",
                            "Min 1 : 1.5",
                            "Min 1 : 2.0 (Standar Pro)",
                            "Min 1 : 3.0 (Sangat Bagus)",
                        ],
                        key="f_rr",
                    )
                with r2c2:
                    f_candle = st.selectbox(
                        "Pola Candlestick:",
                        ["Semua Candlestick", "Hanya Sinyal Bullish", "Hanya Netral / Doji"],
                        key="f_candle",
                    )
                with r2c3:
                    st.button("🔄 Reset Filter", on_click=reset_filters, use_container_width=True)

            df = df_raw.copy()

            if f_strategi == "Buy On Weakness (BOW)":
                df = df[df["Strategy"] == "BOW"]
            elif f_strategi == "Breakout (BOB)":
                df = df[df["Strategy"] == "BOB"]

            if f_grade == "Grade A / A+ (Kualitas Tinggi)":
                df = df[df["Score"] >= 70]
            elif f_grade == "Grade B atau Lebih Rendah":
                df = df[df["Score"] < 70]

            if f_zone == "Dalam Area Beli (Siap Eksekusi)":
                df = df[df["Zone Position"] == "In Buy Zone"]
            elif f_zone == "Mendekati Area Beli":
                df = df[df["Zone Position"] == "Near Zone"]

            if f_rr == "Min 1 : 1.5":
                df = df[df["RR_Val"] >= 1.5]
            elif f_rr == "Min 1 : 2.0 (Standar Pro)":
                df = df[df["RR_Val"] >= 2.0]
            elif f_rr == "Min 1 : 3.0 (Sangat Bagus)":
                df = df[df["RR_Val"] >= 3.0]

            if f_candle == "Hanya Sinyal Bullish":
                df = df[
                    df["Candlestick Pattern"].str.contains(
                        "Engulfing|Morning|Soldiers|Marubozu|Hammer|Dragonfly",
                        case=False,
                        na=False,
                    )
                ]
            elif f_candle == "Hanya Netral / Doji":
                df = df[
                    df["Candlestick Pattern"].str.contains(
                        "Doji|Spinning|Standard", case=False, na=False
                    )
                ]

            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            st.write("")

            h_left, h_center, h_right = st.columns([2.5, 1, 1], vertical_alignment="center")
            with h_left:
                st.markdown(
                    f"<h3 style='color:#00f3ff;'>Daftar Hasil Screener <span style='font-size:0.9rem; color:#00ff66;'>({len(df)} Saham)</span></h3>",
                    unsafe_allow_html=True,
                )
            with h_center:
                if st.button("🗑️ Hapus Cache", use_container_width=True, key="btn_clear_batch"):
                    clear_cache(active_cache_key)
                    st.rerun()

            with h_right:
                if not df.empty:
                    csv_data = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name="trade_planner_results.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

            if df.empty:
                st.warning("⚠️ Tidak ada saham yang sesuai dengan kriteria filter.")
            else:
                st.info("💡 **Tips:** Centang kotak pada tabel untuk menampilkan detail rencana trading saham tersebut.")

                display_cols = [
                    "Symbol",
                    "Score",
                    "Grade",
                    "Strategy",
                    "Last Price",
                    "Zone Position",
                    "Buy Range",
                    "Stop Loss (SL)",
                    "TP 1",
                    "TP 2",
                    "Potential Gain",
                    "SL Risk",
                    "Risk-Reward Ratio",
                    "Candlestick Pattern",
                ]

                if "editor_key_version" not in st.session_state:
                    st.session_state["editor_key_version"] = 0

                current_editor_key = f"batch_editor_v{st.session_state['editor_key_version']}"

                df_table = df.copy()
                df_table.insert(0, "Pilih", False)

                edited_df = st.data_editor(
                    df_table[["Pilih"] + display_cols],
                    column_config={
                        "Pilih": st.column_config.CheckboxColumn(
                            "Pilih",
                            help="Centang untuk melihat detail Trade Plan",
                            default=False,
                        ),
                        "Symbol": st.column_config.TextColumn("Symbol"),
                        "Score": st.column_config.NumberColumn("Score", format="%d"),
                        "Last Price": st.column_config.NumberColumn("Last Price", format="Rp %d"),
                        "Stop Loss (SL)": st.column_config.NumberColumn("Stop Loss", format="Rp %d"),
                        "TP 1": st.column_config.NumberColumn("TP 1", format="Rp %d"),
                        "TP 2": st.column_config.NumberColumn("TP 2", format="Rp %d"),
                    },
                    disabled=display_cols,
                    use_container_width=True,
                    key=current_editor_key,
                )

                selected_rows = edited_df[edited_df["Pilih"] == True]
                num_checked = len(selected_rows)

                col_chk_status, col_chk_btn = st.columns([3, 1], vertical_alignment="center")
                with col_chk_status:
                    if num_checked > 0:
                        st.markdown(
                            f"📌 **{num_checked} saham** dipilih untuk ditampilkan detailnya di bawah.",
                            unsafe_allow_html=True,
                        )
                with col_chk_btn:
                    if num_checked > 0:
                        if st.button("🧹 Hapus Pilihan", use_container_width=True, key="btn_clear_selection"):
                            st.session_state["editor_key_version"] += 1
                            st.toast("Pilihan dibersihkan", icon="✅")
                            st.rerun()

                if not selected_rows.empty:
                    st.write("")
                    selected_symbols = selected_rows["Symbol"].tolist()
                    df_selected_full = df[df["Symbol"].isin(selected_symbols)]
                    render_trade_plan_cards(df_selected_full, is_title_needed=True)

    st.markdown(
        """
        <br>
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #142834; padding-top: 12px; color: #607d8b; font-size: 0.8rem;">
            <div>Trade Planner App</div>
            <div style="color: #00ff66; font-weight: 600;">System Ready</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
