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
            "Symbol": symbol.replace(".JK", ""),
            "Score": int(p["Score"]),
            "Grade": p["Grade"],
            "Strategy": p["Type"],
            "Last Price": curr_close,
            "Zone Position": p["Posisi Harga"],
            "Buy Range": p["Area Buy"],
            "Stop Loss (SL)": int(p["Stop Loss"]),
            "TP 1": int(p["TP 1"]),
            "TP 2": int(p["TP 2"]),
            "Potential Gain": f"+{pot_gain}%",
            "SL Risk": f"-{pot_risk}%",
            "Risk-Reward Ratio": p["Rasio (R:R)"],
            "RR_Val": float(p["RR_Val"]) if "RR_Val" in p else 0.0,
            "Candlestick Pattern": p["Pola Candle"],
            "Analysis & Risk Warning": p["Warning"],
        }
    except Exception:
        return None


def run_batch_execution(ticker_list, cache_key):
    """Multi-threaded execution runner with target cache key saving."""
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
                f"⏳ **Screener Progress:** `{completed}/{total_saham}` stocks processed ({int(percent * 100)}%)"
            )

    progress_bar.empty()
    status_text.empty()
    st.toast(
        f"Successfully analyzed {len(results)} out of {total_saham} stocks!",
        icon="🚀",
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
    st.toast("Cache cleared successfully!", icon="🧹")


def draw_card(title, value, subtext, badge_text="", variant="blue", value_color="white"):
    """Reusable Card Component with Design Specifications."""
    badge_html = (
        f'<span class="zio-badge badge-{variant}">{badge_text}</span>'
        if badge_text
        else ""
    )

    card_html = f"""
    <div class="zio-card zio-card-{variant}">
        <div class="zio-card-header">
            <span class="zio-card-title title-{variant}">{title}</span>
            {badge_html}
        </div>
        <div class="zio-card-value val-{value_color}">{value}</div>
        <p class="zio-card-subtext">{subtext}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_trade_plan_cards(df):
    """Renders all stock data into full Card Grid layout in English."""
    for idx, row in df.iterrows():
        # 1. Stock Header Bar
        st.markdown(
            f"""
            <div style="background: #0D111A; border: 1px solid #1E2638; padding: 16px 22px; border-radius: 12px; margin-top: 24px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                    <span style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF;">{row['Symbol']}</span>
                    <span style="background: rgba(139, 92, 246, 0.2); color: #C084FC; padding: 4px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 700;">STRATEGY: {row['Strategy']}</span>
                    <span style="background: rgba(234, 179, 8, 0.15); color: #FACC15; padding: 4px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 600;">{row['Grade']}</span>
                    <span style="background: rgba(59, 130, 246, 0.15); color: #60A5FA; padding: 4px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 600;">Score: {row['Score']}/100</span>
                </div>
                <div style="color: #94A3B8; font-size: 0.95rem;">
                    Last Price: <strong style="color: #FFFFFF; font-size: 1.15rem;">Rp {row['Last Price']:,}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 2. Main Metric Cards Grid
        col1, col2 = st.columns(2)

        with col1:
            draw_card(
                title="BUY RANGE (ENTRY AREA)",
                value=str(row["Buy Range"]),
                subtext=f"Position Status: {row['Zone Position']}",
                badge_text=str(row["Zone Position"]),
                variant="green",
                value_color="white",
            )

            draw_card(
                title="TARGET 1 (TP 1)",
                value=f"Rp {row['TP 1']:,}",
                subtext="Initial profit target / partial exit zone.",
                badge_text=str(row["Potential Gain"]),
                variant="blue",
                value_color="white",
            )

        with col2:
            draw_card(
                title="STOP LOSS (SL)",
                value=f"Rp {row['Stop Loss (SL)']:,}",
                subtext="Risk management boundary / cutloss level.",
                badge_text=str(row["SL Risk"]),
                variant="red",
                value_color="red",
            )

            draw_card(
                title="TARGET 2 (TP 2)",
                value=f"Rp {row['TP 2']:,}",
                subtext="Main swing target zone.",
                badge_text=f"R:R {row['Risk-Reward Ratio']}",
                variant="green",
                value_color="green",
            )

        # 3. Summary Indicator Grid
        st.markdown(
            f"""
            <div style="background: #111622; border: 1px solid #1E2638; border-radius: 10px; padding: 12px 18px; margin-bottom: 24px; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
                <div>
                    <span style="font-size: 0.75rem; color: #64748B; font-weight: 600; display: block;">RISK : REWARD RATIO</span>
                    <span style="font-size: 0.95rem; color: #F8FAFC; font-weight: 700;">1 : {row['Risk-Reward Ratio']}</span>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #64748B; font-weight: 600; display: block;">CANDLESTICK PATTERN</span>
                    <span style="font-size: 0.95rem; color: #38BDF8; font-weight: 700;">{row['Candlestick Pattern']}</span>
                </div>
                <div style="grid-column: span 2;">
                    <span style="font-size: 0.75rem; color: #64748B; font-weight: 600; display: block;">ANALYSIS & RISK WARNING</span>
                    <span style="font-size: 0.9rem; color: #FCA5A5; font-weight: 600;">{row['Analysis & Risk Warning']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_tab_trade_planner():
    # 🎨 CSS STYLING
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #07090E !important;
        }

        /* Minimalist Header */
        .zio-header-wrapper {
            display: flex;
            align-items: center;
            background-color: #0D111A;
            border: 1px solid #1E2638;
            border-radius: 14px;
            padding: 18px 24px;
            margin-bottom: 24px;
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
        }

        /* Section Title */
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

        /* Custom Inputs */
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

        /* Custom Buttons */
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

        /* CARD COMPONENT DESIGN */
        .zio-card {
            background-color: #111622;
            border-radius: 12px;
            padding: 18px 20px;
            margin-bottom: 16px;
            border: 1px solid #1E2638;
            transition: all 0.2s ease-in-out;
        }
        .zio-card-green { border: 1px solid #059669; }
        .zio-card-red { border: 1px solid #DC2626; }
        .zio-card-blue { border: 1px solid #1E2638; }

        .zio-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .zio-card-title {
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .title-green { color: #10B981; }
        .title-red { color: #EF4444; }
        .title-blue { color: #60A5FA; }

        .zio-badge {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 6px;
        }
        .badge-green { background-color: rgba(16, 185, 129, 0.15); color: #10B981; }
        .badge-red { background-color: rgba(239, 68, 68, 0.15); color: #EF4444; }
        .badge-blue { background-color: rgba(96, 165, 250, 0.15); color: #60A5FA; }

        .zio-card-value {
            font-size: 1.5rem;
            font-weight: 800;
            margin-bottom: 6px;
            line-height: 1.2;
        }
        .val-white { color: #FFFFFF; }
        .val-green { color: #10B981; }
        .val-red { color: #EF4444; }

        .zio-card-subtext {
            font-size: 0.8rem;
            color: #94A3B8;
            line-height: 1.4;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- HEADER ---
    st.markdown(
        """
        <div class="zio-header-wrapper">
            <div class="zio-header-left">
                <div class="zio-icon-square">📊</div>
                <div class="zio-title-text">Smart Execution Screener</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # State Initialization
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

    # --- MODE SELECTION ---
    st.markdown(
        '<div class="zio-form-header"><span style="color:#A855F7;">🎯</span> Choose Screener Mode</div>',
        unsafe_allow_html=True,
    )

    mode_col1, mode_col2 = st.columns(2)
    current_mode = st.session_state["screener_mode"]

    with mode_col1:
        is_single = current_mode == "single"
        btn_type_single = "primary" if is_single else "secondary"
        if st.button(
            "⚡ Single / Custom Ticker Analysis\nAnalyze specific stock tickers",
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
            "🚀 Full Batch Screener Scan\nAuto-scan database ticker list",
            use_container_width=True,
            type=btn_type_batch,
            key="btn_card_batch",
        ):
            if st.session_state["screener_mode"] != "batch":
                st.session_state["screener_mode"] = "batch"
            st.rerun()

    st.write("")

    # Actions Form based on Mode
    if st.session_state["screener_mode"] == "single":
        col_input, col_btn = st.columns([3.5, 1], vertical_alignment="bottom")
        with col_input:
            st.markdown(
                '<span class="zio-label">Enter Stock Tickers:</span>',
                unsafe_allow_html=True,
            )
            input_ticker = st.text_input(
                "Stock Tickers",
                value="",
                placeholder="Example: BBCA, BMRI, TLKM, INCO (comma separated)",
                label_visibility="collapsed",
            )
        with col_btn:
            btn_single = st.button(
                "🔍 Analyze Tickers", type="primary", use_container_width=True
            )

        if btn_single:
            if not input_ticker.strip():
                st.warning("⚠️ Please enter at least one stock ticker!")
            else:
                list_to_scan = [
                    t.strip().upper()
                    for t in input_ticker.split(",")
                    if t.strip()
                ]
                run_batch_execution(list_to_scan, cache_key="df_screener_single")

        # Independent Single Cache Data Check
        active_cache_key = "df_screener_single"

    else:
        all_tickers = load_daftar_saham("daftar_saham.txt")
        if not all_tickers:
            st.error("❌ `daftar_saham.txt` file not found in root folder!")
            return

        col_info, col_batch_btn = st.columns([3, 1], vertical_alignment="center")
        with col_info:
            st.info(f"📁 Ready to analyze **{len(all_tickers)} stocks** from `daftar_saham.txt` database.")
        with col_batch_btn:
            if st.button("🚀 Run Batch Scan", type="primary", use_container_width=True):
                run_batch_execution(all_tickers, cache_key="df_screener_batch")

        # Independent Batch Cache Data Check
        active_cache_key = "df_screener_batch"

    # --- RESULTS DISPLAY ---
    if active_cache_key in st.session_state:
        df_raw = st.session_state[active_cache_key]

        # Filters - ONLY active in Batch mode
        if st.session_state["screener_mode"] == "batch":
            st.write("")
            with st.expander("🛠️ **Parameter & Custom Filter Result**", expanded=True):
                r1c1, r1c2, r1c3 = st.columns(3)
                with r1c1:
                    f_strategi = st.selectbox(
                        "🎯 Trading Strategy:",
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
                        "📍 Price Zone Position:",
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
                        "⚖️ Min Risk-to-Reward:",
                        [
                            "ALL RATIOS",
                            "Min 1 : 1.5",
                            "Min 1 : 2.0 (Pro Standard)",
                            "Min 1 : 3.0 (High Reward)",
                        ],
                        key="f_rr",
                    )
                with r2c2:
                    f_candle = st.selectbox(
                        "🕯️ Candlestick Signal:",
                        ["ALL CANDLES", "Bullish Signal Only", "Neutral / Doji Only"],
                        key="f_candle",
                    )
                with r2c3:
                    st.button("🔄 Reset Filters", on_click=reset_filters, use_container_width=True)

            # Filtering logic
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
            elif f_rr == "Min 1 : 2.0 (Pro Standard)":
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

        else:
            df = df_raw.copy()

        st.write("")

        # Results Header, Export & Clear Cache Buttons
        h_left, h_center, h_right = st.columns([2.5, 1, 1], vertical_alignment="center")
        with h_left:
            st.markdown(
                f"### 📋 Screener Results <span style='font-size:0.9rem; color:#A855F7;'>({len(df)} Stocks)</span>",
                unsafe_allow_html=True,
            )
        with h_center:
            if st.button("🗑️ Clear Cache", use_container_width=True, key=f"btn_clear_{active_cache_key}"):
                clear_cache(active_cache_key)
                st.rerun()

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
            st.warning("⚠️ No analysis data matching selected filters.")
        else:
            # RENDER CARDS GRID
            render_trade_plan_cards(df)

    # Footer
    st.markdown(
        """
        <br>
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #1E2638; padding-top: 12px; color: #475569; font-size: 0.8rem;">
            <div>Official Trade Planner Screener • Serving traders worldwide</div>
            <div style="color: #A855F7; font-weight: 600; cursor: pointer;">System Active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
