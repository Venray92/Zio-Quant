import concurrent.futures
import pandas as pd
import streamlit as st
from trade_planner import TradePlanner
from utils.ui_helpers import load_daftar_saham, render_inline_trade_planner


def render_tab_trade_planner():
    st.header("🎯 Trade Planner & Multi-Category Batch Screener")

    planner_mode = st.radio(
        "Pilih Mode Analisis:",
        ["🔍 Manual Single Input", "⚡ Batch Screener (daftar_saham.txt)"],
        horizontal=True,
    )

    if planner_mode == "🔍 Manual Single Input":
        st.caption("Cari Trade Plan saham pilihan secara manual.")
        col_input1, col_input2 = st.columns([2, 1])
        with col_input1:
            ticker_input = st.text_input(
                "Masukkan Kode Saham (Contoh: BBCA, ASII, BBRI)",
                value="",
                key="manual_ticker_input",
                placeholder="Ketik kode saham...",
            )
        with col_input2:
            period_input = st.selectbox(
                "Pilih Periode Data",
                options=["3mo", "6mo", "1y", "2y"],
                index=0,
                key="manual_period_input",
            )

        if st.button("Generate Trade Plan", key="btn_planner_manual"):
            if ticker_input.strip() == "":
                st.warning("⚠️ Mohon masukkan kode saham terlebih dahulu.")
            else:
                clean_ticker = ticker_input.strip().upper()
                if not clean_ticker.endswith(".JK") and "." not in clean_ticker:
                    clean_ticker += ".JK"
                render_inline_trade_planner(
                    clean_ticker, key_suffix="manual_tab"
                )

    else:  # BATCH SCREENER
        st.caption(
            "Screening otomatis seluruh saham di `daftar_saham.txt` berdasarkan"
            " Status Candle, Support/Resistance, Score, dan Warning."
        )

        batch_period = st.selectbox(
            "Pilih Periode Analysis Batch",
            options=["3mo", "6mo", "1y"],
            index=0,
            key="batch_period_select",
        )

        if st.button(
            "🚀 Run Batch Screener (daftar_saham.txt)", key="btn_run_batch"
        ):
            batch_tickers = load_daftar_saham("daftar_saham.txt")

            if not batch_tickers:
                st.error(
                    "⚠️ File `daftar_saham.txt` tidak ditemukan atau isinya"
                    " kosong."
                )
            else:
                total_batch = len(batch_tickers)
                st.info(
                    f"Memulai screening batch untuk {total_batch} saham dari"
                    " `daftar_saham.txt`..."
                )

                pbar_batch = st.progress(0)
                pstatus_batch = st.empty()

                def process_batch_item(ticker_sym):
                    try:
                        p = TradePlanner(
                            ticker=ticker_sym, period=batch_period
                        )
                        p.fetch_and_prepare_data()

                        df_tp = p.generate_trade_plan()

                        if df_tp is None or len(df_tp) == 0:
                            return None

                        if isinstance(df_tp, pd.DataFrame):
                            tp_row = df_tp.iloc[0].to_dict()
                        elif isinstance(df_tp, dict):
                            tp_row = df_tp
                        else:
                            return None

                        close_p = (
                            p.data["Close"].iloc[-1]
                            if (hasattr(p, "data") and not p.data.empty)
                            else 0
                        )

                        score_val = tp_row.get(
                            "Score", tp_row.get("Total Score", 0)
                        )

                        df_sup = p.get_strong_support()
                        df_res = p.get_strong_resistance()

                        s_level = (
                            df_sup["Level"].iloc[0]
                            if (
                                isinstance(df_sup, pd.DataFrame)
                                and not df_sup.empty
                                and "Level" in df_sup.columns
                            )
                            else 0
                        )
                        r_level = (
                            df_res["Level"].iloc[0]
                            if (
                                isinstance(df_res, pd.DataFrame)
                                and not df_res.empty
                                and "Level" in df_res.columns
                            )
                            else 0
                        )

                        posisi_harga = "Normal / Floating"
                        if (
                            s_level > 0
                            and abs(close_p - s_level) / s_level <= 0.02
                        ):
                            posisi_harga = "🛡️ Dekat Support (<= 2%)"
                        elif r_level > 0 and close_p >= r_level:
                            posisi_harga = "🚀 Breakout Resistance"
                        elif (
                            r_level > 0
                            and close_p > 0
                            and abs(r_level - close_p) / close_p <= 0.02
                        ):
                            posisi_harga = "🧱 Dekat Resistance (<= 2%)"

                        tp_row["Saham"] = ticker_sym.replace(".JK", "")
                        tp_row["Ticker"] = ticker_sym
                        tp_row["Score"] = score_val
                        tp_row["Close Price"] = close_p
                        tp_row["Posisi Harga"] = posisi_harga
                        return tp_row
                    except Exception:
                        return None

                batch_results = []
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=6
                ) as executor:
                    future_to_ticker = {
                        executor.submit(process_batch_item, t): t
                        for t in batch_tickers
                    }
                    completed = 0

                    for future in concurrent.futures.as_completed(
                        future_to_ticker
                    ):
                        completed += 1
                        pct = int((completed / total_batch) * 100)
                        pbar_batch.progress(pct)
                        pstatus_batch.text(
                            f"Memproses Batch Trade Planner:"
                            f" {completed}/{total_batch} saham..."
                        )

                        res = future.result()
                        if res is not None:
                            batch_results.append(res)

                pbar_batch.empty()
                pstatus_batch.empty()

                if batch_results:
                    df_batch_all = pd.DataFrame(batch_results)

                    if "Score" in df_batch_all.columns:
                        df_batch_all = df_batch_all.sort_values(
                            by="Score", ascending=False
                        )

                    st.session_state["df_batch_screener"] = df_batch_all
                    st.success(
                        f"Screening selesai! Berhasil memproses"
                        f" {len(df_batch_all)} dari {total_batch} saham."
                    )
                else:
                    st.error(
                        "Tidak ada data yang berhasil di-screen. Pastikan"
                        " koneksi internet lancar atau file `trade_planner.py`"
                        " berfungsi normal."
                    )

        # MENAMPILKAN HASIL + DROPDOWN CATEGORY FILTER
        if (
            "df_batch_screener" in st.session_state
            and not st.session_state["df_batch_screener"].empty
        ):
            df_batch = st.session_state["df_batch_screener"]

            st.markdown("---")
            st.subheader("📊 Filter Hasil Batch Screener")

            col_f1, col_f2, col_f3 = st.columns(3)

            candle_opts = (
                ["ALL"]
                + sorted(df_batch["Status Candle"].dropna().unique().tolist())
                if "Status Candle" in df_batch.columns
                else ["ALL"]
            )
            with col_f1:
                sel_candle = st.selectbox(
                    "🕯️ Filter Status Candle:",
                    candle_opts,
                    key="filter_batch_candle",
                )

            pos_opts = (
                ["ALL"]
                + sorted(df_batch["Posisi Harga"].dropna().unique().tolist())
                if "Posisi Harga" in df_batch.columns
                else ["ALL"]
            )
            with col_f2:
                sel_posisi = st.selectbox(
                    "📈 Filter Posisi Harga:",
                    pos_opts,
                    key="filter_batch_posisi",
                )

            warn_opts = (
                ["ALL"]
                + sorted(df_batch["Warning"].dropna().unique().tolist())
                if "Warning" in df_batch.columns
                else ["ALL"]
            )
            with col_f3:
                sel_warning = st.selectbox(
                    "⚠️ Filter Status Warning:",
                    warn_opts,
                    key="filter_batch_warning",
                )

            # Terapkan Filter
            df_filtered = df_batch.copy()
            if sel_candle != "ALL" and "Status Candle" in df_filtered.columns:
                df_filtered = df_filtered[
                    df_filtered["Status Candle"] == sel_candle
                ]
            if sel_posisi != "ALL" and "Posisi Harga" in df_filtered.columns:
                df_filtered = df_filtered[
                    df_filtered["Posisi Harga"] == sel_posisi
                ]
            if sel_warning != "ALL" and "Warning" in df_filtered.columns:
                df_filtered = df_filtered[
                    df_filtered["Warning"] == sel_warning
                ]

            st.write(
                f"Menampilkan **{len(df_filtered)}** hasil saham terpilih:"
            )

            display_batch_cols = [
                c
                for c in [
                    "Saham",
                    "Score",
                    "Posisi Harga",
                    "Status Candle",
                    "Warning",
                    "Range Buy",
                    "Stop Loss",
                    "Target 1",
                    "Target 2",
                    "Rasio (R:R)",
                ]
                if c in df_filtered.columns
            ]

            event_batch = st.dataframe(
                df_filtered[display_batch_cols],
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key="table_batch_screener",
            )

            if event_batch.selection and event_batch.selection["rows"]:
                idx_b = event_batch.selection["rows"][0]
                selected_batch_ticker = str(df_filtered.iloc[idx_b]["Ticker"])
                render_inline_trade_planner(
                    selected_batch_ticker, key_suffix="batch_tab"
                )