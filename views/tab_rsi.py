import os
import sys

# Menambahkan root directory ke Python path agar modul utama dapat di-import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Impor modul screener setelah mengatur sys.path
from screener_rsi_divergence import detect_rsi_patterns_and_score

import concurrent.futures
import time
import pandas as pd
import streamlit as st
from ihsg_tickers import get_all_ihsg_tickers
from screener_rsi_divergence import detect_rsi_patterns_and_score
from utils.ui_helpers import render_inline_trade_planner


def render_tab_rsi():
    st.header("Screener RSI Divergence & Technical Patterns")
    st.caption(
        "Screening seluruh saham IHSG yang sedang membentuk Divergence Bullish"
        " maupun Bearish beserta penilaiannya (Score)."
    )

    if st.button("Jalankan Screener RSI (Full IHSG)", key="btn_rsi"):
        with st.spinner("Mengambil daftar lengkap saham IHSG..."):
            all_tickers = get_all_ihsg_tickers()

        total_tickers = len(all_tickers)
        st.info(f"Menganalisis {total_tickers} ticker saham IHSG...")

        pbar_rsi = st.progress(0)
        pstatus_rsi = st.empty()

        results_rsi = []
        success_count = 0
        failed_count = 0

        def fetch_rsi_with_retry(ticker, max_retries=2):
            for attempt in range(max_retries + 1):
                try:
                    res = detect_rsi_patterns_and_score(ticker)
                    return True, res
                except Exception:
                    if attempt < max_retries:
                        time.sleep(0.5 * (attempt + 1))
                    else:
                        return False, None

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=6
        ) as executor:
            future_to_ticker = {
                executor.submit(fetch_rsi_with_retry, t): t for t in all_tickers
            }
            completed = 0

            for future in concurrent.futures.as_completed(future_to_ticker):
                completed += 1
                pct = int((completed / total_tickers) * 100)
                pbar_rsi.progress(pct)
                pstatus_rsi.text(
                    f"Menganalisis RSI: {completed}/{total_tickers} saham..."
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

    if "rsi_stats" in st.session_state:
        stats = st.session_state["rsi_stats"]
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total Ticker Di-scan", f"{stats['total']} Saham")
        col_m2.metric("Sinyal Bullish", f"{stats['bullish_count']} Saham")
        col_m3.metric("Sinyal Bearish", f"{stats['bearish_count']} Saham")
        col_m4.metric("Total Sinyal RSI", f"{stats['matched']} Saham")

        if stats["failed"] > 0:
            st.warning(
                f"⚠️ Terdapat **{stats['failed']} saham** gagal didownload dari"
                " Yahoo Finance."
            )

    col_bull, col_bear = st.columns(2)
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

    with col_bull:
        st.subheader("🟢 Signal Bullish (Divergence)")
        if (
            "df_rsi_bullish" in st.session_state
            and not st.session_state["df_rsi_bullish"].empty
        ):
            df_rsi_bullish = st.session_state["df_rsi_bullish"]

            display_cols = [
                c for c in target_rsi_cols if c in df_rsi_bullish.columns
            ]
            df_display_bull = (
                df_rsi_bullish[display_cols]
                if display_cols
                else df_rsi_bullish
            )

            event_bull = st.dataframe(
                df_display_bull,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key="table_rsi_bullish",
            )
            if event_bull.selection and event_bull.selection["rows"]:
                idx = event_bull.selection["rows"][0]
                selected_rsi_symbol = str(
                    df_rsi_bullish.iloc[idx].get(
                        "Ticker", df_rsi_bullish.iloc[idx].get("Saham")
                    )
                )
        else:
            st.info("Tidak ada sinyal Bullish / Belum di-scan.")

    with col_bear:
        st.subheader("🔴 Signal Bearish (Divergence)")
        if (
            "df_rsi_bearish" in st.session_state
            and not st.session_state["df_rsi_bearish"].empty
        ):
            df_rsi_bearish = st.session_state["df_rsi_bearish"]

            display_cols = [
                c for c in target_rsi_cols if c in df_rsi_bearish.columns
            ]
            df_display_bear = (
                df_rsi_bearish[display_cols]
                if display_cols
                else df_rsi_bearish
            )

            event_bear = st.dataframe(
                df_display_bear,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key="table_rsi_bearish",
            )
            if event_bear.selection and event_bear.selection["rows"]:
                idx = event_bear.selection["rows"][0]
                selected_rsi_symbol = str(
                    df_rsi_bearish.iloc[idx].get(
                        "Ticker", df_rsi_bearish.iloc[idx].get("Saham")
                    )
                )
        else:
            st.info("Tidak ada sinyal Bearish / Belum di-scan.")

    if selected_rsi_symbol:
        if (
            not selected_rsi_symbol.endswith(".JK")
            and "." not in selected_rsi_symbol
        ):
            selected_rsi_symbol += ".JK"
        render_inline_trade_planner(selected_rsi_symbol, key_suffix="rsi_tab")
