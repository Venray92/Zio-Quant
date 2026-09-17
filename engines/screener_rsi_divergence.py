import pandas as pd
import yfinance as yf


# ----------------------------------------------------
# 1. HELPER MATHS & INDICATORS
# ----------------------------------------------------
def calculate_rsi(series, period=10):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).copy()
    loss = (-delta.where(delta < 0, 0)).copy()

    avg_gain = gain.ewm(
        alpha=1 / period, min_periods=period, adjust=False
    ).mean()
    avg_loss = loss.ewm(
        alpha=1 / period, min_periods=period, adjust=False
    ).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_ema(series, period=10):
    return series.ewm(span=period, adjust=False).mean()


# ----------------------------------------------------
# 2. HELPER DETEKSI BASE KONSOLIDASI
# ----------------------------------------------------
def detect_bases(df, min_candles=5, max_width_pct=8.0, window_lookback=60):
    bases = []
    sub_df = df.tail(window_lookback)
    n = len(sub_df)

    i = 0
    while i <= n - min_candles:
        found_base = None
        for length in range(min_candles, min(20, n - i + 1)):
            window = sub_df.iloc[i : i + length]
            base_low = window['Low'].min()
            base_high = window['High'].max()

            if base_low == 0:
                continue

            width_pct = ((base_high - base_low) / base_low) * 100

            if width_pct <= max_width_pct:
                found_base = {
                    'Tgl Mulai Base': window.index[0],
                    'Tgl Akhir Base': window.index[-1],
                    'Jumlah Candle': length,
                    'Base Support': base_low,
                    'Base Resistance': base_high,
                    'Lebar Konsolidasi (%)': round(width_pct, 2),
                }
            else:
                break

        if found_base:
            bases.append(found_base)
            i += found_base['Jumlah Candle']
        else:
            i += 1

    return pd.DataFrame(bases)


# ----------------------------------------------------
# 3. HELPER SWING HIGH / LOW
# ----------------------------------------------------
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
                    'Index_Pos': i,
                    'Nilai': current_val,
                    'Type': 'SWING HIGH',
                    'Status': 'Confirmed',
                })
            elif all(current_val <= val for val in left_vals) and all(
                current_val < val for val in right_vals
            ):
                swings.append({
                    'Tanggal': series.index[i],
                    'Index_Pos': i,
                    'Nilai': current_val,
                    'Type': 'SWING LOW',
                    'Status': 'Confirmed',
                })

    return pd.DataFrame(swings)


# ----------------------------------------------------
# 4. MAIN SCREENER WITH INTEGRATED SCORING SYSTEM
# ----------------------------------------------------
def detect_rsi_patterns_and_score(ticker):
    try:
        df = yf.download(
            ticker, period='6mo', interval='1d', progress=False, auto_adjust=False
        )
        if df.empty or len(df) < 30:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Hitung Harga & % Change
        latest_close = float(df['Close'].iloc[-1])
        prev_close = float(df['Close'].iloc[-2]) if len(df) >= 2 else latest_close
        change_pct = ((latest_close - prev_close) / prev_close) * 100 if prev_close > 0 else 0.0

        # Filter Likuiditas (> 1 Miliar Rupiah)
        latest_volume = df['Volume'].iloc[-1]
        latest_value = latest_volume * latest_close

        if latest_value <= 1_000_000_000:
            return None

        # Calculate Indicators
        df['RSI_10'] = calculate_rsi(df['Close'], period=10)
        df['RSI_EMA10'] = calculate_ema(df['RSI_10'], period=10)
        df = df.dropna(subset=['RSI_10', 'RSI_EMA10'])

        latest_idx = len(df) - 1
        latest_rsi = df['RSI_10'].iloc[-1]
        latest_ema = df['RSI_EMA10'].iloc[-1]

        is_gc = latest_rsi > latest_ema
        is_dc = latest_rsi < latest_ema

        min_rsi_diff = 2.5
        min_price_diff_pct = 0.02
        clean_symbol = ticker.replace('.JK', '')

        df_bases = detect_bases(df, min_candles=5, max_width_pct=8.0)

        # Helper evaluasi base + skornya
        def evaluate_base_score(tgl_titik_1, tgl_titik_2):
            if df_bases.empty:
                return 'Tidak Ada Base', 0

            has_base_t1, has_base_t2 = False, False
            width_t1, width_t2 = 0.0, 0.0

            for _, base in df_bases.iterrows():
                start_t1 = base['Tgl Mulai Base'] - pd.Timedelta(days=5)
                end_t1 = base['Tgl Akhir Base'] + pd.Timedelta(days=5)
                if start_t1 <= tgl_titik_1 <= end_t1:
                    has_base_t1 = True
                    width_t1 = base['Lebar Konsolidasi (%)']

                if (
                    base['Tgl Mulai Base'] >= tgl_titik_1
                    and base['Tgl Akhir Base'] <= tgl_titik_2
                ):
                    if (tgl_titik_2 - base['Tgl Akhir Base']).days <= 5:
                        has_base_t2 = True
                        width_t2 = base['Lebar Konsolidasi (%)']

            if has_base_t1 and has_base_t2:
                return f'Grade A++ (T1: {width_t1}% | T2: {width_t2}%)', 30
            elif has_base_t2:
                return f'Ada Base Sblm Titik 2 ({width_t2}%)', 20
            elif has_base_t1:
                return f'Ada Base Titik 1 ({width_1}%)', 10
            else:
                return 'Tidak Ada Base', 0

        # ==========================================
        # A. BULLISH DIVERGENCE (SWING LOW)
        # ==========================================
        p_swings_low = extract_swings(df, df['Low'])
        rsi_swings_low = extract_swings(df, df['RSI_10'])

        if not p_swings_low.empty and not rsi_swings_low.empty:
            p_swings_low = p_swings_low[
                p_swings_low['Type'] == 'SWING LOW'
            ].sort_values('Index_Pos', ascending=False)
            rsi_swings_low = rsi_swings_low[
                rsi_swings_low['Type'] == 'SWING LOW'
            ].sort_values('Index_Pos', ascending=False)

            if len(p_swings_low) >= 2 and len(rsi_swings_low) >= 2:
                for i in range(len(p_swings_low) - 1):
                    right_p = p_swings_low.iloc[i]

                    bars_from_latest = latest_idx - right_p['Index_Pos']
                    if bars_from_latest > 2:
                        continue

                    for j in range(i + 1, len(p_swings_low)):
                        left_p = p_swings_low.iloc[j]
                        bars_gap = right_p['Index_Pos'] - left_p['Index_Pos']

                        if not (4 <= bars_gap <= 25):
                            continue

                        between_df = df.iloc[
                            int(left_p['Index_Pos']) : int(right_p['Index_Pos']) + 1
                        ]
                        if between_df['Low'].min() < (
                            min(left_p['Nilai'], right_p['Nilai']) * 0.998
                        ):
                            continue

                        rsi_right_match = rsi_swings_low[
                            abs(rsi_swings_low['Index_Pos'] - right_p['Index_Pos']) <= 3
                        ]
                        rsi_left_match = rsi_swings_low[
                            abs(rsi_swings_low['Index_Pos'] - left_p['Index_Pos']) <= 3
                        ]

                        if not rsi_right_match.empty and not rsi_left_match.empty:
                            val_rsi_right = rsi_right_match.iloc[0]['Nilai']
                            val_rsi_left = rsi_left_match.iloc[0]['Nilai']
                            price_diff_pct = (
                                abs(right_p['Nilai'] - left_p['Nilai']) / left_p['Nilai']
                            )
                            rsi_diff = abs(val_rsi_right - val_rsi_left)

                            pattern_type = None

                            if (
                                (right_p['Nilai'] < left_p['Nilai'])
                                and (val_rsi_right > val_rsi_left)
                                and (val_rsi_right <= 35)
                            ):
                                if (
                                    price_diff_pct >= min_price_diff_pct
                                    and rsi_diff >= min_rsi_diff
                                ):
                                    pattern_type = 'Regular Bullish Divergence'

                            elif (
                                (right_p['Nilai'] >= left_p['Nilai'])
                                and (val_rsi_right < val_rsi_left)
                                and (35 <= val_rsi_right <= 65)
                            ):
                                if (
                                    price_diff_pct >= min_price_diff_pct
                                    and rsi_diff >= min_rsi_diff
                                ):
                                    pattern_type = 'Hidden Bullish Divergence'

                            if pattern_type:
                                base_desc, base_score = evaluate_base_score(
                                    left_p['Tanggal'], right_p['Tanggal']
                                )

                                score = 0
                                confirm_score = 30 if is_gc else 15
                                score += confirm_score
                                score += base_score

                                if rsi_diff >= 5.0 and price_diff_pct >= 0.03:
                                    score += 20
                                else:
                                    score += 10

                                if val_rsi_right <= 30:
                                    score += 20
                                elif val_rsi_right <= 35:
                                    score += 10

                                status_bull = (
                                    'Valid (GC Confirmed)'
                                    if is_gc
                                    else 'Potensial (Menunggu GC)'
                                )

                                return {
                                    'Ticker': ticker,
                                    'Saham': clean_symbol,
                                    'Pattern': f'{pattern_type} {status_bull}',
                                    'Score': score,
                                    'Status Base': base_desc,
                                    'Value (Rp)': f'Rp {latest_value:,.0f}',
                                    'Close_Price': latest_close,
                                    'Change_Pct': round(change_pct, 2),
                                    'Tgl Kiri': left_p['Tanggal'].strftime('%Y-%m-%d'),
                                    'Harga Kiri': f"Rp {left_p['Nilai']:,.0f}",
                                    'RSI Kiri': round(val_rsi_left, 2),
                                    'Tgl Kanan': right_p['Tanggal'].strftime('%Y-%m-%d'),
                                    'Harga Kanan': f"Rp {right_p['Nilai']:,.0f}",
                                    'RSI Kanan': round(val_rsi_right, 2),
                                }

        # ==========================================
        # B. BEARISH DIVERGENCE (SWING HIGH)
        # ==========================================
        p_swings_high = extract_swings(df, df['High'])
        rsi_swings_high = extract_swings(df, df['RSI_10'])

        if not p_swings_high.empty and not rsi_swings_high.empty:
            p_swings_high = p_swings_high[
                p_swings_high['Type'] == 'SWING HIGH'
            ].sort_values('Index_Pos', ascending=False)
            rsi_swings_high = rsi_swings_high[
                rsi_swings_high['Type'] == 'SWING HIGH'
            ].sort_values('Index_Pos', ascending=False)

            if len(p_swings_high) >= 2 and len(rsi_swings_high) >= 2:
                for i in range(len(p_swings_high) - 1):
                    right_p = p_swings_high.iloc[i]

                    bars_from_latest = latest_idx - right_p['Index_Pos']
                    if bars_from_latest > 2:
                        continue

                    for j in range(i + 1, len(p_swings_high)):
                        left_p = p_swings_high.iloc[j]
                        bars_gap = right_p['Index_Pos'] - left_p['Index_Pos']

                        if not (4 <= bars_gap <= 25):
                            continue

                        between_df = df.iloc[
                            int(left_p['Index_Pos']) : int(right_p['Index_Pos']) + 1
                        ]
                        if between_df['High'].max() > (
                            max(left_p['Nilai'], right_p['Nilai']) * 1.002
                        ):
                            continue

                        rsi_right_match = rsi_swings_high[
                            abs(rsi_swings_high['Index_Pos'] - right_p['Index_Pos']) <= 3
                        ]
                        rsi_left_match = rsi_swings_high[
                            abs(rsi_swings_high['Index_Pos'] - left_p['Index_Pos']) <= 3
                        ]

                        if not rsi_right_match.empty and not rsi_left_match.empty:
                            val_rsi_right = rsi_right_match.iloc[0]['Nilai']
                            val_rsi_left = rsi_left_match.iloc[0]['Nilai']
                            price_diff_pct = (
                                abs(right_p['Nilai'] - left_p['Nilai']) / left_p['Nilai']
                            )
                            rsi_diff = abs(val_rsi_right - val_rsi_left)

                            pattern_type = None

                            if (
                                (right_p['Nilai'] > left_p['Nilai'])
                                and (val_rsi_right < val_rsi_left)
                                and (val_rsi_right >= 65)
                            ):
                                if (
                                    price_diff_pct >= min_price_diff_pct
                                    and rsi_diff >= min_rsi_diff
                                ):
                                    pattern_type = 'Regular Bearish Divergence'

                            elif (
                                (right_p['Nilai'] <= left_p['Nilai'])
                                and (val_rsi_right > val_rsi_left)
                                and (45 <= val_rsi_right <= 75)
                            ):
                                if (
                                    price_diff_pct >= min_price_diff_pct
                                    and rsi_diff >= min_rsi_diff
                                ):
                                    pattern_type = 'Hidden Bearish Divergence'

                            if pattern_type:
                                base_desc, base_score = evaluate_base_score(
                                    left_p['Tanggal'], right_p['Tanggal']
                                )

                                score = 0
                                confirm_score = 30 if is_dc else 15
                                score += confirm_score
                                score += base_score

                                if rsi_diff >= 5.0 and price_diff_pct >= 0.03:
                                    score += 20
                                else:
                                    score += 10

                                if val_rsi_right >= 70:
                                    score += 20
                                elif val_rsi_right >= 65:
                                    score += 10

                                status_bear = (
                                    'Valid (DC Confirmed)'
                                    if is_dc
                                    else 'Potensial (Menunggu DC)'
                                )

                                return {
                                    'Ticker': ticker,
                                    'Saham': clean_symbol,
                                    'Pattern': f'{pattern_type} {status_bear}',
                                    'Score': score,
                                    'Status Base': base_desc,
                                    'Value (Rp)': f'Rp {latest_value:,.0f}',
                                    'Close_Price': latest_close,
                                    'Change_Pct': round(change_pct, 2),
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
