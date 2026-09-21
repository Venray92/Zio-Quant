import logging
import os
import re
import warnings

import pandas as pd
import ta
import yfinance as yf

from data.ihsg_tickers import get_all_ihsg_tickers
from engines.market_data import candle_is_final, now_wib

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

DEFAULT_SAHAM_LIST = sorted(
    list(
        set([
            "ISAT.JK"
        ])
    )
)

# =============================================================
# PARAMETER (ubah angka di sini, tanpa sentuh logika)
# =============================================================
PERIOD = "6mo"                    # panjang data (MA50 + PSAR butuh warm-up)
MIN_BARS = 55                     # minimal candle agar MA50 bisa dihitung
BATCH_SIZE = 50                   # jumlah ticker per sekali download
MIN_PRICE = 70                    # filter harga
MIN_VALUE_RP = 1_000_000_000      # filter likuiditas (Rp 1 miliar)
BIG_MOVE_PCT = 10.0               # lonjakan/penurunan harian yg dianggap "kejar harga"
MIN_ADX = 20.0                    # di bawah ini PSAR dianggap tidak valid (sideways)
FLIP_LOOKBACK = 3                 # PSAR flip dianggap "baru" kalau <= 3 candle

# Info run terakhir (jumlah gagal download, fallback list dipakai, dll)
LAST_RUN_INFO = {}


def get_last_run_info():
    return dict(LAST_RUN_INFO)


# =============================================================
# DATA: download batch / data siap pakai
# =============================================================
def _fmt_ticker(ticker):
    formatted = str(ticker).strip().upper()
    if not formatted.endswith(".JK"):
        formatted = f"{formatted}.JK"
    return formatted


def _clean_df(df):
    """Rapikan DataFrame OHLCV (kolom datar, buang baris kosong)."""
    if df is None or len(df) == 0:
        return None
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    for col in ("Open", "High", "Low", "Close", "Volume"):
        if col not in df.columns:
            return None
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    df["Volume"] = df["Volume"].fillna(0)
    return df if not df.empty else None


def _extract_from_batch(raw, tickers):
    """Pecah hasil yf.download(list ticker) jadi {ticker: DataFrame}."""
    out = {}
    if raw is None or len(raw) == 0:
        return out
    if not isinstance(raw.columns, pd.MultiIndex):
        if len(tickers) == 1:
            d = _clean_df(raw)
            if d is not None:
                out[tickers[0]] = d
        return out

    lvl0 = set(raw.columns.get_level_values(0))
    lvl1 = set(raw.columns.get_level_values(1))
    for tk in tickers:
        try:
            if tk in lvl0:
                sub = raw[tk]
            elif tk in lvl1:
                sub = raw.xs(tk, axis=1, level=1)
            else:
                continue
            d = _clean_df(sub)
            if d is not None:
                out[tk] = d
        except Exception:
            continue
    return out


def _download_batch(tickers):
    """Download per grup (maks BATCH_SIZE), yang gagal dicoba sekali lagi."""
    got = {}
    for start in range(0, len(tickers), BATCH_SIZE):
        chunk = tickers[start:start + BATCH_SIZE]
        for _ in range(2):
            todo = [t for t in chunk if t not in got]
            if not todo:
                break
            try:
                raw = yf.download(
                    todo,
                    period=PERIOD,
                    interval="1d",
                    group_by="ticker",
                    auto_adjust=False,
                    progress=False,
                    threads=True,
                )
                got.update(_extract_from_batch(raw, todo))
            except Exception:
                pass
    return got


def _is_candle_final(df, now=None):
    """False kalau candle terakhir = hari ini (hari bursa) dan pasar belum tutup (WIB)."""
    try:
        return candle_is_final(pd.Timestamp(df.index[-1]).date(), now or now_wib())
    except Exception:
        return True


def _tags_from_notes(notes):
    """Catatan sinyal -> label pendek untuk kartu (tanpa angka poin, tanpa info volume)."""
    tags = []
    for n in notes[1:]:
        if n.startswith(("Vol ", "Volume ", "Candle hari ini", "Watchlist")):
            continue
        t = re.sub(r"\s*\((?:\+|-)?\d+\)$", "", n).strip()
        t = re.sub(r"PSAR diabaikan \(ADX.*\)", "PSAR diabaikan (ADX rendah)", t)
        tags.append(t)
    return tags


# =============================================================
# INTI PERHITUNGAN (menerima DataFrame, tidak download sendiri)
# =============================================================
def _process_core(ticker, df, include_early=False, now=None):
    formatted_ticker = _fmt_ticker(ticker)
    df = _clean_df(df)
    if df is None or len(df) < MIN_BARS:
        return None, None

    c0 = float(df["Close"].iloc[-1])
    c1 = float(df["Close"].iloc[-2])
    v0 = float(df["Volume"].iloc[-1])
    v1 = float(df["Volume"].iloc[-2])
    l0 = float(df["Low"].iloc[-1])
    h0 = float(df["High"].iloc[-1])
    val0 = c0 * v0

    # Persentase perubahan harga harian
    change_pct = ((c0 - c1) / c1) * 100 if c1 > 0 else 0.0

    # Filter Likuiditas: rata-rata nilai transaksi 20 hari minimal Rp 1 Miliar & Harga > 70
    avg_val20 = float((df["Close"] * df["Volume"]).rolling(window=20).mean().iloc[-1])
    if c0 <= MIN_PRICE or not (avg_val20 >= MIN_VALUE_RP):
        return None, None

    # Volume MA20 = rata-rata 20 hari SEBELUM hari yang dievaluasi
    vol_ma20 = df["Volume"].rolling(window=20).mean().shift(1)

    def vol_ratio(pos):
        m = vol_ma20.iloc[pos]
        v = df["Volume"].iloc[pos]
        return float(v / m) if (pd.notna(m) and m > 0) else 0.0

    # Indikator Stochastic (Custom 10, 5, 5)
    low_min10 = df["Low"].rolling(window=10).min()
    high_max10 = df["High"].rolling(window=10).max()

    diff = high_max10 - low_min10
    diff = diff.replace(0, float("nan"))  # harga flat -> tidak dihitung

    fast_k = 100 * ((df["Close"] - low_min10) / diff)
    df["stoch_k"] = fast_k.rolling(window=5).mean()
    df["stoch_d"] = df["stoch_k"].rolling(window=5).mean()

    # Indikator PSAR (kalau gagal dihitung -> tidak dapat poin PSAR)
    try:
        psar_ind = ta.trend.PSARIndicator(
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            step=0.02,
            max_step=0.2,
        )
        df["psar"] = psar_ind.psar()
        psar_ok = True
    except Exception:
        df["psar"] = float("nan")
        psar_ok = False

    psar_bull = (df["psar"] < df["Low"]).astype(bool)
    psar_bear = (df["psar"] > df["High"]).astype(bool)
    flip_bull = psar_bull & ~psar_bull.shift(1, fill_value=True)
    flip_bear = psar_bear & ~psar_bear.shift(1, fill_value=True)
    bull_flip_fresh = bool(flip_bull.iloc[-FLIP_LOOKBACK:].any())
    bear_flip_fresh = bool(flip_bear.iloc[-FLIP_LOOKBACK:].any())

    # ADX: PSAR hanya dipercaya kalau ada tren (bukan sideways)
    try:
        adx0 = float(
            ta.trend.ADXIndicator(
                high=df["High"], low=df["Low"], close=df["Close"], window=14
            ).adx().iloc[-1]
        )
    except Exception:
        adx0 = float("nan")
    adx_ok = pd.isna(adx0) or adx0 >= MIN_ADX

    # Konteks tren (MA20 / MA50)
    m20 = df["Close"].rolling(window=20).mean().iloc[-1]
    m50 = df["Close"].rolling(window=50).mean().iloc[-1]
    have_ma = pd.notna(m20) and pd.notna(m50)
    uptrend = bool(have_ma and c0 > m50 and m20 > m50)
    downtrend = bool(have_ma and c0 < m50 and m20 < m50)
    above_ma50 = bool(have_ma and c0 > m50)
    below_ma50 = bool(have_ma and c0 < m50)

    k0, d0 = df["stoch_k"].iloc[-1], df["stoch_d"].iloc[-1]
    k1, d1 = df["stoch_k"].iloc[-2], df["stoch_d"].iloc[-2]
    k2, d2 = df["stoch_k"].iloc[-3], df["stoch_d"].iloc[-3]
    k3, d3 = df["stoch_k"].iloc[-4], df["stoch_d"].iloc[-4]
    if any(pd.isna(x) for x in (k0, d0, k1, d1, k2, d2, k3, d3)):
        return None, None
    k0, d0, k1, d1, k2, d2, k3, d3 = (
        float(k0), float(d0), float(k1), float(d1),
        float(k2), float(d2), float(k3), float(d3),
    )
    psar0_bull = bool(psar_bull.iloc[-1]) and psar_ok
    psar0_bear = bool(psar_bear.iloc[-1]) and psar_ok

    final = _is_candle_final(df, now)
    tgl = pd.Timestamp(df.index[-1]).strftime("%Y-%m-%d")
    res_gc = None
    res_dc = None

    # =========================================================
    # 1. GOLDEN CROSS (BULLISH) - WAJIB HARI INI HIJAU (change_pct > 0)
    #    Skor maks 100: cross 30 + PSAR 20 + volume 15 + tren 20 + oversold 15
    # =========================================================
    is_green = change_pct > 0

    gc_today = is_green and (k1 < d1) and (k0 >= d0) and (k0 < 35)
    gc_yesterday = is_green and (k2 < d2) and (k1 >= d1) and (k0 >= d0) and (k1 < 35)
    gc_2days_ago = (
        is_green and (k3 < d3) and (k2 >= d2) and (k1 >= d1) and (k0 >= d0) and (k2 < 35)
    )
    is_almost_gc = (
        is_green and (k0 <= d0) and ((d0 - k0) <= 3.0) and (k0 < 35) and (v0 > v1) and (k0 > k1)
    )

    stoch_signal_gc = None
    if gc_today:
        stoch_signal_gc = {"type": "GC Hari Ini (H-0)", "score": 30, "code": "H0", "pos": -1, "k": k0}
    elif gc_yesterday:
        stoch_signal_gc = {"type": "GC Kemarin (H-1)", "score": 25, "code": "H1", "pos": -2, "k": k1}
    elif gc_2days_ago:
        stoch_signal_gc = {"type": "GC 2 Hari Lalu (H-2)", "score": 20, "code": "H2", "pos": -3, "k": k2}
    elif include_early and is_almost_gc:
        stoch_signal_gc = {"type": "Early Signal (Merapat)", "score": 10, "code": "EARLY", "pos": -1, "k": k0}

    if stoch_signal_gc:
        score = stoch_signal_gc["score"]
        notes = [stoch_signal_gc["type"]]

        # PSAR (hanya dipercaya kalau ADX cukup)
        if psar0_bull:
            if not adx_ok:
                notes.append(f"PSAR diabaikan (ADX {adx0:.0f} < {MIN_ADX:.0f}, sideways)")
            elif bull_flip_fresh:
                score += 20
                notes.append(f"PSAR Flip Bullish <={FLIP_LOOKBACK} candle (+20)")
            else:
                score += 10
                notes.append("PSAR Bullish (+10)")

        # Volume di hari cross (dibanding rata-rata 20 hari sebelumnya)
        vr = vol_ratio(stoch_signal_gc["pos"])
        vol_pending = (not final) and stoch_signal_gc["pos"] == -1
        if vol_pending:
            notes.append("Volume hari ini belum final (tidak dihitung)")
        elif vr >= 1.5:
            score += 15
            notes.append(f"Vol {vr:.1f}x MA20 (+15)")
        elif vr >= 1.0:
            score += 8
            notes.append(f"Vol {vr:.1f}x MA20 (+8)")

        # Konteks tren
        if uptrend:
            score += 20
            notes.append("Pullback di Uptrend (+20)")
        elif above_ma50:
            score += 10
            notes.append("Di atas MA50 (+10)")
        elif have_ma:
            notes.append("Reversal di Downtrend (+0)")

        # Kedalaman oversold saat cross
        if stoch_signal_gc["k"] < 20:
            score += 15
            notes.append("Oversold dalam %K<20 (+15)")
        else:
            score += 8
            notes.append("Zona oversold %K<35 (+8)")

        # Penalti kejar harga
        if change_pct >= BIG_MOVE_PCT:
            score -= 15
            notes.append(f"Lonjakan >={BIG_MOVE_PCT:.0f}% (-15)")

        if stoch_signal_gc["code"] == "EARLY":
            notes.append("Watchlist: belum cross")
        if not final:
            notes.append("Candle hari ini belum final")

        score = max(0, min(100, score))

        res_gc = {
            "Ticker": formatted_ticker.replace(".JK", ""),
            "Harga": int(c0),
            "Change (%)": round(change_pct, 2),
            "Value (M)": round(val0 / 1_000_000_000, 2),
            "Stoch %K": round(k0, 1),
            "Stoch %D": round(d0, 1),
            "Score": score,
            "Detail Signal": " | ".join(notes),
            "_Tgl": tgl,
            "_Final": final,
            "_Kode": stoch_signal_gc["code"],
            "Signal": stoch_signal_gc["code"],
            "Vol x MA20": round(vr, 1),
            "Signal Tags": " | ".join(_tags_from_notes(notes)),
            "Candle Final": bool(final),
            "Data As Of": tgl,
            "Avg Value 20D (M)": round(avg_val20 / 1_000_000_000, 2),
        }

    # =========================================================
    # 2. DEAD CROSS (BEARISH) - WAJIB HARI INI MERAH (change_pct < 0)
    #    Cermin GC (skor negatif, maks -100): makin kuat makin negatif
    # =========================================================
    is_red = change_pct < 0

    dc_today = is_red and (k1 > d1) and (k0 <= d0) and (k0 > 70)
    dc_yesterday = is_red and (k2 > d2) and (k1 <= d1) and (k0 <= d0) and (k1 > 70)
    dc_2days_ago = (
        is_red and (k3 > d3) and (k2 <= d2) and (k1 <= d1) and (k0 <= d0) and (k2 > 70)
    )
    is_almost_dc = is_red and (k0 >= d0) and ((k0 - d0) <= 3.0) and (k0 > 70) and (k0 < k1)

    stoch_signal_dc = None
    if dc_today:
        stoch_signal_dc = {"type": "DC Hari Ini (H-0)", "score": -30, "code": "H0", "pos": -1, "k": k0}
    elif dc_yesterday:
        stoch_signal_dc = {"type": "DC Kemarin (H-1)", "score": -25, "code": "H1", "pos": -2, "k": k1}
    elif dc_2days_ago:
        stoch_signal_dc = {"type": "DC 2 Hari Lalu (H-2)", "score": -20, "code": "H2", "pos": -3, "k": k2}
    elif include_early and is_almost_dc:
        stoch_signal_dc = {"type": "Early DC Signal (Merapat)", "score": -10, "code": "EARLY", "pos": -1, "k": k0}

    if stoch_signal_dc:
        score = stoch_signal_dc["score"]
        notes = [stoch_signal_dc["type"]]

        # PSAR (hanya dipercaya kalau ADX cukup)
        if psar0_bear:
            if not adx_ok:
                notes.append(f"PSAR diabaikan (ADX {adx0:.0f} < {MIN_ADX:.0f}, sideways)")
            elif bear_flip_fresh:
                score -= 20
                notes.append(f"PSAR Flip Bearish <={FLIP_LOOKBACK} candle (-20)")
            else:
                score -= 10
                notes.append("PSAR Bearish (-10)")

        # Volume di hari cross
        vr = vol_ratio(stoch_signal_dc["pos"])
        vol_pending = (not final) and stoch_signal_dc["pos"] == -1
        if vol_pending:
            notes.append("Volume hari ini belum final (tidak dihitung)")
        elif vr >= 1.5:
            score -= 15
            notes.append(f"Vol {vr:.1f}x MA20 (-15)")
        elif vr >= 1.0:
            score -= 8
            notes.append(f"Vol {vr:.1f}x MA20 (-8)")

        # Konteks tren
        if downtrend:
            score -= 20
            notes.append("Lanjutan Downtrend (-20)")
        elif below_ma50:
            score -= 10
            notes.append("Di bawah MA50 (-10)")
        elif have_ma:
            notes.append("Koreksi di Uptrend (-0)")

        # Kedalaman overbought saat cross
        if stoch_signal_dc["k"] > 80:
            score -= 15
            notes.append("Overbought dalam %K>80 (-15)")
        else:
            score -= 8
            notes.append("Zona overbought %K>70 (-8)")

        # Penalti sudah turun tajam (kurang layak dikejar)
        if change_pct <= -BIG_MOVE_PCT:
            score += 15
            notes.append(f"Sudah turun >={BIG_MOVE_PCT:.0f}% (+15)")

        if stoch_signal_dc["code"] == "EARLY":
            notes.append("Watchlist: belum cross")
        if not final:
            notes.append("Candle hari ini belum final")

        score = min(0, max(-100, score))

        res_dc = {
            "Ticker": formatted_ticker.replace(".JK", ""),
            "Harga": int(c0),
            "Change (%)": round(change_pct, 2),
            "Value (M)": round(val0 / 1_000_000_000, 2),
            "Stoch %K": round(k0, 1),
            "Stoch %D": round(d0, 1),
            "Score": score,
            "Detail Signal": " | ".join(notes),
            "_Tgl": tgl,
            "_Final": final,
            "_Kode": stoch_signal_dc["code"],
            "Signal": stoch_signal_dc["code"],
            "Vol x MA20": round(vr, 1),
            "Signal Tags": " | ".join(_tags_from_notes(notes)),
            "Candle Final": bool(final),
            "Data As Of": tgl,
            "Avg Value 20D (M)": round(avg_val20 / 1_000_000_000, 2),
        }

    return res_gc, res_dc


def _process_single_ticker(ticker, df=None, include_early=False, now=None):
    """Proses satu ticker. df = DataFrame OHLCV siap pakai; kalau None,
    data di-download sendiri (kompatibel dengan pemanggilan lama)."""
    try:
        if df is None:
            formatted = _fmt_ticker(ticker)
            df = _download_batch([formatted]).get(formatted)
            if df is None:
                return None, None
        return _process_core(ticker, df, include_early, now)
    except Exception:
        return None, None


# =============================================================
# CATATAN SINYAL (opsional, untuk statistik/backtest nanti)
# =============================================================
def _append_signal_log(path, rows_gc, rows_dc):
    recs = []
    for arah, rows in (("GC", rows_gc), ("DC", rows_dc)):
        for r in rows:
            if not r.get("_Final", True):
                continue  # jangan catat candle yang belum final
            recs.append({
                "Tanggal": r["_Tgl"],
                "Arah": arah,
                "Ticker": r["Ticker"],
                "Harga": r["Harga"],
                "Score": r["Score"],
                "Signal": r["_Kode"],
                "Detail Signal": r["Detail Signal"],
            })
    if not recs:
        return 0
    new = pd.DataFrame(recs)
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    if os.path.exists(path):
        old = pd.read_csv(path)
        seen = set(zip(old["Tanggal"].astype(str), old["Arah"], old["Ticker"]))
        keep = [
            (t, a, k) not in seen
            for t, a, k in zip(new["Tanggal"], new["Arah"], new["Ticker"])
        ]
        new = new[keep]
        if new.empty:
            return 0
        new.to_csv(path, mode="a", header=False, index=False)
    else:
        new.to_csv(path, index=False)
    return len(new)


# =============================================================
# RUNNER
# =============================================================
def run_stoch_psar_screener(
    tickers=None,
    progress_callback=None,
    data=None,
    include_early=False,
    log_path=None,
):
    """
    tickers        : list ticker (None = seluruh IHSG)
    progress_callback(completed, total)
    data           : (opsional) {ticker: DataFrame OHLCV} hasil download yang
                     sudah ada, supaya tidak download ulang. Ticker yang tidak
                     ada di sini tetap di-download otomatis.
    include_early  : (opsional) True = ikutkan Early Signal (watchlist)
    log_path       : (opsional) path CSV untuk mencatat sinyal harian
    Return: (df_gc, df_dc) -> format sama seperti sebelumnya.
    Info run (gagal download, dll) ada di df.attrs["run_info"] atau
    get_last_run_info().
    """
    used_fallback = False
    if tickers is None:
        try:
            tickers = get_all_ihsg_tickers()
        except Exception:
            tickers = DEFAULT_SAHAM_LIST
            used_fallback = True

        if not tickers:
            tickers = DEFAULT_SAHAM_LIST
            used_fallback = True

    if used_fallback:
        logger.warning(
            "Daftar ticker IHSG gagal dimuat, memakai DEFAULT_SAHAM_LIST (%d saham)",
            len(DEFAULT_SAHAM_LIST),
        )

    ordered = list(dict.fromkeys(_fmt_ticker(t) for t in tickers))
    total_tickers = len(ordered)

    provided = {}
    if data:
        for key, frame in data.items():
            provided[_fmt_ticker(key)] = frame

    results_gc = []
    results_dc = []
    failed_download = []
    too_short = []
    calc_error = []
    from_provided = 0
    completed = 0

    for start in range(0, total_tickers, BATCH_SIZE):
        chunk = ordered[start:start + BATCH_SIZE]

        frames = {}
        need = []
        for t in chunk:
            d = _clean_df(provided.get(t)) if t in provided else None
            if d is not None:
                frames[t] = d
                from_provided += 1
            else:
                need.append(t)
        if need:
            frames.update(_download_batch(need))

        for t in chunk:
            d = frames.get(t)
            if d is None:
                failed_download.append(t)
            elif len(d) < MIN_BARS:
                too_short.append(t)
            else:
                try:
                    res_gc, res_dc = _process_core(t, d, include_early)
                    if res_gc:
                        results_gc.append(res_gc)
                    if res_dc:
                        results_dc.append(res_dc)
                except Exception:
                    calc_error.append(t)

            completed += 1
            if progress_callback:
                progress_callback(completed, total_tickers)

    cols = [
        "Ticker",
        "Harga",
        "Change (%)",
        "Value (M)",
        "Stoch %K",
        "Stoch %D",
        "Score",
        "Detail Signal",
        "Signal",
        "Vol x MA20",
        "Signal Tags",
        "Candle Final",
        "Data As Of",
        "Avg Value 20D (M)",
    ]

    df_gc = pd.DataFrame(results_gc)[cols] if results_gc else pd.DataFrame(columns=cols)
    df_dc = pd.DataFrame(results_dc)[cols] if results_dc else pd.DataFrame(columns=cols)

    if not df_gc.empty and "Score" in df_gc.columns:
        df_gc = df_gc.sort_values(by="Score", ascending=False).reset_index(drop=True)
    if not df_dc.empty and "Score" in df_dc.columns:
        df_dc = df_dc.sort_values(by="Score", ascending=True).reset_index(drop=True)

    logged = 0
    if log_path:
        try:
            logged = _append_signal_log(log_path, results_gc, results_dc)
        except Exception as e:
            logger.warning("Gagal menulis catatan sinyal: %s", e)

    if failed_download:
        logger.warning(
            "%d dari %d ticker gagal di-download", len(failed_download), total_tickers
        )

    info = {
        "total": total_tickers,
        "data_siap_pakai": from_provided,
        "gagal_download": failed_download,
        "data_kurang": too_short,
        "error_hitung": calc_error,
        "fallback_list_dipakai": used_fallback,
        "sinyal_gc": len(results_gc),
        "sinyal_dc": len(results_dc),
        "sinyal_dicatat": logged,
    }
    LAST_RUN_INFO.clear()
    LAST_RUN_INFO.update(info)
    df_gc.attrs["run_info"] = info
    df_dc.attrs["run_info"] = info

    return df_gc, df_dc
