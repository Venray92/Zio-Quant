import concurrent.futures
import time
import pandas as pd
import streamlit as st
from ihsg_tickers import get_all_ihsg_tickers
from screener_rsi_divergence import detect_rsi_patterns_and_score
from utils.ui_helpers import render_inline_trade_planner


def render_tab_rsi():
    # Styling CSS Rapi, Kompak, & Sleek
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

        /* Custom Card Button Styling */
        div.stButton > button[key^="card_btn_"] {
            width: 100%;
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 8px 10px;
            text-align: left;
            margin-bottom: 8px;
            transition: all 0.2s ease-in-out;
            height: auto !important;
        }
        div.stButton > button[key^="card_btn_"]:hover {
            border-color: #58A6FF !important;
            background-color: #1F242C;
        }
        div.stButton > button[key^="card_btn_selected"] {
            width: 100%;
            background-color: #0D1117;
            border: 1.5px solid #238636 !important;
            border-radius: 8px;
            padding: 8px 10px;
            text-align: left;
            margin-bottom: 8px;
            height: auto !important;
        }

        /* Card Elements */
        .card-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
        }
        .ticker-symbol {
            font-size: 14px;
            font-weight: 700;
            color: #FFFFFF;
        }
        .price-tag {
            font-size: 13px;
            font-weight: 600;
            color: #C9D1D9;
        }
        .change-badge-green {
            color: #3FB950;
            font-weight: 600;
            font-size: 11px;
            margin-left: 4px;
        }
        .change-badge-red {
            color: #F85149;
            font-weight: 600;
            font-size: 11px;
            margin-left: 4px;
        }
        .pattern-badge-bull {
            background-color: rgba(46, 160, 67, 0.15);
            color: #3FB950;
            border: 1px solid rgba(46, 160, 67, 0.3);
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 10px;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 200px;
        }
        .pattern-badge-bear {
            background-color: rgba(248, 81, 73, 0.15);
            color: #F85149;
            border: 1px solid rgba(248, 81, 73, 0.3);
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 10px;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 200px;
        }
        .card-details-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4px;
            background-color: #0D1117;
            border-radius: 5px;
            padding: 5px 8px;
            margin-top: 6px;
            font-size: 10px;
            width: 100%;
        }
        .detail-item-title {
            color: #8B949E;
            font-weight: 500;
        }
        .detail-item-val {
            color: #C9D1D9;
            font-weight: 600;
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
    # LAYOUT UTAMA: SPLIT SCREEN (KIRI 32% : KANAN 68%)
    # ---------------------------------------------------------
    col_left, col_right = st.columns([1.15, 2.85], gap="medium")

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

        # Tombol Run & Stop dengan ukuran setara (1 : 1)
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

            # Set default selected ticker jika ada hasil
            if not df_rsi_bullish.empty:
                st.session_state["selected_rsi_ticker"] = df_rsi_bullish.iloc[0].get("Ticker", df_rsi_bullish.iloc[0].get("Saham"))
            elif not df_rsi_bearish.empty:
                st.session_state["selected_rsi_ticker"] = df_rsi_bearish.iloc[0].get("Ticker", df_rsi_bearish.iloc[0].get("Saham"))

        st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)

        has_results = "rsi_stats" in st.session_state

        if has_results:
            with st.container(border=True):
                # REVISI 3: Dropdown "Choose Screener Mode" (Default Bullish)
                screener_mode = st.selectbox(
                    "Choose Screener Mode",
                    options=["Bullish", "Bearish"],
                    index=0 if st.session_state.get("active_rsi_type") == "Bullish" else 1,
                    key="rsi_screener_mode_select",
                )
                st.session_state["active_rsi_type"] = screener_mode

                st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

                is_bull_tab = screener_mode == "Bullish"
                if is_bull_tab:
                    df_target = st.session_state.get("df_rsi_bullish", pd.DataFrame())
                else:
                    df_target = st.session_state.get("df_rsi_bearish", pd.DataFrame())

                if not df_target.empty:
                    # Rendering Compact Card untuk Setiap Ticker
                    for idx, row in df_target.iterrows():
                        ticker = row.get("Ticker", row.get("Saham"))
                        saham = row.get("Saham", ticker.replace(".JK", ""))
                        score = row.get("Score", 0)
                        pattern = row.get("Pattern", "-")
                        close_price = row.get("Close_Price", 0)
                        change_pct = row.get("Change_Pct", 0.0)

                        tgl_kiri = row.get("Tgl Kiri", "-")
                        harga_kiri = row.get("Harga Kiri", "-")
                        rsi_kiri = row.get("RSI Kiri", 0.0)

                        tgl_kanan = row.get("Tgl Kanan", "-")
                        harga_kanan = row.get("Harga Kanan", "-")
                        rsi_kanan = row.get("RSI Kanan", 0.0)

                        is_selected = (st.session_state.get("selected_rsi_ticker") == ticker)

                        badge_style = "pattern-badge-bull" if is_bull_tab else "pattern-badge-bear"
                        
                        if change_pct >= 0:
                            change_html = f'<span class="change-badge-green">+{change_pct:.2f}%</span>'
                        else:
                            change_html = f'<span class="change-badge-red">{change_pct:.2f}%</span>'

                        price_str = f"Rp {close_price:,.0f}" if close_price > 0 else "-"

                        # REVISI 1 & 2: Seluruh Kartu Menjadi 1 Tombol Interaktif Ringkas
                        btn_key_prefix = "card_btn_selected" if is_selected else "card_btn"
                        
                        # Format Konten Tampilan dalam Button
                        card_content = f"""
                        <div style="width: 100%;">
                            <div class="card-header-row">
                                <div>
                                    <span class="ticker-symbol">{saham}</span>
                                    {change_html}
                                </div>
                                <div class="price-tag">{price_str}</div>
                            </div>
                            <div class="card-header-row" style="margin-top: 3px;">
                                <div class="{badge_style}" title="{pattern}">{pattern}</div>
                                <div style="font-size: 11px; font-weight: 700; color: #E3B341;">⭐ {score}</div>
                            </div>
                            <div class="card-details-grid">
                                <div>
                                    <div class="detail-item-title">Kiri ({tgl_kiri})</div>
                                    <div class="detail-item-val">{harga_kiri} | RSI: {rsi_kiri}</div>
                                </div>
                                <div>
                                    <div class="detail-item-title">Kanan ({tgl_kanan})</div>
                                    <div class="detail-item-val">{harga_kanan} | RSI: {rsi_kanan}</div>
                                </div>
                            </div>
                        </div>
                        """

                        if st.button(
                            card_content,
                            key=f"{btn_key_prefix}_{ticker}_{idx}",
                            use_container_width=True,
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

            # SAFE RENDERING: Mencegah crash jika key 'Status Candle' missing
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
