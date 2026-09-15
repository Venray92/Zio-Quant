import streamlit as st
from ihsg_tickers import get_all_ihsg_tickers
from screener_stoch_psar import run_stoch_psar_screener
from utils.ui_helpers import render_inline_trade_planner


def render_tab_stoch_psar():
    st.header("Screener Stochastic & Parabolic SAR")
    st.caption(
        "Klik pada baris saham di tabel Golden Cross/Dead Cross untuk melihat"
        " Trade Planner secara otomatis."
    )

    if st.button("Jalankan Screener Stoch & PSAR", key="btn_stoch"):
        with st.spinner("Mengambil daftar lengkap saham IHSG..."):
            all_stoch_tickers = get_all_ihsg_tickers()

        total_stoch_tickers = len(all_stoch_tickers)
        st.info(f"Menganalisis {total_stoch_tickers} ticker saham IHSG...")

        pbar_stoch = st.progress(0)
        pstatus_stoch = st.empty()

        def update_stoch_progress(current, total):
            pct = current / total
            pbar_stoch.progress(pct)
            pstatus_stoch.text(
                f"Menganalisis Stoch & PSAR: {current}/{total} saham..."
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

            st.session_state["df_gc_data"] = df_gc
            st.session_state["df_dc_data"] = df_dc

            gc_len = len(df_gc) if df_gc is not None else 0
            dc_len = len(df_dc) if df_dc is not None else 0

            st.session_state["stoch_stats"] = {
                "total": total_stoch_tickers,
                "matched_gc": gc_len,
                "matched_dc": dc_len,
                "total_signal": gc_len + dc_len,
            }

            st.success("Screening Stochastic & Parabolic SAR Selesai!")
        except Exception as e:
            pbar_stoch.empty()
            pstatus_stoch.empty()
            st.error(f"Terjadi kesalahan: {e}")

    if "stoch_stats" in st.session_state:
        st_stats = st.session_state["stoch_stats"]
        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        c_m1.metric("Total Ticker Di-scan", f"{st_stats['total']} Saham")
        c_m2.metric(
            "Sinyal Beli (Golden Cross)", f"{st_stats['matched_gc']} Saham"
        )
        c_m3.metric(
            "Sinyal Jual (Dead Cross)", f"{st_stats['matched_dc']} Saham"
        )
        c_m4.metric(
            "Total Sinyal Terdeteksi", f"{st_stats['total_signal']} Saham"
        )

    col_gc, col_dc = st.columns(2)
    selected_stoch_symbol = None

    with col_gc:
        st.subheader("🟢 Signal Beli (Golden Cross)")
        if (
            "df_gc_data" in st.session_state
            and not st.session_state["df_gc_data"].empty
        ):
            df_gc = st.session_state["df_gc_data"]

            df_gc_display = (
                df_gc.drop(columns=["Action"], errors="ignore")
                if "Action" in df_gc.columns
                else df_gc
            )

            event_gc = st.dataframe(
                df_gc_display,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key="table_gc",
            )
            if event_gc.selection and event_gc.selection["rows"]:
                idx = event_gc.selection["rows"][0]
                ticker_col = next(
                    (
                        c
                        for c in ["Ticker", "Saham", "Stock", "Symbol"]
                        if c in df_gc.columns
                    ),
                    None,
                )
                if ticker_col:
                    selected_stoch_symbol = str(df_gc.iloc[idx][ticker_col])
        else:
            st.info("Tidak ada data / Belum di-scan.")

    with col_dc:
        st.subheader("🔴 Signal Jual (Dead Cross)")
        if (
            "df_dc_data" in st.session_state
            and not st.session_state["df_dc_data"].empty
        ):
            df_dc = st.session_state["df_dc_data"]

            df_dc_display = (
                df_dc.drop(columns=["Action"], errors="ignore")
                if "Action" in df_dc.columns
                else df_dc
            )

            event_dc = st.dataframe(
                df_dc_display,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key="table_dc",
            )
            if event_dc.selection and event_dc.selection["rows"]:
                idx = event_dc.selection["rows"][0]
                ticker_col = next(
                    (
                        c
                        for c in ["Ticker", "Saham", "Stock", "Symbol"]
                        if c in df_dc.columns
                    ),
                    None,
                )
                if ticker_col:
                    selected_stoch_symbol = str(df_dc.iloc[idx][ticker_col])
        else:
            st.info("Tidak ada data / Belum di-scan.")

    if selected_stoch_symbol:
        if (
            not selected_stoch_symbol.endswith(".JK")
            and "." not in selected_stoch_symbol
        ):
            selected_stoch_symbol += ".JK"
        render_inline_trade_planner(
            selected_stoch_symbol, key_suffix="stoch_tab"
        )