import pandas as pd
import yfinance as yf

from engines.market_data import (
    candle_is_final,
    download_daily_batch,
    normalize_ticker,
    now_wib,
)
from engines.market_view import atr_pct
from engines.trade_planner import HIGH_VOL_ATR_PCT


# ----------------------------------------------------
# 0. PARAMETER (ubah angka di sini, tanpa sentuh logika)
# ----------------------------------------------------
MIN_PRICE_DIFF_PCT = 3.0  # selisih harga T1-T2 minimal (%), khusus Regular
MIN_RSI_DIFF = 4.0        # selisih RSI T1-T2 minimal (poin), Regular & Hidden


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
# 3b. HELPER VALIDASI GARIS T1-T2 & BLOK "KAWAH"
# ----------------------------------------------------
def is_price_line_broken(df, left_idx, right_idx, tol_pct=0.2):
    """BULLISH: tarik garis lurus dari Low T1 ke Low T2. Di antara
    keduanya tidak boleh ada Low candle yang menembus ke bawah garis
    itu (toleransi tol_pct persen). True = garis putus (dibuang)."""
    gap = right_idx - left_idx
    if gap <= 1:
        return False
    y1 = float(df['Low'].iloc[left_idx])
    y2 = float(df['Low'].iloc[right_idx])
    for k in range(left_idx + 1, right_idx):
        line_val = y1 + (y2 - y1) * (k - left_idx) / gap
        if float(df['Low'].iloc[k]) < line_val * (1 - tol_pct / 100):
            return True
    return False


def is_price_line_broken_high(df, left_idx, right_idx, tol_pct=0.2):
    """BEARISH: tarik garis lurus dari High T1 ke High T2. Di antara
    keduanya tidak boleh ada High candle yang menembus ke atas garis
    itu (toleransi tol_pct persen). True = garis putus (dibuang)."""
    gap = right_idx - left_idx
    if gap <= 1:
        return False
    y1 = float(df['High'].iloc[left_idx])
    y2 = float(df['High'].iloc[right_idx])
    for k in range(left_idx + 1, right_idx):
        line_val = y1 + (y2 - y1) * (k - left_idx) / gap
        if float(df['High'].iloc[k]) > line_val * (1 + tol_pct / 100):
            return True
    return False


def is_rsi_line_broken(df, pos_left, pos_right, tol_points=1.0):
    """BULLISH: garis lurus dari RSI di T1 ke RSI di T2 (candle persis di
    swing low, bukan dicari-cari di sekitarnya). Di antara keduanya tidak
    boleh ada RSI yang menembus ke bawah garis (toleransi tol_points poin)
    -- kalau RSI sempat anjlok lebih dalam, berarti titik terendahnya bukan
    T1/T2 yang dipakai. True = garis putus (dibuang)."""
    gap = pos_right - pos_left
    if gap <= 1:
        return False
    r1 = float(df['RSI_10'].iloc[pos_left])
    r2 = float(df['RSI_10'].iloc[pos_right])
    for k in range(pos_left + 1, pos_right):
        line_val = r1 + (r2 - r1) * (k - pos_left) / gap
        if float(df['RSI_10'].iloc[k]) < line_val - tol_points:
            return True
    return False


def is_rsi_line_broken_high(df, pos_left, pos_right, tol_points=1.0):
    """BEARISH: garis lurus dari RSI di T1 ke RSI di T2 (candle persis di
    swing high, bukan dicari-cari di sekitarnya). Di antara keduanya tidak
    boleh ada RSI yang menembus ke atas garis (toleransi tol_points poin)
    -- kalau RSI sempat melonjak lebih tinggi, berarti titik tertingginya
    bukan T1/T2 yang dipakai. Pullback/dip di tengah itu wajar (dua swing
    high pasti ada lembah di antaranya) jadi TIDAK dicek ke bawah.
    True = garis putus (dibuang)."""
    gap = pos_right - pos_left
    if gap <= 1:
        return False
    r1 = float(df['RSI_10'].iloc[pos_left])
    r2 = float(df['RSI_10'].iloc[pos_right])
    for k in range(pos_left + 1, pos_right):
        line_val = r1 + (r2 - r1) * (k - pos_left) / gap
        if float(df['RSI_10'].iloc[k]) > line_val + tol_points:
            return True
    return False


def has_crater_between(swing_df, left_idx, right_idx, right_val,
                       max_diff_pct=3.0):
    """Blok 'kawah': kalau di antara T1 dan T2 ada swing lain
    (low utk bullish, high utk bearish) yang harganya dekat T2
    (selisih <= max_diff_pct persen), berarti T1 dilompati dan
    pasangan ini dibuang. True = ada kawah."""
    if right_val <= 0:
        return False
    for _, s in swing_df.iterrows():
        pos = int(s['Index_Pos'])
        if left_idx < pos < right_idx:
            diff_pct = abs(float(s['Nilai']) - right_val) / right_val * 100
            if diff_pct <= max_diff_pct:
                return True
    return False

# ----------------------------------------------------
# 4. MAIN SCREENER WITH REVISED SCORING & LOGIC
# ----------------------------------------------------
def detect_rsi_patterns_and_score(ticker, df=None, now=None):
    """df: (opsional) DataFrame harian siap pakai (mis. dari file harian bersama).
    Kalau None, data diunduh sendiri seperti sebelumnya."""
    try:
        if df is None:
            df = yf.download(
                ticker,
                period='6mo',
                interval='1d',
                progress=False,
                auto_adjust=False,
            )
        else:
            df = df.copy()
            if 'Date' in df.columns:
                df.index = pd.to_datetime(df['Date'])
                df = df.drop(columns=['Date'])
        if df is None or df.empty or len(df) < 30:
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

        # Syarat 2: Filter Likuiditas (rata-rata nilai transaksi 20 hari > 1 Miliar Rupiah)
        latest_volume = df['Volume'].iloc[-1]
        latest_value = latest_volume * latest_close
        avg_value_20 = float(
            (df['Close'] * df['Volume']).rolling(window=20).mean().iloc[-1]
        )
        if not (avg_value_20 > 1_000_000_000):
            return None

        # Indicator Calculation
        df['RSI_10'] = calculate_rsi(df['Close'], period=10)
        df['RSI_EMA10'] = calculate_ema(df['RSI_10'], period=10)
        # Rata-rata volume 20 hari SEBELUM candle yang dievaluasi (sama dengan screener Stoch)
        df['Vol_MA20'] = df['Volume'].rolling(window=20).mean().shift(1)
        df = df.dropna(subset=['RSI_10', 'RSI_EMA10', 'Vol_MA20'])

        latest_idx = len(df) - 1
        clean_symbol = ticker.replace('.JK', '')

        # Saham bergerak liar (ATR harian > HIGH_VOL_ATR_PCT dari harga, sama seperti Trade Planner):
        # RSI-nya jadi sensitif terhadap selisih kecil data antar sumber (server vs market),
        # jadi T1/T2 yang ditampilkan bisa beda cukup jauh dari platform lain. Catatan saja,
        # TIDAK memotong skor (skor tetap soal kualitas struktur pola).
        latest_atr_pct = float(atr_pct(df).iloc[-1])
        is_volatile = latest_atr_pct > HIGH_VOL_ATR_PCT

        # Candle terakhir sudah final? (kalender & jam bursa IDX). Volume candle
        # yang belum final belum lengkap, jadi tidak dihitung sebagai "di atas rata-rata".
        last_candle_ts = pd.Timestamp(df.index[-1])
        candle_final = candle_is_final(last_candle_ts.date(), now or now_wib())
        as_of = last_candle_ts.strftime('%Y-%m-%d')

        # Base Konsolidasi (Max lebar 5%)
        df_bases = detect_bases(df, min_candles=5, max_width_pct=5.0)

        def get_rsi_at_swing(idx_pos):
            # RSI persis di candle T1/T2 (dulu: max/min dalam window +-2 candle,
            # jadi bisa "nyolong" RSI dari tanggal lain -- selisih T1-T2 yang
            # ditampilkan jadi tidak sesuai dengan yang terlihat di chart pada
            # tanggal itu sendiri).
            return float(df['RSI_10'].iloc[idx_pos])

        get_rsi_at_swing_high = get_rsi_at_swing

        # ==========================================
        # A. BULLISH DIVERGENCE (SWING LOW)
        # ==========================================
        p_swings_low = extract_swings(
            df['Low'], left=2, right=2, swing_type='LOW'
        )

        bullish_candidates = []

        if not p_swings_low.empty:
            p_swings_low = p_swings_low.sort_values(
                'Index_Pos', ascending=False
            )

            if len(p_swings_low) >= 2:
                for i in range(len(p_swings_low) - 1):
                    right_p = p_swings_low.iloc[i]
                    right_p_idx = int(right_p['Index_Pos'])

                    # Umur T2 maksimal H+3
                    bars_from_latest = latest_idx - right_p_idx
                    if bars_from_latest > 3:
                        continue

                    # Keluar: close di bawah low T2 = divergence gagal
                    if latest_close < right_p['Nilai']:
                        continue

                    for j in range(i + 1, len(p_swings_low)):
                        left_p = p_swings_low.iloc[j]
                        left_p_idx = int(left_p['Index_Pos'])
                        bars_gap = right_p_idx - left_p_idx

                        # Jarak Swing: 5 - 25 candle
                        if not (5 <= bars_gap <= 25):
                            continue

                        # Lantai: Tidak Boleh Ada Low Lebih Rendah
                        between_df = df.iloc[left_p_idx : right_p_idx + 1]
                        min_boundary = (
                            min(left_p['Nilai'], right_p['Nilai']) * 0.998
                        )
                        if between_df['Low'].min() < min_boundary:
                            continue

                        # Garis miring harga T1 -> T2 tidak boleh putus
                        if is_price_line_broken(
                            df, left_p_idx, right_p_idx
                        ):
                            continue

                        # Blok kawah (ada dasar lain dekat T2 di tengah)
                        if has_crater_between(
                            p_swings_low,
                            left_p_idx,
                            right_p_idx,
                            right_p['Nilai'],
                        ):
                            continue

                        val_rsi_right = get_rsi_at_swing(right_p_idx)
                        val_rsi_left = get_rsi_at_swing(left_p_idx)

                        pattern_type = None

                        # Selisih T1 -> T2 (harga dalam %, RSI dalam poin)
                        price_diff_pct = (
                            (left_p['Nilai'] - right_p['Nilai'])
                            / left_p['Nilai']
                        ) * 100
                        rsi_diff = val_rsi_right - val_rsi_left

                        # Regular Bullish: RSI 0 - 30
                        if (
                            (price_diff_pct >= MIN_PRICE_DIFF_PCT)
                            and (rsi_diff >= MIN_RSI_DIFF)
                            and (0 <= val_rsi_right <= 30)
                        ):
                            pattern_type = 'Regular Bullish Divergence'

                        # Hidden Bullish: RSI >50 - 75
                        elif (
                            (right_p['Nilai'] >= left_p['Nilai'])
                            and (rsi_diff <= -MIN_RSI_DIFF)
                            and (50 < val_rsi_right <= 75)
                        ):
                            pattern_type = 'Hidden Bullish Divergence'

                        if pattern_type:
                            # Garis miring RSI T1 -> T2 tidak boleh putus
                            if is_rsi_line_broken(df, left_p_idx, right_p_idx):
                                continue

                            score = 0

                            # Pengecekan RSI GC & Volume di Rentang H+0 s.d. H+3
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
                                        (candle_final or idx != latest_idx)
                                        and df['Volume'].iloc[idx]
                                        > df['Vol_MA20'].iloc[idx]
                                    ):
                                        has_gc_with_vol = True
                                        break
                                    else:
                                        has_gc_without_vol = True

                            # Wajib ada GC (status Potensial dihapus)
                            if not (has_gc_with_vol or has_gc_without_vol):
                                continue

                            # SKOR (total 100)
                            # 1) GC RSI (wajib, semua dapat): 30
                            score += 30
                            # 2) Volume hari GC di atas rata-rata: 15
                            if has_gc_with_vol:
                                score += 15

                            # 3) Base konsolidasi di antara T1-T2: 20
                            has_base_t1_t2 = False

                            if not df_bases.empty:
                                for _, base in df_bases.iterrows():
                                    b_start = base['Tgl Mulai Base']
                                    b_end = base['Tgl Akhir Base']

                                    if (
                                        b_start >= left_p['Tanggal']
                                        and b_end <= right_p['Tanggal']
                                    ):
                                        has_base_t1_t2 = True

                            base_status_list = []
                            if has_base_t1_t2:
                                score += 20
                                base_status_list.append('Base T1-T2')

                            # 4) Kesegaran umur T2: H+0/H+1=15, H+2=10, H+3=5
                            if bars_from_latest <= 1:
                                score += 15
                            elif bars_from_latest == 2:
                                score += 10
                            else:
                                score += 5

                            # 5) Jarak close ke low T2: <=3%=20, <=5%=10
                            dist_pct = (
                                (latest_close - right_p['Nilai'])
                                / right_p['Nilai']
                            ) * 100
                            if dist_pct <= 3:
                                score += 20
                            elif dist_pct <= 5:
                                score += 10

                            base_desc = (
                                ' & '.join(base_status_list)
                                if base_status_list
                                else 'Tidak Ada Base'
                            )
                            status_str = 'Valid (GC Confirmed)'

                            bullish_candidates.append({
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
                                'Direction': 'Bullish',
                                'T2 Age': int(bars_from_latest),
                                'Dist to T2 (%)': round(dist_pct, 1),
                                'Vol GC': bool(has_gc_with_vol),
                                'Has Base': bool(has_base_t1_t2),
                                'T2 Confirmed': bool(bars_from_latest >= 2),
                                'Candle Final': bool(candle_final),
                                'Data As Of': as_of,
                                'Avg Value 20D (Rp)': f'Rp {avg_value_20:,.0f}',
                                'ATR % Now': round(latest_atr_pct, 1),
                                'Volatile Tinggi': bool(is_volatile),
                            })

        # Ambil pasangan bullish dengan skor tertinggi
        # (skor sama -> T2 paling baru, lalu T1 terdekat)
        if bullish_candidates:
            return max(bullish_candidates, key=lambda c: c['Score'])

        # ==========================================
        # B. BEARISH DIVERGENCE (SWING HIGH)
        # ==========================================
        p_swings_high = extract_swings(
            df['High'], left=2, right=2, swing_type='HIGH'
        )

        bearish_candidates = []

        if not p_swings_high.empty:
            p_swings_high = p_swings_high.sort_values(
                'Index_Pos', ascending=False
            )

            if len(p_swings_high) >= 2:
                for i in range(len(p_swings_high) - 1):
                    right_p = p_swings_high.iloc[i]
                    right_p_idx = int(right_p['Index_Pos'])

                    # Umur T2 maksimal H+3
                    bars_from_latest = latest_idx - right_p_idx
                    if bars_from_latest > 3:
                        continue

                    # Keluar: close di atas high T2 = divergence gagal
                    if latest_close > right_p['Nilai']:
                        continue

                    for j in range(i + 1, len(p_swings_high)):
                        left_p = p_swings_high.iloc[j]
                        left_p_idx = int(left_p['Index_Pos'])
                        bars_gap = right_p_idx - left_p_idx

                        # Jarak Swing: 5 - 25 candle
                        if not (5 <= bars_gap <= 25):
                            continue

                        # Plafon: Tidak Boleh Ada High Lebih Tinggi
                        between_df = df.iloc[left_p_idx : right_p_idx + 1]
                        max_boundary = (
                            max(left_p['Nilai'], right_p['Nilai']) * 1.002
                        )
                        if between_df['High'].max() > max_boundary:
                            continue

                        # Garis miring harga T1 -> T2 tidak boleh putus
                        if is_price_line_broken_high(
                            df, left_p_idx, right_p_idx
                        ):
                            continue

                        # Blok kawah (ada puncak lain dekat T2 di tengah)
                        if has_crater_between(
                            p_swings_high,
                            left_p_idx,
                            right_p_idx,
                            right_p['Nilai'],
                        ):
                            continue

                        val_rsi_right = get_rsi_at_swing_high(right_p_idx)
                        val_rsi_left = get_rsi_at_swing_high(left_p_idx)

                        # Selisih T1 -> T2 (harga dalam %, RSI dalam poin)
                        price_diff_pct = (
                            (right_p['Nilai'] - left_p['Nilai'])
                            / left_p['Nilai']
                        ) * 100
                        rsi_diff = val_rsi_right - val_rsi_left

                        pattern_type = None

                        # Regular Bearish: RSI 70 - 100
                        if (
                            (price_diff_pct >= MIN_PRICE_DIFF_PCT)
                            and (rsi_diff <= -MIN_RSI_DIFF)
                            and (70 <= val_rsi_right <= 100)
                        ):
                            pattern_type = 'Regular Bearish Divergence'

                        # Hidden Bearish: RSI 30 - 50
                        elif (
                            (right_p['Nilai'] <= left_p['Nilai'])
                            and (rsi_diff >= MIN_RSI_DIFF)
                            and (30 <= val_rsi_right <= 50)
                        ):
                            pattern_type = 'Hidden Bearish Divergence'

                        if pattern_type:
                            # Garis miring RSI T1 -> T2 tidak boleh putus
                            if is_rsi_line_broken_high(df, left_p_idx, right_p_idx):
                                continue

                            score = 0

                            # Pengecekan RSI DC & Volume di Rentang H+0 s.d. H+3
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
                                        (candle_final or idx != latest_idx)
                                        and df['Volume'].iloc[idx]
                                        > df['Vol_MA20'].iloc[idx]
                                    ):
                                        has_dc_with_vol = True
                                        break
                                    else:
                                        has_dc_without_vol = True

                            # Wajib ada DC (status Potensial dihapus)
                            if not (has_dc_with_vol or has_dc_without_vol):
                                continue

                            # SKOR (total 100)
                            # 1) DC RSI (wajib, semua dapat): 30
                            score += 30
                            # 2) Volume hari DC di atas rata-rata: 15
                            if has_dc_with_vol:
                                score += 15

                            # 3) Base konsolidasi di antara T1-T2: 20
                            has_base_t1_t2 = False

                            if not df_bases.empty:
                                for _, base in df_bases.iterrows():
                                    b_start = base['Tgl Mulai Base']
                                    b_end = base['Tgl Akhir Base']

                                    if (
                                        b_start >= left_p['Tanggal']
                                        and b_end <= right_p['Tanggal']
                                    ):
                                        has_base_t1_t2 = True

                            base_status_list = []
                            if has_base_t1_t2:
                                score += 20
                                base_status_list.append('Base T1-T2')

                            # 4) Kesegaran umur T2: H+0/H+1=15, H+2=10, H+3=5
                            if bars_from_latest <= 1:
                                score += 15
                            elif bars_from_latest == 2:
                                score += 10
                            else:
                                score += 5

                            # 5) Jarak close ke high T2: <=3%=20, <=5%=10
                            dist_pct = (
                                (right_p['Nilai'] - latest_close)
                                / right_p['Nilai']
                            ) * 100
                            if dist_pct <= 3:
                                score += 20
                            elif dist_pct <= 5:
                                score += 10

                            base_desc = (
                                ' & '.join(base_status_list)
                                if base_status_list
                                else 'Tidak Ada Base'
                            )
                            status_str = 'Valid (DC Confirmed)'

                            bearish_candidates.append({
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
                                'Direction': 'Bearish',
                                'T2 Age': int(bars_from_latest),
                                'Dist to T2 (%)': round(dist_pct, 1),
                                'Vol DC': bool(has_dc_with_vol),
                                'Has Base': bool(has_base_t1_t2),
                                'T2 Confirmed': bool(bars_from_latest >= 2),
                                'Candle Final': bool(candle_final),
                                'Data As Of': as_of,
                                'Avg Value 20D (Rp)': f'Rp {avg_value_20:,.0f}',
                                'ATR % Now': round(latest_atr_pct, 1),
                                'Volatile Tinggi': bool(is_volatile),
                            })

        # Ambil pasangan bearish dengan skor tertinggi
        # (skor sama -> T2 paling baru, lalu T1 terdekat)
        if bearish_candidates:
            return max(bearish_candidates, key=lambda c: c['Score'])

        return None
    except Exception:
        return None


# ----------------------------------------------------
# 5. RUNNER: banyak saham sekaligus (data file bersama + unduh per grup)
# ----------------------------------------------------
def run_rsi_screener(
    tickers,
    progress_callback=None,
    data=None,
    should_stop=None,
    batch_size=50,
    phase_callback=None,
):
    """
    tickers            : list ticker
    progress_callback  : fungsi(completed, total)
    data               : (opsional) {ticker: DataFrame} dari file harian bersama.
                         Ticker yang tidak ada di sini diunduh per grup (maks batch_size).
    should_stop        : (opsional) fungsi tanpa argumen, True = hentikan scan
    phase_callback     : (opsional) fungsi(fase, grup_ke, jumlah_grup, awal, akhir, total),
                         dipanggil sebelum tiap grup diunduh (fase "download")
    Return: (DataFrame hasil, info). Kolom hasil sama seperti detect_rsi_patterns_and_score.
    """
    ordered = list(dict.fromkeys(normalize_ticker(t) for t in tickers))
    total = len(ordered)
    provided = {normalize_ticker(k): v for k, v in (data or {}).items()}

    results, failed = [], []
    from_file = live = completed = 0

    for start in range(0, total, batch_size):
        if should_stop and should_stop():
            break
        chunk = ordered[start:start + batch_size]

        frames, need = {}, []
        for t in chunk:
            d = provided.get(t)
            if d is not None and len(d) > 0:
                frames[t] = d
                from_file += 1
            else:
                need.append(t)
        if need:
            if phase_callback:
                phase_callback(
                    "download",
                    start // batch_size + 1,
                    -(-total // batch_size),
                    start + 1,
                    min(start + batch_size, total),
                    total,
                )
            got = download_daily_batch(need)
            frames.update(got)
            live += len(got)

        for t in chunk:
            d = frames.get(t)
            if d is None:
                failed.append(t)
            else:
                res = detect_rsi_patterns_and_score(t, d)
                if isinstance(res, dict):
                    results.append(res)
            completed += 1
            if progress_callback:
                progress_callback(completed, total)

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by='Score', ascending=False, kind='stable').reset_index(drop=True)

    info = {
        'total': total,
        'success': completed - len(failed),
        'failed': len(failed),
        'failed_tickers': failed,
        'from_file': from_file,
        'downloaded': live,
        'matched': len(df),
    }
    df.attrs['run_info'] = info
    return df, info
