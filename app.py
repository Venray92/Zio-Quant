import concurrent.futures
import os
import time
import pandas as pd
import streamlit as st

# 1. Import modul internal
from ihsg_tickers import get_all_ihsg_tickers
from screener_rsi_divergence import detect_rsi_patterns_and_score
from screener_stoch_psar import run_stoch_psar_screener
from trade_planner import TradePlanner

# 2. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="ZIO QUANT - Screener & Trade Planner",
    page_icon="📈",
    layout="wide",
)

st.title("📈 ZIO QUANT Dashboard")
st.markdown(
    "Aplikasi screening saham berbasis **RSI Divergence**, **Stochastic &"
    " Parabolic SAR**, serta kalkulator **Trade Planner** dengan Scoring System."
)


# Helper untuk membaca file daftar_saham.txt
def load_daftar_saham(filepath="daftar_saham.txt"):
    if not os.path.exists(filepath):
        st.error(f"⚠️ File `{filepath}` tidak ditemukan.")
        return []
    try:
        df = pd.read_csv(filepath)
        if "Kode" in df.columns:
            tickers = df["Kode"].dropna().astype(str).str.strip().tolist()
            return [t + ".JK" if not t.endswith(".JK") else t for t in tickers if t]
        else:
            st.error(f"⚠️ Kolom 'Kode' tidak ditemukan dalam `{filepath}`.")
            return []
    except Exception as e:
        st.error(f"Gagal membaca `{filepath}`: {e}")
        return []


# Helper function untuk merender detail Trade Planner
def render_inline_trade_planner(ticker_symbol, key_suffix):
    st.markdown("---")
    st.subheader(f"📊 Live Trade Plan: **{ticker_symbol}**")

    period_selected = st.selectbox(
        "Periode Data Analysis",
        options=["3mo", "6mo", "1y", "2y"],
        index=0,
        key=f"period_{key_suffix}",
    )

    with st.spinner(f"Menghitung Trade Plan untuk {ticker_symbol}..."):
        try:
            planner = TradePlanner(
                ticker=ticker_symbol.upper(), period=period_selected
            )
            planner.fetch_and_prepare_data()

            # Direction Market
            st.markdown("#### 📌 Direction Market")
            df_dir = planner.get_direction()
            st.dataframe(df_dir, use_container_width=True)

            direction_val = df_dir["Direction"].iloc[0]
            if direction_val == "BOB":
                st.success("Analisis Arah: **BOB (Breakout Buy)**")
            else:
                st.info("Analisis Arah: **BOW (Buy on Weakness)**")

            # Strategy Trade Plan
            st.markdown("#### 🎯 Trade Plan Recommendation")
            df_plan = planner.generate_trade_plan()
            st.dataframe(df_plan, use_container_width=True)

            warning_msg = df_plan["Warning"].iloc[0]
            candle_type = df_plan["Status Candle"].iloc[0]
            st.warning(f"**Pola Candle Terdeteksi:** {candle_type} — {warning_msg}")

            # Support & Resistance Levels
            col_sup, col_res = st.columns(2)
            with col_sup:
                st.markdown("#### 🛡️ Support Levels")
                st.dataframe(planner.get_strong_support(), use_container_width=True)
            with col_res:
                st.markdown("#### 🧱 Resistance Levels")
                st.dataframe(planner.get_strong_resistance(), use_container_width=True)

            # Swing Points
            st.markdown("#### 📍 Swing Points & Metpoints")
            st.dataframe(planner.get_swing_points(), use_container_width=True)

        except Exception as e:
            st.error(f"Gagal memuat Trade Plan untuk {ticker_symbol}: {e}")


# 3. Membuat Tab Navigasi
tab1, tab2, tab3 = st.tabs([
    "🔄 RSI Divergence",
    "⚡ Stochastic & Parabolic SAR",
    "🎯 Trade Planner & Batch Screener",
])

# ==========================================
# TAB 1: RSI DIVERGENCE & PATTERNS
# ==========================================
with tab1:
    st.header("Screener RSI Divergence & Technical Patterns")
    st.caption(
        "Screening seluruh saham IHSG yang sedang membentuk Divergence Bullish"
        " maupun Bearish beserta penilaannya (Score)."
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

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
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

        df_rsi_all = pd.DataFrame(results_rsi) if results_rsi else pd.DataFrame()
        
        # Sortir dataframe berdasarkan Score secara descending jika kolom Score ada
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

    if "rsi_stats" in st.session_state:
        stats = st.session_state["rsi_stats"]
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total Ticker Di-scan", f"{stats['total']} Saham")
        col_m2.metric("Sinyal Bullish", f"{stats['bullish_count']} Saham")
        col_m3.metric("Sinyal Bearish", f"{stats['bearish_count']} Saham")
        col_m4.metric("Total Sinyal RSI", f"{stats['matched']} Saham")

        if stats["failed"] > 0:
            st.warning(
                f"⚠️ Terdapat **{stats['failed']} saham** gagal didownload dari Yahoo"
                " Finance."
            )

    col_bull, col_bear = st.columns(2)
    selected_rsi_symbol = None

    # Menambahkan 'Score' pada daftar kolom tampilan
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

            display_cols = [c for c in target_rsi_cols if c in df_rsi_bullish.columns]
            df_display_bull = (
                df_rsi_bullish[display_cols] if display_cols else df_rsi_bullish
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

            display_cols = [c for c in target_rsi_cols if c in df_rsi_bearish.columns]
            df_display_bear = (
                df_rsi_bearish[display_cols] if display_cols else df_rsi_bearish
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
        if not selected_rsi_symbol.endswith(".JK") and "." not in selected_rsi_symbol:
            selected_rsi_symbol += ".JK"
        render_inline_trade_planner(selected_rsi_symbol, key_suffix="rsi_tab")


# ==========================================
# TAB 2: STOCHASTIC & PARABOLIC SAR
# ==========================================
with tab2:
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

            # Mengurutkan berdasarkan Score jika kolom Score tersedia
            if df_gc is not None and not df_gc.empty and "Score" in df_gc.columns:
                df_gc = df_gc.sort_values(by="Score", ascending=False)
            if df_dc is not None and not df_dc.empty and "Score" in df_dc.columns:
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
        c_m2.metric("Sinyal Beli (Golden Cross)", f"{st_stats['matched_gc']} Saham")
        c_m3.metric("Sinyal Jual (Dead Cross)", f"{st_stats['matched_dc']} Saham")
        c_m4.metric("Total Sinyal Terdeteksi", f"{st_stats['total_signal']} Saham")

    col_gc, col_dc = st.columns(2)
    selected_stoch_symbol = None

    with col_gc:
        st.subheader("🟢 Signal Beli (Golden Cross)")
        if (
            "df_gc_data" in st.session_state
            and not st.session_state["df_gc_data"].empty
        ):
            df_gc = st.session_state["df_gc_data"]
            event_gc = st.dataframe(
                df_gc,
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
            event_dc = st.dataframe(
                df_dc,
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
        render_inline_trade_planner(selected_stoch_symbol, key_suffix="stoch_tab")

# ==========================================
# TAB 3: TRADE PLANNER & BATCH SCREENER
# ==========================================
with tab3:
    st.header("🎯 Trade Planner & Multi-Category Batch Screener")

    # Pilih Sub-Mode
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
                render_inline_trade_planner(clean_ticker, key_suffix="manual_tab")

    else:  # MODE BATCH SCREENER
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

        # HELPER ROBUST UNTUK MEMBACA DAFTAR SAHAM
        def get_clean_tickers_from_file(filepath="daftar_saham.txt"):
            if not os.path.exists(filepath):
                return []

            tickers = []
            with open(filepath, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()
                for line in lines:
                    item = line.strip().upper()
                    if item and item not in ["KODE", "TICKER", "SAHAM"]:
                        clean_t = item.split(",")[0].replace(".JK", "").strip()
                        if clean_t:
                            tickers.append(f"{clean_t}.JK")
            return sorted(list(set(tickers)))

        if st.button(
            "🚀 Run Batch Screener (daftar_saham.txt)", key="btn_run_batch"
        ):
            batch_tickers = get_clean_tickers_from_file("daftar_saham.txt")

            if not batch_tickers:
                st.error(
                    "⚠️ File `daftar_saham.txt` tidak ditemukan atau isinya kosong."
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
                        p = TradePlanner(ticker=ticker_sym, period=batch_period)
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

                        # Ambil Nilai Score dari TradePlanner (default 0 jika tidak ada)
                        score_val = tp_row.get("Score", tp_row.get("Total Score", 0))

                        # Hitung posisi terhadap Support & Resistance
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
                        if s_level > 0 and abs(close_p - s_level) / s_level <= 0.02:
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
                with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                    future_to_ticker = {
                        executor.submit(process_batch_item, t): t for t in batch_tickers
                    }
                    completed = 0

                    for future in concurrent.futures.as_completed(future_to_ticker):
                        completed += 1
                        pct = int((completed / total_batch) * 100)
                        pbar_batch.progress(pct)
                        pstatus_batch.text(
                            f"Memproses Batch Trade Planner: {completed}/{total_batch}"
                            " saham..."
                        )

                        res = future.result()
                        if res is not None:
                            batch_results.append(res)

                pbar_batch.empty()
                pstatus_batch.empty()

                if batch_results:
                    df_batch_all = pd.DataFrame(batch_results)
                    
                    # Sortir berdasarkan Score tertinggi
                    if "Score" in df_batch_all.columns:
                        df_batch_all = df_batch_all.sort_values(by="Score", ascending=False)
                        
                    st.session_state["df_batch_screener"] = df_batch_all
                    st.success(
                        f"Screening selesai! Berhasil memproses {len(df_batch_all)} dari"
                        f" {total_batch} saham."
                    )
                else:
                    st.error(
                        "Tidak ada data yang berhasil di-screen. Pastikan koneksi internet"
                        " lancar atau file `trade_planner.py` berfungsi normal."
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
                ["ALL"] + sorted(df_batch["Status Candle"].dropna().unique().tolist())
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
                ["ALL"] + sorted(df_batch["Posisi Harga"].dropna().unique().tolist())
                if "Posisi Harga" in df_batch.columns
                else ["ALL"]
            )
            with col_f2:
                sel_posisi = st.selectbox(
                    "📈 Filter Posisi Harga:", pos_opts, key="filter_batch_posisi"
                )

            warn_opts = (
                ["ALL"] + sorted(df_batch["Warning"].dropna().unique().tolist())
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
                df_filtered = df_filtered[df_filtered["Status Candle"] == sel_candle]
            if sel_posisi != "ALL" and "Posisi Harga" in df_filtered.columns:
                df_filtered = df_filtered[df_filtered["Posisi Harga"] == sel_posisi]
            if sel_warning != "ALL" and "Warning" in df_filtered.columns:
                df_filtered = df_filtered[df_filtered["Warning"] == sel_warning]

            st.write(f"Menampilkan **{len(df_filtered)}** hasil saham terpilih:")

            # Menampilkan 'Score' di kolom awal hasil Batch Screener
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
