import pandas as pd
import streamlit as st
from ihsg_tickers import get_all_ihsg_tickers
from screener_stoch_psar import run_stoch_psar_screener
from utils.ui_helpers import render_inline_trade_planner


def render_tab_stoch_psar():
    # 🎨 STYLING MODERN DARK MODE
    st.markdown(
        """
        <style>
        .panel-header-center {
            background-color: #0D111A;
            border: 1px solid #1E2638;
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 12px;
            text-align: center;
        }
        .metric-card {
            background-color: #0D111A;
            border: 1px solid #1E2638;
            border-radius: 10px;
            padding: 10px;
            text-align: center;
        }
        .metric-value {
            font-size: 16px;
            font-weight: 700;
            color: #FFFFFF;
        }
        .metric-label {
            font-size: 10px;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .empty-card {
            background-color: #0D111A;
            border: 1px dashed #1E2638;
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            color: #94A3B8;
        }
        
        /* Input & Select Box Custom Styling */
        div[data-baseweb="select"] > div {
            background-color: #07090E !important;
            border: 1px solid #1E2638 !important;
            border-radius: 8px !important;
            color: #F8FAFC !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "stop_stoch_scan" not in st.session_state:
        st.session_state["stop_stoch_scan"] = False

    if "active_stoch_type" not in st.session_state:
        st.session_state["active_stoch_type"] = "Golden Cross (Beli)"

    if "selected_stoch_ticker" not in st.session_state:
        st.session_state["selected_stoch_ticker"] = None

    col_left, col_right = st.columns([1.3, 2.7], gap="medium")

    # =========================================================
    # PANEL KIRI: SCREENER CONTROL & DAFTAR SAHAM (CARD VIEW)
    # =========================================================
    with col_left:
        st.markdown(
            """
            <div class="panel-header-center">
                <div style="color: #10B981; font-weight: 800; font-size: 15px; letter-spacing: 0.5px;">⚡ STOCHASTIC & PARABOLIC SAR</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_btn_run, col_btn_stop = st.columns([1, 1])

        with col_btn_run:
            run_clicked = st.button(
                "🚀 Run Scan",
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

                if df_gc is not None and not df_gc.empty and "Score" in df_gc.columns:
                    df_gc = df_gc.sort_values(by="Score", ascending=False)
                if df_dc is not None and not df_dc.empty and "Score" in df_dc.columns:
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
                    st.session_state["selected_stoch_ticker"] = first_row.get("Ticker", "")
                elif df_dc is not None and not df_dc.empty:
                    first_row = df_dc.iloc[0]
                    st.session_state["selected_stoch_ticker"] = first_row.get("Ticker", "")

            except Exception as e:
                pbar_stoch.empty()
                pstatus_stoch.empty()
                st.error(f"Terjadi kesalahan: {e}")

        st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)

        has_results = "stoch_stats" in st.session_state

        if has_results:
            screener_mode = st.selectbox(
                "🎯 Choose Signal Mode:",
                options=["Golden Cross (Beli)", "Dead Cross (Jual)"],
                index=0
                if st.session_state.get("active_stoch_type") == "Golden Cross (Beli)"
                else 1,
                key="stoch_screener_mode_select",
            )
            st.session_state["active_stoch_type"] = screener_mode

            st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

            is_gc_tab = screener_mode == "Golden Cross (Beli)"
            df_target = (
                st.session_state.get("df_gc_data", pd.DataFrame())
                if is_gc_tab
                else st.session_state.get("df_dc_data", pd.DataFrame())
            )

            if not df_target.empty:
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

                    change_color = "#10B981" if change_pct >= 0 else "#EF4444"
                    change_icon = "📈" if change_pct >= 0 else "📉"
                    change_str = f"{change_icon} {change_pct:+.2f}%"
                    price_str = f"{int(close_price):,}"

                    # Styling Card Kotak Modern
                    border_style = (
                        "border: 1.5px solid #10B981; background-color: #0D2B1D; box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);"
                        if is_selected
                        else "border: 1px solid #1E2638; background-color: #111622;"
                    )

                    # --- HASIL SCREENER KOTAK-KOTAK (CARD) ---
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="{border_style} border-radius: 10px; padding: 12px 14px; margin-bottom: 6px; transition: all 0.2s ease;">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                    <div>
                                        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
                                            <span style="font-size: 1.1rem; font-weight: 800; color: #FFFFFF;">{saham}</span>
                                            <span style="background-color: rgba(139, 92, 246, 0.2); border: 1px solid #8B5CF6; color: #C084FC; font-size: 10px; padding: 1px 6px; border-radius: 4px; font-weight: 700;">⭐ {score}</span>
                                        </div>
                                        <div style="font-size: 11px; color: #94A3B8; font-weight: 500;">📌 {signal_desc}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 2px;">Rp {price_str}</div>
                                        <div style="font-size: 11px; font-weight: 700; color: {change_color};">{change_str}</div>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        btn_label = (
                            f"✓ Active Workspace ({saham})"
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
                            "<div style='margin-bottom: 12px;'></div>",
                            unsafe_allow_html=True,
                        )
            else:
                st.info(f"Tidak ada signal {screener_mode} yang terdeteksi.")
        else:
            st.info("Klik **🚀 Run Scan** di atas untuk mulai memindai pasar.")

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
                    f"""<div class="metric-card" style="border-color: #10B981;">
                        <div class="metric-label" style="color: #10B981;">Golden Cross</div>
                        <div class="metric-value" style="color: #10B981;">{stats['matched_gc']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m3:
                st.markdown(
                    f"""<div class="metric-card" style="border-color: #EF4444;">
                        <div class="metric-label" style="color: #EF4444;">Dead Cross</div>
                        <div class="metric-value" style="color: #EF4444;">{stats['matched_dc']}</div>
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
                "<div style='margin-bottom: 12px;'></div>",
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
                <div style="background-color: #0D2B1D; border: 1.5px solid #10B981; padding: 10px 16px; border-radius: 10px; color: #FFFFFF; font-weight: 600; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center;">
                    <span>🎯 SELECTED SYMBOL: <strong style="color: #10B981; font-size: 1.1rem; margin-left: 6px;">{selected_stoch_symbol}</strong></span>
                    <span style="color: #94A3B8; font-size: 12px; font-weight: 500;">Interactive Analysis Workspace</span>
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
                        f"Trade Plan rendered with partial data for {selected_stoch_symbol}."
                    )
                else:
                    st.error(
                        f"Failed to load Trade Plan for {selected_stoch_symbol}: {ke}"
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
                    <h3 style="color: #FFFFFF; font-size: 16px; margin-bottom: 4px;">Select a Stock Card from Left Panel</h3>
                    <p style="font-size: 12px; color: #94A3B8; max-width: 400px; margin: 0 auto;">
                        Run screening scan, then click any stock card from the left panel to display complete interactive Trade Plan details.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
