import concurrent.futures
import time
import pandas as pd
import streamlit as st

# 1. Import modul internal
from ihsg_tickers import get_all_ihsg_tickers
from screener import run_full_screener
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
    " Parabolic SAR**, **Bulk IHSG Screener**, serta kalkulator **Trade"
    " Planner**."
)


# Helper function untuk merender Trade Planner di bawah tabel
def render_inline_trade_planner(ticker_symbol, key_suffix):
  st.markdown("---")
  st.subheader(f"📊 Live Trade Plan: **{ticker_symbol}**")

  period_selected = st.selectbox(
      "Periode Data Analysis",
      options=["3mo", "6mo", "1y", "2y"],
      index=1,
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
tab1, tab2, tab3, tab4 = st.tabs([
    "🔄 RSI Divergence",
    "⚡ Stochastic & Parabolic SAR",
    "🌐 Bulk Screener IHSG (Full)",
    "🎯 Custom Trade Planner",
])

# ==========================================
# TAB 1: RSI DIVERGENCE & PATTERNS
# ==========================================
with tab1:
  st.header("Screener RSI Divergence & Technical Patterns")
  st.caption(
      "Screening seluruh saham IHSG yang sedang membentuk Divergence Bullish"
      " maupun Bearish."
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

    # Helper function dengan Retry Mechanism untuk Yahoo Finance
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

    # Memisahkan hasil menjadi Bullish dan Bearish
    df_rsi_all = pd.DataFrame(results_rsi) if results_rsi else pd.DataFrame()

    df_rsi_bullish = pd.DataFrame()
    df_rsi_bearish = pd.DataFrame()

    if not df_rsi_all.empty and "Pattern" in df_rsi_all.columns:
      df_rsi_bullish = df_rsi_all[
          df_rsi_all["Pattern"].str.contains("Bullish", case=False, na=False)
      ]
      df_rsi_bearish = df_rsi_all[
          df_rsi_all["Pattern"].str.contains("Bearish", case=False, na=False)
      ]

      score_col = next(
          (c for c in ["TOTAL SCORE", "Score", "score"] if c in df_rsi_all.columns),
          None,
      )
      if score_col:
        if not df_rsi_bullish.empty:
          df_rsi_bullish = df_rsi_bullish.sort_values(
              by=score_col, ascending=False
          ).reset_index(drop=True)
        if not df_rsi_bearish.empty:
          df_rsi_bearish = df_rsi_bearish.sort_values(
              by=score_col, ascending=False
          ).reset_index(drop=True)

    # Simpan ke Session State
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

  # --- RINGKASAN METRICS TAB 1 ---
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

  # --- TAMPILAN 2 KOLOM (KIRI: BULLISH, KANAN: BEARISH) ---
  col_bull, col_bear = st.columns(2)
  selected_rsi_symbol = None

  with col_bull:
    st.subheader("🟢 Signal Bullish (Divergence)")
    if (
        "df_rsi_bullish" in st.session_state
        and not st.session_state["df_rsi_bullish"].empty
    ):
      df_rsi_bullish = st.session_state["df_rsi_bullish"]
      event_bull = st.dataframe(
          df_rsi_bullish,
          use_container_width=True,
          on_select="rerun",
          selection_mode="single-row",
          key="table_rsi_bullish",
      )
      if event_bull.selection and event_bull.selection["rows"]:
        idx = event_bull.selection["rows"][0]
        ticker_col = next(
            (
                c
                for c in ["Ticker", "Saham", "Stock", "Symbol"]
                if c in df_rsi_bullish.columns
            ),
            None,
        )
        if ticker_col:
          selected_rsi_symbol = str(df_rsi_bullish.iloc[idx][ticker_col])
    else:
      st.info("Tidak ada sinyal Bullish / Belum di-scan.")

  with col_bear:
    st.subheader("🔴 Signal Bearish (Divergence)")
    if (
        "df_rsi_bearish" in st.session_state
        and not st.session_state["df_rsi_bearish"].empty
    ):
      df_rsi_bearish = st.session_state["df_rsi_bearish"]
      event_bear = st.dataframe(
          df_rsi_bearish,
          use_container_width=True,
          on_select="rerun",
          selection_mode="single-row",
          key="table_rsi_bearish",
      )
      if event_bear.selection and event_bear.selection["rows"]:
        idx = event_bear.selection["rows"][0]
        ticker_col = next(
            (
                c
                for c in ["Ticker", "Saham", "Stock", "Symbol"]
                if c in df_rsi_bearish.columns
            ),
            None,
        )
        if ticker_col:
          selected_rsi_symbol = str(df_rsi_bearish.iloc[idx][ticker_col])
    else:
      st.info("Tidak ada sinyal Bearish / Belum di-scan.")

  # Render Trade Planner otomatis saat salah satu baris di-klik
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
      # Panggil screener
      df_gc, df_dc = run_stoch_psar_screener(
          tickers=all_stoch_tickers,
          progress_callback=update_stoch_progress,
      )
      pbar_stoch.empty()
      pstatus_stoch.empty()

      st.session_state["df_gc_data"] = df_gc
      st.session_state["df_dc_data"] = df_dc

      # Hitung total temuan
      gc_len = len(df_gc) if df_gc is not None else 0
      dc_len = len(df_dc) if df_dc is not None else 0

      # Catat statistik
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

  # --- RINGKASAN METRICS TAB 2 ---
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
# TAB 3: BULK SCREENER IHSG (FULL SAHAM)
# ==========================================
with tab3:
  st.header("🌐 Screener Massal Seluruh Saham IHSG")
  st.caption(
      "Screening cepat seluruh emiten IHSG menggunakan Multi-Threading Bulk"
      " Download."
  )

  if st.button("🚀 Screening Seluruh Saham IHSG", key="btn_bulk_ihsg"):
    with st.spinner("Mengambil daftar lengkap ticker saham IHSG..."):
      all_ihsg_tickers = get_all_ihsg_tickers()

    st.info(f"Total {len(all_ihsg_tickers)} ticker siap di-scan.")

    pbar = st.progress(0)
    pstatus = st.empty()

    def update_progress_ui(pct, msg):
      pbar.progress(pct)
      pstatus.text(msg)

    df_bulk = run_full_screener(
        all_ihsg_tickers, progress_callback=update_progress_ui
    )

    pbar.empty()
    pstatus.empty()

    if not df_bulk.empty:
      st.session_state["df_bulk_ihsg"] = df_bulk
      st.success(
          f"Berhasil me-screen {len(df_bulk)} saham aktif secara bersamaan!"
      )
    else:
      st.error("Gagal mendapatkan data screening masal.")

  if (
      "df_bulk_ihsg" in st.session_state
      and not st.session_state["df_bulk_ihsg"].empty
  ):
    df_bulk = st.session_state["df_bulk_ihsg"]

    st.subheader("🎯 Ringkasan Saham Potensial")
    df_potensial = df_bulk[
        df_bulk["Sinyal Stochastic"].str.contains("Oversold|Golden Cross")
    ]
    st.dataframe(df_potensial, use_container_width=True)

    st.subheader("📋 Hasil Lengkap Seluruh Saham")
    event_bulk = st.dataframe(
        df_bulk,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="table_bulk_ihsg",
    )

    if event_bulk.selection and event_bulk.selection["rows"]:
      idx = event_bulk.selection["rows"][0]
      symbol_selected = str(df_bulk.iloc[idx]["Ticker"])
      if not symbol_selected.endswith(".JK"):
        symbol_selected += ".JK"
      render_inline_trade_planner(symbol_selected, key_suffix="bulk_tab")


# ==========================================
# TAB 4: CUSTOM TRADE PLANNER (MANUAL INPUT)
# ==========================================
with tab4:
  st.header("Custom Trade Planner Calculator")
  st.caption("Cari Trade Plan saham pilihan secara manual.")

  col_input1, col_input2 = st.columns([2, 1])
  with col_input1:
    ticker_input = st.text_input(
        "Masukkan Ticker Saham", value="INCO.JK", key="manual_ticker_input"
    )
  with col_input2:
    period_input = st.selectbox(
        "Pilih Periode Data",
        options=["3mo", "6mo", "1y", "2y"],
        index=1,
        key="manual_period_input",
    )

  if st.button("Generate Trade Plan", key="btn_planner_manual"):
    render_inline_trade_planner(ticker_input, key_suffix="manual_tab")
