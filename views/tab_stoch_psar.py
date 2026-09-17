import pandas as pd
import streamlit as st
from data.ihsg_tickers import get_all_ihsg_tickers
from screener_stoch_psar import run_stoch_psar_screener
from utils.ui_helpers import render_inline_trade_planner


def render_tab_stoch_psar():
    # Style CSS Full Cyberpunk & Neon Futuristic
    st.markdown(
        """
        <style>
        /* =========================================================
           1. CYBERPUNK HEADER BANNER
           ========================================================= */
        .cyber-header-container {
            position: relative;
            background: linear-gradient(135deg, rgba(255, 0, 127, 0.2) 0%, rgba(0, 243, 255, 0.2) 100%);
            border: 1.5px solid #00F3FF;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 14px;
            text-align: center;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.35), inset 0 0 12px rgba(255, 0, 127, 0.25);
        }
        .cyber-header-title {
            font-size: 16px;
            font-weight: 900;
            letter-spacing: 2.5px;
            text-transform: uppercase;
            background: linear-gradient(90deg, #FF007F, #00F3FF, #00FF66);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 12px rgba(0, 243, 255, 0.6);
            margin: 0;
        }

        /* Status Dot Cyberpunk */
        .cyber-status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #FF007F;
            border-radius: 50%;
            box-shadow: 0 0 10px #FF007F, 0 0 18px #FF007F;
            margin-right: 6px;
            animation: cyberpunk-pulse 1.5s infinite alternate;
        }

        @keyframes cyberpunk-pulse {
            0% { transform: scale(0.9); box-shadow: 0 0 6px #FF007F; }
            100% { transform: scale(1.3); box-shadow: 0 0 15px #00F3FF; background-color: #00F3FF; }
        }

        /* =========================================================
           2. SECTION LABEL "CHOOSE SIGNAL MODE"
           ========================================================= */
        .cyber-section-label {
            font-size: 11px;
            font-weight: 800;
            color: #FF007F;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            text-shadow: 0 0 8px rgba(255, 0, 127, 0.6);
            margin-top: 14px;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* =========================================================
           3. STYLING STREAMLIT BUTTONS (RUN & STOP)
           ========================================================= */
        /* Tombol Run Screening */
        div[data-testid="stColumn"]:has(div[key="btn_run_stoch_screener"]) button {
            background: linear-gradient(135deg, #00F3FF 0%, #00FF66 100%) !important;
            color: #050811 !important;
            font-weight: 900 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            border: none !important;
            border-radius: 6px !important;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.5) !important;
            transition: all 0.25s ease-in-out !important;
        }
        div[data-testid="stColumn"]:has(div[key="btn_run_stoch_screener"]) button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 0 25px rgba(0, 255, 102, 0.8) !important;
        }

        /* Tombol Stop */
        div[data-testid="stColumn"]:has(div[key="btn_stop_stoch_screener"]) button {
            background: linear-gradient(135deg, #FF007F 0%, #7928CA 100%) !important;
            color: #FFFFFF !important;
            font-weight: 900 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            border: none !important;
            border-radius: 6px !important;
            box-shadow: 0 0 15px rgba(255, 0, 127, 0.5) !important;
            transition: all 0.25s ease-in-out !important;
        }
        div[data-testid="stColumn"]:has(div[key="btn_stop_stoch_screener"]) button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 0 25px rgba(255, 0, 127, 0.8) !important;
        }

        /* =========================================================
           4. STYLING SELECT SAHAM BUTTON (OVERRIDE WARNA MERAH)
           ========================================================= */
        /* All Stock Selection Buttons */
        div[data-testid="stColumn"] button[kind="primary"],
        div[data-testid="stColumn"] button[kind="secondary"] {
            transition: all 0.25s ease-in-out !important;
            border-radius: 6px !important;
            font-weight: 800 !important;
        }

        /* Primary Button (Saat STATUS SELECTED / DITEKAN) */
        div[data-testid="stColumn"] button[kind="primary"] {
            background: linear-gradient(135deg, #FF007F 0%, #00F3FF 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid #00F3FF !important;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.6) !important;
            text-shadow: 0 0 6px rgba(0,0,0,0.8) !important;
        }
        div[data-testid="stColumn"] button[kind="primary"]:hover {
            box-shadow: 0 0 25px rgba(255, 0, 127, 0.8) !important;
            transform: translateY(-1px) !important;
        }

        /* Secondary Button (Saat UNSELECTED) */
        div[data-testid="stColumn"] button[kind="secondary"] {
            background-color: #161B22 !important;
            color: #00F3FF !important;
            border: 1px solid #30363D !important;
        }
        div[data-testid="stColumn"] button[kind="secondary"]:hover {
            border-color: #00F3FF !important;
            color: #FFFFFF !important;
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.3) !important;
        }

        /* =========================================================
           5. STYLING SELECTBOX / DROPDOWN (NEON BORDER & TEXT)
           ========================================================= */
        div[data-testid="stSelectbox"] > div > div {
            background-color: #0D1117 !important;
            border: 1.5px solid #00F3FF !important;
            border-radius: 6px !important;
            color: #00F3FF !important;
            font-weight: 700 !important;
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.2) !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[data-testid="stSelectbox"] > div > div:hover {
            border-color: #FF007F !important;
            box-shadow: 0 0 15px rgba(255, 0, 127, 0.4) !important;
        }
        div[data-testid="stSelectbox"] div[role="button"] {
            color: #00F3FF !important;
            font-weight: 700 !important;
        }

        /* =========================================================
           6. METRIC CARDS & CONTAINER STYLES
           ========================================================= */
        .metric-card {
            background: #161B22;
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 10px 12px;
            text-align: center;
            box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.5);
        }
        .metric-value {
            font-size: 18px;
            font-weight: 800;
            color: #FFFFFF;
        }
        .metric-label {
            font-size: 10px;
            color: #8B949E;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .empty-card {
            background-color: #161B22;
            border: 1px dashed #30363D;
            border-radius: 10px;
            padding: 50px 20px;
            text-align: center;
            color: #8B949E;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "stop_stoch_scan" not in st.session_state:
        st.session_state["stop_stoch_scan"] = False

    if "active_stoch_type" not in st.session_state:
        st.session_state["active_stoch_type"] = "Golden Cross (Buy)"

    if "selected_stoch_ticker" not in st.session_state:
        st.session_state["selected_stoch_ticker"] = None

    col_left, col_right = st.columns([1.3, 2.7], gap="medium")

    # =========================================================
    # LEFT PANEL: SCREENER CONTROL & STOCK LIST
    # =========================================================
    with col_left:
        # Header Banner Cyberpunk dengan Glowing Status Dot
        st.markdown(
            """
            <div class="cyber-header-container">
                <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 4px;">
                    <span class="cyber-status-dot"></span>
                </div>
                <div class="cyber-header-title">⚡ STOCH-TREND RADAR</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_btn_run, col_btn_stop = st.columns([1, 1])

        with col_btn_run:
            run_clicked = st.button(
                "▶ Run Screening",
                key="btn_run_stoch_screener",
                use_container_width=True,
            )

        with col_btn_stop:
            stop_clicked = st.button(
                "🛑 Stop",
                key="btn_stop_stoch_screener",
                use_container_width=True,
            )

        if stop_clicked:
            st.session_state["stop_stoch_scan"] = True

        if run_clicked:
            st.session_state["stop_stoch_scan"] = False
            with st.spinner("Fetching IHSG Tickers List..."):
                all_stoch_tickers = get_all_ihsg_tickers()

            total_stoch_tickers = len(all_stoch_tickers)
            pbar_stoch = st.progress(0)
            pstatus_stoch = st.empty()

            def update_stoch_progress(current, total):
                if st.session_state.get("stop_stoch_scan", False):
                    pstatus_stoch.warning("Screening process cancelled by user.")
                    return
                pct = current / total if total > 0 else 0
                pbar_stoch.progress(pct)
                pstatus_stoch.text(
                    f"Scanning Stoch & PSAR: {current}/{total} tickers..."
                )

            try:
                df_gc, df_dc = run_stoch_psar_screener(
                    tickers=all_stoch_tickers,
                    progress_callback=update_stoch_progress,
                )
                pbar_stoch.empty()
                pstatus_stoch.empty()

                if (
                    df_gc is not None
                    and not df_gc.empty
                    and "Score" in df_gc.columns
                ):
                    df_gc = df_gc.sort_values(by="Score", ascending=False)
                if (
                    df_dc is not None
                    and not df_dc.empty
                    and "Score" in df_dc.columns
                ):
                    df_dc = df_dc.sort_values(by="Score", ascending=False)

                st.session_state["df_gc_data"] = (
                    df_gc if df_gc is not None else pd.DataFrame()
                )
                st.session_state["df_dc_data"] = (
                    df_dc if df_dc is not None else pd.DataFrame()
                )

                gc_len = len(df_gc) if df_gc is not None else 0
                dc_len = len(df_dc) if df_dc is not None else 0

                st.session_state["stoch_stats"] = {
                    "total": total_stoch_tickers,
                    "matched_gc": gc_len,
                    "matched_dc": dc_len,
                    "total_signal": gc_len + dc_len,
                }

                if df_gc is not None and not df_gc.empty:
                    first_row = df_gc.iloc[0]
                    st.session_state["selected_stoch_ticker"] = first_row.get(
                        "Ticker", ""
                    )
                elif df_dc is not None and not df_dc.empty:
                    first_row = df_dc.iloc[0]
                    st.session_state["selected_stoch_ticker"] = first_row.get(
                        "Ticker", ""
                    )

            except Exception as e:
                pbar_stoch.empty()
                pstatus_stoch.empty()
                st.error(f"An error occurred: {e}")

        st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)

        has_results = "stoch_stats" in st.session_state

        if has_results:
            st.markdown(
                '<div class="cyber-section-label">⚙ CHOOSE SIGNAL MODE</div>',
                unsafe_allow_html=True,
            )

            screener_mode = st.selectbox(
                "Choose Signal Mode",
                options=["Golden Cross (Buy)", "Dead Cross (Sell)"],
                index=0
                if "Buy" in st.session_state.get("active_stoch_type", "Golden Cross (Buy)")
                else 1,
                key="stoch_screener_mode_select",
                label_visibility="collapsed",
            )
            st.session_state["active_stoch_type"] = screener_mode

            st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

            is_gc_tab = "Buy" in screener_mode
            df_target = (
                st.session_state.get("df_gc_data", pd.DataFrame())
                if is_gc_tab
                else st.session_state.get("df_dc_data", pd.DataFrame())
            )

            if not df_target.empty:
                # =========================================================
                # BUNGKUS DENGAN CONTAINER UNTUK SCROLLING (MAX HEIGHT)
                # =========================================================
                with st.container(height=550, border=False):
                    for idx, row in df_target.iterrows():
                        ticker = str(row.get("Ticker", ""))
                        saham = ticker.replace(".JK", "")
                        score = row.get("Score", 0)

                        signal_desc = row.get("Detail Signal", "-")

                        close_price = row.get("Harga", 0)
                        change_pct = row.get("Change (%)", 0.0)

                        try:
                            close_price = float(close_price)
                        except (ValueError, TypeError):
                            close_price = 0.0

                        try:
                            change_pct = float(change_pct)
                        except (ValueError, TypeError):
                            change_pct = 0.0

                        is_selected = (
                            st.session_state.get("selected_stoch_ticker") == ticker
                        )

                        change_color = "#00FF66" if change_pct >= 0 else "#FF007F"
                        change_icon = "📈" if change_pct >= 0 else "📉"
                        change_str = f"{change_icon} {change_pct:+.2f}%"
                        price_str = f"{close_price:,.0f}".replace(",", ".")

                        border_style = (
                            "border: 1.5px solid #00F3FF; background: linear-gradient(135deg, rgba(0, 243, 255, 0.12) 0%, rgba(255, 0, 127, 0.1) 100%); box-shadow: 0 0 12px rgba(0, 243, 255, 0.3);"
                            if is_selected
                            else "border: 1px solid #30363D; background-color: #161B22;"
                        )

                        # Render Kartu Saham
                        st.markdown(
                            f"""
                            <div style="{border_style} border-radius: 8px; padding: 10px 12px; margin-bottom: 4px;">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                    <div>
                                        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 2px;">
                                            <span style="font-size: 15px; font-weight: 800; color: #FFFFFF;">{saham}</span>
                                            <span style="background-color: rgba(255, 0, 127, 0.2); border: 1px solid #FF007F; color: #FF007F; font-size: 10px; padding: 1px 6px; border-radius: 4px; font-weight: 700;">⭐ {score}</span>
                                        </div>
                                        <div style="font-size: 11px; color: #8B949E; margin-bottom: 2px;">📌 {signal_desc}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 15px; font-weight: 800; color: #FFFFFF; margin-bottom: 2px;">Rp {price_str}</div>
                                        <div style="font-size: 11px; font-weight: 700; color: {change_color};">{change_str}</div>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        btn_label = (
                            f"✓ SELECTED ({saham})"
                            if is_selected
                            else f"SELECT {saham}"
                        )
                        btn_type = "primary" if is_selected else "secondary"

                        if st.button(
                            btn_label,
                            key=f"select_stoch_btn_{ticker}_{idx}",
                            use_container_width=True,
                            type=btn_type,
                        ):
                            st.session_state["selected_stoch_ticker"] = ticker
                            st.rerun()

                        st.markdown(
                            "<div style='margin-bottom: 10px;'></div>",
                            unsafe_allow_html=True,
                        )
            else:
                st.info(f"No {screener_mode} signals detected.")
        else:
            st.info(
                "Click **▶ Run Screening** above to scan the market."
            )

    # =========================================================
    # RIGHT PANEL: WORKSPACE & LIVE TRADE PLANNER
    # =========================================================
    with col_right:
        if "stoch_stats" in st.session_state:
            stats = st.session_state["stoch_stats"]
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(
                    f"""<div class="metric-card">
                        <div class="metric-label">Total Scanned</div>
                        <div class="metric-value">{stats['total']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m2:
                st.markdown(
                    f"""<div class="metric-card" style="border-color: #00FF66;">
                        <div class="metric-label" style="color: #00FF66;">Golden Cross</div>
                        <div class="metric-value" style="color: #00FF66;">{stats['matched_gc']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m3:
                st.markdown(
                    f"""<div class="metric-card" style="border-color: #FF007F;">
                        <div class="metric-label" style="color: #FF007F;">Dead Cross</div>
                        <div class="metric-value" style="color: #FF007F;">{stats['matched_dc']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m4:
                st.markdown(
                    f"""<div class="metric-card">
                        <div class="metric-label">Total Signals</div>
                        <div class="metric-value">{stats['total_signal']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            st.markdown(
                "<div style='margin-bottom: 10px;'></div>",
                unsafe_allow_html=True,
            )

        selected_stoch_symbol = st.session_state.get("selected_stoch_ticker")

        if selected_stoch_symbol:
            if (
                not selected_stoch_symbol.endswith(".JK")
                and "." not in selected_stoch_symbol
            ):
                selected_stoch_symbol += ".JK"

            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, rgba(0, 243, 255, 0.12) 0%, rgba(255, 0, 127, 0.1) 100%); border: 1.5px solid #00F3FF; padding: 8px 14px; border-radius: 8px; color: #FFFFFF; font-weight: 600; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 0 12px rgba(0, 243, 255, 0.25);">
                    <span>🎯 SELECTED SYMBOL: <strong style="color: #00F3FF; font-size: 15px; margin-left: 6px;">{selected_stoch_symbol}</strong></span>
                    <span style="color: #8B949E; font-size: 11px; font-weight: 500;">Interactive Analysis Workspace</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            try:
                render_inline_trade_planner(
                    selected_stoch_symbol, key_suffix="stoch_tab"
                )
            except KeyError as ke:
                if "Status Candle" in str(ke):
                    st.warning(
                        "Trade Plan rendered with partial data for"
                        f" {selected_stoch_symbol}."
                    )
                else:
                    st.error(
                        "Failed to load Trade Plan for"
                        f" {selected_stoch_symbol}: {ke}"
                    )
            except Exception as e:
                st.error(
                    f"Failed to load Trade Plan for {selected_stoch_symbol}: {e}"
                )
        else:
            st.markdown(
                """
                <div class="empty-card">
                    <div style="font-size: 32px; margin-bottom: 8px;">👈</div>
                    <h3 style="color: #FFFFFF; font-size: 16px; margin-bottom: 4px;">Select a Stock from Left Panel</h3>
                    <p style="font-size: 12px; color: #8B949E; max-width: 400px; margin: 0 auto;">
                        Run the screening process, then click any stock card from the left panel to inspect full Trade Planner details.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
