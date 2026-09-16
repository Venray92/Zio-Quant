import concurrent.futures
import time
import pandas as pd
import streamlit as st
from ihsg_tickers import get_all_ihsg_tickers
from screener_rsi_divergence import detect_rsi_patterns_and_score
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
    # CSS Custom dasar
    st.markdown(
        """
        <style>
        .panel-header-center {
            background-color: #161B22;
            border: 1px solid #21262D;
            border-radius: 8px;
            padding: 8px;
            margin-bottom: 10px;
            text-align: center;
        }
        .metric-card {
            background-color: #161B22;
            border: 1px solid #21262D;
            border-radius: 8px;
            padding: 8px 10px;
            text-align: center;
        }
        .metric-value {
            font-size: 16px;
            font-weight: 700;
            color: #FFFFFF;
        }
        .metric-label {
            font-size: 9px;
            color: #8B949E;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 2px;
        }
        .empty-card {
            background-color: #161B22;
            border: 1px dashed #30363D;
            border-radius: 8px;
            padding: 40px 20px;
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
        st.markdown(
            """
            <div class="panel-header-center">
                <div style="color: #00E676; font-weight: 700; font-size: 15px; letter-spacing: 0.5px;">RSI DIVERGENCE</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_btn_run, col_btn_stop = st.columns([1, 1])

        with col_btn_run:
            run_clicked = st.button(
                "Run Screening",
                key="btn_run_rsi_screener",
                use_container_width=True,
                type="primary",
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

            # Gunakan ThreadPoolExecutor
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
                    # Cek flag stop
                    if st.session_state.get("stop_rsi_scan", False):
                        pstatus_rsi.warning("Screening process cancelled.")
                        break

                    completed += 1
                    pct = int((completed / total_tickers) * 100)
                    pbar_rsi.progress(pct)
                    pstatus_rsi.text(
                        f"Scanning: {completed}/{total_tickers}"
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

            # Set default terpilih ke saham teratas
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
            "<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True
        )

        has_results = "rsi_stats" in st.session_state

        if has_results:
            screener_mode = st.selectbox(
                "Choose Screener Mode",
                options=["Bullish", "Bearish"],
                index=0
                if st.session_state.get("active_rsi_type") == "Bullish"
                else 1,
                key="rsi_screener_mode_select",
            )
            st.session_state["active_rsi_type"] = screener_mode

            st.markdown(
                "<div style='margin-bottom: 6px;'></div>",
                unsafe_allow_html=True,
            )

            is_bull_tab = screener_mode == "Bullish"
            df_target = (
                st.session_state.get("df_rsi_bullish", pd.DataFrame())
                if is_bull_tab
                else st.session_state.get("df_rsi_bearish", pd.DataFrame())
            )

            if not df_target.empty:
                for idx, row in df_target.iterrows():
                    ticker = row.get("Ticker", row.get("Saham", ""))
                    saham = row.get("Saham", ticker.replace(".JK", ""))
                    score = row.get("Score", 0)
                    pattern_raw = row.get("Pattern", "-")
                    pattern_short = shorten_pattern(pattern_raw)

                    close_price = row.get("Close_Price", 0)
                    change_pct = row.get("Change_Pct", 0.0)

                    tgl_kiri = str(row.get("Tgl Kiri", "-"))
                    tgl_kanan = str(row.get("Tgl Kanan", "-"))

                    is_selected = (
                        st.session_state.get("selected_rsi_ticker") == ticker
                    )

                    change_color = (
                        "#00E676" if change_pct >= 0 else "#FF5252"
                    )
                    change_icon = "📈" if change_pct >= 0 else "📉"
                    change_str = f"{change_icon} {change_pct:+.2f}%"
                    price_str = f"{close_price:,.0f}".replace(",", ".")

                    border_style = (
                        "border: 1.5px solid #00E676; background-color:"
                        " #0D2B1D;"
                        if is_selected
                        else "border: 1px solid #30363D; background-color:"
                        " #161B22;"
                    )

                    # Container Kartu Rapi
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="{border_style} border-radius: 8px; padding: 10px 12px; margin-bottom: 4px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 2px;">
                                            <span style="font-size: 15px; font-weight: 800; color: #FFFFFF;">{saham}</span>
                                            <span style="background-color: #21262D; border: 1px solid #30363D; color: #E6BDFB; font-size: 10px; padding: 1px 5px; border-radius: 4px; font-weight: 600;">⭐ {score}</span>
                                        </div>
                                        <div style="font-size: 11px; color: #8B949E; margin-bottom: 2px;">📌 {pattern_short}</div>
                                        <div style="font-size: 10px; color: #6E7681;">🗓️ {tgl_kiri} ➔ {tgl_kanan}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 16px; font-weight: 700; color: #FFFFFF; margin-bottom: 2px;">{price_str}</div>
                                        <div style="font-size: 11px; font-weight: 600; color: {change_color};">{change_str}</div>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        btn_label = (
                            f"✓ Selected ({saham})"
                            if is_selected
                            else f"Select {saham}"
                        )
                        btn_type = "primary" if is_selected else "secondary"

                        if st.button(
                            btn_label,
                            key=f"select_btn_{ticker}_{idx}",
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
                "Click **Run Screening** above to start scanning the market."
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
                    f"""<div class="metric-card" style="border-color: #00E676;">
                        <div class="metric-label" style="color: #00E676;">Bullish</div>
                        <div class="metric-value" style="color: #00E676;">{stats['bullish_count']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m3:
                st.markdown(
                    f"""<div class="metric-card" style="border-color: #FF5252;">
                        <div class="metric-label" style="color: #FF5252;">Bearish</div>
                        <div class="metric-value" style="color: #FF5252;">{stats['bearish_count']}</div>
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
                <div style="background-color: #0D2B1D; border: 1.5px solid #00E676; padding: 8px 14px; border-radius: 8px; color: #FFFFFF; font-weight: 600; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                    <span>🎯 SELECTED SYMBOL: <strong style="color: #00E676; font-size: 15px; margin-left: 6px;">{selected_rsi_symbol}</strong></span>
                    <span style="color: #8B949E; font-size: 11px; font-weight: 400;">Interactive Analysis Workspace</span>
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
                    <div style="font-size: 28px; margin-bottom: 8px;">👈</div>
                    <h3 style="color: #FFFFFF; font-size: 16px; margin-bottom: 4px;">Select a Stock from Left Panel</h3>
                    <p style="font-size: 12px; color: #8B949E; max-width: 400px; margin: 0 auto;">
                        Run the screening process, then click any stock card from the left panel to inspect full Trade Planner details.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
