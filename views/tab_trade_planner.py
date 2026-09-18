import concurrent.futures
import json
import os
import pandas as pd
import streamlit as st

from engines.trade_planner import TradePlanner


def load_daftar_saham(filename=os.path.join("data", "daftar_saham.txt")):
    """Reads ticker list from file inside data folder or fallback to root."""
    target_path = filename
    
    if not os.path.exists(target_path):
        alt_path = os.path.basename(filename)
        if os.path.exists(alt_path):
            target_path = alt_path
        else:
            return []

    try:
        with open(target_path, "r", encoding="utf-8") as f:
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
        # --- Tambahan hitungan untuk Target 2 ---
        pot_gain_tp2 = (
            round(((p["TP 2"] - entry_mid) / entry_mid) * 100, 1)
            if entry_mid > 0
            else 0
        )
        # ----------------------------------------
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
        st.warning("⚠️ Ticker list is empty!")
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
                f"⏳ **Analyzing stocks:** `{completed}/{total_saham}` processed ({int(percent * 100)}%)"
            )

    progress_bar.empty()
    status_text.empty()
    st.toast(
        f"Analysis Complete: Analyzed {len(results)} out of {total_saham} stocks!",
        icon="✅",
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
    st.toast("Data Cache Cleared", icon="🧹")


def add_tickers_to_watchlist(symbols_list):
    """Menambahkan list ticker terpilih ke file JSON watchlist_storage.json & sinkronisasi session_state."""
    storage_file = "watchlist_storage.json"
    
    try:
        watchlist_data = []
        if os.path.exists(storage_file):
            try:
                with open(storage_file, "r", encoding="utf-8") as f:
                    watchlist_data = json.load(f)
            except Exception:
                watchlist_data = []
        
        existing_tickers = set()
        for item in watchlist_data:
            if isinstance(item, str):
                existing_tickers.add(item.upper())
            elif isinstance(item, dict):
                t = item.get("Ticker", "")
                if t:
                    existing_tickers.add(t.upper())
        
        added_count = 0
        active_screener_name = st.session_state.get("active_screener_name", "Trade Planner Screener")

        for sym in symbols_list:
            clean_sym = sym.strip().upper()
            formatted = clean_sym if clean_sym.endswith(".JK") else f"{clean_sym}.JK"
            
            if formatted not in existing_tickers and clean_sym not in existing_tickers:
                new_item = {
                    "Ticker": formatted,
                    "Notes": active_screener_name,
                    "Target Price": 0
                }
                watchlist_data.append(new_item)
                
                if "watchlist" in st.session_state and isinstance(st.session_state["watchlist"], list):
                    st.session_state["watchlist"].append(new_item)
                if "watchlist_data" in st.session_state and isinstance(st.session_state["watchlist_data"], list):
                    st.session_state["watchlist_data"].append(new_item)

                existing_tickers.add(formatted)
                existing_tickers.add(clean_sym)
                added_count += 1
        
        if added_count > 0:
            with open(storage_file, "w", encoding="utf-8") as f:
                json.dump(watchlist_data, f, indent=4)
            st.toast(f"Berhasil menambahkan {added_count} saham ke Watchlist!", icon="⭐")
        else:
            st.toast("Saham terpilih sudah ada di dalam Watchlist.", icon="ℹ️")
            
    except Exception as e:
        st.error(f"Gagal menyimpan ke watchlist: {e}")


def draw_card(title, value, subtext, badge_text="", variant="blue", value_color="blue"):
    """Reusable Dashboard Card Component."""
    badge_html = (
        f'<span class="card-badge badge-{variant}">{badge_text}</span>'
        if badge_text
        else ""
    )

    card_html = f"""
    <div class="card card-{variant}">
        <div class="card-header">
            <span class="card-title title-{variant}">{title}</span>
            {badge_html}
        </div>
        <div class="card-value val-{value_color}">{value}</div>
        <p class="card-subtext">{subtext}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_trade_plan_cards(df_data, is_title_needed=True):
    """Renders Trade Plan Cards for given stocks Dataframe."""
    if is_title_needed:
        st.markdown(
            f"""
            <h3 class="glow-title">
                <span class="cyan-dot"></span>Trade Plans 
                <span style='font-size:0.9rem; color:#94a3b8;'>({len(df_data)} items)</span>
            </h3>
            """,
            unsafe_allow_html=True,
        )

    for idx, row in df_data.iterrows():
        st.markdown(
            f"""
            <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 16px 20px; margin-top: 20px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                    <span style="font-size: 1.5rem; font-weight: 800; color: #00F3FF;">{row['Symbol']}</span>
                    <span style="background: #1e293b; color: #cbd5e1; border: 1px solid #334155; padding: 3px 10px; font-size: 0.8rem; font-weight: 600; border-radius: 4px;">Strategy: {row['Strategy']}</span>
                    <span style="background: #451a03; color: #fcd34d; border: 1px solid #78350f; padding: 3px 10px; font-size: 0.8rem; font-weight: 600; border-radius: 4px;">Grade: {row['Grade']}</span>
                    <span style="background: #0c4a6e; color: #38bdf8; border: 1px solid #0284c7; padding: 3px 10px; font-size: 0.8rem; font-weight: 600; border-radius: 4px;">Score: {row['Score']}/100</span>
                </div>
                <div style="color: #94a3b8; font-size: 0.9rem;">
                    Last Price: <strong style="color: #00F3FF; font-size: 1.2rem;">Rp {row['Last Price']:,}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            draw_card(
                title="BUY RANGE / ENTRY ZONE",
                value=str(row["Buy Range"]),
                subtext=f"Status: {row['Zone Position']}",
                badge_text=str(row["Zone Position"]),
                variant="blue",
                value_color="blue",
            )
            draw_card(
                title="TARGET 1 (TP 1)",
                value=f"Rp {row['TP 1']:,}",
                subtext="Initial profit target / partial exit.",
                badge_text=str(row["Potential Gain"]),
                variant="green",
                value_color="green",
            )

        with col2:
            draw_card(
                title="STOP LOSS (SL)",
                value=f"Rp {row['Stop Loss (SL)']:,}",
                subtext="Risk management limit.",
                badge_text=str(row["SL Risk"]),
                variant="red",
                value_color="red",
            )
draw_card(
                title="TARGET 2 (TP 2)",
                value=f"Rp {row['TP 2']:,}",
                subtext="Main swing target zone.",
                badge_text=str(row["Potential Gain TP2"]),
                variant="blue",
                value_color="blue",
            )

        st.markdown(
            f"""
            <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 14px 18px; margin-bottom: 28px; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
                <div>
                    <span style="font-size: 0.75rem; color: #64748b; display: block; font-weight: 600;">RISK : REWARD</span>
                    <span style="font-size: 0.95rem; color: #f8fafc; font-weight: 700;">1 : {row['Risk-Reward Ratio']}</span>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #64748b; display: block; font-weight: 600;">CANDLESTICK PATTERN</span>
                    <span style="font-size: 0.95rem; color: #f8fafc; font-weight: 700;">{row['Candlestick Pattern']}</span>
                </div>
                <div style="grid-column: span 2;">
                    <span style="font-size: 0.75rem; color: #64748b; display: block; font-weight: 600;">ANALYSIS & WARNING</span>
                    <span style="font-size: 0.88rem; color: #ef4444; font-weight: 600;">{row['Analysis & Risk Warning']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_tab_trade_planner():
    # 🎨 CUSTOM CSS STYLING
    st.markdown(
        """
        <style>
        @keyframes pulseGlow {
            0% { opacity: 0.3; box-shadow: 0 0 4px #00F3FF, 0 0 8px #00F3FF; transform: scale(0.9); }
            50% { opacity: 1; box-shadow: 0 0 12px #00F3FF, 0 0 22px #00F3FF, 0 0 32px #10b981; transform: scale(1.15); }
            100% { opacity: 0.3; box-shadow: 0 0 4px #00F3FF, 0 0 8px #00F3FF; transform: scale(0.9); }
        }

        .header-banner {
            border: 1px solid #00F3FF;
            box-shadow: 0 0 14px rgba(0, 243, 255, 0.4), inset 0 0 14px rgba(0, 243, 255, 0.15);
            border-radius: 8px;
            padding: 12px 24px;
            margin-bottom: 24px;
            background: #0d1117;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 6px;
            text-align: center;
            width: 100%;
        }

        .top-glowing-dot {
            width: 10px;
            height: 10px;
            background-color: #00F3FF;
            border-radius: 50%;
            animation: pulseGlow 2.5s infinite ease-in-out;
        }

        .header-banner h1 {
            margin: 0;
            font-size: 1.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00F3FF 0%, #10b981 50%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 8px rgba(0, 243, 255, 0.5));
            line-height: 1.2;
        }

        .glow-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 800;
            font-size: 1.3rem;
            background: linear-gradient(90deg, #00F3FF 0%, #10b981 60%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 5px rgba(0, 243, 255, 0.4));
            margin-top: 10px;
            margin-bottom: 10px;
        }

        .cyan-dot {
            width: 10px;
            height: 10px;
            background-color: #00F3FF;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px #00F3FF, 0 0 12px #00F3FF;
            flex-shrink: 0;
        }

        div.stButton > button {
            border: 1px solid #00F3FF !important;
            box-shadow: 0 0 8px rgba(0, 243, 255, 0.3) !important;
            border-radius: 6px !important;
            transition: all 0.25s ease-in-out !important;
        }

        div.stButton > button[data-testid="stBaseButton-primary"] {
            background: linear-gradient(135deg, #00b4d8 0%, #00f3ff 100%) !important;
            color: #020617 !important;
            font-weight: 700 !important;
            border: 1px solid #00F3FF !important;
            box-shadow: 0 0 12px rgba(0, 243, 255, 0.6) !important;
        }

        div.stButton > button[data-testid="stBaseButton-primary"]:hover {
            background: linear-gradient(135deg, #00f3ff 0%, #10b981 100%) !important;
            color: #000000 !important;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.9), 0 0 10px rgba(16, 185, 129, 0.8) !important;
        }

        div.stButton > button:hover {
            border-color: #00F3FF !important;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.8) !important;
        }

        .card {
            background-color: #0f172a;
            border-radius: 6px;
            padding: 16px 18px;
            margin-bottom: 14px;
        }
        .card-blue { border: 1px solid #0284c7; }
        .card-red { border: 1px solid #dc2626; }
        .card-green { border: 1px solid #059669; }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .card-title {
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .title-blue { color: #38bdf8; }
        .title-red { color: #f87171; }
        .title-green { color: #34d399; }

        .card-badge {
            font-size: 0.7rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
        }
        .badge-blue { background: #0c4a6e; color: #7dd3fc; }
        .badge-red { background: #450a0a; color: #fca5a5; }
        .badge-green { background: #064e3b; color: #6ee7b7; }

        .card-value {
            font-size: 1.4rem;
            font-weight: 800;
            margin-bottom: 4px;
            line-height: 1.2;
        }
        .val-blue { color: #38bdf8; }
        .val-red { color: #f87171; }
        .val-green { color: #34d399; }

        .card-subtext {
            font-size: 0.78rem;
            color: #94a3b8;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- BANNER HEADER ---
    st.markdown(
        """
        <div class="header-banner">
            <div class="top-glowing-dot"></div>
            <h1>Stock Trade Planner</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "screener_mode" not in st.session_state:
        st.session_state["screener_mode"] = "single"
    if "f_strategi" not in st.session_state:
        st.session_state["f_strategi"] = "ALL STRATEGIES"
    if "f_grade" not in st.session_state:
        st.session_state["f_grade"] = "ALL GRADES"
    if "f_zone" not in st.session_state:
        st.session_state["f_zone"] = "ALL POSITIONS"
    if "f_rr" not in st.session_state:
        st.session_state["f_rr"] = "ALL RATIOS"
    if "f_candle" not in st.session_state:
        st.session_state["f_candle"] = "ALL CANDLES"

    st.markdown(
        """
        <div class="glow-title">
            <span class="cyan-dot"></span>Select Execution Mode
        </div>
        """,
        unsafe_allow_html=True,
    )

    mode_col1, mode_col2 = st.columns(2)
    current_mode = st.session_state["screener_mode"]

    with mode_col1:
        is_single = current_mode == "single"
        btn_type_single = "primary" if is_single else "secondary"
        if st.button(
            "Single Ticker Analysis",
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
            " Batch Screener Analysis",
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
                """
                <div class="glow-title" style="font-size: 1rem;">
                    <span class="cyan-dot"></span>Enter Tickers
                </div>
                """,
                unsafe_allow_html=True,
            )
            input_ticker = st.text_input(
                "Stock Tickers",
                value="",
                placeholder="BBCA, BMRI, TLKM, INCO...",
                label_visibility="collapsed",
            )
        with col_btn:
            btn_single = st.button(
                "Run Analyze", type="primary", use_container_width=True
            )

        if btn_single:
            if not input_ticker.strip():
                st.warning("⚠️ Input ticker list is empty.")
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
            # Header dengan Tombol Add to Watchlist di sebelah Clear Data
            h_left, h_btn_wl, h_right = st.columns([2.2, 1.2, 1], vertical_alignment="center")
            
            with h_left:
                st.markdown(
                    f"""
                    <h3 class="glow-title">
                        <span class="cyan-dot"></span>Analysis Results 
                        <span style='font-size:0.9rem; color:#94a3b8;'>({len(df_single_res)} items)</span>
                    </h3>
                    """,
                    unsafe_allow_html=True,
                )
            
            with h_btn_wl:
                if not df_single_res.empty:
                    if st.button("⭐ + Watchlist", use_container_width=True, key="btn_add_watchlist_single_header"):
                        symbols_to_add = df_single_res["Symbol"].tolist()
                        add_tickers_to_watchlist(symbols_to_add)

            with h_right:
                if st.button("🗑️ Clear Data", use_container_width=True, key="btn_clear_single"):
                    clear_cache(active_cache_key)
                    st.rerun()

            if df_single_res.empty:
                st.warning("⚠️ No valid data returned for the selected tickers.")
            else:
                render_trade_plan_cards(df_single_res, is_title_needed=False)

    else:
        all_tickers = load_daftar_saham()
        if not all_tickers:
            st.error("❌ File `daftar_saham.txt` tidak ditemukan di folder `data/` maupun di direktori utama!")
            return

        col_info, col_batch_btn = st.columns([3, 1], vertical_alignment="center")
        with col_info:
            st.info("💡 **Click Run To Screen All Ticker**")
        with col_batch_btn:
            if st.button("Run Screener", type="primary", use_container_width=True):
                run_batch_execution(all_tickers, cache_key="df_screener_batch")

        active_cache_key = "df_screener_batch"

        if active_cache_key in st.session_state:
            df_raw = st.session_state[active_cache_key]

            st.write("")
            with st.expander("🛠️ **Filters & Criteria**", expanded=True):
                r1c1, r1c2, r1c3 = st.columns(3)
                with r1c1:
                    f_strategi = st.selectbox(
                        "🎯 Strategy:",
                        ["ALL STRATEGIES", "Buy On Weakness (BOW)", "Breakout (BOB)"],
                        key="f_strategi",
                    )
                with r1c2:
                    f_grade = st.selectbox(
                        "🏆 Setup Grade:",
                        [
                            "ALL GRADES",
                            "Grade A / A+ Only (High Quality)",
                            "Grade B or Lower (Moderate/Risk)",
                        ],
                        key="f_grade",
                    )
                with r1c3:
                    f_zone = st.selectbox(
                        "📍 Price Zone:",
                        [
                            "ALL POSITIONS",
                            "In Buy Zone (Ready to Execute)",
                            "Near Zone (Approaching Entry)",
                        ],
                        key="f_zone",
                    )

                r2c1, r2c2, r2c3 = st.columns([1.5, 1.5, 1], vertical_alignment="bottom")
                with r2c1:
                    f_rr = st.selectbox(
                        "⚖️ Min Risk-Reward:",
                        [
                            "ALL RATIOS",
                            "Min 1 : 1.5",
                            "Min 1 : 2.0 (Standard)",
                            "Min 1 : 3.0 (High Reward)",
                        ],
                        key="f_rr",
                    )
                with r2c2:
                    f_candle = st.selectbox(
                        "🕯️ Candlestick Pattern:",
                        ["ALL CANDLES", "Bullish Signal Only", "Neutral / Doji Only"],
                        key="f_candle",
                    )
                with r2c3:
                    st.button("🔄 Reset Filters", on_click=reset_filters, use_container_width=True)

            df = df_raw.copy()

            if f_strategi == "Buy On Weakness (BOW)":
                df = df[df["Strategy"] == "BOW"]
            elif f_strategi == "Breakout (BOB)":
                df = df[df["Strategy"] == "BOB"]

            if f_grade == "Grade A / A+ Only (High Quality)":
                df = df[df["Score"] >= 70]
            elif f_grade == "Grade B or Lower (Moderate/Risk)":
                df = df[df["Score"] < 70]

            if f_zone == "In Buy Zone (Ready to Execute)":
                df = df[df["Zone Position"] == "In Buy Zone"]
            elif f_zone == "Near Zone (Approaching Entry)":
                df = df[df["Zone Position"] == "Near Zone"]

            if f_rr == "Min 1 : 1.5":
                df = df[df["RR_Val"] >= 1.5]
            elif f_rr == "Min 1 : 2.0 (Standard)":
                df = df[df["RR_Val"] >= 2.0]
            elif f_rr == "Min 1 : 3.0 (High Reward)":
                df = df[df["RR_Val"] >= 3.0]

            if f_candle == "Bullish Signal Only":
                df = df[
                    df["Candlestick Pattern"].str.contains(
                        "Engulfing|Morning|Soldiers|Marubozu|Hammer|Dragonfly",
                        case=False,
                        na=False,
                    )
                ]
            elif f_candle == "Neutral / Doji Only":
                df = df[
                    df["Candlestick Pattern"].str.contains(
                        "Doji|Spinning|Standard", case=False, na=False
                    )
                ]

            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            st.write("")

            h_left, h_btn1, h_btn2, h_right = st.columns([2, 1, 1, 1], vertical_alignment="center")
            with h_left:
                st.markdown(
                    f"""
                    <h3 class="glow-title">
                        <span class="cyan-dot"></span>Screener Results 
                        <span style='font-size:0.9rem; color:#94a3b8;'>({len(df)} items)</span>
                    </h3>
                    """,
                    unsafe_allow_html=True,
                )

            if "editor_key_version" not in st.session_state:
                st.session_state["editor_key_version"] = 0

            current_editor_key = f"batch_editor_v{st.session_state['editor_key_version']}"

            df_table = df.copy()
            df_table.insert(0, "Select", False)

            edited_df = st.data_editor(
                df_table[["Select"] + ["Symbol", "Score", "Grade", "Strategy", "Last Price", "Zone Position", "Buy Range", "Stop Loss (SL)", "TP 1", "TP 2", "Potential Gain", "SL Risk", "Risk-Reward Ratio", "Candlestick Pattern"]],
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Check to view detailed Trade Plan cards",
                        default=False,
                    ),
                    "Symbol": st.column_config.TextColumn("Symbol"),
                    "Score": st.column_config.NumberColumn("Score", format="%d"),
                    "Last Price": st.column_config.NumberColumn("Last Price", format="Rp %d"),
                    "Stop Loss (SL)": st.column_config.NumberColumn("Stop Loss", format="Rp %d"),
                    "TP 1": st.column_config.NumberColumn("TP 1", format="Rp %d"),
                    "TP 2": st.column_config.NumberColumn("TP 2", format="Rp %d"),
                },
                disabled=["Symbol", "Score", "Grade", "Strategy", "Last Price", "Zone Position", "Buy Range", "Stop Loss (SL)", "TP 1", "TP 2", "Potential Gain", "SL Risk", "Risk-Reward Ratio", "Candlestick Pattern"],
                use_container_width=True,
                key=current_editor_key,
            )

            selected_rows = edited_df[edited_df["Select"] == True]
            num_checked = len(selected_rows)

            with h_btn1:
                if st.button("⭐ + Add to Watchlist", use_container_width=True, key="btn_add_watchlist"):
                    if num_checked > 0:
                        symbols_to_add = selected_rows["Symbol"].tolist()
                        add_tickers_to_watchlist(symbols_to_add)
                    else:
                        st.warning("⚠️ Centang minimal 1 saham di tabel terlebih dahulu!")

            with h_btn2:
                if st.button("🗑️ Clear Cache", use_container_width=True, key="btn_clear_batch"):
                    clear_cache(active_cache_key)
                    st.rerun()

            with h_right:
                if not df.empty:
                    csv_data = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Export CSV",
                        data=csv_data,
                        file_name="trade_planner_results.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

            if df.empty:
                st.warning("⚠️ No stock tickers match the selected filter criteria.")
            else:
                st.info("💡 Select the checkbox on any row to display its detailed Trade Plan card.")

            col_chk_status, col_chk_btn = st.columns([3, 1], vertical_alignment="center")
            with col_chk_status:
                if num_checked > 0:
                    st.markdown(
                        f"📌 **Selected:** `{num_checked}` stock(s) loaded for detailed view.",
                        unsafe_allow_html=True,
                    )
            with col_chk_btn:
                if num_checked > 0:
                    if st.button("🧹 Clear Selection", use_container_width=True, key="btn_clear_selection"):
                        st.session_state["editor_key_version"] += 1
                        st.toast("Selection cleared", icon="✅")
                        st.rerun()

            if not selected_rows.empty:
                st.write("")
                selected_symbols = selected_rows["Symbol"].tolist()
                df_selected_full = df[df["Symbol"].isin(selected_symbols)]
                render_trade_plan_cards(df_selected_full, is_title_needed=True)

    # --- FOOTER ---
    st.markdown(
        """
        <br>
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #1e293b; padding-top: 12px; color: #94a3b8; font-size: 0.8rem;">
            <div>Trade Planner</div>
            <div style="color: #10b981; font-weight: 600;">Status: Ready</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
