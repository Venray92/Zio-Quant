import concurrent.futures
import numpy as np
import pandas as pd
import yfinance as yf


def analyze_single_ticker(ticker):
  """Menganalisis 1 ticker untuk Stochastic %K/%D dan Parabolic SAR."""
  try:
    # 1. Pastikan akhiran .JK untuk yfinance
    symbol = ticker.strip().upper()
    if not symbol.endswith(".JK"):
      symbol = f"{symbol}.JK"

    # 2. Download Data 6 bulan terakhir
    df = yf.download(symbol, period="6m", progress=False)
    if df.empty or len(df) < 30:
      return None, None

    # 3. Ratakan MultiIndex jika ada (fitur yfinance terbaru)
    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    # Clean missing values
    df = df.dropna(subset=["Close", "High", "Low"])

    # --- HITUNG STOCHASTIC (14, 3, 3) ---
    low_14 = df["Low"].rolling(window=14).min()
    high_14 = df["High"].rolling(window=14).max()

    # Mencegah division by zero
    denom = high_14 - low_14
    denom = denom.replace(0, np.nan)

    df["%K"] = 100 * ((df["Close"] - low_14) / denom)
    df["%D"] = df["%K"].rolling(window=3).mean()

    # --- LOGIKA CROSSOVER STOCHASTIC ---
    k_curr, k_prev = df["%K"].iloc[-1], df["%K"].iloc[-2]
    d_curr, d_prev = df["%D"].iloc[-1], df["%D"].iloc[-2]
    close_curr = df["Close"].iloc[-1]

    # Golden Cross: %K memotong %D ke atas & di bawah area Oversold (misal < 80 atau < 20)
    is_gc = (k_prev <= d_prev) and (k_curr > d_curr)

    # Dead Cross: %K memotong %D ke bawah
    is_dc = (k_prev >= d_prev) and (k_curr < d_curr)

    row_data = {
        "Ticker": ticker.replace(".JK", ""),
        "Close": round(float(close_curr), 2),
        "Stoch_%K": round(float(k_curr), 2),
        "Stoch_%D": round(float(d_curr), 2),
    }

    gc_res = row_data if is_gc else None
    dc_res = row_data if is_dc else None

    return gc_res, dc_res

  except Exception as e:
    # Jika ada error pada ticker tertentu, kembalikan None
    return None, None


def run_stoch_psar_screener(tickers, max_workers=8, progress_callback=None):
  """Fungsi utama yang dipanggil oleh app.py."""
  results_gc = []
  results_dc = []
  total = len(tickers)

  with concurrent.futures.ThreadPoolExecutor(
      max_workers=max_workers
  ) as executor:
    future_to_ticker = {
        executor.submit(analyze_single_ticker, t): t for t in tickers
    }

    for i, future in enumerate(
        concurrent.futures.as_completed(future_to_ticker)
    ):
      gc_item, dc_item = future.result()

      if gc_item:
        results_gc.append(gc_item)
      if dc_item:
        results_dc.append(dc_item)

      # Callback untuk update progress bar di Streamlit
      if progress_callback:
        progress_callback(i + 1, total)

  df_gc = pd.DataFrame(results_gc) if results_gc else pd.DataFrame()
  df_dc = pd.DataFrame(results_dc) if results_dc else pd.DataFrame()

  return df_gc, df_dc
