import concurrent.futures
import time
import pandas as pd
import streamlit as st
from ihsg_tickers import get_all_ihsg_tickers
from screener_rsi_divergence import detect_rsi_patterns_and_score
from utils.ui_helpers import render_inline_trade_planner


def shorten_pattern(pattern_name):
    """Menyingkat nama pattern agar rapi."""
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
    res = res.replace(" Valid", "")
    return res


def render_tab_rsi():
    # CSS Custom untuk Menyulap st.button Menjadi Card Sesuai Gambar
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

        /* STYLING UTAMA: MENGUBAH ST.BUTTON MENJADI CARD DENGAN KANAN-KIRI LAYOUT */
        div[data-testid="stColumn"] div.stButton > button {
            text-align: left !important;
            padding: 10px 14px !important;
            border-radius: 10px !important;
            min-height: 80px !important;
            margin-bottom: 6px !important;
        }

        /* Format Teks Didalam Tombol Kartu */
        .card-inner-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
        }
        .card-left-side {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .card-right-side {
            text-align: right;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .card-ticker-title {
            font-size: 15px;
            font-weight: 800;
            color: #FFFFFF;
        }
        .card-badge-score {
            font-size: 10px;
            background-color: #21262D;
            border: 1px solid #30363D;
            color: #E6BDFB;
            padding: 1px 5px;
            border-radius: 4px;
            margin-left: 6px;
        }
        .card-pattern-text {
            font-size: 11px;
            color: #8B949E;
        }
        .card-date-text {
            font-size: 10px;
            color: #6E7681;
        }
        .card-price-value {
            font-size: 16px;
            font-weight: 700;
            color: #FFFFFF;
        }
        .card-change-pos {
            font-size: 11px;
            font-weight: 600;
            color: #00E676;
        }
        .card-change-neg {
            font-size: 11px;
            font-weight: 600;
            color: #FF5252;
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
    # PANEL KIRI: SCREENER CONTROL & DAFTAR SAHAM (CARD VIEW)
    # =========================================================
    with col_left:
        # Header Center
        st.markdown(
            """
            <div class="panel-header-center">
                <div style="color: #00E676; font-weight: 700; font-size: 15px; letter-spacing: 0.5px;">RSI DIVERGENCE</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tombol Run & Stop
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
                    executor.submit(fetch_rsi_with_retry, t): t
                    for t in all_tickers
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

            df_rsi_all = (
                pd.DataFrame(results_rsi) if results_rsi else pd.DataFrame()
            )

            if not df_rsi_all.empty and "Score" in df_rsi_all.columns:
                df_rsi_all = df_rsi_all.sort_values(by="Score", ascending=False)

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

            # Default selection
            if not df_rsi_bullish.empty:
                st.session_state["selected_rsi_ticker"] = df_rsi_bullish.iloc[0].get("Ticker", df_rsi_bullish.iloc[0].get("Saham"))
            elif not df_rsi_bearish.empty:
                st.session_state["selected_rsi_ticker"] = df_rsi_bearish.iloc[0].get("Ticker", df_rsi_bearish.iloc[0].get("Saham"))

        st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)

        has_results = "rsi_stats" in st.session_state

        if has_results:
            screener_mode = st.selectbox(
                "Choose Screener Mode",
                options=["Bullish", "Bearish"],
                index=0 if st.session_state.get("active_rsi_type") == "Bullish" else 1,
                key="rsi_screener_mode_select",
            )
            st.session_state["active_rsi_type"] = screener_mode

            st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)

            is_bull_tab = screener_mode == "Bullish"
            df_target = (
                st.session_state.get("df_rsi_bullish", pd.DataFrame())
                if is_bull_tab
                else st.session_state.get("df_rsi_bearish", pd.DataFrame())
            )

            if not df_target.empty:
                for idx, row in df_target.iterrows():
                    ticker = row.get("Ticker", row.get("Saham"))
                    saham = row.get("Saham", ticker.replace(".JK", ""))
                    score = row.get("Score", 0)
                    pattern_raw = row.get("Pattern", "-")
                    pattern_short = shorten_pattern(pattern_raw)
                    
                    close_price = row.get("Close_Price", 0)
                    change_pct = row.get("Change_Pct", 0.0)

                    tgl_kiri = str(row.get("Tgl Kiri", "-"))
                    tgl_kanan = str(row.get("Tgl Kanan", "-"))

                    is_selected = (st.session_state.get("selected_rsi_ticker") == ticker)

                    change_class = "card-change-pos" if change_pct >= 0 else "card-change-neg"
                    change_icon = "📈" if change_pct >= 0 else "📉"
                    change_str = f"{change_icon} {change_pct:+.2f}%"
                    price_str = f"{close_price:,.0f}".replace(",", ".")

                    # MEMBUAT SATU KARTU UTUH DALAM 1 ST.BUTTON TANPA TOMBOL "SELECT" TERPISAH
                    # Teks diformat menjadi HTML yang disuntikkan langsung ke tombol
                    button_html_label = f"""
                    <div class="card-inner-container">
                        <div class="card-left-side">
                            <div>
                                <span class="card-ticker-title">{saham}</span>
                                <span class="card-badge-score">⭐ {score}</span>
                            </div>
                            <div class="card-pattern-text">📌 {pattern_short}</div>
                            <div class="card-date-text">🗓️ {tgl_kiri} ➔ {tgl_kanan}</div>
                        </div>
                        <div class="card-right-side">
                            <div class="card-price-value">{price_str}</div>
                            <div class="{change_class}">{change_str}</div>
                        </div>
                    </div>
                    """

                    # Jika dipilih, tombol diberi tipe 'primary' (berwarna hijau highlight)
                    btn_type = "primary" if is_selected else "secondary"

                    if st.button(
                        button_html_label,
                        key=f"card_btn_{ticker}_{idx}",
                        use_container_width=True,
                        type=btn_type,
                    ):
                        st.session_state["selected_rsi_ticker"] = ticker
                        st.rerun()

            else:
                st.info(f"No {screener_mode} patterns detected.")
        else:
            st.info("Click **Run Screening** above to start scanning the market.")

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
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

        selected_rsi_symbol = st.session_state.get("selected_rsi_ticker")

        if selected_rsi_symbol:
            if not selected_rsi_symbol.endswith(".JK") and "." not in selected_rsi_symbol:
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
                render_inline_trade_planner(selected_rsi_symbol, key_suffix="rsi_tab")
            except KeyError as ke:
                if "Status Candle" in str(ke):
                    st.warning(f"Trade Plan rendered with partial data for {selected_rsi_symbol}.")
                else:
                    st.error(f"Failed to load Trade Plan for {selected_rsi_symbol}: {ke}")
            except Exception as e:
                st.error(f"Failed to load Trade Plan for {selected_rsi_symbol}: {e}")
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
