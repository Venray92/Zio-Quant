# ----------------------------------------------------
# MAIN SCREENER WITH TRUE LINEAR TRENDLINE CHECK
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
        if df.empty or len(df) < 50:
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

        # Calculation EMA untuk Filter Hidden Bullish Trend
        df['EMA_5'] = calculate_ema(df['Close'], period=5)
        df['EMA_10'] = calculate_ema(df['Close'], period=10)
        df['EMA_20'] = calculate_ema(df['Close'], period=20)
        df['EMA_50'] = calculate_ema(df['Close'], period=50)

        df = df.dropna(
            subset=[
                'RSI_10',
                'RSI_EMA10',
                'Vol_MA20',
                'EMA_5',
                'EMA_10',
                'EMA_20',
                'EMA_50',
            ]
        )

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

                    # Titik 2 Wajib di H-1
                    bars_from_latest = latest_idx - right_p_idx
                    if bars_from_latest != 1:
                        continue

                    # Konfirmasi H+1: Price Hari Ini (H0) harus > Price Kemarin (H-1)
                    if latest_close <= right_p['Nilai']:
                        continue

                    for j in range(i + 1, len(p_swings_low)):
                        left_p = p_swings_low.iloc[j]
                        left_p_idx = int(left_p['Index_Pos'])
                        bars_gap = right_p_idx - left_p_idx

                        # Range Jarak Swing 5 - 20 candle
                        if not (5 <= bars_gap <= 20):
                            continue

                        # ----------------------------------------------------
                        # REVISI: TRUE DIAGONAL LINEAR CHECK (BULLISH)
                        # ----------------------------------------------------
                        p1 = left_p['Nilai']
                        p2 = right_p['Nilai']
                        slope = (p2 - p1) / bars_gap

                        is_broken = False
                        # Pengecekan setiap candle di antara T1 dan T2
                        for k in range(1, bars_gap):
                            current_idx = left_p_idx + k
                            # Menggunakan persamaan garis miring: y = p1 + slope * k
                            line_val = p1 + (slope * k)
                            # Toleransi kebocoran 0.2% di bawah garis miring
                            line_limit = line_val * 0.998

                            if df['Low'].iloc[current_idx] < line_limit:
                                is_broken = True
                                break

                        if is_broken:
                            continue

                        val_rsi_right = get_rsi_at_swing(right_p_idx)
                        val_rsi_left = get_rsi_at_swing(left_p_idx)

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
                            p_t2 = df['Close'].iloc[right_p_idx]
                            e5_t2 = df['EMA_5'].iloc[right_p_idx]
                            e10_t2 = df['EMA_10'].iloc[right_p_idx]
                            e20_t2 = df['EMA_20'].iloc[right_p_idx]
                            e50_t2 = df['EMA_50'].iloc[right_p_idx]

                            is_ema_bullish_aligned = (
                                (p_t2 > e5_t2)
                                and (e5_t2 > e10_t2)
                                and (e10_t2 > e20_t2)
                                and (e20_t2 > e50_t2)
                            )

                            if is_ema_bullish_aligned:
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

                    # Titik 2 Wajib di H-1
                    bars_from_latest = latest_idx - right_p_idx
                    if bars_from_latest != 1:
                        continue

                    # Konfirmasi H+1: Price Hari Ini (H0) harus < Price Kemarin (H-1)
                    if latest_close >= right_p['Nilai']:
                        continue

                    for j in range(i + 1, len(p_swings_high)):
                        left_p = p_swings_high.iloc[j]
                        left_p_idx = int(left_p['Index_Pos'])
                        bars_gap = right_p_idx - left_p_idx

                        # Range Jarak Swing 5 - 20 candle
                        if not (5 <= bars_gap <= 20):
                            continue

                        # ----------------------------------------------------
                        # REVISI: TRUE DIAGONAL LINEAR CHECK (BEARISH)
                        # ----------------------------------------------------
                        p1 = left_p['Nilai']
                        p2 = right_p['Nilai']
                        slope = (p2 - p1) / bars_gap

                        is_broken = False
                        # Pengecekan setiap candle di antara T1 dan T2
                        for k in range(1, bars_gap):
                            current_idx = left_p_idx + k
                            # Persamaan garis miring
                            line_val = p1 + (slope * k)
                            # Toleransi kebocoran 0.2% di atas garis miring
                            line_limit = line_val * 1.002

                            if df['High'].iloc[current_idx] > line_limit:
                                is_broken = True
                                break

                        if is_broken:
                            continue

                        val_rsi_right = get_rsi_at_swing_high(right_p_idx)
                        val_rsi_left = get_rsi_at_swing_high(left_p_idx)

                        pattern_type = None

                        # Regular Bearish: RSI 70 - 100
                        if (
                            (right_p['Nilai'] > left_p['Nilai'])
                            and (val_rsi_right < val_rsi_left)
                            and (60 <= val_rsi_right <= 100)
                        ):
                            pattern_type = 'Regular Bearish Divergence'

                        # Hidden Bearish: RSI 30 - 50
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
