import concurrent.futures
import time
import pandas as pd
import streamlit as st

# Import modul fungsi screener kamu
from screener_rsi_divergence import detect_rsi_patterns_and_score


# Dummy function untuk ticker IHSG & trade planner jika belum diset terpisah
def get_all_ihsg_tickers():
  # Ganti dengan logika/list ticker IHSG Anda yang sebenarnya
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
  st.info(f"📊 Trade Planner Placeholder untuk: **{symbol}**")


# Set Config
st.set_page_config(page_title="IHSG Technical Screener", layout="wide")

st.title("📈 Stock Screener Dashboard")

# Navigation Tabs
tab1, tab2 = st.tabs(["RSI Divergence", "Other Screener"])

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

  # Tampilkan Ringkasan Statistik
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

  # 1. Definisi Urutan Kolom (Score disertakan di depan)
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

  # 2. Function untuk Mempersingkat Nama Pattern
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

  # TABEL BULLISH
  with col_bull:
    st.subheader("🟢 Signal Bullish (Divergence)")
    if (
        "df_rsi_bullish" in st.session_state
        and not st.session_state["df_rsi_bullish"].empty
    ):
      df_rsi_bullish = simplify_pattern_text(
          st.session_state["df_rsi_bullish"]
      )

      # Sort otomatis berdasarkan Score tertinggi
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

  # TABEL BEARISH
  with col_bear:
    st.subheader("🔴 Signal Bearish (Divergence)")
    if (
        "df_rsi_bearish" in st.session_state
        and not st.session_state["df_rsi_bearish"].empty
    ):
      df_rsi_bearish = simplify_pattern_text(
          st.session_state["df_rsi_bearish"]
      )

      # Sort otomatis berdasarkan Score tertinggi
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

  # Inline Planner apabila saham di-klik
  if selected_rsi_symbol:
    if not selected_rsi_symbol.endswith(".JK") and "." not in selected_rsi_symbol:
      selected_rsi_symbol += ".JK"
    render_inline_trade_planner(selected_rsi_symbol, key_suffix="rsi_tab")

with tab2:
  st.write("Screener Lainnya...")
