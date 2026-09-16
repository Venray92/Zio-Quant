
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

                f"⏳ <span style='color:#00f3ff; font-family: monospace;'>[SCANNING_GRID]:</span> `{completed}/{total_saham}` stocks processed ({int(percent * 100)}%)",

                unsafe_allow_html=True,

            )



    progress_bar.empty()

    status_text.empty()

    st.toast(

        f"SYSTEM ONLINE: Analyzed {len(results)} out of {total_saham} stocks!",

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

    st.toast("CACHE PURGED // MEMORY RESET", icon="🧹")





def draw_card(title, value, subtext, badge_text="", variant="cyan", value_color="cyan"):

    """Reusable Cyberpunk Card Component."""

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

    """Renders Cyberpunk Trade Plan Cards for given stocks Dataframe."""

    if is_title_needed:

        st.markdown(

            f"<h3 style='color:#00f3ff; font-family: monospace; text-shadow: 0 0 10px #00f3ff;'>// TRADE_PLANS_TARGETS <span style='font-size:0.9rem; color:#ff0055;'>({len(df_data)} UNITS)</span></h3>",

            unsafe_allow_html=True,

        )



    for idx, row in df_data.iterrows():

        st.markdown(

            f"""

            <div style="background: #0d0f18; border: 1px solid #00f3ff; box-shadow: 0 0 15px rgba(0, 243, 255, 0.2); padding: 16px 20px; border-radius: 4px; margin-top: 20px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; font-family: monospace;">

                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">

                    <span style="font-size: 1.6rem; font-weight: 900; color: #ff0055; text-shadow: 0 0 8px #ff0055; letter-spacing: 2px;">{row['Symbol']}</span>

                    <span style="background: rgba(0, 243, 255, 0.1); color: #00f3ff; border: 1px solid #00f3ff; padding: 3px 10px; font-size: 0.8rem; font-weight: 700;">STRATEGY: {row['Strategy']}</span>

                    <span style="background: rgba(255, 230, 0, 0.1); color: #ffe600; border: 1px solid #ffe600; padding: 3px 10px; font-size: 0.8rem; font-weight: 700;">Grade: {row['Grade']}</span>

                    <span style="background: rgba(255, 0, 85, 0.1); color: #ff0055; border: 1px solid #ff0055; padding: 3px 10px; font-size: 0.8rem; font-weight: 700;">Score: {row['Score']}/100</span>

                </div>

                <div style="color: #8a8b98; font-size: 0.9rem;">

                    LAST_PRICE: <strong style="color: #00f3ff; font-size: 1.2rem; text-shadow: 0 0 5px #00f3ff;">Rp {row['Last Price']:,}</strong>

                </div>

            </div>

            """,

            unsafe_allow_html=True,

        )



        col1, col2 = st.columns(2)

        with col1:

            draw_card(

                title="BUY RANGE // ENTRY_ZONE",

                value=str(row["Buy Range"]),

                subtext=f"STATUS: {row['Zone Position']}",

                badge_text=str(row["Zone Position"]),

                variant="cyan",

                value_color="cyan",

            )

            draw_card(

                title="TARGET 1 // TP_01",

                value=f"Rp {row['TP 1']:,}",

                subtext="Initial profit target / partial exit.",

                badge_text=str(row["Potential Gain"]),

                variant="yellow",

                value_color="yellow",

            )



        with col2:

            draw_card(

                title="STOP LOSS // CUT_OFF",

                value=f"Rp {row['Stop Loss (SL)']:,}",

                subtext="Hard boundary risk limit.",

                badge_text=str(row["SL Risk"]),

                variant="magenta",

                value_color="magenta",

            )

            draw_card(

                title="TARGET 2 // TP_02",

                value=f"Rp {row['TP 2']:,}",

                subtext="Main swing target zone.",

                badge_text=f"R:R {row['Risk-Reward Ratio']}",

                variant="cyan",

                value_color="cyan",

            )



        st.markdown(

            f"""

            <div style="background: #05060a; border: 1px solid #1e2230; padding: 14px 18px; margin-bottom: 28px; font-family: monospace; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">

                <div>

                    <span style="font-size: 0.75rem; color: #5a5c6e; display: block;">RISK : REWARD</span>

                    <span style="font-size: 0.95rem; color: #00f3ff; font-weight: 700;">1 : {row['Risk-Reward Ratio']}</span>

                </div>

                <div>

                    <span style="font-size: 0.75rem; color: #5a5c6e; display: block;">CANDLE_PATTERN</span>

                    <span style="font-size: 0.95rem; color: #ffe600; font-weight: 700;">{row['Candlestick Pattern']}</span>

                </div>

                <div style="grid-column: span 2;">

                    <span style="font-size: 0.75rem; color: #5a5c6e; display: block;">SYSTEM_ANALYSIS & WARNING</span>

                    <span style="font-size: 0.88rem; color: #ff0055; font-weight: 600;">{row['Analysis & Risk Warning']}</span>

                </div>

            </div>

            """,

            unsafe_allow_html=True,

        )





def render_tab_trade_planner():

    # 🎨 CYBERPUNK CSS STYLING

    st.markdown(

        """

        <style>

        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');



        /* Dark Glitch Background */

        .stApp {

            background-color: #030407 !important;

            color: #c0c5d0 !important;

            font-family: 'Share Tech Mono', monospace !important;

        }



        /* Cyberpunk Header Wrapper */

        .cp-header-wrapper {

            display: flex;

            align-items: center;

            background: #090b10;

            border: 2px solid #ff0055;

            box-shadow: 0 0 15px rgba(255, 0, 85, 0.3), inset 0 0 15px rgba(255, 0, 85, 0.1);

            padding: 18px 24px;

            margin-bottom: 24px;

            clip-path: polygon(0 0, 100% 0, 98% 100%, 0 100%);

        }

        .cp-title-text {

            color: #00f3ff;

            font-size: 1.5rem;

            font-weight: 900;

            text-shadow: 0 0 8px #00f3ff;

            letter-spacing: 3px;

            text-transform: uppercase;

        }



        /* Inputs Styling */

        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {

            background-color: #070910 !important;

            border: 1px solid #00f3ff !important;

            color: #00f3ff !important;

            border-radius: 0px !important;

            box-shadow: 0 0 5px rgba(0, 243, 255, 0.2);

            font-family: 'Share Tech Mono', monospace !important;

        }

        div[data-baseweb="input"]:focus-within > div, div[data-baseweb="select"]:focus-within > div {

            border-color: #ff0055 !important;

            box-shadow: 0 0 10px #ff0055 !important;

        }



        /* Neon Cyber Buttons */

        div.stButton > button {

            background: #090c15 !important;

            color: #00f3ff !important;

            border: 1px solid #00f3ff !important;

            border-radius: 0px !important;

            font-weight: 700 !important;

            font-family: 'Share Tech Mono', monospace !important;

            text-transform: uppercase;

            letter-spacing: 1px;

            padding: 12px 18px !important;

            transition: all 0.2s ease-in-out !important;

        }

        div.stButton > button:hover {

            background: #00f3ff !important;

            color: #000000 !important;

            box-shadow: 0 0 15px #00f3ff !important;

        }

        div.stButton > button[kind="primary"] {

            background: #ff0055 !important;

            color: #ffffff !important;

            border: 1px solid #ff0055 !important;

            box-shadow: 0 0 12px #ff0055 !important;

            text-shadow: 0 0 5px #ffffff;

        }

        div.stButton > button[kind="primary"]:hover {

            background: #ffffff !important;

            color: #ff0055 !important;

            box-shadow: 0 0 20px #ff0055 !important;

        }



        /* Expander */

        div[data-testid="stExpander"] {

            background-color: #080a10 !important;

            border: 1px solid #ff0055 !important;

            border-radius: 0px !important;

            box-shadow: 0 0 8px rgba(255, 0, 85, 0.2);

        }



        /* Cyberpunk Cards */

        .cp-card {

            background-color: #080a12;

            padding: 16px 18px;

            margin-bottom: 14px;

            font-family: 'Share Tech Mono', monospace;

            position: relative;

        }

        .cp-card-cyan { border: 1px solid #00f3ff; box-shadow: 0 0 10px rgba(0, 243, 255, 0.15); }

        .cp-card-magenta { border: 1px solid #ff0055; box-shadow: 0 0 10px rgba(255, 0, 85, 0.15); }

        .cp-card-yellow { border: 1px solid #ffe600; box-shadow: 0 0 10px rgba(255, 230, 0, 0.15); }



        .cp-card-header {

            display: flex;

            justify-content: space-between;

            align-items: center;

            margin-bottom: 8px;

        }

        .cp-card-title {

            font-size: 0.8rem;

            font-weight: 700;

            letter-spacing: 1px;

            text-transform: uppercase;

        }

        .title-cyan { color: #00f3ff; }

        .title-magenta { color: #ff0055; }

        .title-yellow { color: #ffe600; }



        .cp-badge {

            font-size: 0.7rem;

            font-weight: 700;

            padding: 2px 6px;

            border-radius: 0px;

        }

        .badge-cyan { background: rgba(0, 243, 255, 0.1); color: #00f3ff; border: 1px solid #00f3ff; }

        .badge-magenta { background: rgba(255, 0, 85, 0.1); color: #ff0055; border: 1px solid #ff0055; }

        .badge-yellow { background: rgba(255, 230, 0, 0.1); color: #ffe600; border: 1px solid #ffe600; }



        .cp-card-value {

            font-size: 1.4rem;

            font-weight: 900;

            margin-bottom: 4px;

            line-height: 1.2;

        }

        .val-cyan { color: #00f3ff; text-shadow: 0 0 5px #00f3ff; }

        .val-magenta { color: #ff0055; text-shadow: 0 0 5px #ff0055; }

        .val-yellow { color: #ffe600; text-shadow: 0 0 5px #ffe600; }



        .cp-card-subtext {

            font-size: 0.78rem;

            color: #6c7086;

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

            <div class="cp-title-text">⚡ TRADE_PLANNER // CYBER_SCREENER_v2.0</div>

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

        '<div style="color:#ff0055; font-family:monospace; font-weight:bold; margin-bottom:10px;">[SELECT_EXECUTION_MODE]</div>',

        unsafe_allow_html=True,

    )



    mode_col1, mode_col2 = st.columns(2)

    current_mode = st.session_state["screener_mode"]



    with mode_col1:

        is_single = current_mode == "single"

        btn_type_single = "primary" if is_single else "secondary"

        if st.button(

            "⚡ SINGLE_TARGET_SCAN\nAnalyze specific tickers",

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

            "🚀 BATCH_DATABASE_SWEEP\nFull scan ticker list",

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

                '<span style="color:#00f3ff; font-family:monospace; font-size:0.85rem;">INPUT_TARGET_TICKERS:</span>',

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

                "🔍 EXECUTE_SCAN", type="primary", use_container_width=True

            )



        if btn_single:

            if not input_ticker.strip():

                st.warning("⚠️ TARGET_INPUT_EMPTY!")

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

                    f"<h3 style='color:#00f3ff; font-family:monospace;'>// SCAN_RESULTS <span style='font-size:0.9rem; color:#ff0055;'>({len(df_single_res)} UNITS)</span></h3>",

                    unsafe_allow_html=True,

                )

            with h_right:

                if st.button("🗑️ PURGE_DATA", use_container_width=True, key="btn_clear_single"):

                    clear_cache(active_cache_key)

                    st.rerun()



            if df_single_res.empty:

                st.warning("⚠️ NO_VALID_DATA_RETURNED")

            else:

                render_trade_plan_cards(df_single_res, is_title_needed=False)



    else:

        all_tickers = load_daftar_saham("daftar_saham.txt")

        if not all_tickers:

            st.error("❌ `daftar_saham.txt` FILE_NOT_FOUND!")

            return



        col_info, col_batch_btn = st.columns([3, 1], vertical_alignment="center")

        with col_info:

            st.info(f"📁 GRID_DATABASE: Ready to scan **{len(all_tickers)} stocks** from `daftar_saham.txt`.")

        with col_batch_btn:

            if st.button("🚀 INITIALIZE_SWEEP", type="primary", use_container_width=True):

                run_batch_execution(all_tickers, cache_key="df_screener_batch")



        active_cache_key = "df_screener_batch"



        if active_cache_key in st.session_state:

            df_raw = st.session_state[active_cache_key]



            st.write("")

            with st.expander("🛠️ **CYBER_FILTERS & PARAMETERS**", expanded=True):

                r1c1, r1c2, r1c3 = st.columns(3)

                with r1c1:

                    f_strategi = st.selectbox(

                        "🎯 STRATEGY:",

                        ["ALL STRATEGIES", "Buy On Weakness (BOW)", "Breakout (BOB)"],

                        key="f_strategi",

                    )

                with r1c2:

                    f_grade = st.selectbox(

                        "🏆 SETUP_GRADE:",

                        [

                            "ALL GRADES",

                            "Grade A / A+ Only (High Quality)",

                            "Grade B or Lower (Moderate/Risk)",

                        ],

                        key="f_grade",

                    )

                with r1c3:

                    f_zone = st.selectbox(

                        "📍 PRICE_ZONE:",

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

                        "⚖️ MIN_RISK_REWARD:",

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

                        "🕯️ CANDLE_PATTERN:",

                        ["ALL CANDLES", "Bullish Signal Only", "Neutral / Doji Only"],

                        key="f_candle",

                    )

                with r2c3:

                    st.button("🔄 RESET_FILTERS", on_click=reset_filters, use_container_width=True)



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



            st.write("")



            h_left, h_center, h_right = st.columns([2.5, 1, 1], vertical_alignment="center")

            with h_left:

                st.markdown(

                    f"<h3 style='color:#00f3ff; font-family:monospace;'>// SCREENER_RESULTS <span style='font-size:0.9rem; color:#ff0055;'>({len(df)} UNITS)</span></h3>",

                    unsafe_allow_html=True,

                )

            with h_center:

                if st.button("🗑️ PURGE_CACHE", use_container_width=True, key="btn_clear_batch"):

                    clear_cache(active_cache_key)

                    st.rerun()



            with h_right:

                if not df.empty:

                    csv_data = df.to_csv(index=False).encode("utf-8")

                    st.download_button(

                        label="📥 EXPORT_CSV",

                        data=csv_data,

                        file_name="cyber_trade_planner.csv",

                        mime="text/csv",

                        use_container_width=True,

                    )



            if df.empty:

                st.warning("⚠️ NO_TARGETS_MATCH_CURRENT_FILTER")

            else:

                st.info("💡 **SYSTEM_TIP:** Select checkbox on target stock to load visual trade plan cards.")



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

                df_table.insert(0, "Select", False)



                edited_df = st.data_editor(

                    df_table[["Select"] + display_cols],

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

                    disabled=display_cols,

                    use_container_width=True,

                    key=current_editor_key,

                )



                selected_rows = edited_df[edited_df["Select"] == True]

                num_checked = len(selected_rows)



                col_chk_status, col_chk_btn = st.columns([3, 1], vertical_alignment="center")

                with col_chk_status:

                    if num_checked > 0:

                        st.markdown(

                            f"📌 SELECTED: **{num_checked} targets** loaded for deep analysis.",

                            unsafe_allow_html=True,

                        )

                with col_chk_btn:

                    if num_checked > 0:

                        if st.button("🧹 CLEAR_SELECTION", use_container_width=True, key="btn_clear_selection"):

                            st.session_state["editor_key_version"] += 1

                            st.toast("SELECTION_CLEARED", icon="✅")

                            st.rerun()



                if not selected_rows.empty:

                    st.write("")

                    selected_symbols = selected_rows["Symbol"].tolist()

                    df_selected_full = df[df["Symbol"].isin(selected_symbols)]

                    render_trade_plan_cards(df_selected_full, is_title_needed=True)



    st.markdown(

        """

        <br>

        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #ff0055; padding-top: 12px; color: #5a5c6e; font-family: monospace; font-size: 0.8rem;">

            <div>SYSTEM // CYBER_TRADE_PLANNER_v2.0</div>

            <div style="color: #00f3ff; font-weight: 700; text-shadow: 0 0 5px #00f3ff;">[SYSTEM_ONLINE]</div>

        </div>

        """,

        unsafe_allow_html=True,

    ) 

