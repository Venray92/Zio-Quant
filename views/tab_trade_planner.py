def render_tab_trade_planner():
    # 🎨 CYBERPUNK 2077 CSS STYLING
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Rajdhani:wght@500;600;700&display=swap');

        /* Global Cyberpunk Theme */
        .stApp {
            background-color: #05050a !important;
            font-family: 'Rajdhani', sans-serif !important;
            color: #00f0ff !important;
        }

        /* Ambient Cyber Grid & Overlay Effects */
        .stApp::before {
            content: " ";
            display: block;
            position: fixed;
            top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
            z-index: 999;
            background-size: 100% 3px, 6px 100%;
            pointer-events: none;
        }

        /* Cyber Header Panel */
        .zio-header-wrapper {
            display: flex;
            align-items: center;
            background: rgba(10, 10, 18, 0.85);
            border: 1px solid #00f0ff;
            border-left: 5px solid #ff003c;
            border-radius: 2px;
            padding: 16px 24px;
            margin-bottom: 24px;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.25), inset 0 0 15px rgba(0, 240, 255, 0.1);
            position: relative;
            clip-path: polygon(0 0, 97% 0, 100% 30%, 100% 100%, 0 100%);
        }
        .zio-header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .zio-icon-square {
            background: #ff003c;
            color: #fcee0a;
            width: 44px;
            height: 44px;
            clip-path: polygon(20% 0%, 100% 0, 100% 80%, 80% 100%, 0 100%, 0% 20%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 10px #ff003c;
        }
        .zio-title-text {
            color: #fcee0a;
            font-family: 'Orbitron', sans-serif;
            font-size: 1.4rem;
            font-weight: 900;
            letter-spacing: 2px;
            text-shadow: 2px 2px #ff003c, -1px -1px #00f0ff;
            text-transform: uppercase;
        }

        /* Form Subheader */
        .zio-form-header {
            color: #00f0ff;
            font-family: 'Orbitron', sans-serif;
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
            text-shadow: 0 0 8px rgba(0, 240, 255, 0.6);
        }
        .zio-label {
            color: #ff003c;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 1px;
            margin-bottom: 6px;
            display: block;
            text-transform: uppercase;
        }

        /* Input Customization */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
            background-color: #080811 !important;
            border: 1px solid #00f0ff !important;
            border-radius: 0px !important;
            color: #fcee0a !important;
            font-family: 'Rajdhani', sans-serif !important;
            font-weight: 600 !important;
        }
        div[data-baseweb="input"]:focus-within > div, div[data-baseweb="select"]:focus-within > div {
            border-color: #ff003c !important;
            box-shadow: 0 0 12px rgba(255, 0, 60, 0.6) !important;
        }

        /* Cyberpunk Tactical Buttons */
        div.stButton > button {
            background: #0d0e1b !important;
            color: #00f0ff !important;
            border: 1px solid #00f0ff !important;
            border-radius: 0px !important;
            font-family: 'Orbitron', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: 1.5px !important;
            text-transform: uppercase !important;
            padding: 12px 18px !important;
            transition: all 0.2s ease-in-out !important;
            clip-path: polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px) !important;
        }
        div.stButton > button:hover {
            background: #00f0ff !important;
            color: #000000 !important;
            box-shadow: 0 0 20px #00f0ff !important;
        }
        div.stButton > button[kind="primary"] {
            background: #ff003c !important;
            color: #fcee0a !important;
            border: 1px solid #fcee0a !important;
            box-shadow: 0 0 15px rgba(255, 0, 60, 0.5) !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background: #fcee0a !important;
            color: #ff003c !important;
            box-shadow: 0 0 25px #fcee0a !important;
        }

        /* Expander Frame */
        div[data-testid="stExpander"] {
            background-color: rgba(10, 10, 18, 0.9) !important;
            border: 1px solid #00f0ff !important;
            border-radius: 0px !important;
            box-shadow: inset 0 0 10px rgba(0, 240, 255, 0.1) !important;
        }

        /* CYBER HUD CARD DESIGN */
        .zio-card {
            background: rgba(12, 13, 24, 0.9);
            border-radius: 0px;
            padding: 16px 18px;
            margin-bottom: 14px;
            border: 1px solid #00f0ff;
            position: relative;
            box-shadow: 0 0 10px rgba(0, 240, 255, 0.15);
            clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 15px, 100% 100%, 15px 100%, 0 calc(100% - 15px));
        }
        .zio-card-green { border: 1px solid #00ff66; box-shadow: 0 0 10px rgba(0, 255, 102, 0.2); }
        .zio-card-red { border: 1px solid #ff003c; box-shadow: 0 0 10px rgba(255, 0, 60, 0.2); }
        .zio-card-blue { border: 1px solid #00f0ff; }

        .zio-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .zio-card-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .title-green { color: #00ff66; text-shadow: 0 0 5px #00ff66; }
        .title-red { color: #ff003c; text-shadow: 0 0 5px #ff003c; }
        .title-blue { color: #00f0ff; text-shadow: 0 0 5px #00f0ff; }

        .zio-badge {
            font-family: 'Orbitron', sans-serif;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 0px;
            text-transform: uppercase;
        }
        .badge-green { background-color: rgba(0, 255, 102, 0.15); color: #00ff66; border: 1px solid #00ff66; }
        .badge-red { background-color: rgba(255, 0, 60, 0.15); color: #ff003c; border: 1px solid #ff003c; }
        .badge-blue { background-color: rgba(0, 240, 255, 0.15); color: #00f0ff; border: 1px solid #00f0ff; }

        .zio-card-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.4rem;
            font-weight: 900;
            margin-bottom: 4px;
            line-height: 1.2;
            letter-spacing: 1px;
        }
        .val-white { color: #ffffff; text-shadow: 0 0 8px #ffffff; }
        .val-green { color: #00ff66; text-shadow: 0 0 8px #00ff66; }
        .val-red { color: #ff003c; text-shadow: 0 0 8px #ff003c; }

        .zio-card-subtext {
            font-size: 0.82rem;
            color: #8a99ad;
            font-weight: 600;
            line-height: 1.3;
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
                <div class="zio-icon-square">⚡</div>
                <div class="zio-title-text">CYBER EXECUTION SCREENER v2.077</div>
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
        '<div class="zio-form-header"><span style="color:#ff003c;">//</span> SELECT SCANNING PROTOCOL</div>',
        unsafe_allow_html=True,
    )

    mode_col1, mode_col2 = st.columns(2)
    current_mode = st.session_state["screener_mode"]

    with mode_col1:
        is_single = current_mode == "single"
        btn_type_single = "primary" if is_single else "secondary"
        if st.button(
            "⚡ SINGLE / CUSTOM TICKER ANALYSIS\nAnalyze targeted asset nodes",
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
            "🚀 FULL BATCH SCREENER SCAN\nExecute full neural database scan",
            use_container_width=True,
            type=btn_type_batch,
            key="btn_card_batch",
        ):
            if st.session_state["screener_mode"] != "batch":
                st.session_state["screener_mode"] = "batch"
            st.rerun()

    st.write("")

    # --- SINGLE MODE PROCESSOR ---
    if st.session_state["screener_mode"] == "single":
        col_input, col_btn = st.columns([3.5, 1], vertical_alignment="bottom")
        with col_input:
            st.markdown(
                '<span class="zio-label">> INPUT ASSET TICKERS:</span>',
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
                "🔍 ANALYZE TARGETS", type="primary", use_container_width=True
            )

        if btn_single:
            if not input_ticker.strip():
                st.warning("⚠️ PROTOCOL ERROR: Please enter at least one stock ticker!")
            else:
                list_to_scan = [
                    t.strip().upper()
                    for t in input_ticker.split(",")
                    if t.strip()
                ]
                run_batch_execution(list_to_scan, cache_key="df_screener_single")

        active_cache_key = "df_screener_single"

        # SINGLE MODE RESULT -> HUD CARDS
        if active_cache_key in st.session_state:
            df_single_res = st.session_state[active_cache_key]

            st.write("")
            h_left, h_right = st.columns([3, 1], vertical_alignment="center")
            with h_left:
                st.markdown(
                    f"<h3 style='font-family: Orbitron; color: #fcee0a; text-shadow: 0 0 10px #fcee0a;'>🎯 TARGET ANALYSIS DATA <span style='font-size:0.9rem; color:#00f0ff;'>[{len(df_single_res)} UNITS]</span></h3>",
                    unsafe_allow_html=True,
                )
            with h_right:
                if st.button("🗑️ PURGE DATA", use_container_width=True, key="btn_clear_single"):
                    clear_cache(active_cache_key)
                    st.rerun()

            if df_single_res.empty:
                st.warning("⚠️ SYSTEM WARNING: No valid data returned for the target tickers.")
            else:
                render_trade_plan_cards(df_single_res, is_title_needed=False)

    # --- BATCH SCREENER MODE PROCESSOR ---
    else:
        all_tickers = load_daftar_saham("daftar_saham.txt")
        if not all_tickers:
            st.error("❌ CRITICAL ERROR: `daftar_saham.txt` data block not found!")
            return

        col_info, col_batch_btn = st.columns([3, 1], vertical_alignment="center")
        with col_info:
            st.info(f"📁 DATABASE READY: **{len(all_tickers)} asset nodes** indexed from `daftar_saham.txt`.")
        with col_batch_btn:
            if st.button("🚀 INITIATE BATCH SCAN", type="primary", use_container_width=True):
                run_batch_execution(all_tickers, cache_key="df_screener_batch")

        active_cache_key = "df_screener_batch"

        if active_cache_key in st.session_state:
            df_raw = st.session_state[active_cache_key]

            # Filters
            st.write("")
            with st.expander("🛠️ **CYBER MATRIX FILTER PARAMETERS**", expanded=True):
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
                    st.button("🔄 OVERRIDE FILTERS", on_click=reset_filters, use_container_width=True)

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

            st.write("")

            # Header, Export & Clear Cache
            h_left, h_center, h_right = st.columns([2.5, 1, 1], vertical_alignment="center")
            with h_left:
                st.markdown(
                    f"<h3 style='font-family: Orbitron; color: #fcee0a; text-shadow: 0 0 10px #fcee0a;'>📋 SCREENER MATRIX <span style='font-size:0.9rem; color:#00f0ff;'>[{len(df)} UNITS MATCHED]</span></h3>",
                    unsafe_allow_html=True,
                )
            with h_center:
                if st.button("🗑️ PURGE CACHE", use_container_width=True, key="btn_clear_batch"):
                    clear_cache(active_cache_key)
                    st.rerun()

            with h_right:
                if not df.empty:
                    csv_data = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 EXPORT DATA",
                        data=csv_data,
                        file_name="cyber_trade_planner.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

            if df.empty:
                st.warning("⚠️ ZERO MATCHES: No data aligned with active filter matrix.")
            else:
                st.info("💡 **SYSTEM INSTRUCTION:** Toggle any target row to stream full **HUD Trade Plan** telemetry below.")

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
                            help="Lock node to render HUD tactical view",
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
                    hide_index=True,
                    use_container_width=True,
                    key=current_editor_key,
                )

                selected_rows = edited_df[edited_df["Select"] == True]
                num_checked = len(selected_rows)

                col_chk_status, col_chk_btn = st.columns([3, 1], vertical_alignment="center")
                with col_chk_status:
                    if num_checked > 0:
                        st.markdown(
                            f"📌 **TARGETS LOCKED:** `{num_checked} units` queued for detailed telemetry.",
                            unsafe_allow_html=True,
                        )
                with col_chk_btn:
                    if num_checked > 0:
                        if st.button("🧹 DESELECT ALL", use_container_width=True, key="btn_clear_selection"):
                            st.session_state["editor_key_version"] += 1
                            st.toast("TARGET SELECTIONS PURGED!", icon="✅")
                            st.rerun()

                if not selected_rows.empty:
                    st.write("")
                    selected_symbols = selected_rows["Symbol"].tolist()
                    df_selected_full = df[df["Symbol"].isin(selected_symbols)]
                    render_trade_plan_cards(df_selected_full, is_title_needed=True)

    # Cyberpunk Footer
    st.markdown(
        """
        <br>
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #00f0ff; padding-top: 12px; color: #00f0ff; font-family: Orbitron; font-size: 0.75rem; text-shadow: 0 0 5px #00f0ff;">
            <div>CYBERPUNK HUD INTERFACE • NEURAL GRID ACTIVE</div>
            <div style="color: #fcee0a; font-weight: 800; text-shadow: 0 0 8px #fcee0a;">ONLINE 100%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
