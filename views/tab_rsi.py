import concurrent.futures
import time
import pandas as pd
import streamlit as st
from ihsg_tickers import get_all_ihsg_tickers
from screener_rsi_divergence import detect_rsi_patterns_and_score
from utils.ui_helpers import render_inline_trade_planner


def render_tab_rsi():
    # Overhead Styling
    st.markdown(
        """
        <style>
        .panel-header-center {
            background-color: #161B22;
            border: 1px solid #21262D;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 12px;
            text-align: center;
        }
        .metric-card {
            background-color: #161B22;
            border: 1px solid #21262D;
            border-radius: 8px;
            padding: 10px 14px;
            text-align: center;
        }
        .metric-value {
            font-size: 18px;
            font-weight: 700;
            color: #FFFFFF;
        }
        .metric-label {
            font-size: 10px;
            color: #8B949E;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 2px;
        }
        .empty-card {
            background-color: #161B22;
            border: 1px dashed #30363D;
            border-radius: 8px;
            padding: 60px 20px;
            text-align: center;
            color: #8B949E;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # State Inisialisasi
    if "stop_rsi_scan" not in st.session_state:
        st.session_state["stop_rsi_scan"] = False
    
    if "active_rsi_type" not in st.session_state:
        st.session_state["active_rsi_type"] = "bullish"  # Default 'bullish' atau 'bearish'

    # ---------------------------------------------------------
    # LAYOUT UTAMA: SPLIT SCREEN (KIRI 32% : KANAN 68%)
    # ---------------------------------------------------------
    col_left, col_right = st.columns([1.15, 2.85], gap="medium")

    selected_rsi_symbol = None

    target_rsi_cols = [
        "Saham",
        "Score",
        "Pattern",
        "Tgl Kiri",
        "Tgl Kanan",
        "Harga Kiri",
        "Harga Kanan",
        "RSI Kiri",
        "RSI Kanan",
    ]

    column_configuration = {
        "Saham": st.column_config.TextColumn("Ticker", width="small"),
        "Score": st.column_config.NumberColumn("Score", format="%d ⭐"),
        "Pattern": st.column_config.TextColumn("Pattern"),
        "Harga Kiri": st.column_config.NumberColumn("Price L", format="Rp %d"),
        "Harga Kanan": st.column_config.NumberColumn("Price R", format="Rp %d"),
        "RSI Kiri": st.column_config.NumberColumn("RSI L", format="%.1f"),
        "RSI Kanan": st.column_config.NumberColumn("RSI R", format="%.1f"),
    }

    # =========================================================
    # PANEL KIRI: SCREENER CONTROL & DAFTAR SAHAM
    # =========================================================
    with col_left:
        # Header tanpa IHSG Market Screener
        st.markdown(
            """
            <div class="panel-header-center">
                <div style="color: #00E676; font-weight: 700; font-size: 16px; letter-spacing: 0.5px;">RSI DIVERGENCE</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tombol Run & Stop dengan ukuran setara (1 : 1)
        col_btn_run, col_btn_stop = st.columns([1, 1])

        with col_btn_run:
            run_clicked = st.button("Run Screening", key="btn_run_rsi_screener", use_container_width=True, type="primary")

        with col_btn_stop:
            stop_clicked = st.button("🛑 Stop", key="btn_stop_rsi_screener", use_container_width=True)

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

            def fetch_rsi_with_retry(ticker, max_retries=2):
                if st.session_state.get("stop_rsi_scan", False):
                    return False, None
                for attempt in range(max_retries + 1):
                    try:
                        res = detect_rsi_patterns_and_score(ticker)
                        return True, res
                    except Exception:
                        if attempt < max_retries:
                            time.sleep(0.3 * (attempt + 1))
                        else:
                            return False, None

            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                future_to_ticker = {
                    executor.submit(fetch_rsi_with_retry, t): t for t in all_tickers
                }
                completed = 0

                for future in concurrent.futures.as_completed(future_to_ticker):
                    if st.session_state.get("stop_rsi_scan", False):
                        pstatus_rsi.warning("Screening process cancelled.")
                        break

                    completed += 1
                    pct = int((completed / total_tickers) * 100)
                    pbar_rsi.progress(pct)
                    pstatus_rsi.text(f"Scanning: {completed}/{total_tickers}")

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

            df_rsi_all = pd.DataFrame(results_rsi) if results_rsi else pd.DataFrame()

            if not df_rsi_all.empty and "Score" in df_rsi_all.columns:
                df_rsi_all = df_rsi_all.sort_values(by="Score", ascending=False)

            df_rsi_bullish = pd.DataFrame()
            df_rsi_bearish = pd.DataFrame()

            if not df_rsi_all.empty and "Pattern" in df_rsi_all.columns:
                df_rsi_bullish = df_rsi_all[
                    df_rsi_all["Pattern"].str.contains("Bullish", case=False, na=False)
                ]
                df_rsi_bearish = df_rsi_all[
                    df_rsi_all["Pattern"].str.contains("Bearish", case=False, na=False)
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

        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        # CONTAINER UNTUK HASIL SCREENING & TOMBOL SWITCH BULLISH/BEARISH
        with st.container(border=True):
            col_bull_btn, col_bear_btn = st.columns([1, 1])

            with col_bull_btn:
                btn_type_bull = "primary" if st.session_state["active_rsi_type"] == "bullish" else "secondary"
                if st.button("🟢 Bullish Divergence", key="btn_switch_bull", use_container_width=True, type=btn_type_bull):
                    st.session_state["active_rsi_type"] = "bullish"
                    st.rerun()

            with col_bear_btn:
                btn_type_bear = "primary" if st.session_state["active_rsi_type"] == "bearish" else "secondary"
                if st.button("🔴 Bearish Divergence", key="btn_switch_bear", use_container_width=True, type=btn_type_bear):
                    st.session_state["active_rsi_type"] = "bearish"
                    st.rerun()

            st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)

            # Tampilkan data berdasarkan tombol yang aktif
            if st.session_state["active_rsi_type"] == "bullish":
                if (
                    "df_rsi_bullish" in st.session_state
                    and not st.session_state["df_rsi_bullish"].empty
                ):
                    df_rsi_bullish = st.session_state["df_rsi_bullish"]
                    display_cols = [c for c in target_rsi_cols if c in df_rsi_bullish.columns]
                    df_display_bull = df_rsi_bullish[display_cols] if display_cols else df_rsi_bullish

                    event_bull = st.dataframe(
                        df_display_bull,
                        use_container_width=True,
                        column_config=column_configuration,
                        on_select="rerun",
                        selection_mode="single-row",
                        key="table_rsi_bullish",
                        height=460,
                        hide_index=True,
                    )
                    if event_bull.selection and event_bull.selection["rows"]:
                        idx = event_bull.selection["rows"][0]
                        selected_rsi_symbol = str(
                            df_rsi_bullish.iloc[idx].get(
                                "Ticker", df_rsi_bullish.iloc[idx].get("Saham")
                            )
                        )
                else:
                    st.info("No Bullish data available. Click **Run Screening** above.")

            else:  # Bearish
                if (
                    "df_rsi_bearish" in st.session_state
                    and not st.session_state["df_rsi_bearish"].empty
                ):
                    df_rsi_bearish = st.session_state["df_rsi_bearish"]
                    display_cols = [c for c in target_rsi_cols if c in df_rsi_bearish.columns]
                    df_display_bear = df_rsi_bearish[display_cols] if display_cols else df_rsi_bearish

                    event_bear = st.dataframe(
                        df_display_bear,
                        use_container_width=True,
                        column_config=column_configuration,
                        on_select="rerun",
                        selection_mode="single-row",
                        key="table_rsi_bearish",
                        height=460,
                        hide_index=True,
                    )
                    if event_bear.selection and event_bear.selection["rows"]:
                        idx = event_bear.selection["rows"][0]
                        selected_rsi_symbol = str(
                            df_rsi_bearish.iloc[idx].get(
                                "Ticker", df_rsi_bearish.iloc[idx].get("Saham")
                            )
                        )
                else:
                    st.info("No Bearish data available. Click **Run Screening** above.")

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
            st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

        if selected_rsi_symbol:
            if not selected_rsi_symbol.endswith(".JK") and "." not in selected_rsi_symbol:
                selected_rsi_symbol += ".JK"

            st.markdown(
                f"""
                <div style="background-color: #0D2B1D; border: 1.5px solid #00E676; padding: 10px 16px; border-radius: 8px; color: #FFFFFF; font-weight: 600; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center;">
                    <span>🎯 SELECTED SYMBOL: <strong style="color: #00E676; font-size: 16px; margin-left: 6px;">{selected_rsi_symbol}</strong></span>
                    <span style="color: #8B949E; font-size: 12px; font-weight: 400;">Interactive Analysis Workspace</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_inline_trade_planner(selected_rsi_symbol, key_suffix="rsi_tab")
        else:
            st.markdown(
                """
                <div class="empty-card">
                    <div style="font-size: 32px; margin-bottom: 10px;">👈</div>
                    <h3 style="color: #FFFFFF; font-size: 18px; margin-bottom: 6px;">Select a Stock from Left Panel</h3>
                    <p style="font-size: 13px; color: #8B949E; max-width: 440px; margin: 0 auto;">
                        Run the screening process, then select any stock row from the left table to inspect full Trade Planner details.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
