import pandas as pd
import streamlit as st
import yfinance as yf


# --- CACHING DATA SEMENTARA (1 HARI / 1 JAM) ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_bulk_data(ticker_list, period="6mo"):
  """Mengunduh data historical banyak saham sekaligus menggunakan Multi-Threading.

  Data dibungkus `@st.cache_data` agar pengunduhan hanya berjalan 1x per jam.
  """
  try:
    # yf.download secara cepat mengambil 800+ saham sekaligus
    data = yf.download(
        tickers=ticker_list,
        period=period,
        interval="1d",
        group_by="ticker",
        threads=True,
        progress=False,
    )
    return data
  except Exception as e:
    st.error(f"Error fetching bulk data: {e}")
    return pd.DataFrame()


def calculate_rsi(series, period=14):
  """Kalkulasi Relative Strength Index (RSI)."""
  delta = series.diff()
  gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

  rs = gain / loss
  rsi = 100 - (100 / (1 + rs))
  return rsi


def calculate_stochastic(df, k_period=14, d_period=3):
  """Kalkulasi Stochastic Oscillator (%K dan %D)."""
  low_min = df["Low"].rolling(window=k_period).min()
  high_max = df["High"].rolling(window=k_period).max()

  k_fast = 100 * ((df["Close"] - low_min) / (high_max - low_min))
  d_slow = k_fast.rolling(window=d_period).mean()
  return k_fast, d_slow


def run_full_screener(ticker_list, progress_callback=None):
  """Me-screen seluruh list ticker untuk kondisi RSI dan Stochastic.

  Menyediakan callback untuk update progress bar di Streamlit UI.
  """
  bulk_data = fetch_bulk_data(ticker_list)
  results = []

  total_tickers = len(ticker_list)

  for i, ticker in enumerate(ticker_list):
    # Update progress bar visual ke Streamlit
    if progress_callback:
      progress_callback(
          (i + 1) / total_tickers, f"Menganalisis {ticker} ({i+1}/{total_tickers})"
      )

    try:
      # Mengambil data dataframe spesifik per ticker
      if isinstance(bulk_data.columns, pd.MultiIndex):
        if ticker not in bulk_data.columns.levels[0]:
          continue
        df = bulk_data[ticker].dropna()
      else:
        df = bulk_data.dropna()

      if len(df) < 30:  # Skip jika data historis terlalu sedikit
        continue

      # Hitung Indikator
      df["RSI"] = calculate_rsi(df["Close"])
      df["Stoch_K"], df["Stoch_D"] = calculate_stochastic(df)

      last_row = df.iloc[-1]
      prev_row = df.iloc[-2]

      last_close = round(last_row["Close"], 2)
      rsi_val = round(last_row["RSI"], 2)
      k_val = round(last_row["Stoch_K"], 2)
      d_val = round(last_row["Stoch_D"], 2)

      # Evaluasi Kondisi
      rsi_status = "Normal"
      if rsi_val <= 30:
        rsi_status = "Oversold (Murah)"
      elif rsi_val >= 70:
        rsi_status = "Overbought (Mahal)"

      stoch_signal = "Neutral"
      # Cross Up dari bawah 20 (Golden Cross Oversold)
      if (
          prev_row["Stoch_K"] < prev_row["Stoch_D"]
          and k_val > d_val
          and k_val <= 30
      ):
        stoch_signal = "Golden Cross (Oversold)"
      elif k_val <= 20 and d_val <= 20:
        stoch_signal = "Oversold Area"
      elif k_val >= 80 and d_val >= 80:
        stoch_signal = "Overbought Area"

      results.append({
          "Ticker": ticker.replace(".JK", ""),
          "Harga Terakhir": last_close,
          "RSI (14)": rsi_val,
          "Status RSI": rsi_status,
          "Stoch %K": k_val,
          "Stoch %D": d_val,
          "Sinyal Stochastic": stoch_signal,
      })

    except Exception:
      continue

  return pd.DataFrame(results)
