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
    """Single ticker execution processor (pure data processing, no Streamlit UI calls)."""
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
    """Multi-threaded execution runner with safe main-thread UI updates."""
    total_saham = len(ticker_list)
    if total_saham == 0:
        st.warning("⚠️ Daftar ticker saham kosong!")
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
                f"⏳ <span style='color:#00f3ff; font-weight:600;'>[MEMPROSES]:</span> `{completed}/{total_saham}` saham selesai dianalisis ({int(percent * 100)}%)",
                unsafe_allow_html=True,
            )

    progress_bar.empty()
    status_text.empty()
    st.toast(
        f"Analisis Selesai: Berhasil menganalisis {len(results)} dari {total_saham} saham!",
        icon="⚡",
    )

    if results:
        df_res = pd.DataFrame(results)
        st.session_state[cache_key] = df_res


def reset_filters():
    """Callback function to reset filter choices to defaults."""
    st.session_state["f_strategi"] = "ALL STRATEGIES"
    st.session_state["f_grade"] = "ALL GRADES"
    st.session_state["f_zone"] = "ALL POSITIONS"
    st.session_state["f_rr"] = "ALL RATIOS"
    st.session_state["f_candle"] = "ALL CANDLES"


def clear_cache(cache_key):
    """Clear specific cache mode."""
    st.session_state.pop(cache_key, None)
    st.toast("Cache Berhasil Dibersihkan", icon="🧹")


def draw_card(title, value, subtext, badge_text="", variant="cyan", value_color="cyan"):
    """Reusable Trade Planner Card Component."""
    badge_html = (
        f'<span class="tp-badge badge-{variant}">{badge_text}</span>'
        if badge_text
        else ""
    )

    card_html = f"""
    <div class="tp-card tp-card-{variant}">
        <div class="tp-card-header">
            <span class="tp-card-title title-{variant}"><span class="dot-icon">●</span> {title}</span>
            {badge_html}
        </div>
        <div class="tp-card-value val-{value_color}">{value}</div>
        <p class="tp-card-subtext">{subtext}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_trade_plan_cards(df_data, is_title_needed=True):
    """Renders Trade Plan Cards for given stocks Dataframe."""
    if is_title_needed:
        st.markdown(
            f"<h3 style='color:#00f3ff; font-weight: 700; text-shadow: 0 0 10px rgba(0, 243, 255, 0.4); margin-top: 25px;'><span style='color:#00f3ff;'>●</span> REKOMENDASI RENCANA TRADING <span style='font-size:0.95rem; color:#ff007f; margin-left:8px;'>({len(df_data)} SAHAM)</span></h3>",
            unsafe_allow_html=True,
        )

    for idx, row in df_data.iterrows():
        st.markdown(
            f"""
            <div style="background: #0b0f19; border: 1px solid #00f3ff; box-shadow: 0 0 12px rgba(0, 243, 255, 0.25); padding: 16px 20px; border-radius: 6px; margin-top: 20px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                    <span style="font-size: 1.6rem; font-weight: 900; color: #00f3ff; text-shadow: 0 0 8px rgba(0, 243, 255, 0.6); letter-spacing: 1px;">● {row['Symbol']}</span>
                    <span style="background: rgba(0, 243, 255, 0.1); color: #00f3ff; border: 1px solid #00f3ff; padding: 3px 10px; font-size: 0.8rem; font-weight: 700; border-radius: 4px;">STRATEGI: {row['Strategy']}</span>
                    <span style="background: rgba(0, 255, 153, 0.1); color: #00ff99; border: 1px solid #00ff99; padding: 3px 10px; font-size: 0.8rem; font-weight: 700; border-radius: 4px;">Grade: {row['Grade']}</span>
                    <span style="background: rgba(255, 0, 127, 0.1); color: #ff007f; border: 1px solid #ff007f; padding: 3px 10px; font-size: 0.8rem; font-weight: 700; border-radius: 4px;">Score: {row['Score']}/100</span>
                </div>
                <div style="color: #94a3b8; font-size: 0.95rem;">
                    HARGA TERAKHIR: <strong style="color: #00f3ff; font-size: 1.25rem; text-shadow: 0 0 8px rgba(0, 243, 255, 0.5);">Rp {row['Last Price']:,}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            draw_card(
                title="AREA BELI (BUY RANGE)",
                value=str(row["Buy Range"]),
                subtext=f"Posisi: {row['Zone Position']}",
                badge_text=str(row["Zone Position"]),
                variant="cyan",
                value_color="cyan",
            )
            draw_card(
                title="TARGET 1 (TP 1)",
                value=f"Rp {row['TP 1']:,}",
                subtext="Target profit awal / parsial exit.",
                badge_text=str(row["Potential Gain"]),
                variant="green",
                value_color="green",
            )

        with col2:
            draw_card(
                title="STOP LOSS (SL)",
                value=f"Rp {row['Stop Loss (SL)']:,}",
                subtext="Batas toleransi risiko maksimal.",
                badge_text=str(row["SL Risk"]),
                variant="pink",
                value_color="pink",
            )
            draw_card(
                title="TARGET 2 (TP 2)",
                value=f"Rp {row['TP 2']:,}",
                subtext="Target utama swing trading.",
                badge_text=f"R:R {row['Risk-Reward Ratio']}",
                variant="cyan",
                value_color="cyan",
            )

        st.markdown(
            f"""
            <div style="background: #070a12; border: 1px solid #1e293b; padding: 14px 18px; margin-bottom: 28px; border-radius: 6px; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
                <div>
                    <span style="font-size: 0.78rem; color: #64748b; display: block;">RISK : REWARD</span>
                    <span style="font-size: 0.95rem; color: #00f3ff; font-weight: 700;">1 : {row['Risk-Reward Ratio']}</span>
                </div>
                <div>
                    <span style="font-size: 0.78rem; color: #64748b; display: block;">POLA CANDLESTICK</span>
                    <span style="font-size: 0.95rem; color: #00ff99; font-weight: 700;">{row['Candlestick Pattern']}</span>
                </div>
                <div style="grid-column: span 2;">
                    <span style="font-size: 0.78rem; color: #64748b; display: block;">ANALISIS & PERINGATAN RISIKO</span>
                    <span style="font-size: 0.88rem; color: #ff007f; font-weight: 600;">{row['Analysis & Risk Warning']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_tab_trade_planner():
    # 🎨 TRADE PLANNER CLEAN UI & STYLING
    st.markdown(
        """
        <style>
        /* Modern Dark Theme Background */
        .stApp {
            background-color: #060911 !important;
            color: #cbd5e1 !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }

        /* Header Banner Styling dengan Efek Glowing Neon Cyan Border */
        .tp-header-wrapper {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: linear-gradient(135deg, #0b1120 0%, #070a14 100%);
            border: 1px solid #00f3ff;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.4), inset 0 0 15px rgba(0, 243, 255, 0.08);
            padding: 20px 24px;
            margin-bottom: 24px;
            border-radius: 8px;
        }

        .tp-title-text {
            color: #00f3ff;
            font-size: 1.5rem;
            font-weight: 800;
            text-shadow: 0 0 10px rgba(0, 243, 255, 0.6);
            letter-spacing: 1.5px;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .tp-title-text .dot-indicator {
            color: #00f3ff;
            font-size: 1.2rem;
            text-shadow: 0 0 8px #00f3ff;
        }

        /* Form Inputs & Select Styling */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
            background-color: #090d18 !important;
            border: 1px solid #00f3ff !important;
            color: #00f3ff !important;
            border-radius: 6px !important;
            box-shadow: 0 0 6px rgba(0, 243, 255, 0.2);
        }
        div[data-baseweb="input"]:focus-within > div, div[data-baseweb="select"]:focus-within > div {
            border-color: #00ff99 !important;
            box-shadow: 0 0 10px rgba(0, 255, 153, 0.4) !important;
        }

        /* Clean Modern Buttons */
        div.stButton > button {
            background: #0b1120 !important;
            color: #00f3ff !important;
            border: 1px solid #00f3ff !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
            letter-spacing: 0.5px;
            padding: 10px 20px !important;
            transition: all 0.25s ease-in-out !important;
            box-shadow: 0 0 8px rgba(0, 243, 255, 0.2);
        }
        div.stButton > button:hover {
            background: #00f3ff !important;
            color: #060911 !important;
            box-shadow: 0 0 18px rgba(0, 243, 255, 0.6) !important;
        }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #00f3ff, #00ff99) !important;
            color: #060911 !important;
            border: 1px solid #00f3ff !important;
            box-shadow: 0 0 14px rgba(0, 243, 255, 0.4) !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(90deg, #00ff99, #00f3ff) !important;
            box-shadow: 0 0 22px rgba(0, 255, 153, 0.6) !important;
        }

        /* Expander */
        div[data-testid="stExpander"] {
            background-color: #080d1a !important;
            border: 1px solid #00f3ff !important;
            border-radius: 6px !important;
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.15);
        }

        /* Trade Planner Cards */
        .tp-card {
            background-color: #090d18;
            padding: 16px 18px;
            margin-bottom: 14px;
            border-radius: 6px;
            position: relative;
        }
        .tp-card-cyan { border: 1px solid #00f3ff; box-shadow: 0 0 10px rgba(0, 243, 255, 0.15); }
        .tp-card-pink { border: 1px solid #ff007f; box-shadow: 0 0 10px rgba(255, 0, 127, 0.15); }
        .tp-card-green { border: 1px solid #00ff99; box-shadow: 0 0 10px rgba(0, 255, 153, 0.15); }

        .tp-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .tp-card-title {
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .title-cyan { color: #00f3ff; }
        .title-pink { color: #ff007f; }
        .title-green { color: #00ff99; }

        .dot-icon {
            font-size: 0.8rem;
            margin-right: 4px;
            vertical-align: middle;
            text-shadow: 0 0 6px currentColor;
        }

        .tp-badge {
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
        }
        .badge-cyan { background: rgba(0, 243, 255, 0.1); color: #00f3ff; border: 1px solid #00f3ff; }
        .badge-pink { background: rgba(255, 0, 127, 0.1); color: #ff007f; border: 1px solid #ff007f; }
        .badge-green { background: rgba(0, 255, 153, 0.1); color: #00ff99; border: 1px solid #00ff99; }

        .tp-card-value {
            font-size: 1.35rem;
            font-weight: 800;
            margin-bottom: 4px;
            line-height: 1.25;
        }
        .val-cyan { color: #00f3ff; text-shadow: 0 0 6px rgba(0, 243, 255, 0.4); }
        .val-pink { color: #ff007f; text-shadow: 0 0 6px rgba(255, 0, 127, 0.4); }
        .val-green { color: #00ff99; text-shadow: 0 0 6px rgba(0, 255, 153, 0.4); }

        .tp-card-subtext {
            font-size: 0.8rem;
            color: #94a3b8;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header Banner
    st.markdown(
        """
        <div class="tp-header-wrapper">
            <div class="tp-title-text">
                <span class="dot-indicator">●</span> ANALISIS & RENCANA TRADING SAHAM
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tickers = load_daftar_saham()
    cache_key = "trade_planner_data"

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        if st.button("🚀 JALANKAN ANALISIS SAHAM", type="primary"):
            run_batch_execution(tickers, cache_key)
    with col_btn2:
        if st.button("🧹 BERSIHKAN CACHE"):
            clear_cache(cache_key)

    if cache_key in st.session_state:
        df_results = st.session_state[cache_key]

        with st.expander("🔍 FILTRASI RENCANA TRADING", expanded=True):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                st.selectbox(
                    "Strategi",
                    ["ALL STRATEGIES"] + list(df_results["Strategy"].unique()),
                    key="f_strategi",
                )
            with f_col2:
                st.selectbox(
                    "Grade",
                    ["ALL GRADES"] + list(df_results["Grade"].unique()),
                    key="f_grade",
                )
            with f_col3:
                st.selectbox(
                    "Posisi Harga",
                    ["ALL POSITIONS"] + list(df_results["Zone Position"].unique()),
                    key="f_zone",
                )
            with f_col4:
                st.button("RESET FILTER", on_click=reset_filters)

        filtered_df = df_results.copy()
        if st.session_state.get("f_strategi") != "ALL STRATEGIES":
            filtered_df = filtered_df[filtered_df["Strategy"] == st.session_state["f_strategi"]]
        if st.session_state.get("f_grade") != "ALL GRADES":
            filtered_df = filtered_df[filtered_df["Grade"] == st.session_state["f_grade"]]
        if st.session_state.get("f_zone") != "ALL POSITIONS":
            filtered_df = filtered_df[filtered_df["Zone Position"] == st.session_state["f_zone"]]

        render_trade_plan_cards(filtered_df)
