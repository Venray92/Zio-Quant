import concurrent.futures
import time
import pandas as pd
import streamlit as st
from data.ihsg_tickers import get_all_ihsg_tickers
from engines.screener_rsi_divergence import detect_rsi_patterns_and_score
from utils.ui_helpers import render_inline_trade_planner


def shorten_pattern(pattern_name):
    """Menyingkat nama pattern agar rapi di UI."""
    if not pattern_name or pattern_name == "-":
        return "-"

    res = str(pattern_name)
    res = res.replace("Regular Bullish Divergence", "Reg Bull Div")
    res = res.replace("Hidden Bullish Divergence", "Hid Bull Div")
    res = res.replace("Regular Bearish Divergence", "Reg Bear Div")
    res = res.replace("Hidden Bearish Divergence", "Hid Bear Div")
    res = res.replace("Bullish Divergence", "Bull Div")
    res = res.replace("Bearish Divergence", "Bear Div")
    res = res.replace(" Potensial (Menunggu GC)", " [Potensial]")
    res = res.replace(" Valid (GC Confirmed)", " [GC]")
    res = res.replace(" Valid (DC Confirmed)", " [DC]")
    res = res.replace(" Valid", "")
    return res


def fetch_rsi_worker(ticker, max_retries=1):
    """Worker function independen luar thread context Streamlit."""
    for attempt in range(max_retries + 1):
        try:
            res = detect_rsi_patterns_and_score(ticker)
            return True, res
        except Exception:
            if attempt < max_retries:
                time.sleep(0.2 * (attempt + 1))
            else:
                return False, None


def render_tab_rsi():
    # Style CSS Full Cyberpunk & Neon Futuristic
    st.markdown(
        """
        <style>
        /* =========================================================
           1. CYBERPUNK HEADER BANNER & GLOWING STATUS DOT
           ========================================================= */
        .cyber-header-container {
            position: relative;
            background: linear-gradient(135deg, rgba(255, 0, 127, 0.2) 0%, rgba(0, 243, 255, 0.2) 100%);
            border: 1.5px solid #00F3FF;
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 14px;
            text-align: center;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.35), inset 0 0 12px rgba(255, 0, 127, 0.25);
        }
        .cyber-header-title {
            font-size: 18px;
            font-weight: 900;
            letter-spacing: 2.5px;
            text-transform: uppercase;
            background: linear-gradient(90deg, #FF007F, #00F3FF, #00FF66);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 12px rgba(0, 243, 255, 0.6);
            margin: 0;
        }
        /* Styling 1 Titik Glowing Cyan di atas Teks */
        .cyber-status-dot {
            width: 10px;
            height: 10px;
            background-color: #00F3FF;
            border-radius: 50%;
            box-shadow: 0 0 10px #00F3FF, 0 0 20px #00F3FF;
            display: inline-block;
            margin-bottom: 6px;
            animation: pulse-glow 2s infinite ease-in-out;
        }

        @keyframes pulse-glow {
            0% { opacity: 0.5; box-shadow: 0 0 5px #00F3FF; }
            50% { opacity: 1; box-shadow: 0 0 15px #00F3FF, 0 0 25px #00F3FF; }
            100% { opacity: 0.5; box-shadow: 0 0 5px #00F3FF; }
        }

        /* =========================================================
           2. SECTION LABEL "CHOOSE SCREENER MODE"
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
        div[data-testid="stColumn"]:has(div[key="btn_run_rsi_screener"]) button {
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
        div[data-testid="stColumn"]:has(div[key="btn_run_rsi_screener"]) button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 0 25px rgba(0, 255, 102, 0.8) !important;
        }

        /* Tombol Stop */
        div[data-testid="stColumn"]:has(div[key="btn_stop_rsi_screener"]) button {
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
        div[data-testid="stColumn"]:has(div[key="btn_stop_rsi_screener"]) button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 0 25px rgba(255, 0, 127, 0.8) !important;
        }

        /* =========================================================
           4. STYLING SELECT SAHAM BUTTON (OVERRIDE WARNA MERAH)
           ========================================================= */
        div[data-testid="stColumn"] button[kind="primary"],
        div[data-testid="stColumn"] button[kind="secondary"] {
            transition: all 0.25s ease-in-out !important;
            border-radius: 6px !important;
            font-weight: 800 !important;
        }

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
           5. STYLING SELECTBOX / DROPDOWN
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

    # Inisialisasi State
    if "stop_rsi_scan" not in st.session_state:
        st.session_state["stop_rsi_scan"] = False

    if "active_rsi_type" not in st.session_state:
        st.session_state["active_rsi_type"] = "Bullish"

    if "selected_rsi_ticker" not in st.session_state:
        st.session_state["selected_rsi_ticker"] = None

    # ---------------------------------------------------------
    # LAYOUT UTAMA: SPLIT SCREEN (KIRI 38% : KANAN 62%)
    # ---------------------------------------------------------
    col_left, col_right = st.columns([1.3, 2.7], gap="medium")

    # =========================================================
    # PANEL KIRI: SCREENER CONTROL & DAFTAR SAHAM
    # =========================================================
    with col_left:
        # Header Banner Cyberpunk dengan 1 Glowing Status Dot di Atas Teks
        st.markdown(
            """
            <div class="cyber-header-container">
                <div style="display: flex; justify-content: center; align-items: center;">
                    <span class="cyber-status-dot"></span>
                </div>
                <div class="cyber-header-title">⚡ RSI MATRIX</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_btn_run, col_btn_stop = st.columns([1, 1])

        with col_btn_run:
            run_clicked = st.button(
                "▶ Run Screening",
                key="btn_run_rsi_screener",
                use_container_width=True,
            )

        with col_btn_stop:
            stop_clicked = st.button(
                "🛑 Stop", key="btn_stop_rsi_screener", use_container_width=True
            )

        if stop_clicked:
            st.session_state["stop_rsi_scan"] = True

        if run_clicked:
            st.session_state["stop_rsi_scan"] = False
            with st.spinner("Fetching IHSG tickers list..."):
                all_tickers = get_all_ihsg_tickers()

            total_tickers = len(all_tickers)
            pbar_rsi = st.progress(0)
            pstatus_rsi = st.empty()

            results_rsi = []
            success_count = 0
            failed_count = 0

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=8
            ) as executor:
                future_to_ticker = {
                    executor.submit(fetch_rsi_worker, t): t for t in all_tickers
                }
                completed = 0

                for future in concurrent.futures.as_completed(
                    future_to_ticker
                ):
                    if st.session_state.get("stop_rsi_scan", False):
                        pstatus_rsi.warning("Screening process cancelled.")
                        break

                    completed += 1
                    pct = int((completed / total_tickers) * 100)
                    pbar_rsi.progress(pct)
                    pstatus_rsi.text(
                        f"Scanning RSI: {completed}/{total_tickers} tickers..."
                    )

                    try:
                        is_success, res = future.result()
                        if is_success:
                            success_count += 1
                            if res is not None and isinstance(res, dict):
                                results_rsi.append(res)
                        else:
                            failed_count += 1
                    except Exception:
                        failed_count += 1

            pbar_rsi.empty()
            pstatus_rsi.empty()

            df_rsi_all = (
                pd.DataFrame(results_rsi) if results_rsi else pd.DataFrame()
            )

            if not df_rsi_all.empty and "Score" in df_rsi_all.columns:
                df_rsi_all = df_rsi_all.sort_values(
                    by="Score", ascending=False
                )

            df_rsi_bullish = pd.DataFrame()
            df_rsi_bearish = pd.DataFrame()

            if not df_rsi_all.empty and "Pattern" in df_rsi_all.columns:
                df_rsi_bullish = df_rsi_all[
                    df_rsi_all["Pattern"].str.contains(
                        "Bullish", case=False, na=False
                    )
                ]
                df_rsi_bearish = df_rsi_all[
                    df_rsi_all["Pattern"].str.contains(
                        "Bearish", case=False, na=False
                    )
                ]

            st.session_state["rsi_stats"] = {
                "total": total_tickers,
                "success": success_count,
                "failed": failed_count,
                "bullish_count": len(df_rsi_bullish),
                "bearish_count": len(df_rsi_bearish),
                "matched": len(df_rsi_all),
            }

            st.session_state["df_rsi_bullish"] = df_rsi_bullish
            st.session_state["df_rsi_bearish"] = df_rsi_bearish

            if not df_rsi_bullish.empty:
                st.session_state["selected_rsi_ticker"] = df_rsi_bullish.iloc[
                    0
                ].get(
                    "Ticker", df_rsi_bullish.iloc[0].get("Saham")
                )
            elif not df_rsi_bearish.empty:
                st.session_state["selected_rsi_ticker"] = df_rsi_bearish.iloc[
                    0
                ].get(
                    "Ticker", df_rsi_bearish.iloc[0].get("Saham")
                )

        st.markdown(
            "<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True
        )

        has_results = "rsi_stats" in st.session_state

     if has_results:
            st.markdown(
                '<div class="cyber-section-label">⚙ CHOOSE SCREENER MODE</div>',
                unsafe_allow_html=True,
            )

            # --- BAGIAN INI YANG DIUBAH (DIBAGI JADI 2 KOLOM) ---
            col_filter, col_export = st.columns([1, 2])

            with col_filter:
                screener_mode = st.selectbox(
                    "Choose Screener Mode",
                    options=["Bullish", "Bearish"],
                    index=0
                    if st.session_state.get("active_rsi_type") == "Bullish"
                    else 1,
                    key="rsi_screener_mode_select",
                    label_visibility="collapsed",
                )
            
            with col_export:
                # Tombol Export di sebelah kanan dropdown
                if st.button("📥 Export Semua Saham"):
                    # Tentukan dataframe aktif yang akan di-export
                    df_export = (
                        st.session_state.get("df_rsi_bullish", pd.DataFrame())
                        if screener_mode == "Bullish"
                        else st.session_state.get("df_rsi_bearish", pd.DataFrame())
                    )
                    if not df_export.empty:
                        csv_data = df_export.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Klik Disini untuk Download CSV",
                            data=csv_data,
                            file_name=f"hasil_screening_{screener_mode.lower()}.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning("Tidak ada data untuk di-export.")
            # ----------------------------------------------------

            st.session_state["active_rsi_type"] = screener_mode

            st.markdown(
                "<div style='margin-bottom: 12px;'></div>",
                unsafe_allow_html=True,
            )

            is_bull_tab = screener_mode == "Bullish"
            df_target = (
                st.session_state.get("df_rsi_bullish", pd.DataFrame())
                if is_bull_tab
                else st.session_state.get("df_rsi_bearish", pd.DataFrame())
            )

            if not df_target.empty:
                # BUNGKUS DENGAN SCROLLABLE CONTAINER (800px sesuai kode Anda)
                with st.container(height=800, border=False):
                    for idx, row in df_target.iterrows():
                        ticker = str(row.get("Ticker", row.get("Saham", "")))
                        saham = row.get("Saham", ticker.replace(".JK", ""))
                        score = row.get("Score", 0)
                        pattern_raw = row.get("Pattern", "-")
                        pattern_short = shorten_pattern(pattern_raw)

                        close_price = row.get("Close_Price", 0)
                        change_pct = row.get("Change_Pct", 0.0)

                        try:
                            close_price = float(close_price)
                        except (ValueError, TypeError):
                            close_price = 0.0

                        try:
                            change_pct = float(change_pct)
                        except (ValueError, TypeError):
                            change_pct = 0.0

                        tgl_kiri = str(row.get("Tgl Kiri", "-"))
                        tgl_kanan = str(row.get("Tgl Kanan", "-"))

                        is_selected = (
                            st.session_state.get("selected_rsi_ticker") == ticker
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

                        with st.container():
                            st.markdown(
                                f"""
                                <div style="{border_style} border-radius: 8px; padding: 10px 12px; margin-bottom: 4px;">
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                        <div>
                                            <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 2px;">
                                                <span style="font-size: 15px; font-weight: 800; color: #FFFFFF;">{saham}</span>
                                                <span style="background-color: rgba(255, 0, 127, 0.2); border: 1px solid #FF007F; color: #FF007F; font-size: 10px; padding: 1px 6px; border-radius: 4px; font-weight: 700;">⭐ {score}</span>
                                            </div>
                                            <div style="font-size: 11px; color: #8B949E; margin-bottom: 2px;">📌 {pattern_short}</div>
                                            <div style="font-size: 10px; color: #6E7681;">🗓️ {tgl_kiri} ➔ {tgl_kanan}</div>
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
                                key=f"select_rsi_btn_{ticker}_{idx}",
                                use_container_width=True,
                                type=btn_type,
                            ):
                                st.session_state["selected_rsi_ticker"] = ticker
                                st.rerun()

                            st.markdown(
                                "<div style='margin-bottom: 10px;'></div>",
                                unsafe_allow_html=True,
                            )
            else:
                st.info(f"No {screener_mode} patterns detected.")
        else:
            st.info(
                "Click **▶ Run Screening** above to start scanning the market."
            )

    # =========================================================
    # PANEL KANAN: WORKSPACE & LIVE TRADE PLANNER
    # =========================================================
    with col_right:
        if "rsi_stats" in st.session_state:
            stats = st.session_state["rsi_stats"]
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
                        <div class="metric-label" style="color: #00FF66;">Bullish</div>
                        <div class="metric-value" style="color: #00FF66;">{stats['bullish_count']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m3:
                st.markdown(
                    f"""<div class="metric-card" style="border-color: #FF007F;">
                        <div class="metric-label" style="color: #FF007F;">Bearish</div>
                        <div class="metric-value" style="color: #FF007F;">{stats['bearish_count']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m4:
                st.markdown(
                    f"""<div class="metric-card">
                        <div class="metric-label">Signals Found</div>
                        <div class="metric-value">{stats['matched']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            st.markdown(
                "<div style='margin-bottom: 10px;'></div>",
                unsafe_allow_html=True,
            )

        selected_rsi_symbol = st.session_state.get("selected_rsi_ticker")

        if selected_rsi_symbol:
            if (
                not selected_rsi_symbol.endswith(".JK")
                and "." not in selected_rsi_symbol
            ):
                selected_rsi_symbol += ".JK"

            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, rgba(0, 243, 255, 0.12) 0%, rgba(255, 0, 127, 0.1) 100%); border: 1.5px solid #00F3FF; padding: 8px 14px; border-radius: 8px; color: #FFFFFF; font-weight: 600; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 0 12px rgba(0, 243, 255, 0.25);">
                    <span>🎯 SELECTED SYMBOL: <strong style="color: #00F3FF; font-size: 15px; margin-left: 6px;">{selected_rsi_symbol}</strong></span>
                    <span style="color: #8B949E; font-size: 11px; font-weight: 500;">Interactive Analysis Workspace</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            try:
                render_inline_trade_planner(
                    selected_rsi_symbol, key_suffix="rsi_tab"
                )
            except KeyError as ke:
                if "Status Candle" in str(ke):
                    st.warning(
                        "Trade Plan rendered with partial data for"
                        f" {selected_rsi_symbol}."
                    )
                else:
                    st.error(
                        "Failed to load Trade Plan for"
                        f" {selected_rsi_symbol}: {ke}"
                    )
            except Exception as e:
                st.error(
                    f"Failed to load Trade Plan for {selected_rsi_symbol}: {e}"
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
