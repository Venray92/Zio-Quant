import pandas as pd
import pandas_ta as ta
import yfinance as yf


def extract_swings(df_in, series, left=2, right=2):
  swings = []
  n = len(series)

  for i in range(left, n):
    current_val = series.iloc[i]
    left_vals = series.iloc[i - left : i]
    remaining_right = n - 1 - i

    if remaining_right >= right:
      right_vals = series.iloc[i + 1 : i + 1 + right]

      if all(current_val >= val for val in left_vals) and all(
          current_val > val for val in right_vals
      ):
        swings.append({
            "Tanggal": series.index[i],
            "Nilai": current_val,
            "Harga Close": df_in["Close"].iloc[i],
            "Type": "SWING HIGH",
            "Status": "Confirmed",
        })
      elif all(current_val <= val for val in left_vals) and all(
          current_val < val for val in right_vals
      ):
        swings.append({
            "Tanggal": series.index[i],
            "Nilai": current_val,
            "Harga Close": df_in["Close"].iloc[i],
            "Type": "SWING LOW",
            "Status": "Confirmed",
        })

    elif remaining_right >= 0:
      right_vals = series.iloc[i + 1 : n]
      if len(right_vals) > 0:
        is_low = all(current_val <= val for val in left_vals) and all(
            current_val <= val for val in right_vals
        )
        is_high = all(current_val >= val for val in left_vals) and all(
            current_val >= val for val in right_vals
        )
      else:
        is_low = all(current_val <= val for val in left_vals)
        is_high = all(current_val <= val for val in left_vals)

      if is_low:
        swings.append({
            "Tanggal": series.index[i],
            "Nilai": current_val,
            "Harga Close": df_in["Close"].iloc[i],
            "Type": "SWING LOW",
            "Status": "Potential",
        })
      elif is_high:
        swings.append({
            "Tanggal": series.index[i],
            "Nilai": current_val,
            "Harga Close": df_in["Close"].iloc[i],
            "Type": "SWING HIGH",
            "Status": "Potential",
        })

  return pd.DataFrame(swings)


def detect_all_divergences(df_data, is_gc, is_dc):
  max_date = df_data.index.max()
  cutoff_scan = max_date - pd.Timedelta(days=30)
  cutoff_fresh = max_date - pd.Timedelta(days=4)

  min_rsi_diff = 3.0
  min_price_diff_pct = 0.015

  div_results = []

  # A. DETEKSI BULLISH DIVERGENCE (SWING LOW)
  p_swings_low = extract_swings(df_data, df_data["Low"])
  p_swings_low = (
      p_swings_low[p_swings_low["Type"] == "SWING LOW"]
      .sort_values("Tanggal", ascending=False)
      .reset_index(drop=True)
  )

  rsi_swings_low = extract_swings(df_data, df_data["RSI_10"])
  rsi_swings_low = (
      rsi_swings_low[rsi_swings_low["Type"] == "SWING LOW"]
      .sort_values("Tanggal", ascending=False)
      .reset_index(drop=True)
  )

  for i in range(len(p_swings_low) - 1):
    right_p = p_swings_low.iloc[i]
    if right_p["Tanggal"] < cutoff_scan or right_p["Tanggal"] < cutoff_fresh:
      continue

    for j in range(i + 1, len(p_swings_low)):
      left_p = p_swings_low.iloc[j]
      days_gap = (right_p["Tanggal"] - left_p["Tanggal"]).days
      if not (4 <= days_gap <= 60):
        continue

      rsi_right_match = rsi_swings_low[
          (rsi_swings_low["Tanggal"] >= right_p["Tanggal"] - pd.Timedelta(days=5))
          & (
              rsi_swings_low["Tanggal"]
              <= right_p["Tanggal"] + pd.Timedelta(days=5)
          )
      ]

      rsi_left_match = rsi_swings_low[
          (rsi_swings_low["Tanggal"] >= left_p["Tanggal"] - pd.Timedelta(days=5))
          & (
              rsi_swings_low["Tanggal"]
              <= left_p["Tanggal"] + pd.Timedelta(days=5)
          )
      ]

      if not rsi_right_match.empty and not rsi_left_match.empty:
        val_rsi_right = rsi_right_match.iloc[0]["Nilai"]
        val_rsi_left = rsi_left_match.iloc[0]["Nilai"]

        price_diff_pct = (
            abs(right_p["Nilai"] - left_p["Nilai"]) / left_p["Nilai"]
        )
        rsi_diff = abs(val_rsi_right - val_rsi_left)

        status_bull = (
            "Valid (GC Confirmed)" if is_gc else "Potensial (Menunggu GC)"
        )
        pattern_type = None

        rsi_in_between = df_data.loc[
            left_p["Tanggal"] : right_p["Tanggal"], "RSI_10"
        ]

        if (
            (right_p["Nilai"] < left_p["Nilai"])
            and (val_rsi_right > val_rsi_left)
            and (val_rsi_right < 30)
        ):
          if (rsi_in_between <= 30).all():
            if (
                price_diff_pct >= min_price_diff_pct
                and rsi_diff >= min_rsi_diff
            ):
              pattern_type = f"Regular Bullish Divergence {status_bull}"

        elif (
            (right_p["Nilai"] >= left_p["Nilai"])
            and (val_rsi_right < val_rsi_left)
            and (35 <= val_rsi_right <= 65)
        ):
          if price_diff_pct >= min_price_diff_pct and rsi_diff >= min_rsi_diff:
            pattern_type = f"Hidden Bullish Divergence {status_bull}"

        if pattern_type:
          div_results.append({
              "Jenis Divergence": pattern_type,
              "Tanggal Kiri": left_p["Tanggal"],
              "Harga Kiri": left_p["Nilai"],
              "RSI Kiri": val_rsi_left,
              "Tanggal Kanan": right_p["Tanggal"],
              "Harga Kanan": right_p["Nilai"],
              "RSI Kanan": val_rsi_right,
          })
          break

  # B. DETEKSI BEARISH DIVERGENCE (SWING HIGH)
  p_swings_high = extract_swings(df_data, df_data["High"])
  p_swings_high = (
      p_swings_high[p_swings_high["Type"] == "SWING HIGH"]
      .sort_values("Tanggal", ascending=False)
      .reset_index(drop=True)
  )

  rsi_swings_high = extract_swings(df_data, df_data["RSI_10"])
  rsi_swings_high = (
      rsi_swings_high[rsi_swings_high["Type"] == "SWING HIGH"]
      .sort_values("Tanggal", ascending=False)
      .reset_index(drop=True)
  )

  for i in range(len(p_swings_high) - 1):
    right_p = p_swings_high.iloc[i]
    if right_p["Tanggal"] < cutoff_scan or right_p["Tanggal"] < cutoff_fresh:
      continue

    for j in range(i + 1, len(p_swings_high)):
      left_p = p_swings_high.iloc[j]
      days_gap = (right_p["Tanggal"] - left_p["Tanggal"]).days
      if not (4 <= days_gap <= 60):
        continue

      rsi_right_match = rsi_swings_high[
          (rsi_swings_high["Tanggal"] >= right_p["Tanggal"] - pd.Timedelta(days=5))
          & (
              rsi_swings_high["Tanggal"]
              <= right_p["Tanggal"] + pd.Timedelta(days=5)
          )
      ]

      rsi_left_match = rsi_swings_high[
          (rsi_swings_high["Tanggal"] >= left_p["Tanggal"] - pd.Timedelta(days=5))
          & (
              rsi_swings_high["Tanggal"]
              <= left_p["Tanggal"] + pd.Timedelta(days=5)
          )
      ]

      if not rsi_right_match.empty and not rsi_left_match.empty:
        val_rsi_right = rsi_right_match.iloc[0]["Nilai"]
        val_rsi_left = rsi_left_match.iloc[0]["Nilai"]

        price_diff_pct = (
            abs(right_p["Nilai"] - left_p["Nilai"]) / left_p["Nilai"]
        )
        rsi_diff = abs(val_rsi_right - val_rsi_left)

        status_bear = (
            "Valid (DC Confirmed)" if is_dc else "Potensial (Menunggu DC)"
        )
        pattern_type = None

        rsi_in_between = df_data.loc[
            left_p["Tanggal"] : right_p["Tanggal"], "RSI_10"
        ]

        if (
            (right_p["Nilai"] > left_p["Nilai"])
            and (val_rsi_right < val_rsi_left)
            and (val_rsi_right > 80)
        ):
          if (rsi_in_between >= 80).all():
            if (
                price_diff_pct >= min_price_diff_pct
                and rsi_diff >= min_rsi_diff
            ):
              pattern_type = f"Regular Bearish Divergence {status_bear}"

        elif (
            (right_p["Nilai"] <= left_p["Nilai"])
            and (val_rsi_right > val_rsi_left)
            and (45 <= val_rsi_right <= 75)
        ):
          if price_diff_pct >= min_price_diff_pct and rsi_diff >= min_rsi_diff:
            pattern_type = f"Hidden Bearish Divergence {status_bear}"

        if pattern_type:
          div_results.append({
              "Jenis Divergence": pattern_type,
              "Tanggal Kiri": left_p["Tanggal"],
              "Harga Kiri": left_p["Nilai"],
              "RSI Kiri": val_rsi_left,
              "Tanggal Kanan": right_p["Tanggal"],
              "Harga Kanan": right_p["Nilai"],
              "RSI Kanan": val_rsi_right,
          })
          break

  res_df = pd.DataFrame(div_results)
  if not res_df.empty:
    res_df = res_df.drop_duplicates(
        subset=["Jenis Divergence", "Tanggal Kiri", "Tanggal Kanan"]
    ).reset_index(drop=True)

  return res_df


def detect_rsi_patterns_and_score(ticker: str):
  """Fungsi utama yang dipanggil oleh app.py untuk melakukan screening RSI Divergence."""
  try:
    df = yf.download(ticker, period="1y", interval="1d", progress=False)
    if df.empty:
      return None

    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    if len(df) < 30:
      return None

    # Hitung indikator
    df["RSI_10"] = df.ta.rsi(close=df["Close"], length=10)
    df["RSI_EMA10"] = df.ta.ema(close=df["RSI_10"], length=10)

    latest_rsi_daily = df["RSI_10"].iloc[-1]
    latest_ema10_daily = df["RSI_EMA10"].iloc[-1]

    is_golden_cross = latest_rsi_daily > latest_ema10_daily
    is_dead_cross = latest_rsi_daily < latest_ema10_daily

    # Deteksi Divergence
    df_div = detect_all_divergences(df, is_golden_cross, is_dead_cross)

    if df_div.empty:
      return None

    # Ambil pola pertama yang ditemukan untuk ditampilkan di ringkasan tabel screener
    first_row = df_div.iloc[0]
    pattern_name = first_row["Jenis Divergence"]

    # Berikan skor sederhana untuk sorting di dashboard (misal: 100 jika valid, 50 jika potensial)
    score = 100 if "Valid" in pattern_name else 50

    return {
        "Ticker": ticker,
        "Saham": ticker.replace(".JK", ""),
        "Pattern": pattern_name,
        "RSI Daily": round(float(latest_rsi_daily), 2),
        "EMA 10 Daily": round(float(latest_ema10_daily), 2),
        "TOTAL SCORE": score,
    }
  except Exception:
    return None