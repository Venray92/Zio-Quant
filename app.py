import concurrent.futures
import time
import pandas as pd
import streamlit as st

# Import modul screener
from screener_rsi_divergence import detect_rsi_patterns_and_score
from screener_stoch_psar import detect_stoch_psar_signals

# Import helper IHSG & Planner jika ada di file terpisah (sesuaikan jika ada modul sendiri)
try:
  from helper import get_all_ihsg_tickers, render_inline_trade_planner
except ImportError:

  def get_all_ihsg_tickers():
    return [
        "BBCA.JK",
        "BBRI.JK",
        "BMRI.JK",
        "TLKM.JK",
        "ASII.JK",
        "SOFA.JK",
        "GOTO.JK",
    ]

  def render_inline_trade_planner(symbol, key_suffix=""):
    st.info(f"📊 Trade Planner untuk: **{symbol}**")


# Set Config Streamlit
st.set_page_config(
    page_title="IHSG Technical Screener", layout="wide", page_icon="📈"
)

st.title("📈 Stock Screener Dashboard")

# Navigation Tabs
tab1, tab2 = st.tabs(
    ["🟢 RSI Divergence", "⚡ Stochastic & PSAR (Reversal/Breakout)"]
)

# ==========================================
# HELPER: Mempersingkat Nama Pattern
# ==========================================
def simplify_pattern_text(df):
  if df.empty or "Pattern" not in df.columns:
    return df
  df = df.copy()
  replacements = {
      "Regular Bullish Divergence Valid (GC Confirmed)": "Reg Bull (GC)",
      "Regular Bullish Divergence Potensial (Menunggu GC)": "Reg Bull (Wait)",
      "Hidden Bullish Divergence Valid (GC Confirmed)": "Hid Bull (GC)",
      "Hidden Bullish Divergence Potensial (Menunggu GC)": "Hid Bull (Wait)",
      "Regular Bearish Divergence Valid (DC Confirmed)": "Reg Bear (DC)",
      "Regular Bearish Divergence Potensial (Menunggu DC)": "Reg Bear (Wait)",
      "Hidden Bearish Divergence Valid (DC Confirmed)": "Hid Bear (DC)",
      "Hidden Bearish Divergence Potensial (Menunggu DC)": "Hid Bear (Wait)",
  }
  df["Pattern"] = df["Pattern"].replace(replacements)
  return df


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

  target_rsi_cols = [
      "Saham",
      "Score",
      "Pattern",
      "Tgl Kiri",
      "Harga Kiri",
      "RSI Kiri",
      "Tgl Kanan",
      "Harga Kanan",
      "RSI Kanan",
      "Status Base",
  ]

  # BULLISH TABLE
  with col_bull:
    st.subheader("🟢 Signal Bullish (Divergence)")
    if (
        "df_rsi_bullish" in st.session_state
        and not st.session_state["df_rsi_bullish"].empty
    ):
      df_rsi_bullish = simplify_pattern_text(
          st.session_state["df_rsi_bullish"]
      )
      if "Score" in df_rsi_bullish.columns:
        df_rsi_bullish = df_rsi_bullish.sort_values(
            by="Score", ascending=False
        )

      display_cols = [c for c in target_rsi_cols if c in df_rsi_bullish.columns]
      df_display_bull = df_rsi_bullish[display_cols]

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

  # BEARISH TABLE
  with col_bear:
    st.subheader("🔴 Signal Bearish (Divergence)")
    if (
        "df_rsi_bearish" in st.session_state
        and not st.session_state["df_rsi_bearish"].empty
    ):
      df_rsi_bearish = simplify_pattern_text(
          st.session_state["df_rsi_bearish"]
      )
      if "Score" in df_rsi_bearish.columns:
        df_rsi_bearish = df_rsi_bearish.sort_values(
            by="Score", ascending=False
        )

      display_cols = [c for c in target_rsi_cols if c in df_rsi_bearish.columns]
      df_display_bear = df_rsi_bearish[display_cols]

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
# TAB 2: STOCHASTIC & PSAR SCREENER
# ==========================================
with tab2:
  st.header("⚡ Screener Stochastic & Parabolic SAR")
  st.caption(
      "Memindai setup Reversal (Oversold GC) dan Breakout Momentum berbasis"
      " Stoch & PSAR."
  )

  if st.button("Jalankan Screener Stoch & PSAR", key="btn_stoch"):
    with st.spinner("Mengambil daftar lengkap saham IHSG..."):
      all_tickers = get_all_ihsg_tickers()

    total_tickers = len(all_tickers)
    st.info(f"Menganalisis {total_tickers} ticker saham IHSG...")

    pbar_stoch = st.progress(0)
    pstatus_stoch = st.empty()

    results_stoch = []
    success_stoch = 0
    failed_stoch = 0

    def fetch_stoch_with_retry(ticker, max_retries=2):
      for attempt in range(max_retries + 1):
        try:
          res = detect_stoch_psar_signals(ticker)
          return True, res
        except Exception:
          if attempt < max_retries:
            time.sleep(0.5 * (attempt + 1))
          else:
            return False, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
      future_to_ticker = {
          executor.submit(fetch_stoch_with_retry, t): t for t in all_tickers
      }
      completed = 0

      for future in concurrent.futures.as_completed(future_to_ticker):
        completed += 1
        pct = int((completed / total_tickers) * 100)
        pbar_stoch.progress(pct)
        pstatus_stoch.text(
            f"Menganalisis Stoch/PSAR: {completed}/{total_tickers} saham..."
        )

        try:
          is_success, res = future.result()
          if is_success:
            success_stoch += 1
            if res is not None and isinstance(res, dict):
              results_stoch.append(res)
          else:
            failed_stoch += 1
        except Exception:
          failed_stoch += 1

    pbar_stoch.empty()
    pstatus_stoch.empty()

    df_stoch_all = pd.DataFrame(results_stoch) if results_stoch else pd.DataFrame()

    st.session_state["stoch_stats"] = {
        "total": total_tickers,
        "success": success_stoch,
        "failed": failed_stoch,
        "matched": len(df_stoch_all),
    }
    st.session_state["df_stoch_all"] = df_stoch_all

  if "stoch_stats" in st.session_state:
    stats_st = st.session_state["stoch_stats"]
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Total Ticker Di-scan", f"{stats_st['total']} Saham")
    col_s2.metric("Sinyal Terdeteksi", f"{stats_st['matched']} Saham")
    col_s3.metric("Gagal Download", f"{stats_st['failed']} Saham")

  selected_stoch_symbol = None

  if (
      "df_stoch_all" in st.session_state
      and not st.session_state["df_stoch_all"].empty
  ):
    df_stoch_display = st.session_state["df_stoch_all"]

    # Sort berdasarkan Score jika kolom Score tersedia
    if "Score" in df_stoch_display.columns:
      df_stoch_display = df_stoch_display.sort_values(
          by="Score", ascending=False
      )

    event_stoch = st.dataframe(
        df_stoch_display,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="table_stoch_psar",
    )
    if event_stoch.selection and event_stoch.selection["rows"]:
      idx = event_stoch.selection["rows"][0]
      selected_stoch_symbol = str(
          df_stoch_display.iloc[idx].get(
              "Ticker", df_stoch_display.iloc[idx].get("Saham")
          )
      )
  else:
    st.info("Belum ada data Stochastic & PSAR. Klik tombol di atas untuk scan.")

  if selected_stoch_symbol:
    if not selected_stoch_symbol.endswith(".JK") and "." not in selected_stoch_symbol:
      selected_stoch_symbol += ".JK"
    render_inline_trade_planner(selected_stoch_symbol, key_suffix="stoch_tab")
