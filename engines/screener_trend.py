"""Trend Scanner: 3 mode berbasis struktur harga & volume (bukan oscillator seperti RSI/Stoch).

  Breakout Surge     : saham baru tembus resistance disertai lonjakan volume.
  Trend Reset        : saham tren naik yang lagi koreksi sehat ke area support.
  Quiet Accumulation : saham harga menyempit (squeeze) sambil volume naik -- layak dipantau,
                        BUKAN sinyal beli (tanpa skor, tanpa arah).

Semua threshold di bagian PARAMETER adalah titik awal ("best effort"), bisa disesuaikan
setelah kelihatan hasilnya di data riil -- sama seperti preset Money Management.
"""
import numpy as np
import pandas as pd

from engines.market_data import candle_is_final, download_daily_batch, normalize_ticker, now_wib
from engines.market_view import atr_pct, ema, swing_points
from engines.trade_planner import HIGH_VOL_ATR_PCT

# ---------------------------------------------------------------- PARAMETER
MIN_PRICE = 50
MIN_VALUE_RP = 1_000_000_000      # likuiditas: rata-rata nilai transaksi 20 hari
MIN_BARS_TREND = 210              # Breakout Surge & Trend Reset butuh EMA200
MIN_BARS_SQUEEZE = 60             # Quiet Accumulation cukup EMA20 + ATR14

# Breakout Surge
BRK_HIGH_LOOKBACK = 20            # tembus level tertinggi N candle (tidak termasuk hari ini)
BRK_BASE_LOOKBACK = BRK_HIGH_LOOKBACK  # jendela cek "lagi ngumpul" -- SAMA dgn jendela level tembus (dulu 15 vs 20, tidak sinkron)
BRK_BASE_MAX_WIDTH_PCT = 12.0
BRK_VOL_MULT = 2.0
BRK_MAX_AGE = 2                   # tembus maksimal H+2
BRK_BONUS_VOL_MULT = 3.0
BRK_BONUS_DIST_PCT = 5.0
BRK_SQUEEZE_LOOKBACK = (5, 10)     # cek status squeeze N hari sebelum tembus (rentang hari ke belakang)

# Trend Reset
RST_TREND_MIN_BARS = 20           # tren (Close>EMA50>EMA200) harus bertahan >= N candle
RST_SHALLOW_PCT = 8.0
RST_VOL_BOUNCE_MULT = 1.2

# Quiet Accumulation
SQZ_BB_PERIOD = 20
SQZ_BB_STD = 2.0
SQZ_KC_PERIOD = 20
SQZ_KC_ATR_MULT = 1.5
SQZ_WIDTH_LOOKBACK = 60           # "tersempit dalam N hari", dibatasi maks segini
SQZ_MAX_DECLINE_PCT = 15.0        # kalau turun lebih dari ini dlm SQZ_DECLINE_LOOKBACK hari terakhir,
                                   # dianggap baru saja jebol support, bukan squeeze asli
SQZ_DECLINE_LOOKBACK = 40         # sengaja LEBIH PANJANG dari SQZ_BB_PERIOD (20): begitu Bollinger Band
                                   # "lupa" sama hari jebolnya (~20-30 hari), pengecekan ini masih inget


# ---------------------------------------------------------------- indikator tambahan (Bollinger & Keltner)
def bollinger_bands(close, n=SQZ_BB_PERIOD, k=SQZ_BB_STD):
    mid = close.rolling(n).mean()
    sd = close.rolling(n).std(ddof=0)
    return mid, mid + k * sd, mid - k * sd


def keltner_channel(df, n=SQZ_KC_PERIOD, mult=SQZ_KC_ATR_MULT):
    mid = ema(df["Close"], n)
    a = atr_pct(df, 14) * df["Close"] / 100  # ATR absolut (atr_pct sudah dites, tinggal balikin ke satuan harga)
    return mid, mid + mult * a, mid - mult * a


def squeeze_series(df):
    """True di hari-hari Bollinger Band berada di DALAM Keltner Channel (harga lagi menyempit)."""
    _, bb_hi, bb_lo = bollinger_bands(df["Close"])
    _, kc_hi, kc_lo = keltner_channel(df)
    return (bb_hi < kc_hi) & (bb_lo > kc_lo)


def bb_width_pct(df):
    mid, hi, lo = bollinger_bands(df["Close"])
    return (hi - lo) / mid.replace(0, np.nan) * 100


# ---------------------------------------------------------------- candle sederhana (dipakai Trend Reset)
def is_bullish_reversal_candle(df, idx):
    """Candle balik arah sederhana: Hammer (bayangan bawah panjang) ATAU Bullish Engulfing."""
    o, h, l, c = (float(df[col].iloc[idx]) for col in ("Open", "High", "Low", "Close"))
    body = abs(c - o)
    rng = max(h - l, 1e-9)
    lower_shadow = min(o, c) - l
    upper_shadow = h - max(o, c)
    is_green = c > o
    is_hammer = is_green and lower_shadow >= 2.0 * body and upper_shadow <= 0.3 * max(body, rng * 0.05)
    engulf = False
    if idx > 0:
        po, pc = float(df["Open"].iloc[idx - 1]), float(df["Close"].iloc[idx - 1])
        p_is_red = pc < po
        engulf = is_green and p_is_red and c >= po and o <= pc
    return bool(is_green and (is_hammer or engulf))


# ---------------------------------------------------------------- persiapan data
def _prepare(df):
    """Rapikan df OHLCV: kolom Date, urut, tanpa duplikat tanggal, index 0..n-1."""
    if df is None:
        return None
    d = df.copy()
    if "Date" not in d.columns:
        d = d.reset_index().rename(columns={d.reset_index().columns[0]: "Date"})
    d["Date"] = pd.to_datetime(d["Date"])
    need = {"Date", "Open", "High", "Low", "Close", "Volume"}
    if not need.issubset(d.columns):
        return None
    for c in ("Open", "High", "Low", "Close", "Volume"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["Open", "High", "Low", "Close"]).sort_values("Date").drop_duplicates("Date", keep="last")
    d["Volume"] = d["Volume"].fillna(0.0)
    return d.reset_index(drop=True) if len(d) else None


def _liquidity_ok(d):
    avg_value = float((d["Close"] * d["Volume"]).rolling(20).mean().iloc[-1])
    return d["Close"].iloc[-1] > MIN_PRICE and avg_value >= MIN_VALUE_RP


def _volatility_flags(d):
    """ATR% candle terakhir + status 'saham liar' (>HIGH_VOL_ATR_PCT). Sama definisi dgn Trade Planner & RSI Reversal.
    Catatan saja, TIDAK memotong skor."""
    v = float(atr_pct(d).iloc[-1])
    return round(v, 1), bool(v > HIGH_VOL_ATR_PCT)


def _recent_swings(d, lookback=120, left=3, right=3):
    """(swing high PALING BARU, swing low PALING BARU) dalam `lookback` candle terakhir, atau
    (None, None) kalau tidak ada yg terkonfirmasi. Dulu beberapa tempat salah pakai max(harga)
    (swing TERTINGGI sepanjang histori), bukan yang PALING BARU -- diperbaiki di sini, satu tempat,
    dipakai ulang di detect_trend_reset & detect_quiet_accumulation."""
    window = d.tail(lookback).reset_index(drop=True)
    highs, lows = swing_points(window, left=left, right=right)
    return (highs[-1][1] if highs else None), (lows[-1][1] if lows else None)


# ---------------------------------------------------------------- Breakout Surge
def detect_breakout_surge(ticker, df, now=None):
    d = _prepare(df)
    if d is None or len(d) < MIN_BARS_TREND or not _liquidity_ok(d):
        return None

    close, vol = d["Close"], d["Volume"]
    e50, e200 = ema(close, 50), ema(close, 200)
    # Rata-rata volume 20 hari SEBELUM hari yg dicek (shift(1) -- exclude hari itu sendiri dari
    # baseline-nya sendiri, konsisten dgn prior_high20 yg juga exclude hari ini).
    vol_ma20 = vol.rolling(20).mean().shift(1)
    prior_high20 = close.rolling(BRK_HIGH_LOOKBACK).max().shift(1)
    sqz = squeeze_series(d)
    n = len(d)
    latest_idx = n - 1

    if not (close.iloc[latest_idx] > e50.iloc[latest_idx] > e200.iloc[latest_idx]):
        return None

    breakout_idx = None
    for idx in range(latest_idx, max(latest_idx - BRK_MAX_AGE - 1, BRK_HIGH_LOOKBACK), -1):
        level = prior_high20.iloc[idx]
        if pd.isna(level) or pd.isna(vol_ma20.iloc[idx]) or vol_ma20.iloc[idx] <= 0:
            continue
        if close.iloc[idx] <= level:
            continue
        if vol.iloc[idx] < BRK_VOL_MULT * vol_ma20.iloc[idx]:
            continue
        base = d.iloc[max(0, idx - BRK_BASE_LOOKBACK):idx]
        if len(base) < 5:
            continue
        base_width_pct = (base["High"].max() - base["Low"].min()) / max(base["Low"].min(), 1e-9) * 100
        if base_width_pct > BRK_BASE_MAX_WIDTH_PCT:
            continue
        breakout_idx = idx
        break
    if breakout_idx is None:
        return None
    # Breakout harus MASIH VALID sekarang -- kalau harga sudah balik ke bawah level tembusnya
    # (breakout gagal/palsu), jangan tetap dianggap sinyal, walau masih dalam umur H+0..H+2.
    if close.iloc[latest_idx] < float(prior_high20.iloc[breakout_idx]):
        return None

    age = latest_idx - breakout_idx
    h, l, c = d["High"].iloc[breakout_idx], d["Low"].iloc[breakout_idx], d["Close"].iloc[breakout_idx]
    level = float(prior_high20.iloc[breakout_idx])
    dist_pct = (float(close.iloc[latest_idx]) - level) / level * 100

    score = 0
    if vol.iloc[breakout_idx] >= BRK_BONUS_VOL_MULT * vol_ma20.iloc[breakout_idx]:
        score += 20
    if 0 <= dist_pct <= BRK_BONUS_DIST_PCT:
        score += 20
    closing_strength = (c - l) / max(h - l, 1e-9)
    if closing_strength >= 0.75:
        score += 15
    streak = breakout_idx >= 2 and close.iloc[breakout_idx] > close.iloc[breakout_idx - 1] > close.iloc[breakout_idx - 2]
    if streak:
        score += 15
    base_now = d.iloc[max(0, breakout_idx - 5):breakout_idx]
    base_before = d.iloc[max(0, breakout_idx - BRK_BASE_LOOKBACK):max(0, breakout_idx - 5)]
    narrowing = False
    if len(base_now) >= 3 and len(base_before) >= 5:
        w_now = base_now["High"].max() - base_now["Low"].min()
        w_before = base_before["High"].max() - base_before["Low"].min()
        narrowing = w_now < w_before
    if narrowing:
        score += 10
    if age <= 1:
        score += 10
    lo_s, hi_s = BRK_SQUEEZE_LOOKBACK
    from_squeeze = bool(sqz.iloc[max(0, breakout_idx - hi_s):max(0, breakout_idx - lo_s + 1)].any()) if breakout_idx >= lo_s else False
    if from_squeeze:
        score += 10

    atr_now, is_volatile = _volatility_flags(d)
    last_ts = pd.Timestamp(d["Date"].iloc[-1])
    return {
        "Ticker": normalize_ticker(ticker), "Saham": str(ticker).replace(".JK", ""),
        "Close_Price": float(close.iloc[-1]), "Change_Pct": float((close.iloc[-1] / close.iloc[-2] - 1) * 100) if n > 1 else 0.0,
        "Breakout Level": round(level), "Tgl Breakout": pd.Timestamp(d["Date"].iloc[breakout_idx]).strftime("%Y-%m-%d"),
        "Age": int(age), "Dist to Level (%)": round(dist_pct, 1),
        "Vol x MA20": round(float(vol.iloc[breakout_idx] / vol_ma20.iloc[breakout_idx]), 1),
        "Closing Strength": round(float(closing_strength) * 100, 0),
        "Streak": bool(streak), "Narrowing Base": bool(narrowing), "From Squeeze": from_squeeze,
        "Score": int(score), "ATR % Now": atr_now, "Volatile Tinggi": is_volatile,
        "Value (Rp)": f"Rp {float(vol.iloc[-1] * close.iloc[-1]):,.0f}",
        "Avg Value 20D (Rp)": f"Rp {float((close * vol).rolling(20).mean().iloc[-1]):,.0f}",
        "Candle Final": bool(candle_is_final(last_ts.date(), now or now_wib())),
        "Data As Of": last_ts.strftime("%Y-%m-%d"),
    }


# ---------------------------------------------------------------- Trend Reset
def detect_trend_reset(ticker, df, now=None):
    d = _prepare(df)
    if d is None or len(d) < MIN_BARS_TREND or not _liquidity_ok(d):
        return None

    close = d["Close"]
    e20, e50, e200 = ema(close, 20), ema(close, 50), ema(close, 200)
    # Rata-rata volume SEBELUM hari ini (shift(1)) -- dulu ikut menghitung volume hari ini sendiri,
    # jadi kontradiksi sama bonus "volume balik naik" (lonjakan hari ini malah bikin syarat wajib
    # "volume mengering" lebih susah lolos, padahal itu justru skenario paling ideal).
    vol_ma20 = d["Volume"].rolling(20).mean().shift(1)
    vol_ma5 = d["Volume"].rolling(5).mean().shift(1)
    n = len(d)
    latest_idx = n - 1

    trend_ok = (close > e50) & (e50 > e200)
    if len(trend_ok) < RST_TREND_MIN_BARS or not bool(trend_ok.iloc[-RST_TREND_MIN_BARS:].all()):
        return None

    last_close = float(close.iloc[latest_idx])
    e20_now, e50_now = float(e20.iloc[latest_idx]), float(e50.iloc[latest_idx])
    # Harga di antara EMA50 dan EMA20 (toleransi 0,1% di atas EMA20) -- koreksi wajar, belum tembus
    # jauh di bawah EMA50. Kalau EMA20 sempat turun di bawah EMA50 (koreksi tajam & lama), batas
    # atasnya otomatis jadi EMA50 sendiri (area yang masuk akal makin sempit).
    if not (e50_now <= last_close <= max(e20_now, e50_now) * 1.001):
        return None

    recent_high, swing_low = _recent_swings(d)
    if recent_high is None:
        recent_high = float(d["Close"].tail(60).max())
    depth_pct = (recent_high - last_close) / recent_high * 100 if recent_high > 0 else 0.0

    if swing_low is not None and last_close < swing_low:
        return None  # struktur sudah rusak

    if not (float(vol_ma5.iloc[latest_idx]) < float(vol_ma20.iloc[latest_idx])):
        return None
    if not (last_close > float(close.iloc[latest_idx - 1]) and last_close > float(d["Open"].iloc[latest_idx])):
        return None

    score = 0
    if 0 <= depth_pct <= RST_SHALLOW_PCT:
        score += 25
    vol_today, vol_prev5 = float(d["Volume"].iloc[latest_idx]), float(vol_ma5.iloc[latest_idx])
    vol_bounce = vol_prev5 > 0 and vol_today >= RST_VOL_BOUNCE_MULT * vol_prev5
    if vol_bounce:
        score += 20
    near_ema20 = abs(last_close - e20_now) / e20_now * 100 <= 2.0 if e20_now > 0 else False
    if near_ema20:
        score += 20
    reversal_candle = is_bullish_reversal_candle(d, latest_idx)
    if reversal_candle:
        score += 20
    score += 15  # fresh: definisinya memang candle balik arah HARI INI (H+0)

    atr_now, is_volatile = _volatility_flags(d)
    last_ts = pd.Timestamp(d["Date"].iloc[-1])
    return {
        "Ticker": normalize_ticker(ticker), "Saham": str(ticker).replace(".JK", ""),
        "Close_Price": last_close, "Change_Pct": float((last_close / close.iloc[-2] - 1) * 100) if n > 1 else 0.0,
        "Depth From High (%)": round(depth_pct, 1), "Recent High": round(recent_high),
        "Near EMA20": bool(near_ema20), "Vol Bounce": bool(vol_bounce), "Reversal Candle": bool(reversal_candle),
        "Score": int(score), "ATR % Now": atr_now, "Volatile Tinggi": is_volatile,
        "Value (Rp)": f"Rp {float(d['Volume'].iloc[-1] * last_close):,.0f}",
        "Avg Value 20D (Rp)": f"Rp {float((close * d['Volume']).rolling(20).mean().iloc[-1]):,.0f}",
        "Candle Final": bool(candle_is_final(last_ts.date(), now or now_wib())),
        "Data As Of": last_ts.strftime("%Y-%m-%d"),
    }


# ---------------------------------------------------------------- Quiet Accumulation
def detect_quiet_accumulation(ticker, df, now=None):
    d = _prepare(df)
    if d is None or len(d) < MIN_BARS_SQUEEZE or not _liquidity_ok(d):
        return None

    sqz = squeeze_series(d)
    if not bool(sqz.iloc[-1]):
        return None

    # Harga TIDAK BOLEH baru saja jebol/crash dalam SQZ_DECLINE_LOOKBACK hari terakhir (LEBIH PANJANG
    # dari jendela Bollinger, sengaja -- begitu Bollinger "lupa" sama hari jebolnya, cek ini masih inget).
    # Tanpa ini, saham yang baru jebol support -- volatilitasnya melebar pas jebol, lalu "diam" lagi di
    # level baru yang lebih rendah begitu hari jebolnya keluar dari jendela BB/Keltner -- bisa ke-deteksi
    # squeeze juga, padahal itu sisa reruntuhan, bukan "lagi ngumpul sehat".
    # (Sempat dicoba pakai swing low terakhir, tapi ternyata swing ikut "pindah" ke level baru begitu
    # saham cukup lama ngumpul di sana -- jadi dipakai perubahan harga langsung, lebih tegas.)
    if len(d) > SQZ_DECLINE_LOOKBACK:
        price_then = float(d["Close"].iloc[-1 - SQZ_DECLINE_LOOKBACK])
        price_now = float(d["Close"].iloc[-1])
        if price_then > 0 and (price_now / price_then - 1) * 100 < -SQZ_MAX_DECLINE_PCT:
            return None

    # Rata-rata volume SEBELUM hari ini (shift(1)) -- konsisten sama fix di Breakout Surge/Trend Reset.
    vol_ma5 = d["Volume"].rolling(5).mean().shift(1)
    vol_ma20 = d["Volume"].rolling(20).mean().shift(1)
    if not (float(vol_ma5.iloc[-1]) > float(vol_ma20.iloc[-1])):
        return None

    days = 0
    for v in sqz.iloc[::-1]:
        if not bool(v):
            break
        days += 1

    width = bb_width_pct(d)
    w_now = float(width.iloc[-1])
    window = width.iloc[-min(SQZ_WIDTH_LOOKBACK, len(width)):]
    narrowest_in = int((window >= w_now).sum())  # termasuk hari ini

    vol_ratio_pct = (float(vol_ma5.iloc[-1]) / float(vol_ma20.iloc[-1]) - 1) * 100

    atr_now, is_volatile = _volatility_flags(d)
    last_ts = pd.Timestamp(d["Date"].iloc[-1])
    return {
        "Ticker": normalize_ticker(ticker), "Saham": str(ticker).replace(".JK", ""),
        "Close_Price": float(d["Close"].iloc[-1]), "Change_Pct": float((d["Close"].iloc[-1] / d["Close"].iloc[-2] - 1) * 100) if len(d) > 1 else 0.0,
        "Squeeze Days": int(days), "Narrowest In (Days)": int(narrowest_in), "Vol Increase (%)": round(vol_ratio_pct, 0),
        "ATR % Now": atr_now, "Volatile Tinggi": is_volatile,
        "Value (Rp)": f"Rp {float(d['Volume'].iloc[-1] * d['Close'].iloc[-1]):,.0f}",
        "Avg Value 20D (Rp)": f"Rp {float((d['Close'] * d['Volume']).rolling(20).mean().iloc[-1]):,.0f}",
        "Candle Final": bool(candle_is_final(last_ts.date(), now or now_wib())),
        "Data As Of": last_ts.strftime("%Y-%m-%d"),
    }


# ---------------------------------------------------------------- RUNNER
def run_trend_screener(tickers, progress_callback=None, data=None, should_stop=None, batch_size=50, phase_callback=None, now=None):
    """Jalankan ketiga mode sekaligus (satu kali baca data per saham). Return (df_breakout, df_reset, df_squeeze, info)."""
    ordered = list(dict.fromkeys(normalize_ticker(t) for t in tickers))
    total = len(ordered)
    provided = {normalize_ticker(k): v for k, v in (data or {}).items()}

    breakout, reset, squeeze, failed = [], [], [], []
    from_file = live = completed = 0

    for start in range(0, total, batch_size):
        if should_stop and should_stop():
            break
        chunk = ordered[start:start + batch_size]
        frames, need = {}, []
        for t in chunk:
            v = provided.get(t)
            if v is not None and len(v) > 0:
                frames[t] = v
                from_file += 1
            else:
                need.append(t)
        if need:
            if phase_callback:
                phase_callback("download", start // batch_size + 1, -(-total // batch_size), start + 1, min(start + batch_size, total), total)
            got = download_daily_batch(need, period="1y")
            frames.update(got)
            live += len(got)

        for t in chunk:
            d = frames.get(t)
            if d is None:
                failed.append(t)
            else:
                try:
                    for fn, bucket in ((detect_breakout_surge, breakout), (detect_trend_reset, reset), (detect_quiet_accumulation, squeeze)):
                        res = fn(t, d, now=now)
                        if res:
                            bucket.append(res)
                except Exception:
                    failed.append(t)
            completed += 1
            if progress_callback:
                progress_callback(completed, total)

    df_b = pd.DataFrame(breakout)
    df_r = pd.DataFrame(reset)
    df_s = pd.DataFrame(squeeze)
    if not df_s.empty and not df_b.empty:
        # Saham yang HARI INI sudah tembus (Breakout Surge) tidak perlu lagi ditandai "lagi ngumpul"
        # di Quiet Accumulation -- membingungkan kalau satu saham muncul di dua status yang berlawanan.
        df_s = df_s[~df_s["Ticker"].isin(set(df_b["Ticker"]))].reset_index(drop=True)
    if not df_b.empty:
        df_b = df_b.sort_values("Score", ascending=False, kind="stable").reset_index(drop=True)
    if not df_r.empty:
        df_r = df_r.sort_values("Score", ascending=False, kind="stable").reset_index(drop=True)
    if not df_s.empty:
        df_s = df_s.sort_values("Squeeze Days", ascending=False, kind="stable").reset_index(drop=True)

    info = {"total": total, "success": completed - len(failed), "failed": len(failed), "failed_tickers": failed,
            "from_file": from_file, "downloaded": live, "matched_breakout": len(df_b), "matched_reset": len(df_r), "matched_squeeze": len(df_s)}
    for df_ in (df_b, df_r, df_s):
        df_.attrs["run_info"] = info
    return df_b, df_r, df_s, info
