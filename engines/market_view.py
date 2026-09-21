"""Arah pasar (IHSG): tren, momentum, sebaran saham (breadth), support/resisten, mode pasar, dan ringkasan teks.

Murni (tanpa Streamlit). Semua aturan pasti (deterministik), jadi hasilnya bisa diuji dan dijelaskan.
Ini pandangan teknikal otomatis dari data harga, bukan prediksi dan bukan rekomendasi.
"""
import math

import numpy as np
import pandas as pd

MIN_ROWS = 60
MODE_LABELS = {"risk_on": "Agresif", "neutral": "Netral", "defensive": "Defensif"}
MODE_DESC = {
    "risk_on": "Tren dan sebaran saham sama-sama menguat.",
    "neutral": "Sinyal campur: sebagian faktor menguat, sebagian melemah.",
    "defensive": "Banyak faktor melemah. Biasanya trader memperkecil ukuran posisi dan lebih selektif.",
}


# ---------------------------------------------------------------- format angka gaya Indonesia
def id_num(x, d=0):
    return f"{x:,.{d}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def id_pct(x, d=1, sign=False):
    return (f"{x:+,.{d}f}" if sign else f"{x:,.{d}f}").replace(",", "#").replace(".", ",").replace("#", ".") + "%"


# ---------------------------------------------------------------- indikator
def ema(series, n):
    return series.ewm(span=n, adjust=False).mean()


def rsi(series, n=14):
    """RSI Wilder (RMA)."""
    d = series.diff()
    up, dn = d.clip(lower=0), -d.clip(upper=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    out = 100 - 100 / (1 + au / ad.replace(0, np.nan))
    return out.where(ad != 0, 100.0)


def atr_pct(df, n=14):
    """ATR Wilder dibagi close, dalam persen."""
    c1 = df["Close"].shift(1)
    tr = pd.concat([df["High"] - df["Low"], (df["High"] - c1).abs(), (df["Low"] - c1).abs()], axis=1).max(axis=1)
    tr.iloc[0] = df["High"].iloc[0] - df["Low"].iloc[0]
    atr = tr.ewm(alpha=1 / n, adjust=False).mean()
    return atr / df["Close"] * 100


def _clean(df):
    need = ["Date", "Open", "High", "Low", "Close"]
    if df is None or not set(need) <= set(df.columns):
        return None
    d = df.copy()
    d["Date"] = pd.to_datetime(d["Date"])
    for c in ("Open", "High", "Low", "Close"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=need).sort_values("Date").drop_duplicates("Date", keep="last").reset_index(drop=True)
    return d if len(d) else None


# ---------------------------------------------------------------- swing dan support/resisten
def swing_points(df, left=5, right=5):
    """Swing high/low terkonfirmasi (butuh `right` candle sesudahnya). Return (highs, lows) berisi (indeks, harga)."""
    H, L = df["High"].to_numpy(), df["Low"].to_numpy()
    highs, lows = [], []
    for i in range(left, len(df) - right):
        if H[i] > H[i - left:i].max() and H[i] >= H[i + 1:i + right + 1].max():
            highs.append((i, float(H[i])))
        if L[i] < L[i - left:i].min() and L[i] <= L[i + 1:i + right + 1].min():
            lows.append((i, float(L[i])))
    return highs, lows


def _round_step(price):
    return 10 ** math.floor(math.log10(price)) / 2 if price > 0 else 1


def sr_levels(df, tol_pct=0.6, lookback=250, keep=2):
    """Support dan resisten terdekat dari swing, EMA50/200, dan angka bulat. Return dict supports/resistances."""
    d = df.tail(lookback).reset_index(drop=True)
    close = float(d["Close"].iloc[-1])
    highs, lows = swing_points(d)
    cands = [(p, "swing") for _, p in highs + lows]
    e50, e200 = float(ema(df["Close"], 50).iloc[-1]), float(ema(df["Close"], 200).iloc[-1])
    cands.append((e50, "ema"))
    if len(df) >= 200:
        cands.append((e200, "ema"))
    step = _round_step(close)
    k = math.floor(close * 0.9 / step)
    while k * step <= close * 1.1:
        if k * step > 0:
            cands.append((k * step, "round"))
        k += 1
    cands.sort(key=lambda x: x[0])
    groups = []
    for p, kind in cands:
        if groups and (p - np.mean([g[0] for g in groups[-1]])) / np.mean([g[0] for g in groups[-1]]) * 100 <= tol_pct:
            groups[-1].append((p, kind))
        else:
            groups.append([(p, kind)])
    levels = []
    for g in groups:
        kinds = [k_ for _, k_ in g]
        strength = kinds.count("swing") + (1 if "ema" in kinds else 0) + (1 if "round" in kinds else 0)
        price = float(np.mean([p for p, _ in g]))
        levels.append({"price": price, "pct": (price / close - 1) * 100, "strength": strength, "kinds": sorted(set(kinds))})
    strong = [lv for lv in levels if lv["strength"] >= 2]
    sup = sorted([lv for lv in strong if lv["price"] < close * 0.999], key=lambda lv: -lv["price"])[:keep]
    res = sorted([lv for lv in strong if lv["price"] > close * 1.001], key=lambda lv: lv["price"])[:keep]
    return {"supports": sup, "resistances": res}


# ---------------------------------------------------------------- sebaran saham
def compute_breadth(data_map, last_date, min_avg_value=1_000_000_000, min_price=50, min_rows=51):
    """Sebaran dari saham likuid yang punya candle di last_date: % di atas EMA20/EMA50, naik/turun, high/low 20 sesi."""
    last = str(last_date)[:10]
    n = a20 = a50 = adv = dec = nh = nl = 0
    for df in (data_map or {}).values():
        try:
            if df is None or len(df) < min_rows:
                continue
            dates = pd.to_datetime(df["Date"]) if "Date" in df.columns else pd.to_datetime(df.index)
            if pd.Timestamp(dates.iloc[-1]).strftime("%Y-%m-%d") != last:
                continue
            c = pd.to_numeric(df["Close"], errors="coerce").astype(float).reset_index(drop=True)
            v = pd.to_numeric(df["Volume"], errors="coerce").astype(float).reset_index(drop=True)
            if c.isna().iloc[-1] or c.iloc[-1] < min_price or (c * v).tail(20).mean() < min_avg_value:
                continue
            n += 1
            a20 += int(c.iloc[-1] > ema(c, 20).iloc[-1])
            a50 += int(c.iloc[-1] > ema(c, 50).iloc[-1])
            adv += int(c.iloc[-1] > c.iloc[-2])
            dec += int(c.iloc[-1] < c.iloc[-2])
            nh += int(c.iloc[-1] >= c.tail(20).max())
            nl += int(c.iloc[-1] <= c.tail(20).min())
        except Exception:
            continue
    if n == 0:
        return None
    return {"n": n, "pct_above_ema20": a20 / n * 100, "pct_above_ema50": a50 / n * 100, "adv": adv, "dec": dec, "new_high": nh, "new_low": nl}


# ---------------------------------------------------------------- mode pasar
def _factor(key, label, value, points, note):
    return {"key": key, "label": label, "value": value, "points": points, "note": note}


def market_mode(m):
    """Skor dari beberapa faktor teknikal transparan. m: dict indikator dari build_market_view."""
    f = []
    c, e50, e200 = m["close"], m["ema50"], m["ema200"]
    f.append(_factor("trend_short", "Harga vs EMA50", f"{id_num(c)} vs {id_num(e50)}", 1 if c > e50 else -1, "di atas EMA50" if c > e50 else "di bawah EMA50"))
    if e200 is not None:
        f.append(_factor("trend_mid", "EMA50 vs EMA200", f"{id_num(e50)} vs {id_num(e200)}", 1 if e50 > e200 else -1, "tren menengah naik" if e50 > e200 else "tren menengah turun"))
    r = m["rsi"]
    f.append(_factor("rsi", "Momentum (RSI 14)", id_num(r, 1), 1 if r > 55 else (-1 if r < 45 else 0), "kuat" if r > 55 else ("lemah" if r < 45 else "netral")))
    ret = m["ret20"]
    f.append(_factor("ret20", "Return 20 sesi", id_pct(ret, 1, True), 1 if ret > 2 else (-1 if ret < -2 else 0), "naik" if ret > 2 else ("turun" if ret < -2 else "datar")))
    b = m.get("breadth")
    if b:
        p50, p20 = b["pct_above_ema50"], b["pct_above_ema20"]
        f.append(_factor("breadth50", "Saham di atas EMA50", id_pct(p50, 0), 1 if p50 >= 55 else (-1 if p50 <= 40 else 0), "mayoritas kuat" if p50 >= 55 else ("mayoritas lemah" if p50 <= 40 else "campur")))
        f.append(_factor("breadth20", "Saham di atas EMA20", id_pct(p20, 0), 1 if p20 >= 55 else (-1 if p20 <= 40 else 0), "mayoritas kuat" if p20 >= 55 else ("mayoritas lemah" if p20 <= 40 else "campur")))
        near_high = m["dist_high20"] <= 1.0
        f.append(_factor("divergence", "Reli sempit", "ya" if (near_high and p50 < 45) else "tidak", -1 if (near_high and p50 < 45) else 0, "indeks dekat puncak tapi sebagian besar saham lemah" if (near_high and p50 < 45) else "tidak terdeteksi"))
    ratio = m["atr_ratio"]
    f.append(_factor("volatility", "Volatilitas", f"{id_num(ratio, 1)}x biasanya", -1 if ratio > 1.5 else 0, "bergejolak" if ratio > 1.5 else "normal"))
    score = sum(x["points"] for x in f)
    mode = "risk_on" if score >= 3 else ("defensive" if score <= -3 else "neutral")
    return {"mode": mode, "label": MODE_LABELS[mode], "desc": MODE_DESC[mode], "score": score, "factors": f, "n_factors": len(f)}


# ---------------------------------------------------------------- ringkasan teks
def build_outlook(v):
    """Kalimat ringkas deterministik (bahasa Indonesia) dari hasil analisis."""
    out = []
    c = v["close"]
    if v["ema200"] is not None:
        pos = "di atas" if c > v["ema50"] and c > v["ema200"] else ("di bawah" if c < v["ema50"] and c < v["ema200"] else "di antara")
        out.append(f"IHSG {id_num(c)} berada {pos} EMA50 ({id_num(v['ema50'])}) dan EMA200 ({id_num(v['ema200'])}).")
    else:
        out.append(f"IHSG {id_num(c)} berada {'di atas' if c > v['ema50'] else 'di bawah'} EMA50 ({id_num(v['ema50'])}).")
    out.append(f"RSI {id_num(v['rsi'], 0)}, return 20 sesi {id_pct(v['ret20'], 1, True)}.")
    b = v.get("breadth")
    if b:
        d = next((x for x in v["mode"]["factors"] if x["key"] == "divergence"), None)
        if d and d["points"] < 0:
            out.append(f"Hanya {id_pct(b['pct_above_ema50'], 0)} saham likuid di atas EMA50: kenaikan indeks ditopang segelintir saham.")
        else:
            out.append(f"{id_pct(b['pct_above_ema50'], 0)} saham likuid di atas EMA50, {b['adv']} naik dan {b['dec']} turun hari ini.")
    sup, res = v["levels"]["supports"], v["levels"]["resistances"]
    if sup:
        out.append("Support terdekat " + ", ".join(f"{id_num(x['price'])} ({id_pct(x['pct'], 1, True)})" for x in sup) + ".")
    if res:
        out.append("Resisten terdekat " + ", ".join(f"{id_num(x['price'])} ({id_pct(x['pct'], 1, True)})" for x in res) + ".")
    else:
        out.append("Tidak ada resisten historis terdekat di data 1 tahun: harga berada di area tertinggi.")
    if res and sup:
        nxt = f" membuka ruang ke {id_num(res[1]['price'])}" if len(res) > 1 else " membuka ruang lebih tinggi"
        dn = f" membuka koreksi ke {id_num(sup[1]['price'])}" if len(sup) > 1 else " membuka koreksi lebih dalam"
        out.append(f"Skenario naik: bertahan di atas {id_num(sup[0]['price'])} lalu tembus {id_num(res[0]['price'])}{nxt}.")
        out.append(f"Skenario turun: close di bawah {id_num(sup[0]['price'])}{dn}.")
    return out


def build_market_view(ihsg_df, breadth=None):
    """Analisis IHSG lengkap. None kalau data belum cukup (butuh minimal 60 candle)."""
    d = _clean(ihsg_df)
    if d is None or len(d) < MIN_ROWS:
        return None
    c = d["Close"]
    ema50s = ema(c, 50)
    last = float(c.iloc[-1])
    atrp = atr_pct(d)
    base = float(atrp.tail(60).median())
    m = {
        "asof": d["Date"].iloc[-1].strftime("%Y-%m-%d"),
        "close": last,
        "chg": (last / float(c.iloc[-2]) - 1) * 100 if len(d) > 1 else 0.0,
        "ema20": float(ema(c, 20).iloc[-1]),
        "ema50": float(ema50s.iloc[-1]),
        "ema200": float(ema(c, 200).iloc[-1]) if len(d) >= 200 else None,
        "rsi": float(rsi(c).iloc[-1]),
        "ret20": (last / float(c.iloc[-21]) - 1) * 100 if len(d) > 20 else 0.0,
        "atr_pct": float(atrp.iloc[-1]),
        "atr_ratio": float(atrp.iloc[-1]) / base if base > 0 else 1.0,
        "dist_high20": (float(c.tail(20).max()) / last - 1) * 100,
        "breadth": breadth,
        "levels": sr_levels(d),
    }
    m["mode"] = market_mode(m)
    m["outlook"] = build_outlook(m)
    return m
