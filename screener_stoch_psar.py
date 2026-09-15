import concurrent.futures
import pandas as pd
import yfinance as yf


def analyze_single_ticker(ticker):
  """Fungsi pembantu untuk menganalisis 1 ticker saham secara independen."""
  try:
    # 1. Download data (opsional: tambahkan timeout/period sesuai kebutuhan)
    df = yf.download(ticker, period="6m", progress=False)
    if df.empty or len(df) < 20:
      return None, None

    # Normalisasi kolom MultiIndex jika ada (fitur yfinance terbaru)
    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    # 2. Hitung Indikator (Stochastic & Parabolic SAR)
    # --- Contoh kalkulasi sederhana, sesuaikan dengan rumus di file kamu ---
    # Stochastic (14, 3, 3)
    low_min = df['Low'].rolling(window=14).min()
    high_max = df['High'].rolling(window=14).max()
    df['%K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    df['%D'] = df['%K'].rolling(window=3).mean()

    # Logika Parabolic SAR & Sinyal (Gunakan logika eksisting kamu di sini)
    # ...
    # -----------------------------------------------------------------------

    # Contoh penentuan sinyal (sesuaikan dengan output DF yang kamu harapkan):
    is_golden_cross = False  # Logika GC kamu
    is_dead_cross = False  # Logika DC kamu

    gc_row = None
    dc_row = None

    if is_golden_cross:
      gc_row = {
          "Ticker": ticker,
          "Close": df["Close"].iloc[-1],
          "Stoch_%K": df["%K"].iloc[-1],
          "Stoch_%D": df["%D"].iloc[-1],
      }

    if is_dead_cross:
      dc_row = {
          "Ticker": ticker,
          "Close": df["Close"].iloc[-1],
          "Stoch_%K": df["%K"].iloc[-1],
          "Stoch_%D": df["%D"].iloc[-1],
      }

    return gc_row, dc_row

  except Exception:
    return None, None


def run_stoch_psar_screener(tickers, max_workers=6, progress_callback=None):
  """Menjalankan screening Stoch & PSAR menggunakan multithreading."""
  results_gc = []
  results_dc = []
  total_tickers = len(tickers)

  # Menggunakan ThreadPoolExecutor di dalam modul
  with concurrent.futures.ThreadPoolExecutor(
      max_workers=max_workers
  ) as executor:
    # Mapping task ke ticker
    future_to_ticker = {
        executor.submit(analyze_single_ticker, ticker): ticker
        for ticker in tickers
    }

    for i, future in enumerate(
        concurrent.futures.as_completed(future_to_ticker)
    ):
      gc_data, dc_data = future.result()

      if gc_data:
        results_gc.append(gc_data)
      if dc_data:
        results_dc.append(dc_data)

      # Kirim progress balik ke Streamlit UI jika callback disediakan
      if progress_callback:
        progress_callback(i + 1, total_tickers)

  df_gc = pd.DataFrame(results_gc) if results_gc else pd.DataFrame()
  df_dc = pd.DataFrame(results_dc) if results_dc else pd.DataFrame()

  return df_gc, df_dc
