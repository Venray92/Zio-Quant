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
            'Tanggal': series.index[i],
            'Nilai': current_val,
            'Harga Close': df_in['Close'].iloc[i],
            'Type': 'SWING HIGH',
            'Status': 'Confirmed',
        })
      elif all(current_val <= val for val in left_vals) and all(
          current_val < val for val in right_vals
      ):
        swings.append({
            'Tanggal': series.index[i],
            'Nilai': current_val,
            'Harga Close': df_in['Close'].iloc[i],
            'Type': 'SWING LOW',
            'Status': 'Confirmed',
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
        is_high = all(current_val >= val for val in left_vals)

      if is_low:
        swings.append({
            'Tanggal': series.index[i],
            'Nilai': current_val,
            'Harga Close': df_in['Close'].iloc[i],
            'Type': 'SWING LOW',
            'Status': 'Potential',
        })
      elif is_high:
        swings.append({
            'Tanggal': series.index[i],
            'Nilai': current_val,
            'Harga Close': df_in['Close'].iloc[i],
            'Type': 'SWING HIGH',
            'Status': 'Potential',
        })

  return pd.DataFrame(swings)


def detect_rsi_patterns_and_score(ticker):
  try:
    df = yf.download(
        ticker, period='6mo', interval='1d', progress=False, auto_adjust=False
    )
    if df.empty or len(df) < 30:
      return None

    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    # Hitung RSI 10 dan EMA 10 RSI
    df['RSI_10'] = df.ta.rsi(close=df['Close'], length=10)
    df['RSI_EMA10'] = df.ta.ema(close=df['RSI_10'], length=10)
    df = df.dropna(subset=['RSI_10', 'RSI_EMA10'])

    latest_date = df.index.max()

    # Golden Cross / Dead Cross Daily
    latest_rsi = df['RSI_10'].iloc[-1]
    latest_ema = df['RSI_EMA10'].iloc[-1]
    is_gc = latest_rsi > latest_ema
    is_dc = latest_rsi < latest_ema

    min_rsi_diff = 2.5
    min_price_diff_pct = 0.01

    clean_symbol = ticker.replace('.JK', '')

    # ==========================================
    # A. DETEKSI BULLISH DIVERGENCE (SWING LOW)
    # ==========================================
    p_swings_low = extract_swings(df, df['Low'])
    if not p_swings_low.empty:
      p_swings_low = (
          p_swings_low[p_swings_low['Type'] == 'SWING LOW']
          .sort_values('Tanggal', ascending=False)
          .reset_index(drop=True)
      )

    rsi_swings_low = extract_swings(df, df['RSI_10'])
    if not rsi_swings_low.empty:
      rsi_swings_low = (
          rsi_swings_low[rsi_swings_low['Type'] == 'SWING LOW']
          .sort_values('Tanggal', ascending=False)
          .reset_index(drop=True)
      )

    if len(p_swings_low) >= 2 and len(rsi_swings_low) >= 2:
      for i in range(len(p_swings_low) - 1):
        right_p = p_swings_low.iloc[i]

        # Titik Kanan (V2) harus fresh (maksimal 7 hari kalender dari data terbaru)
        if (latest_date - right_p['Tanggal']).days > 7:
          continue

        for j in range(i + 1, len(p_swings_low)):
          left_p = p_swings_low.iloc[j]
          days_gap = (right_p['Tanggal'] - left_p['Tanggal']).days

          # BATAS 1 BULAN: Jarak Kiri ke Kanan minimal 4 hari, maksimal 35 hari kalender
          if not (4 <= days_gap <= 35):
            continue

          # VALIDASI SWING MELOMPAT (Intervening Low Check):
          # Tidak boleh ada Low di antara Tgl Kiri & Kanan yang lebih rendah dari min(Low_Kiri, Low_Kanan)
          between_df = df.loc[left_p['Tanggal'] : right_p['Tanggal']]
          lowest_in_between = between_df['Low'].min()
          allowed_min = min(left_p['Nilai'], right_p['Nilai'])

          if lowest_in_between < (allowed_min * 0.998):
            continue  # Ada low yang lebih rendah melompati garis trend -> Skip!

          # Matching dengan RSI Swing Low
          rsi_right_match = rsi_swings_low[
              (
                  rsi_swings_low['Tanggal']
                  >= right_p['Tanggal'] - pd.Timedelta(days=3)
              )
              & (
                  rsi_swings_low['Tanggal']
                  <= right_p['Tanggal'] + pd.Timedelta(days=3)
              )
          ]
          rsi_left_match = rsi_swings_low[
              (
                  rsi_swings_low['Tanggal']
                  >= left_p['Tanggal'] - pd.Timedelta(days=3)
              )
              & (
                  rsi_swings_low['Tanggal']
                  <= left_p['Tanggal'] + pd.Timedelta(days=3)
              )
          ]

          if not rsi_right_match.empty and not rsi_left_match.empty:
            val_rsi_right = rsi_right_match.iloc[0]['Nilai']
            val_rsi_left = rsi_left_match.iloc[0]['Nilai']

            price_diff_pct = (
                abs(right_p['Nilai'] - left_p['Nilai']) / left_p['Nilai']
            )
            rsi_diff = abs(val_rsi_right - val_rsi_left)

            status_bull = (
                'Valid (GC Confirmed)' if is_gc else 'Potensial (Menunggu GC)'
            )
            pattern_type = None

            # 1. Regular Bullish
            if (
                (right_p['Nilai'] < left_p['Nilai'])
                and (val_rsi_right > val_rsi_left)
                and (val_rsi_right <= 35)
            ):
              if price_diff_pct >= min_price_diff_pct and rsi_diff >= min_rsi_diff:
                pattern_type = f'Regular Bullish Divergence {status_bull}'

            # 2. Hidden Bullish
            elif (
                (right_p['Nilai'] >= left_p['Nilai'])
                and (val_rsi_right < val_rsi_left)
                and (35 <= val_rsi_right <= 65)
            ):
              if price_diff_pct >= min_price_diff_pct and rsi_diff >= min_rsi_diff:
                pattern_type = f'Hidden Bullish Divergence {status_bull}'

            if pattern_type:
              return {
                  'Ticker': ticker,
                  'Saham': clean_symbol,
                  'Pattern': pattern_type,
                  'Tgl Kiri': left_p['Tanggal'].strftime('%Y-%m-%d'),
                  'Harga Kiri': f"Rp {left_p['Nilai']:,.0f}",
                  'RSI Kiri': round(val_rsi_left, 2),
                  'Tgl Kanan': right_p['Tanggal'].strftime('%Y-%m-%d'),
                  'Harga Kanan': f"Rp {right_p['Nilai']:,.0f}",
                  'RSI Kanan': round(val_rsi_right, 2),
              }

    # ==========================================
    # B. DETEKSI BEARISH DIVERGENCE (SWING HIGH)
    # ==========================================
    p_swings_high = extract_swings(df, df['High'])
    if not p_swings_high.empty:
      p_swings_high = (
          p_swings_high[p_swings_high['Type'] == 'SWING HIGH']
          .sort_values('Tanggal', ascending=False)
          .reset_index(drop=True)
      )

    rsi_swings_high = extract_swings(df, df['RSI_10'])
    if not rsi_swings_high.empty:
      rsi_swings_high = (
          rsi_swings_high[rsi_swings_high['Type'] == 'SWING HIGH']
          .sort_values('Tanggal', ascending=False)
          .reset_index(drop=True)
      )

    if len(p_swings_high) >= 2 and len(rsi_swings_high) >= 2:
      for i in range(len(p_swings_high) - 1):
        right_p = p_swings_high.iloc[i]

        if (latest_date - right_p['Tanggal']).days > 7:
          continue

        for j in range(i + 1, len(p_swings_high)):
          left_p = p_swings_high.iloc[j]
          days_gap = (right_p['Tanggal'] - left_p['Tanggal']).days

          if not (4 <= days_gap <= 35):
            continue

          # VALIDASI SWING MELOMPAT (Intervening High Check):
          between_df = df.loc[left_p['Tanggal'] : right_p['Tanggal']]
          highest_in_between = between_df['High'].max()
          allowed_max = max(left_p['Nilai'], right_p['Nilai'])

          if highest_in_between > (allowed_max * 1.002):
            continue  # Ada high yang lebih tinggi melompati garis trend -> Skip!

          rsi_right_match = rsi_swings_high[
              (
                  rsi_swings_high['Tanggal']
                  >= right_p['Tanggal'] - pd.Timedelta(days=3)
              )
              & (
                  rsi_swings_high['Tanggal']
                  <= right_p['Tanggal'] + pd.Timedelta(days=3)
              )
          ]
          rsi_left_match = rsi_swings_high[
              (
                  rsi_swings_high['Tanggal']
                  >= left_p['Tanggal'] - pd.Timedelta(days=3)
              )
              & (
                  rsi_swings_high['Tanggal']
                  <= left_p['Tanggal'] + pd.Timedelta(days=3)
              )
          ]

          if not rsi_right_match.empty and not rsi_left_match.empty:
            val_rsi_right = rsi_right_match.iloc[0]['Nilai']
            val_rsi_left = rsi_left_match.iloc[0]['Nilai']

            price_diff_pct = (
                abs(right_p['Nilai'] - left_p['Nilai']) / left_p['Nilai']
            )
            rsi_diff = abs(val_rsi_right - val_rsi_left)

            status_bear = (
                'Valid (DC Confirmed)' if is_dc else 'Potensial (Menunggu DC)'
            )
            pattern_type = None

            # 3. Regular Bearish
            if (
                (right_p['Nilai'] > left_p['Nilai'])
                and (val_rsi_right < val_rsi_left)
                and (val_rsi_right >= 65)
            ):
              if price_diff_pct >= min_price_diff_pct and rsi_diff >= min_rsi_diff:
                pattern_type = f'Regular Bearish Divergence {status_bear}'

            # 4. Hidden Bearish
            elif (
                (right_p['Nilai'] <= left_p['Nilai'])
                and (val_rsi_right > val_rsi_left)
                and (45 <= val_rsi_right <= 75)
            ):
              if price_diff_pct >= min_price_diff_pct and rsi_diff >= min_rsi_diff:
                pattern_type = f'Hidden Bearish Divergence {status_bear}'

            if pattern_type:
              return {
                  'Ticker': ticker,
                  'Saham': clean_symbol,
                  'Pattern': pattern_type,
                  'Tgl Kiri': left_p['Tanggal'].strftime('%Y-%m-%d'),
                  'Harga Kiri': f"Rp {left_p['Nilai']:,.0f}",
                  'RSI Kiri': round(val_rsi_left, 2),
                  'Tgl Kanan': right_p['Tanggal'].strftime('%Y-%m-%d'),
                  'Harga Kanan': f"Rp {right_p['Nilai']:,.0f}",
                  'RSI Kanan': round(val_rsi_right, 2),
              }

    return None
  except Exception:
    return None
