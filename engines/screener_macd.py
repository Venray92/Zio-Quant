"""MACD Momentum: crossover MACD + filter tren (EMA) + ADX (kekuatan tren) + volume + candle.

Beda dari Stoch Momentum (yang pakai PSAR): di sini yang menyaring "tren beneran lahir vs cuma
noise" adalah ADX, bukan PSAR. MACD sendirian gampang whipsaw di saham sideways -- ADX naik dari
bawah 20 + +DI motong -DI itu tanda tren baru BENERAN kebentuk, bukan cuma pantulan sesaat.
"""
import pandas as pd

from engines.market_data import candle_is_final, download_daily_batch, normalize_ticker, now_wib
from engines.market_view import atr_pct, ema
from engines.trade_planner import HIGH_VOL_ATR_PCT

# ---------------------------------------------------------------- PARAMETER
MIN_PRICE = 50
MIN_VALUE_RP = 1_000_000_000
MIN_BARS = 210                    # butuh EMA200 utk filter tren (sama seperti Trend Scanner)
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
ADX_PERIOD = 14
ADX_LOW = 20.0                    # di bawah ini = pasar belum jelas arahnya (choppy)
ADX_RISING_LOOKBACK = 10          # ADX harus pernah di bawah ADX_LOW dlm N hari terakhir, LALU naik
MAX_AGE = 2                       # crossover maksimal H+2
VOL_MULT = 1.2                    # volume hari crossover minimal segini x rata-rata 20 hari


# ---------------------------------------------------------------- indikator
def macd(close, fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL):
    """(garis MACD, garis Sinyal, Histogram)."""
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line, macd_line - signal_line


def adx_di(df, period=ADX_PERIOD):
    """(+DI, -DI, ADX) gaya Wilder. Referensi standar: Welles Wilder, New Concepts in Technical
    Trading Systems (1978)."""
    high, low, close = df["High"], df["Low"], df["Close"]
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = ((up_move > down_move) & (up_move > 0)) * up_move.clip(lower=0)
    minus_dm = ((down_move > up_move) & (down_move > 0)) * down_move.clip(lower=0)
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)

    def _wilder(s, n):
        return s.ewm(alpha=1 / n, adjust=False).mean()

    atr = _wilder(tr, period)
    plus_di = 100 * _wilder(plus_dm, period) / atr.replace(0, pd.NA)
    minus_di = 100 * _wilder(minus_dm, period) / atr.replace(0, pd.NA)
    denom = (plus_di + minus_di).replace(0, pd.NA)
    dx = 100 * (plus_di - minus_di).abs() / denom
    adx = _wilder(dx.fillna(0), period)
    return plus_di, minus_di, adx


# ---------------------------------------------------------------- persiapan & helper (sama pola dgn screener_trend.py)
def _prepare(df):
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
    v = float(atr_pct(d).iloc[-1])
    return round(v, 1), bool(v > HIGH_VOL_ATR_PCT)


def _closing_strength(d, idx):
    h, l, c = float(d["High"].iloc[idx]), float(d["Low"].iloc[idx]), float(d["Close"].iloc[idx])
    return (c - l) / max(h - l, 1e-9)


# ---------------------------------------------------------------- deteksi
def _detect(ticker, df, direction, now=None):
    """direction: 'bull' (Golden Cross) atau 'bear' (Dead Cross)."""
    d = _prepare(df)
    if d is None or len(d) < MIN_BARS or not _liquidity_ok(d):
        return None

    close = d["Close"]
    e50, e200 = ema(close, 50), ema(close, 200)
    macd_line, signal_line, hist = macd(close)
    plus_di, minus_di, adx = adx_di(d)
    vol_ma20 = d["Volume"].rolling(20).mean().shift(1)
    latest_idx = len(d) - 1

    trend_up = close.iloc[latest_idx] > e50.iloc[latest_idx] > e200.iloc[latest_idx]
    trend_down = close.iloc[latest_idx] < e50.iloc[latest_idx] < e200.iloc[latest_idx]
    if direction == "bull" and not trend_up:
        return None
    if direction == "bear" and not trend_down:
        return None

    cross_idx = None
    for idx in range(latest_idx, max(latest_idx - MAX_AGE - 1, 0), -1):
        if idx < 1:
            break
        prev_diff = macd_line.iloc[idx - 1] - signal_line.iloc[idx - 1]
        now_diff = macd_line.iloc[idx] - signal_line.iloc[idx]
        if pd.isna(prev_diff) or pd.isna(now_diff) or pd.isna(vol_ma20.iloc[idx]) or vol_ma20.iloc[idx] <= 0:
            continue
        crossed_up = prev_diff <= 0 and now_diff > 0
        crossed_down = prev_diff >= 0 and now_diff < 0
        if direction == "bull" and not crossed_up:
            continue
        if direction == "bear" and not crossed_down:
            continue
        if d["Volume"].iloc[idx] < VOL_MULT * vol_ma20.iloc[idx]:
            continue
        cross_idx = idx
        break
    if cross_idx is None:
        return None

    age = latest_idx - cross_idx
    # ADX: pernah di bawah ADX_LOW dlm ADX_RISING_LOOKBACK hari sebelum crossover, LALU naik sampai
    # hari crossover -- tanda tren baru lahir dari kondisi choppy, bukan tren tua yg udah lama jalan.
    win_start = max(0, cross_idx - ADX_RISING_LOOKBACK)
    adx_was_low = bool((adx.iloc[win_start:cross_idx + 1] < ADX_LOW).any())
    adx_rising = bool(adx.iloc[cross_idx] > adx.iloc[max(0, cross_idx - 1)]) if cross_idx > 0 else False
    di_confirms = bool(plus_di.iloc[cross_idx] > minus_di.iloc[cross_idx]) if direction == "bull" else bool(minus_di.iloc[cross_idx] > plus_di.iloc[cross_idx])
    fresh_trend = adx_was_low and adx_rising and di_confirms

    score = 0
    if fresh_trend:
        score += 30
    above_zero = bool(macd_line.iloc[cross_idx] > 0) if direction == "bull" else bool(macd_line.iloc[cross_idx] < 0)
    if above_zero:
        score += 20
    if d["Volume"].iloc[cross_idx] >= 1.5 * vol_ma20.iloc[cross_idx]:
        score += 15
    cs = _closing_strength(d, cross_idx)
    strong_candle = cs >= 0.75 if direction == "bull" else cs <= 0.25
    if strong_candle:
        score += 15
    if age <= 1:
        score += 10
    hist_prev = float(hist.iloc[cross_idx - 1]) if cross_idx > 0 else 0.0
    hist_now = float(hist.iloc[cross_idx])
    expanding = (hist_now > hist_prev) if direction == "bull" else (hist_now < hist_prev)
    if expanding:
        score += 10

    atr_now, is_volatile = _volatility_flags(d)
    last_ts = pd.Timestamp(d["Date"].iloc[-1])
    n = len(d)
    return {
        "Ticker": normalize_ticker(ticker), "Saham": str(ticker).replace(".JK", ""),
        "Close_Price": float(close.iloc[-1]), "Change_Pct": float((close.iloc[-1] / close.iloc[-2] - 1) * 100) if n > 1 else 0.0,
        "Direction": "Bullish" if direction == "bull" else "Bearish",
        "Tgl Crossover": pd.Timestamp(d["Date"].iloc[cross_idx]).strftime("%Y-%m-%d"), "Age": int(age),
        "MACD": round(float(macd_line.iloc[cross_idx]), 2), "Signal": round(float(signal_line.iloc[cross_idx]), 2),
        "ADX": round(float(adx.iloc[cross_idx]), 1), "Fresh Trend": fresh_trend, "Above Zero": above_zero,
        "Strong Candle": strong_candle, "Score": int(score),
        "ATR % Now": atr_now, "Volatile Tinggi": is_volatile,
        "Value (Rp)": f"Rp {float(d['Volume'].iloc[-1] * close.iloc[-1]):,.0f}",
        "Avg Value 20D (Rp)": f"Rp {float((close * d['Volume']).rolling(20).mean().iloc[-1]):,.0f}",
        "Candle Final": bool(candle_is_final(last_ts.date(), now or now_wib())),
        "Data As Of": last_ts.strftime("%Y-%m-%d"),
    }


def detect_macd_golden_cross(ticker, df, now=None):
    return _detect(ticker, df, "bull", now=now)


def detect_macd_dead_cross(ticker, df, now=None):
    return _detect(ticker, df, "bear", now=now)


# ---------------------------------------------------------------- RUNNER
def run_macd_screener(tickers, progress_callback=None, data=None, should_stop=None, batch_size=50, phase_callback=None, now=None):
    """Return (df_golden_cross, df_dead_cross, info)."""
    ordered = list(dict.fromkeys(normalize_ticker(t) for t in tickers))
    total = len(ordered)
    provided = {normalize_ticker(k): v for k, v in (data or {}).items()}

    gc_list, dc_list, failed = [], [], []
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
                    r_gc = detect_macd_golden_cross(t, d, now=now)
                    if r_gc:
                        gc_list.append(r_gc)
                    r_dc = detect_macd_dead_cross(t, d, now=now)
                    if r_dc:
                        dc_list.append(r_dc)
                except Exception:
                    failed.append(t)
            completed += 1
            if progress_callback:
                progress_callback(completed, total)

    df_gc = pd.DataFrame(gc_list)
    df_dc = pd.DataFrame(dc_list)
    if not df_gc.empty:
        df_gc = df_gc.sort_values("Score", ascending=False, kind="stable").reset_index(drop=True)
    if not df_dc.empty:
        df_dc = df_dc.sort_values("Score", ascending=False, kind="stable").reset_index(drop=True)

    info = {"total": total, "success": completed - len(failed), "failed": len(failed), "failed_tickers": failed,
            "from_file": from_file, "downloaded": live, "matched_gc": len(df_gc), "matched_dc": len(df_dc)}
    for df_ in (df_gc, df_dc):
        df_.attrs["run_info"] = info
    return df_gc, df_dc, info
