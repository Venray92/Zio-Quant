"""Rekap screener harian dan mingguan dari riwayat hasil (scripts/update_market_data.py menyimpannya tiap hari).

Murni (tanpa Streamlit). Hasil memakai pengaturan bawaan tiap screener, jadi bisa berbeda dari hasil di halaman screener
kalau pengguna mengubah pilihan di sana. Hasil weekly hanya statistik masa lalu (tanpa biaya transaksi), bukan jaminan.
"""
import math

import pandas as pd

# Trend Scanner: Breakout Surge & Trend Reset ikut direkap (satu arah, selalu "Bullish" -- keduanya
# memang cuma punya versi bullish, tidak ada versi bearish di engine). Quiet Accumulation SENGAJA tidak
# direkap di sini: dia watchlist tanpa skor & tanpa arah beli/jual, jadi "hasilnya" tidak bisa diukur
# dengan cara yang sama (rekap butuh harga sinyal + arah utk menghitung searah/tidaknya pergerakan).
SCREENERS = (("rsi", "RSI Reversal"), ("stoch_psar", "Stoch Momentum"), ("breakout_surge", "Breakout Surge"), ("trend_reset", "Trend Reset"))
SINGLE_DIRECTION = {"breakout_surge", "trend_reset"}  # tidak ada versi Bearish, sembunyikan baris itu di UI
KEEP_DAYS = 40


def _t(x):
    x = str(x).strip().upper()
    return x if x.endswith(".JK") else x + ".JK"


def _f(x, default=0.0):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


# ---------------------------------------------------------------- hasil screener -> daftar sinyal ringkas
def hits_from_rsi(df):
    out = []
    if df is None or len(df) == 0:
        return out
    for _, r in df.iterrows():
        d = str(r.get("Direction", ""))
        if d not in ("Bullish", "Bearish"):
            continue
        out.append({"t": _t(r["Ticker"]), "d": d, "s": _f(r.get("Score")), "p": _f(r.get("Close_Price")), "c": _f(r.get("Change_Pct")), "n": str(r.get("Pattern", ""))[:60]})
    return out


def hits_from_stoch(df_gc, df_dc):
    out = []
    for df, d in ((df_gc, "Bullish"), (df_dc, "Bearish")):
        if df is None or len(df) == 0:
            continue
        for _, r in df.iterrows():
            out.append({"t": _t(r["Ticker"]), "d": d, "s": _f(r.get("Score")), "p": _f(r.get("Harga")), "c": _f(r.get("Change (%)")), "n": str(r.get("Signal", ""))[:60]})
    return out


def hits_from_breakout(df):
    """Trend Scanner - Breakout Surge. Selalu 'Bullish' (tidak ada versi bearish)."""
    out = []
    if df is None or len(df) == 0:
        return out
    for _, r in df.iterrows():
        out.append({
            "t": _t(r["Ticker"]), "d": "Bullish", "s": _f(r.get("Score")), "p": _f(r.get("Close_Price")), "c": _f(r.get("Change_Pct")),
            "n": f"Tembus {_f(r.get('Breakout Level')):,.0f}".replace(",", "."),
        })
    return out


def hits_from_trend_reset(df):
    """Trend Scanner - Trend Reset. Selalu 'Bullish' (tidak ada versi bearish)."""
    out = []
    if df is None or len(df) == 0:
        return out
    for _, r in df.iterrows():
        out.append({
            "t": _t(r["Ticker"]), "d": "Bullish", "s": _f(r.get("Score")), "p": _f(r.get("Close_Price")), "c": _f(r.get("Change_Pct")),
            "n": f"Koreksi {_f(r.get('Depth From High (%)')):.1f}% dari puncak",
        })
    return out


def add_day(history, date, entries, updated_at="", keep=KEEP_DAYS):
    """Tambahkan hasil satu hari. entries: {kunci_screener: {"hits": [...]} atau {"error": "..."}}. Return riwayat baru."""
    h = history if isinstance(history, dict) else {}
    days = dict(h.get("days") or {})
    days[str(date)[:10]] = entries
    days = dict(sorted(days.items())[-keep:])
    return {"version": 1, "updated_at_wib": updated_at, "days": days}


def clean_history(raw):
    """Buang entri rusak supaya halaman tidak crash kalau file berisi sampah."""
    out = {}
    days = raw.get("days") if isinstance(raw, dict) else None
    if not isinstance(days, dict):
        return {"version": 1, "days": {}}
    for d, entries in days.items():
        if not isinstance(entries, dict) or pd.isna(pd.to_datetime(str(d), errors="coerce")):
            continue
        day = {}
        for key, _ in SCREENERS:
            e = entries.get(key)
            if not isinstance(e, dict):
                continue
            if "error" in e:
                day[key] = {"error": str(e["error"])[:120]}
                continue
            hits = [h for h in (e.get("hits") if isinstance(e.get("hits"), list) else []) if isinstance(h, dict) and h.get("t") and h.get("d") in ("Bullish", "Bearish")]
            day[key] = {"hits": [{"t": _t(h["t"]), "d": h["d"], "s": _f(h.get("s")), "p": _f(h.get("p")), "c": _f(h.get("c")), "n": str(h.get("n", ""))[:60]} for h in hits]}
        out[str(d)[:10]] = day
    return {"version": 1, "updated_at_wib": str(raw.get("updated_at_wib", "")), "days": dict(sorted(out.items()))}


# ---------------------------------------------------------------- rekap harian
def daily_recap(history, key, date=None):
    """Rekap satu screener pada satu hari (default: hari terbaru). None kalau tidak ada data."""
    days = (history or {}).get("days") or {}
    keys = sorted(days)
    if not keys:
        return None
    date = str(date)[:10] if date else keys[-1]
    if date not in days or key not in days[date] or "hits" not in days[date][key]:
        return None
    prev_date = next((d for d in reversed(keys) if d < date and key in days[d] and "hits" in days[d][key]), None)
    prev = {(h["t"], h["d"]) for h in days[prev_date][key]["hits"]} if prev_date else set()
    hits = days[date][key]["hits"]
    out = {"date": date, "prev_date": prev_date, "n": len(hits)}
    for d, name in (("Bullish", "bull"), ("Bearish", "bear")):
        sel = sorted([h for h in hits if h["d"] == d], key=lambda h: (-h["s"] if d == "Bullish" else h["s"], h["t"]))
        out[f"n_{name}"] = len(sel)
        out[f"n_new_{name}"] = sum(1 for h in sel if (h["t"], d) not in prev) if prev_date else None
        out[f"top_{name}"] = sel[:5]
    return out


# ---------------------------------------------------------------- leaderboard akurasi screener
def leaderboard(history, last_close, window=20):
    """Ranking screener dari yang paling akurat: win rate (persen sinyal yang gerak searah prediksi)
    lalu rata-rata edge sebagai tiebreak. Gabungan Bullish+Bearish utk screener 2 arah (RSI, Stoch),
    cuma Bullish utk yang searah (Breakout Surge, Trend Reset). window = berapa hari bursa terakhir
    dari riwayat yang dipakai (bukan lama pengukuran -- itu otomatis dari selisih tanggal ke hari ini).
    """
    rows = []
    for key, name in SCREENERS:
        w = weekly_recap(history, key, last_close, window=window)
        if w is None:
            continue
        sides = ("bull",) if key in SINGLE_DIRECTION else ("bull", "bear")
        n_measured = sum(w[s]["n_measured"] for s in sides)
        n_right = sum(w[s]["n_right"] for s in sides)
        edges = [w[s]["avg_edge"] for s in sides for _ in range(w[s]["n_measured"]) if w[s]["avg_edge"] is not None]
        rows.append({
            "key": key, "name": name, "single_direction": key in SINGLE_DIRECTION,
            "n_days": len(w["dates"]), "n_unique": w["n_unique"],
            "n_measured": n_measured, "n_right": n_right,
            "win_rate": (n_right / n_measured * 100) if n_measured else None,
            "avg_edge": (sum(edges) / len(edges)) if edges else None,
        })
    rows.sort(key=lambda r: (r["win_rate"] is None, -(r["win_rate"] or 0), -(r["avg_edge"] if r["avg_edge"] is not None else -999)))
    return rows


# ---------------------------------------------------------------- rekap mingguan
def weekly_recap(history, key, last_close, window=5):
    """Sinyal `window` hari bursa terakhir yang ada di riwayat + hasilnya sampai harga terakhir.

    last_close: {ticker: harga terakhir}. Tiap saham dihitung dari kemunculan PERTAMA di jendela itu.
    edge = gerak harga searah sinyal (bullish: naik = positif, bearish: turun = positif), belum termasuk biaya.
    """
    days = (history or {}).get("days") or {}
    keys = [d for d in sorted(days) if key in days[d] and "hits" in days[d][key]][-window:]
    if not keys:
        return None
    first, count = {}, {}
    for d in keys:
        for h in days[d][key]["hits"]:
            k = (h["t"], h["d"])
            count[k] = count.get(k, 0) + 1
            first.setdefault(k, (d, h))
    rows = []
    for (t, d), (date0, h) in first.items():
        last = _f(last_close.get(t))
        entry = _f(h["p"])
        elapsed = sum(1 for x in keys if x > date0)
        if entry <= 0 or last <= 0 or elapsed == 0:
            rows.append({"t": t, "d": d, "first": date0, "days": count[(t, d)], "elapsed": elapsed, "chg": None, "edge": None, "score": h["s"]})
            continue
        chg = (last / entry - 1) * 100
        rows.append({"t": t, "d": d, "first": date0, "days": count[(t, d)], "elapsed": elapsed, "chg": chg, "edge": chg if d == "Bullish" else -chg, "score": h["s"]})
    out = {"dates": keys, "per_day": [{"date": d, "n": len(days[d][key]["hits"])} for d in keys], "n_unique": len(rows)}
    for d, name in (("Bullish", "bull"), ("Bearish", "bear")):
        sel = [r for r in rows if r["d"] == d]
        done = [r for r in sel if r["edge"] is not None]
        edges = sorted(r["edge"] for r in done)
        out[name] = {
            "n": len(sel), "n_measured": len(done),
            "n_right": sum(1 for r in done if r["edge"] > 0),
            "hit_rate": sum(1 for r in done if r["edge"] > 0) / len(done) * 100 if done else None,
            "avg_edge": sum(edges) / len(edges) if edges else None,
            "median_edge": (edges[len(edges) // 2] if len(edges) % 2 else (edges[len(edges) // 2 - 1] + edges[len(edges) // 2]) / 2) if edges else None,
            "repeat": sorted([r for r in sel if r["days"] >= 2], key=lambda r: (-r["days"], -r["score"] if d == "Bullish" else r["score"], r["t"]))[:5],
        }
    return out
