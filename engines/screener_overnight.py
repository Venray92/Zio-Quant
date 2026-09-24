"""BSJP (Beli Sore Jual Pagi) & BPJS (Beli Pagi Jual Sore) -- screener struktur harga & volume,
BUKAN oscillator. Sama pola dgn engines/screener_trend.py (2 mode, 1 runner).

Keterbatasan data yg JUJUR perlu dipahami: seluruh app ini kerja dari candle HARIAN (1 candle/hari),
bukan data intraday (per menit/jam). Ini bikin dua mode ini kekuatannya BEDA:
- BSJP (jelang closing, 16:00-17:40 WIB): COCOK sama data harian -- begitu jam segini, candle hari itu
  sudah "matang", walau teknisnya belum tutup persis jam 17:40.
- BPJS (pembukaan, 09:00-10:00 WIB): LEBIH LEMAH dari sisi data. "Gap" dan "opening range" di sini
  cuma proxy kasar (Open hari ini vs Close kemarin, harga sekarang vs Open hari ini) -- BUKAN analisis
  microstructure 15/30 menit pertama yg presisi (butuh data intraday yg kita tidak punya). BPJS hanya
  sungguh berarti kalau dijalankan LIVE pas jam segitu (data live, bukan file harian sesudahnya) --
  dijalankan sesudahnya cuma jadi "saham yang nutup hijau setelah gap", bukan lagi day-trade signal.
"""
import pandas as pd

from engines.market_data import candle_is_final, download_daily_batch, normalize_ticker, now_wib
from engines.market_view import atr_pct, ema
from engines.screener_macd import adx_di

# ---------------------------------------------------------------- PARAMETER
MIN_PRICE = 50
MIN_VALUE_RP = 1_000_000_000
MIN_BARS = 60

# --- BSJP ---
BSJP_CS_MIN = 0.75                # closing strength minimal (nutup di 75% teratas rentang hari itu)
BSJP_CHG_ATR_MIN = 0.8            # naik hari itu minimal 0,8x ATR% saham itu sendiri
BSJP_CHG_ATR_MAX = 2.5            # ...maksimal 2,5x -- lebih dari ini dianggap euforia/klimaks, bukan makin bagus
BSJP_VOL_MULT = 1.3               # volume hari itu minimal 1,3x rata-rata 20 hari (exclude hari ini)
BSJP_ADX_MAX = 40.0               # tren yg sudah TERLALU kuat/tua -- closing kuat bisa klimaks, bukan lanjutan
BSJP_RESISTANCE_LOOKBACK = 20     # dipakai jg utk cek "masih ada ruang ke resistance" (bonus)

# --- BPJS ---
BPJS_GAP_ATR_MIN = 0.8            # gap pagi minimal 0,8x ATR% saham itu sendiri (relatif, bukan angka tetap)
BPJS_GAP_ATR_MAX = 2.5
BPJS_VOL_SOFAR_MIN_FRAC = 0.15    # volume "sejauh ini" minimal 15% dari rata-rata volume SATU HARI PENUH
                                   # (kasar -- kita tidak simpan histori volume per jam, lihat catatan modul)


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


def _closing_strength(h, l, c):
    return (c - l) / max(h - l, 1e-9)


def _volatility_flags(d):
    from engines.trade_planner import HIGH_VOL_ATR_PCT

    v = float(atr_pct(d).iloc[-1])
    return round(v, 1), bool(v > HIGH_VOL_ATR_PCT)


# ---------------------------------------------------------------- BSJP
def detect_bsjp(ticker, df, now=None, breakout_tickers=None, hot_sectors=None, sector_of=None):
    """breakout_tickers: set ticker yg lolos Breakout Surge HARI INI (opsional, utk bonus confluence).
    hot_sectors + sector_of: set sektor yg 'menyala' HARI INI + fungsi ticker->sektor (opsional)."""
    d = _prepare(df)
    if d is None or len(d) < MIN_BARS or not _liquidity_ok(d):
        return None

    close, high, low, opn, vol = d["Close"], d["High"], d["Low"], d["Open"], d["Volume"]
    latest = len(d) - 1
    e20 = ema(close, 20)
    atr_pct_series = atr_pct(d)
    vol_ma20 = vol.rolling(20).mean().shift(1)
    _, _, adx = adx_di(d)

    if not (close.iloc[latest] > e20.iloc[latest]):
        return None
    if not (close.iloc[latest] > opn.iloc[latest]):
        return None

    cs_today = _closing_strength(high.iloc[latest], low.iloc[latest], close.iloc[latest])
    if cs_today < BSJP_CS_MIN:
        return None

    chg_pct = float((close.iloc[latest] / close.iloc[latest - 1] - 1) * 100) if latest > 0 else 0.0
    atr_now = float(atr_pct_series.iloc[latest])
    if not (BSJP_CHG_ATR_MIN * atr_now <= chg_pct <= BSJP_CHG_ATR_MAX * atr_now):
        return None

    if pd.isna(vol_ma20.iloc[latest]) or vol_ma20.iloc[latest] <= 0 or vol.iloc[latest] < BSJP_VOL_MULT * vol_ma20.iloc[latest]:
        return None

    adx_now = float(adx.iloc[latest]) if not pd.isna(adx.iloc[latest]) else 0.0
    if adx_now > BSJP_ADX_MAX:
        return None

    score = 0
    cs_prev1 = _closing_strength(high.iloc[latest - 1], low.iloc[latest - 1], close.iloc[latest - 1]) if latest >= 1 else 0
    cs_prev2 = _closing_strength(high.iloc[latest - 2], low.iloc[latest - 2], close.iloc[latest - 2]) if latest >= 2 else 0
    streak3 = latest >= 2 and cs_today >= cs_prev1 >= cs_prev2
    if streak3:
        score += 20
    vol_streak = latest >= 2 and float(vol.iloc[latest - 2]) < float(vol.iloc[latest - 1]) < float(vol.iloc[latest])
    if vol_streak:
        score += 15
    if cs_today >= 0.9:
        score += 15
    t = normalize_ticker(ticker)
    is_breakout_today = bool(breakout_tickers and t in breakout_tickers)
    if is_breakout_today:
        score += 20
    sector_hot = bool(hot_sectors and sector_of and sector_of(t) in hot_sectors)
    if sector_hot:
        score += 15
    prior_high = float(close.rolling(BSJP_RESISTANCE_LOOKBACK).max().shift(1).iloc[latest]) if latest >= BSJP_RESISTANCE_LOOKBACK else 0.0
    has_room = prior_high <= 0 or close.iloc[latest] <= prior_high * 0.97
    if has_room:
        score += 15

    atr_now_flag, is_volatile = _volatility_flags(d)
    last_ts = pd.Timestamp(d["Date"].iloc[-1])
    return {
        "Ticker": t, "Saham": str(ticker).replace(".JK", ""),
        "Close_Price": float(close.iloc[latest]), "Change_Pct": round(chg_pct, 2),
        "Closing Strength": round(cs_today, 2), "ADX": round(adx_now, 1),
        "Streak 3 Hari": streak3, "Volume Naik Bertahap": vol_streak, "Dari Breakout Surge": is_breakout_today,
        "Sektor Menyala": sector_hot, "Ada Ruang ke Resistance": has_room, "Score": int(score),
        "ATR % Now": atr_now_flag, "Volatile Tinggi": is_volatile,
        "Value (Rp)": f"Rp {float(vol.iloc[latest] * close.iloc[latest]):,.0f}",
        "Avg Value 20D (Rp)": f"Rp {float((close * vol).rolling(20).mean().iloc[-1]):,.0f}",
        "Candle Final": bool(candle_is_final(last_ts.date(), now or now_wib())),
        "Data As Of": last_ts.strftime("%Y-%m-%d"),
    }


# ---------------------------------------------------------------- BPJS
def detect_bpjs(ticker, df, now=None, ihsg_df=None, breakout_tickers_prev=None, hot_sectors_prev=None, sector_of=None):
    """ihsg_df: histori IHSG (opsional) -- kalau ada, gap saham dibandingkan ke gap IHSG hari yg sama
    supaya bisa bedain 'gap spesial saham ini' dari 'cuma ikut market'. *_prev: confluence dari HARI
    SEBELUMNYA (kemarin), karena BPJS jalan di pagi hari sebelum ada hasil Breakout Surge/Sector Radar
    hari ini sendiri."""
    d = _prepare(df)
    if d is None or len(d) < MIN_BARS + 1 or not _liquidity_ok(d):
        return None

    close, high, low, opn, vol = d["Close"], d["High"], d["Low"], d["Open"], d["Volume"]
    latest = len(d) - 1
    prev_close = float(close.iloc[latest - 1])
    open_today = float(opn.iloc[latest])
    now_price = float(close.iloc[latest])
    if prev_close <= 0:
        return None

    gap_pct = (open_today / prev_close - 1) * 100
    atr_yday = float(atr_pct(d.iloc[:latest]).iloc[-1]) if latest >= 15 else 0.0
    if atr_yday <= 0:
        return None
    if not (BPJS_GAP_ATR_MIN * atr_yday <= gap_pct <= BPJS_GAP_ATR_MAX * atr_yday):
        return None
    if not (now_price > open_today):
        return None

    ihsg_gap_pct = None
    if ihsg_df is not None:
        idg = _prepare(ihsg_df)
        if idg is not None and len(idg) >= 2:
            match = idg[idg["Date"] == d["Date"].iloc[latest]]
            if len(match):
                i_open, i_prev = float(match["Open"].iloc[0]), float(idg[idg["Date"] < d["Date"].iloc[latest]]["Close"].iloc[-1])
                if i_prev > 0:
                    ihsg_gap_pct = (i_open / i_prev - 1) * 100

    vol_ma20_full_day = float(vol.iloc[:latest].rolling(20).mean().iloc[-1]) if latest >= 20 else 0.0
    vol_so_far = float(vol.iloc[latest])
    if vol_ma20_full_day <= 0 or vol_so_far < BPJS_VOL_SOFAR_MIN_FRAC * vol_ma20_full_day:
        return None

    score = 0
    cs_yday = _closing_strength(float(high.iloc[latest - 1]), float(low.iloc[latest - 1]), prev_close)
    if cs_yday >= 0.75:
        score += 25
    special_vs_ihsg = ihsg_gap_pct is not None and gap_pct > 0 and ihsg_gap_pct <= 0.2
    if special_vs_ihsg:
        score += 25
    strong_vol_sofar = vol_ma20_full_day > 0 and vol_so_far >= 0.25 * vol_ma20_full_day
    if strong_vol_sofar:
        score += 25
    t = normalize_ticker(ticker)
    confluence = bool((breakout_tickers_prev and t in breakout_tickers_prev) or (hot_sectors_prev and sector_of and sector_of(t) in hot_sectors_prev))
    if confluence:
        score += 25

    atr_now_flag, is_volatile = _volatility_flags(d)
    last_ts = pd.Timestamp(d["Date"].iloc[-1])
    return {
        "Ticker": t, "Saham": str(ticker).replace(".JK", ""),
        "Close_Price": now_price, "Change_Pct": round((now_price / prev_close - 1) * 100, 2),
        "Gap (%)": round(gap_pct, 2), "Gap vs IHSG (%)": round(ihsg_gap_pct, 2) if ihsg_gap_pct is not None else None,
        "Closing Strength Kemarin": round(cs_yday, 2), "Vol Sejauh Ini vs Rata2 Harian": round(vol_so_far / vol_ma20_full_day, 2) if vol_ma20_full_day else 0.0,
        "Lebih Spesial dari IHSG": special_vs_ihsg, "Volume Kuat Sejauh Ini": strong_vol_sofar, "Confluence Kemarin": confluence,
        "Score": int(score), "ATR % Now": atr_now_flag, "Volatile Tinggi": is_volatile,
        "Value (Rp)": f"Rp {float(vol_so_far * now_price):,.0f}",
        "Avg Value 20D (Rp)": f"Rp {float((close * vol).iloc[:latest].rolling(20).mean().iloc[-1]):,.0f}" if latest >= 20 else "Rp 0",
        "Candle Final": bool(candle_is_final(last_ts.date(), now or now_wib())),
        "Data As Of": last_ts.strftime("%Y-%m-%d"),
    }


# ---------------------------------------------------------------- RUNNER
def run_overnight_screener(tickers, progress_callback=None, data=None, should_stop=None, batch_size=50,
                            phase_callback=None, now=None, ihsg_df=None, breakout_tickers=None,
                            hot_sectors=None, sector_of=None):
    """Return (df_bsjp, df_bpjs, info). breakout_tickers/hot_sectors/sector_of: opsional, dipakai utk
    bonus confluence di dua-duanya (BSJP pakai hari ini, BPJS pakai sbg proxy 'kemarin' -- lihat catatan
    di detect_bpjs)."""
    ordered = list(dict.fromkeys(normalize_ticker(t) for t in tickers))
    total = len(ordered)
    provided = {normalize_ticker(k): v for k, v in (data or {}).items()}

    bsjp_list, bpjs_list, failed = [], [], []
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
                    r1 = detect_bsjp(t, d, now=now, breakout_tickers=breakout_tickers, hot_sectors=hot_sectors, sector_of=sector_of)
                    if r1:
                        bsjp_list.append(r1)
                    r2 = detect_bpjs(t, d, now=now, ihsg_df=ihsg_df, breakout_tickers_prev=breakout_tickers, hot_sectors_prev=hot_sectors, sector_of=sector_of)
                    if r2:
                        bpjs_list.append(r2)
                except Exception:
                    failed.append(t)
            completed += 1
            if progress_callback:
                progress_callback(completed, total)

    df_bsjp = pd.DataFrame(bsjp_list)
    df_bpjs = pd.DataFrame(bpjs_list)
    if not df_bsjp.empty:
        df_bsjp = df_bsjp.sort_values("Score", ascending=False, kind="stable").reset_index(drop=True)
    if not df_bpjs.empty:
        df_bpjs = df_bpjs.sort_values("Score", ascending=False, kind="stable").reset_index(drop=True)

    info = {"total": total, "success": completed - len(failed), "failed": len(failed), "failed_tickers": failed,
            "from_file": from_file, "downloaded": live, "matched_bsjp": len(df_bsjp), "matched_bpjs": len(df_bpjs)}
    for df_ in (df_bsjp, df_bpjs):
        df_.attrs["run_info"] = info
    return df_bsjp, df_bpjs, info
