import pandas as pd
import streamlit as st
from ihsg_tickers import get_all_ihsg_tickers
from screener_stoch_psar import run_stoch_psar_screener
from utils.ui_helpers import render_inline_trade_planner


def render_tab_stoch_psar():
    # CSS Custom disamakan dengan tab_rsi
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

    # Inisialisasi Session State
    if "stop_stoch_scan" not in st.session_state:
        st.session_state["stop_stoch_scan"] = False

    if "active_stoch_type" not in st.session_state:
        st.session_state["active_stoch_type"] = "Golden Cross (Beli)"

    if "selected_stoch_ticker" not in st.session_state:
        st.session_state["selected_stoch_ticker"] = None

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
                <div style="color: #00E676; font-weight: 700; font-size: 15px; letter-spacing: 0.5px;">STOCHASTIC & PARABOLIC SAR</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_btn_run, col_btn_stop = st.columns([1, 1])

        with col_btn_run:
            run_clicked = st.button(
                "Run Screening",
                key="btn_run_stoch_screener",
                use_container_width=True,
                type="primary",
            )

        with col_btn_stop:
            stop_clicked = st.button(
                "🛑 Stop", key="btn_stop_stoch_screener", use_container_width=True
            )

        if stop_clicked:
            st.session_state["stop_stoch_scan"] = True

        if run_clicked:
            st.session_state["stop_stoch_scan"] = False
            with st.spinner("Fetching IHSG tickers list..."):
                all_stoch_tickers = get_all_ihsg_tickers()

            total_stoch_tickers = len(all_stoch_tickers)
            pbar_stoch = st.progress(0)
            pstatus_stoch = st.empty()

            def update_stoch_progress(current, total):
                if st.session_state.get("stop_stoch_scan", False):
                    pstatus_stoch.warning("Screening cancelled.")
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

                # Auto-select saham paling atas
                if df_gc is not None and not df_gc.empty:
                    first_row = df_gc.iloc[0]
                    st.session_state["selected_stoch_ticker"] = first_row.get(
                        "Ticker", first_row.get("Saham", first_row.get("Symbol", ""))
                    )
                elif df_dc is not None and not df_dc.empty:
                    first_row = df_dc.iloc[0]
                    st.session_state["selected_stoch_ticker"] = first_row.get(
                        "Ticker", first_row.get("Saham", first_row.get("Symbol", ""))
                    )

            except Exception as e:
                pbar_stoch.empty()
                pstatus_stoch.empty()
                st.error(f"Terjadi kesalahan: {e}")

        st.markdown(
            "<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True
        )

        has_results = "stoch_stats" in st.session_state

        if has_results:
            screener_mode = st.selectbox(
                "Choose Signal Mode",
                options=["Golden Cross (Beli)", "Dead Cross (Jual)"],
                index=0
                if st.session_state.get("active_stoch_type")
                == "Golden Cross (Beli)"
                else 1,
                key="stoch_screener_mode_select",
            )
            st.session_state["active_stoch_type"] = screener_mode

            st.markdown(
                "<div style='margin-bottom: 6px;'></div>",
                unsafe_allow_html=True,
            )

            is_gc_tab = screener_mode == "Golden Cross (Beli)"
            df_target = (
                st.session_state.get("df_gc_data", pd.DataFrame())
                if is_gc_tab
                else st.session_state.get("df_dc_data", pd.DataFrame())
            )

            if not df_target.empty:
                for idx, row in df_target.iterrows():
                    # 1. Ambil Nama Ticker & Saham
                    ticker = str(
                        row.get("Ticker", row.get("Saham", row.get("Symbol", row.get("Stock", ""))))
                    )
                    saham = str(row.get("Saham", ticker.replace(".JK", "")))
                    score = row.get("Score", row.get("Skor", 0))

                    # 2. Ambil Harga Close
                    close_price = row.get("Close", row.get("Harga", row.get("Close_Price", 0)))
                    try:
                        close_price = float(close_price)
                        price_str = f"Rp {close_price:,.0f}".replace(",", ".")
                    except (ValueError, TypeError):
                        price_str = f"Rp {close_price}"

                    # 3. Ambil Indikator Khas Stoch & PSAR (K%, D%, PSAR, Status)
                    stoch_k = row.get("Stoch %K", row.get("%K", row.get("K", "-")))
                    stoch_d = row.get("Stoch %D", row.get("%D", row.get("D", "-")))
                    psar_val = row.get("PSAR", row.get("Parabolic SAR", "-"))
                    status_val = row.get("Status", row.get("Signal", row.get("Action", "-")))

                    # Format string indikator
                    if isinstance(stoch_k, (int, float)) and isinstance(stoch_d, (int, float)):
                        stoch_str = f"%K: {stoch_k:.1f} | %D: {stoch_d:.1f}"
                    else:
                        stoch_str = f"%K: {stoch_k} | %D: {stoch_d}"

                    if isinstance(psar_val, (int, float)):
                        psar_str = f"PSAR: {psar_val:,.0f}".replace(",", ".")
                    else:
                        psar_str = f"PSAR: {psar_val}"

                    # Selection State
                    is_selected = (
                        st.session_state.get("selected_stoch_ticker") == ticker
                    )

                    border_style = (
                        "border: 1.5px solid #00E676; background-color: #0D2B1D;"
                        if is_selected
                        else "border: 1px solid #30363D; background-color: #161B22;"
                    )

                    # Badge Status Warna
                    status_color = "#00E676" if is_gc_tab else "#FF5252"

                    # 4. Rendering Kartu Saham dengan Semua Informasi Table
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="{border_style} border-radius: 8px; padding: 10px 12px; margin-bottom: 4px;">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                    <div>
                                        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
                                            <span style="font-size: 15px; font-weight: 800; color: #FFFFFF;">{saham}</span>
                                            <span style="background-color: #21262D; border: 1px solid #30363D; color: #E6BDFB; font-size: 10px; padding: 1px 5px; border-radius: 4px; font-weight: 600;">⭐ {score}</span>
                                        </div>
                                        <div style="font-size: 11px; color: #8B949E; margin-bottom: 2px;">📊 {stoch_str}</div>
                                        <div style="font-size: 10px; color: #6E7681;">📍 {psar_str}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 15px; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;">{price_str}</div>
                                        <div style="font-size: 10px; font-weight: 700; color: {status_color}; background-color: #21262D; padding: 2px 6px; border-radius: 4px; display: inline-block;">{status_val}</div>
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
                st.info(f"Tidak ada signal {screener_mode} yang terdeteksi.")
        else:
            st.info(
                "Klik **Run Screening** di atas untuk mulai memindai pasar."
            )

    # =========================================================
    # PANEL KANAN: WORKSPACE & LIVE TRADE PLANNER
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
                    f"""<div class="metric-card" style="border-color: #00E676;">
                        <div class="metric-label" style="color: #00E676;">Golden Cross</div>
                        <div class="metric-value" style="color: #00E676;">{stats['matched_gc']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m3:
                st.markdown(
                    f"""<div class="metric-card" style="border-color: #FF5252;">
                        <div class="metric-label" style="color: #FF5252;">Dead Cross</div>
                        <div class="metric-value" style="color: #FF5252;">{stats['matched_dc']}</div>
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
                <div style="background-color: #0D2B1D; border: 1.5px solid #00E676; padding: 8px 14px; border-radius: 8px; color: #FFFFFF; font-weight: 600; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                    <span>🎯 SELECTED SYMBOL: <strong style="color: #00E676; font-size: 15px; margin-left: 6px;">{selected_stoch_symbol}</strong></span>
                    <span style="color: #8B949E; font-size: 11px; font-weight: 400;">Interactive Analysis Workspace</span>
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
                    <div style="font-size: 28px; margin-bottom: 8px;">👈</div>
                    <h3 style="color: #FFFFFF; font-size: 16px; margin-bottom: 4px;">Select a Stock from Left Panel</h3>
                    <p style="font-size: 12px; color: #8B949E; max-width: 400px; margin: 0 auto;">
                        Run the screening process, then click any stock card from the left panel to inspect full Trade Planner details.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
