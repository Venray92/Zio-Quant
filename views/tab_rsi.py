import concurrent.futures
import time
import pandas as pd
import streamlit as st
from ihsg_tickers import get_all_ihsg_tickers
from screener_rsi_divergence import detect_rsi_patterns_and_score
from utils.ui_helpers import render_inline_trade_planner


def render_tab_rsi():
    # Overhead Styling untuk layout terpisah & komponen yang rapat
    st.markdown(
        """
        <style>
        .panel-box {
            background-color: #161B22;
            border: 1px solid #21262D;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 12px;
        }
        .empty-card {
            background-color: #161B22;
            border: 1px dashed #30363D;
            border-radius: 8px;
            padding: 40px 15px;
            text-align: center;
            color: #8B949E;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------
    # LAYOUT UTAMA: SPLIT SCREEN (KIRI 30% : KANAN 70%)
    # ---------------------------------------------------------
    col_left, col_right = st.columns([1.1, 2.9], gap="medium")

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

    # =========================================================
    # PANEL KIRI: SCREENER CONTROL & DAFTAR SAHAM
    # =========================================================
    with col_left:
        st.markdown(
            """
            <div class="panel-box">
                <span style="color: #00E676; font-weight: 700; font-size: 15px;">🔄 RSI Divergence Screener</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # LOGIKA ASLI: Tombol Jalankan Screener RSI
        if st.button("🚀 Jalankan Screener RSI", key="btn_rsi", use_container_width=True):
            with st.spinner("Mengambil daftar lengkap saham IHSG..."):
                all_tickers = get_all_ihsg_tickers()

            total_tickers = len(all_tickers)
            pbar_rsi = st.progress(0)
            pstatus_rsi = st.empty()

            results_rsi = []
            success_count = 0
            failed_count = 0

            # LOGIKA ASLI: Multi-threading & retry fetch
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

            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                future_to_ticker = {
                    executor.submit(fetch_rsi_with_retry, t): t for t in all_tickers
                }
                completed = 0

                for future in concurrent.futures.as_completed(future_to_ticker):
                    completed += 1
                    pct = int((completed / total_tickers) * 100)
                    pbar_rsi.progress(pct)
                    pstatus_rsi.text(f"Scan RSI: {completed}/{total_tickers}")

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

        # LOGIKA ASLI: Sub Tab untuk memisah Bullish & Bearish di panel kiri
        sub_tab_bull, sub_tab_bear = st.tabs(["🟢 Bullish", "🔴 Bearish"])

        with sub_tab_bull:
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
                    on_select="rerun",
                    selection_mode="single-row",
                    key="table_rsi_bullish",
                    height=500,
                )
                if event_bull.selection and event_bull.selection["rows"]:
                    idx = event_bull.selection["rows"][0]
                    selected_rsi_symbol = str(
                        df_rsi_bullish.iloc[idx].get(
                            "Ticker", df_rsi_bullish.iloc[idx].get("Saham")
                        )
                    )
            else:
                st.caption("Belum ada data / Klik 'Jalankan Screener RSI'")

        with sub_tab_bear:
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
                    on_select="rerun",
                    selection_mode="single-row",
                    key="table_rsi_bearish",
                    height=500,
                )
                if event_bear.selection and event_bear.selection["rows"]:
                    idx = event_bear.selection["rows"][0]
                    selected_rsi_symbol = str(
                        df_rsi_bearish.iloc[idx].get(
                            "Ticker", df_rsi_bearish.iloc[idx].get("Saham")
                        )
                    )
            else:
                st.caption("Belum ada data / Klik 'Jalankan Screener RSI'")

    # =========================================================
    # PANEL KANAN: WORKSPACE & LIVE TRADE PLANNER
    # =========================================================
    with col_right:
        # LOGIKA ASLI: Menampilkan Ringkasan Stats di bagian atas panel kanan
        if "rsi_stats" in st.session_state:
            stats = st.session_state["rsi_stats"]
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Total Scan", f"{stats['total']}")
            col_m2.metric("Bullish", f"{stats['bullish_count']}")
            col_m3.metric("Bearish", f"{stats['bearish_count']}")
            col_m4.metric("Total Sinyal", f"{stats['matched']}")

        # LOGIKA ASLI: Jika saham diklik, tampilkan Trade Planner
        if selected_rsi_symbol:
            if not selected_rsi_symbol.endswith(".JK") and "." not in selected_rsi_symbol:
                selected_rsi_symbol += ".JK"
            
            # Header Informasi Saham Terpilih
            st.markdown(
                f"""
                <div style="background-color: #0D2B1D; border: 1px solid #00E676; padding: 10px 16px; border-radius: 6px; color: #00E676; font-weight: 600; margin-top: 10px;">
                    🎯 TERPILIH: <strong>{selected_rsi_symbol}</strong> — Memuat Analisis Trade Planner...
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_inline_trade_planner(selected_rsi_symbol, key_suffix="rsi_tab")
        else:
            # Workspace Kosong jika Belum Diklik
            st.markdown(
                """
                <div class="empty-card" style="margin-top: 15px;">
                    <h3 style="color: #C9D1D9; margin-bottom: 8px;">👈 Pilih Saham di Panel Kiri</h3>
                    <p>Jalankan scan RSI, lalu klik salah satu baris saham pada tabel di sebelah kiri untuk melihat analisis Trade Plan secara detail di sini.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
