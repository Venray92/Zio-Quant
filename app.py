import concurrent.futures
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
    "Aplikasi screening saham berbasis **RSI Divergence**, **Stochastic & Parabolic SAR**, **Bulk IHSG Screener**, serta kalkulator **Trade Planner**."
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
    "🔄 RSI Divergence (Full IHSG)",
    "⚡ Stochastic & Parabolic SAR",
    "🌐 Bulk Screener IHSG (Quick)",
    "🎯 Custom Trade Planner",
])

# ==========================================
# TAB 1: RSI DIVERGENCE (SELEURUH SAHAM IHSG)
# ==========================================
with tab1:
  st.header("Screener RSI Divergence & Patterns (Seluruh Saham IHSG)")
  st.caption(
      "Klik pada salah satu baris saham untuk langsung melihat Trade Planner di"
      " bawah tabel."
  )

  if st.button("Jalankan Screener RSI (Full IHSG)", key="btn_rsi"):
    with st.spinner("Mengambil daftar saham IHSG..."):
      all_tickers = get_all_ihsg_tickers()

    with st.spinner(f"Menganalisis {len(all_tickers)} saham IHSG..."):
      results_rsi = []
      # Meningkatkan max_workers ke 20 agar screening 800+ saham jauh lebih cepat
      with concurrent.futures.ThreadPoolExecutor(
          max_workers=20
      ) as executor:
        futures = [
            executor.submit(detect_rsi_patterns_and_score, ticker)
            for ticker in all_tickers
        ]
        for future in concurrent.futures.as_completed(futures):
          res = future.result()
          if res is not None:
            results_rsi.append(res)

      if results_rsi:
        df_rsi = pd.DataFrame(results_rsi)
        score_col = next(
            (
                c
                for c in ["Score", "score", "total_score", "RSI_Score"]
                if c in df_rsi.columns
            ),
            None,
        )
        if score_col:
          df_rsi = df_rsi.sort_values(
              by=score_col, ascending=False
          ).reset_index(drop=True)
        st.session_state["df_rsi_data"] = df_rsi
      else:
        st.session_state["df_rsi_data"] = pd.DataFrame()

  if (
      "df_rsi_data" in st.session_state
      and not st.session_state["df_rsi_data"].empty
  ):
    df_rsi = st.session_state["df_rsi_data"]
    st.success(f"Screening selesai! Ditemukan {len(df_rsi)} hasil.")

    event_rsi = st.dataframe(
        df_rsi,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="table_rsi",
    )

    if event_rsi.selection and event_rsi.selection["rows"]:
      selected_idx = event_rsi.selection["rows"][0]
      ticker_col = next(
          (
              c
              for c in ["Ticker", "Saham", "Stock", "Symbol"]
              if c in df_rsi.columns
          ),
          None,
      )
      if ticker_col:
        symbol = str(df_rsi.iloc[selected_idx][ticker_col])
        if not symbol.endswith(".JK") and "." not in symbol:
          symbol += ".JK"
        render_inline_trade_planner(symbol, key_suffix="rsi_tab")

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
    with st.spinner("Menganalisis signal Stochastic & Parabolic SAR..."):
      try:
        df_gc, df_dc = run_stoch_psar_screener()
        st.session_state["df_gc_data"] = df_gc
        st.session_state["df_dc_data"] = df_dc
      except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")

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
# TAB 3: BULK SCREENER IHSG (FAST DOWNLOAD)
# ==========================================
with tab3:
  st.header("🌐 Quick Screener Seluruh Saham IHSG")
  st.caption(
      "Screening cepat seluruh emiten IHSG menggunakan Multi-Threading Bulk"
      " Download."
  )

  if st.button("🚀 Screening Seluruh Saham IHSG", key="btn_bulk_ihsg"):
    with st.spinner("Mengambil daftar lengkap ticker saham IHSG..."):
      all_ihsg_tickers = get_all_ihsg_tickers()

    st.info(f"Total {len(all_ihsg_tickers)} ticker siap di-scan.")

    # UI Progress Bar
    pbar = st.progress(0)
    pstatus = st.empty()

    def update_progress_ui(pct, msg):
      pbar.progress(pct)
      pstatus.text(msg)

    # Executing Screener
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
