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
# 2. HELPER DETEKSI BASE KONSOLIDASI (REVISI MAX 5%)
# ----------------------------------------------------
def detect_bases(df, min_candles=5, max_width_pct=5.0, window_lookback=60):
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
# 3. HELPER SWING HIGH / LOW (AKURAT & PRESISI)
# ----------------------------------------------------
def extract_swings(series, left=2, right=2, swing_type='LOW'):
    swings = []
    n = len(series)

    for i in range(left, n):
        current_val = series.iloc[i]
        left_vals = series.iloc[i - left : i]

        right_len = min(right, n - 1 - i)
        if right_len == 0:
            right_vals = pd.Series(dtype=float)
        else:
            right_vals = series.iloc[i + 1 : i + 1 + right_len]

        if swing_type == 'HIGH':
            is_left_ok = all(current_val >= val for val in left_vals)
            is_right_ok = (
                all(current_val > val for val in right_vals)
                if len(right_vals) > 0
                else True
            )

            if is_left_ok and is_right_ok:
                swings.append({
                    'Tanggal': series.index[i],
                    'Index_Pos': i,
                    'Nilai': current_val,
                    'Type': 'SWING HIGH',
                })

        elif swing_type == 'LOW':
            is_left_ok = all(current_val <= val for val in left_vals)
            is_right_ok = (
                all(current_val < val for val in right_vals)
                if len(right_vals) > 0
                else True
            )

            if is_left_ok and is_right_ok:
                swings.append({
                    'Tanggal': series.index[i],
                    'Index_Pos': i,
                    'Nilai': current_val,
                    'Type': 'SWING LOW',
                })

    return pd.DataFrame(swings)


# ----------------------------------------------------
# 4. MAIN SCREENER WITH REVISED SCORING & LOGIC
# ----------------------------------------------------
def detect_rsi_patterns_and_score(ticker):
    try:
        df = yf.download(
            ticker,
            period='6mo',
            interval='1d',
            progress=False,
            auto_adjust=False,
        )
        if df.empty or len(df) < 30:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Hitung Harga & % Change
        latest_close = float(df['Close'].iloc[-1])
        prev_close = (
            float(df['Close'].iloc[-2]) if len(df) >= 2 else latest_close
        )
        change_pct = (
            ((latest_close - prev_close) / prev_close) * 100
            if prev_close > 0
            else 0.0
        )

        # Syarat 1: Price > 70
        if latest_close <= 70:
            return None

        # Syarat 2: Filter Likuiditas (> 1 Miliar Rupiah)
        latest_volume = df['Volume'].iloc[-1]
        latest_value = latest_volume * latest_close
        if latest_value <= 1_000_000_000:
            return None

        # Indicator Calculation
        df['RSI_10'] = calculate_rsi(df['Close'], period=10)
        df['RSI_EMA10'] = calculate_ema(df['RSI_10'], period=10)
        df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
        df = df.dropna(subset=['RSI_10', 'RSI_EMA10', 'Vol_MA20'])

        latest_idx = len(df) - 1
        clean_symbol = ticker.replace('.JK', '')

        # Base Konsolidasi (Max lebar 5%)
        df_bases = detect_bases(df, min_candles=5, max_width_pct=5.0)

        def get_rsi_at_swing(idx_pos, window=2):
            start = max(0, idx_pos - window)
            end = min(len(df) - 1, idx_pos + window)
            return df['RSI_10'].iloc[start : end + 1].min()

        def get_rsi_at_swing_high(idx_pos, window=2):
            start = max(0, idx_pos - window)
            end = min(len(df) - 1, idx_pos + window)
            return df['RSI_10'].iloc[start : end + 1].max()

        # ==========================================
        # A. BULLISH DIVERGENCE (SWING LOW)
        # ==========================================
        p_swings_low = extract_swings(
            df['Low'], left=2, right=2, swing_type='LOW'
        )

        if not p_swings_low.empty:
            p_swings_low = p_swings_low.sort_values(
                'Index_Pos', ascending=False
            )

            if len(p_swings_low) >= 2:
                for i in range(len(p_swings_low) - 1):
                    right_p = p_swings_low.iloc[i]
                    right_p_idx = int(right_p['Index_Pos'])

                    bars_from_latest = latest_idx - right_p_idx
                    if bars_from_latest > 3:
                        continue

                    for j in range(i + 1, len(p_swings_low)):
                        left_p = p_swings_low.iloc[j]
                        left_p_idx = int(left_p['Index_Pos'])
                        bars_gap = right_p_idx - left_p_idx

                        # Revisi Jarak Swing: 5 - 25 candle
                        if not (5 <= bars_gap <= 25):
                            continue

                        val_rsi_right = get_rsi_at_swing(right_p_idx)
                        val_rsi_left = get_rsi_at_swing(left_p_idx)

                        # --- STRICT LINE CHECK (CANDLE LOW-TO-LOW & RSI) ---
                        price_low_t1 = left_p['Nilai']
                        price_low_t2 = right_p['Nilai']
                        trend_break = False

                        for step in range(1, bars_gap):
                            curr_idx = left_p_idx + step
                            
                            # 1. Garis Miring Harga (Low to Low Wicks)
                            expected_price_low = price_low_t1 + ((price_low_t2 - price_low_t1) / bars_gap) * step
                            actual_price_low = df['Low'].iloc[curr_idx]
                            
                            # 2. Garis Miring RSI
                            expected_rsi = val_rsi_left + ((val_rsi_right - val_rsi_left) / bars_gap) * step
                            actual_rsi = df['RSI_10'].iloc[curr_idx]

                            # Cek Penembusan (Toleransi 0.2% untuk Harga, 0.5 poin untuk RSI)
                            if (actual_price_low < expected_price_low * 0.998) or (actual_rsi < expected_rsi - 0.5):
                                trend_break = True
                                break

                        if trend_break:
                            continue

                        pattern_type = None

                        # Regular Bullish: RSI 0 - 30
                        if (
                            (right_p['Nilai'] < left_p['Nilai'])
                            and (val_rsi_right > val_rsi_left)
                            and (0 <= val_rsi_right <= 30)
                        ):
                            pattern_type = 'Regular Bullish Divergence'

                        # Hidden Bullish: RSI >50 - 75
                        elif (
                            (right_p['Nilai'] >= left_p['Nilai'])
                            and (val_rsi_right < val_rsi_left)
                            and (50 < val_rsi_right <= 75)
                        ):
                            pattern_type = 'Hidden Bullish Divergence'

                        if pattern_type:
                            score = 0

                            has_gc_with_vol = False
                            has_gc_without_vol = False

                            eval_end = min(latest_idx + 1, right_p_idx + 4)
                            for idx in range(right_p_idx, eval_end):
                                rsi_curr = df['RSI_10'].iloc[idx]
                                rsi_ema_curr = df['RSI_EMA10'].iloc[idx]
                                rsi_prev = df['RSI_10'].iloc[idx - 1]
                                rsi_ema_prev = df['RSI_EMA10'].iloc[idx - 1]

                                is_gc = (rsi_curr > rsi_ema_curr) and (
                                    rsi_prev <= rsi_ema_prev
                                )
                                if is_gc:
                                    if (
                                        df['Volume'].iloc[idx]
                                        > df['Vol_MA20'].iloc[idx]
                                    ):
                                        has_gc_with_vol = True
                                        break
                                    else:
                                        has_gc_without_vol = True

                            if has_gc_with_vol:
                                score += 50
                            elif has_gc_without_vol:
                                score += 40

                            if val_rsi_right >= val_rsi_left:
                                score += 20

                            has_base_t1_t2 = False
                            has_base_after_t2 = False

                            if not df_bases.empty:
                                for _, base in df_bases.iterrows():
                                    b_start = base['Tgl Mulai Base']
                                    b_end = base['Tgl Akhir Base']

                                    if (
                                        b_start >= left_p['Tanggal']
                                        and b_end <= right_p['Tanggal']
                                    ):
                                        has_base_t1_t2 = True

                                    if b_start >= right_p['Tanggal']:
                                        has_base_after_t2 = True

                            base_status_list = []
                            if has_base_t1_t2:
                                score += 20
                                base_status_list.append('Base T1-T2')
                            if has_base_after_t2:
                                score += 20
                                base_status_list.append('Base Post-T2')

                            base_desc = (
                                ' & '.join(base_status_list)
                                if base_status_list
                                else 'Tidak Ada Base'
                            )
                            status_str = (
                                'Valid (GC Confirmed)'
                                if (has_gc_with_vol or has_gc_without_vol)
                                else 'Potensial'
                            )

                            return {
                                'Ticker': ticker,
                                'Saham': clean_symbol,
                                'Pattern': f'{pattern_type} {status_str}',
                                'Score': score,
                                'Status Base': base_desc,
                                'Value (Rp)': f'Rp {latest_value:,.0f}',
                                'Close_Price': latest_close,
                                'Change_Pct': round(change_pct, 2),
                                'Tgl Kiri': left_p['Tanggal'].strftime(
                                    '%Y-%m-%d'
                                ),
                                'Harga Kiri': f"Rp {left_p['Nilai']:,.0f}",
                                'RSI Kiri': round(val_rsi_left, 2),
                                'Tgl Kanan': right_p['Tanggal'].strftime(
                                    '%Y-%m-%d'
                                ),
                                'Harga Kanan': f"Rp {right_p['Nilai']:,.0f}",
                                'RSI Kanan': round(val_rsi_right, 2),
                            }

        # ==========================================
        # B. BEARISH DIVERGENCE (SWING HIGH)
        # ==========================================
        p_swings_high = extract_swings(
            df['High'], left=2, right=2, swing_type='HIGH'
        )

        if not p_swings_high.empty:
            p_swings_high = p_swings_high.sort_values(
                'Index_Pos', ascending=False
            )

            if len(p_swings_high) >= 2:
                for i in range(len(p_swings_high) - 1):
                    right_p = p_swings_high.iloc[i]
                    right_p_idx = int(right_p['Index_Pos'])

                    bars_from_latest = latest_idx - right_p_idx
                    if bars_from_latest > 3:
                        continue

                    for j in range(i + 1, len(p_swings_high)):
                        left_p = p_swings_high.iloc[j]
                        left_p_idx = int(left_p['Index_Pos'])
                        bars_gap = right_p_idx - left_p_idx

                        if not (5 <= bars_gap <= 25):
                            continue

                        val_rsi_right = get_rsi_at_swing_high(right_p_idx)
                        val_rsi_left = get_rsi_at_swing_high(left_p_idx)

                        # --- STRICT LINE CHECK (CANDLE HIGH-TO-HIGH & RSI) ---
                        price_high_t1 = left_p['Nilai']
                        price_high_t2 = right_p['Nilai']
                        trend_break = False

                        for step in range(1, bars_gap):
                            curr_idx = left_p_idx + step
                            
                            # 1. Garis Miring Harga (High to High Wicks)
                            expected_price_high = price_high_t1 + ((price_high_t2 - price_high_t1) / bars_gap) * step
                            actual_price_high = df['High'].iloc[curr_idx]
                            
                            # 2. Garis Miring RSI
                            expected_rsi = val_rsi_left + ((val_rsi_right - val_rsi_left) / bars_gap) * step
                            actual_rsi = df['RSI_10'].iloc[curr_idx]

                            # Cek Penembusan (Toleransi 0.2% untuk Harga, 0.5 poin untuk RSI)
                            if (actual_price_high > expected_price_high * 1.002) or (actual_rsi > expected_rsi + 0.5):
                                trend_break = True
                                break

                        if trend_break:
                            continue

                        pattern_type = None

                        # Regular Bearish: RSI 60 - 100
                        if (
                            (right_p['Nilai'] > left_p['Nilai'])
                            and (val_rsi_right < val_rsi_left)
                            and (60 <= val_rsi_right <= 100)
                        ):
                            pattern_type = 'Regular Bearish Divergence'

                        # Hidden Bearish: RSI 30 - 60
                        elif (
                            (right_p['Nilai'] <= left_p['Nilai'])
                            and (val_rsi_right > val_rsi_left)
                            and (30 <= val_rsi_right <= 60)
                        ):
                            pattern_type = 'Hidden Bearish Divergence'

                        if pattern_type:
                            score = 0

                            has_dc_with_vol = False
                            has_dc_without_vol = False

                            eval_end = min(latest_idx + 1, right_p_idx + 4)
                            for idx in range(right_p_idx, eval_end):
                                rsi_curr = df['RSI_10'].iloc[idx]
                                rsi_ema_curr = df['RSI_EMA10'].iloc[idx]
                                rsi_prev = df['RSI_10'].iloc[idx - 1]
                                rsi_ema_prev = df['RSI_EMA10'].iloc[idx - 1]

                                is_dc = (rsi_curr < rsi_ema_curr) and (
                                    rsi_prev >= rsi_ema_prev
                                )
                                if is_dc:
                                    if (
                                        df['Volume'].iloc[idx]
                                        > df['Vol_MA20'].iloc[idx]
                                    ):
                                        has_dc_with_vol = True
                                        break
                                    else:
                                        has_dc_without_vol = True

                            if has_dc_with_vol:
                                score += 50
                            elif has_dc_without_vol:
                                score += 40

                            if val_rsi_right <= val_rsi_left:
                                score += 20

                            has_base_t1_t2 = False
                            has_base_after_t2 = False

                            if not df_bases.empty:
                                for _, base in df_bases.iterrows():
                                    b_start = base['Tgl Mulai Base']
                                    b_end = base['Tgl Akhir Base']

                                    if (
                                        b_start >= left_p['Tanggal']
                                        and b_end <= right_p['Tanggal']
                                    ):
                                        has_base_t1_t2 = True

                                    if b_start >= right_p['Tanggal']:
                                        has_base_after_t2 = True

                            base_status_list = []
                            if has_base_t1_t2:
                                score += 20
                                base_status_list.append('Base T1-T2')
                            if has_base_after_t2:
                                score += 20
                                base_status_list.append('Base Post-T2')

                            base_desc = (
                                ' & '.join(base_status_list)
                                if base_status_list
                                else 'Tidak Ada Base'
                            )
                            status_str = (
                                'Valid (DC Confirmed)'
                                if (has_dc_with_vol or has_dc_without_vol)
                                else 'Potensial'
                            )

                            return {
                                'Ticker': ticker,
                                'Saham': clean_symbol,
                                'Pattern': f'{pattern_type} {status_str}',
                                'Score': score,
                                'Status Base': base_desc,
                                'Value (Rp)': f'Rp {latest_value:,.0f}',
                                'Close_Price': latest_close,
                                'Change_Pct': round(change_pct, 2),
                                'Tgl Kiri': left_p['Tanggal'].strftime(
                                    '%Y-%m-%d'
                                ),
                                'Harga Kiri': f"Rp {left_p['Nilai']:,.0f}",
                                'RSI Kiri': round(val_rsi_left, 2),
                                'Tgl Kanan': right_p['Tanggal'].strftime(
                                    '%Y-%m-%d'
                                ),
                                'Harga Kanan': f"Rp {right_p['Nilai']:,.0f}",
                                'RSI Kanan': round(val_rsi_right, 2),
                            }

        return None
    except Exception:
        return None
