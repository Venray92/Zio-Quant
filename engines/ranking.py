"""Ranking Leaderboard: gabungan pengganti "Leaderboard Screener" + "Rekap Screener" lama.

Rank 1 = Top N saham (default 30) dengan kenaikan % terbesar dari harga sinyal ke harga terakhir,
DEDUP per saham (satu saham cuma muncul sekali walau kena beberapa screener/hari -- diukur dari
kemunculan PERTAMA di jendela yang dipilih, sama seperti pola engines.recap.weekly_recap()).
Hanya sinyal BULLISH yang dihitung (fitur ini soal "saham menarik utk dibeli/dilirik", bukan short).

Rank 2 = kontribusi & akurasi tiap screener, SINKRON ke filter min_gain_pct yang sama dengan Rank 1:
dari saham unik yang bisa diukur kenaikannya (n_signals), berapa % yang tembus >= min_gain_pct
(win_rate) dan berapa banyak yang masuk (n_in_top -- kalau min_gain_pct 0%, hampir semua yang
kepantau ikut terhitung). avg_edge = rata2 gain% dari yang bisa diukur itu. "streak" = hari aktif
beruntun (sinyal terakhir kali screener itu KOSONG, bukan klaim menang beruntun -- supaya
jujur/tidak dilebih-lebihkan) -- metrik ini independen dari min_gain_pct.

Murni (tanpa Streamlit), dipakai oleh views/tab_ranking.py.
"""
import math

from engines import recap as RC

WINDOW_TRADING_DAYS = {"harian": 1, "mingguan": 5, "bulanan": 20, "tahunan": 240}
WINDOW_LABELS = {"harian": "Harian", "mingguan": "Mingguan", "bulanan": "Bulanan", "tahunan": "Tahunan"}


def _f(x, default=0.0):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


def _norm_ticker(t):
    t = str(t).strip().upper()
    return t if t.endswith(".JK") else t + ".JK"


def resolve_days(history, window_key=None, date_start=None, date_end=None):
    """Tanggal2 bursa (yg ADA di riwayat) yang dipakai. date_start/date_end (kalau diisi keduanya)
    MENANG dari window_key (mutually exclusive di UI). Return (list tanggal terurut, label)."""
    days_all = sorted((history or {}).get("days") or {})
    if date_start and date_end:
        d0, d1 = str(date_start)[:10], str(date_end)[:10]
        if d0 > d1:
            d0, d1 = d1, d0
        keys = [d for d in days_all if d0 <= d <= d1]
        return keys, f"{d0} s/d {d1}"
    key = window_key if window_key in WINDOW_TRADING_DAYS else "mingguan"
    n = WINDOW_TRADING_DAYS[key]
    keys = days_all[-n:]
    return keys, WINDOW_LABELS[key]


def _screener_streak(history, key):
    """Berapa hari BURSA TERAKHIR BERTURUT-TURUT (dari histori penuh, bukan cuma jendela yg dipilih)
    screener itu masih mengeluarkan minimal 1 sinyal Bullish. 0 kalau hari terakhir saja sudah kosong.
    Ini metrik "aktif beruntun", BUKAN "menang beruntun" -- kita tidak melebih-lebihkan klaim akurasi."""
    days = sorted((history or {}).get("days") or {})
    streak = 0
    for d in reversed(days):
        entry = (history.get("days") or {}).get(d, {}).get(key)
        if isinstance(entry, dict) and any(h.get("d") == "Bullish" for h in entry.get("hits", [])):
            streak += 1
        else:
            break
    return streak


def build_ranking(history, last_close, window_key=None, date_start=None, date_end=None,
                   min_gain_pct=10.0, watchlist=None, top_n=30):
    """Return dict siap-pakai utk halaman:
    {dates, range_label, rows (Rank 1, sudah top_n & terurut), screener_stats (Rank 2),
     n_candidates (jumlah saham unik SEBELUM filter min_gain), min_gain_pct, top_n}
    rows[i]: rank, ticker, screener_key, screener_name, signal_date, signal_price, last_price,
             gain_pct, is_new (sinyal baru muncul di hari TERAKHIR jendela)
    """
    keys, range_label = resolve_days(history, window_key, date_start, date_end)
    empty = {
        "dates": keys, "range_label": range_label, "rows": [], "screener_stats": [],
        "n_candidates": 0, "min_gain_pct": min_gain_pct, "top_n": top_n,
    }
    if not keys:
        return empty

    wl = None
    if watchlist:
        wl = {_norm_ticker(t) for t in watchlist}

    screener_names = dict(RC.SCREENERS)
    days_map = history.get("days") or {}
    best, all_hits_count = {}, {k: 0 for k, _ in RC.SCREENERS}

    for d in keys:
        day = days_map.get(d) or {}
        for key, _name in RC.SCREENERS:
            entry = day.get(key)
            if not isinstance(entry, dict) or "hits" not in entry:
                continue
            for h in entry["hits"]:
                if h.get("d") != "Bullish":
                    continue
                t = _norm_ticker(h.get("t", ""))
                if not t or (wl is not None and t not in wl):
                    continue
                all_hits_count[key] += 1
                cand = {"t": t, "screener": key, "date": d, "price": _f(h.get("p")), "score": _f(h.get("s"))}
                cur = best.get(t)
                # Kemunculan PERTAMA di jendela ini (biar kenaikan% diukur dari titik masuk paling awal).
                # Kalau dua screener kena hari yg SAMA, ambil yg skornya tertinggi sbg "screener asal".
                if cur is None or d < cur["date"] or (d == cur["date"] and cand["score"] > cur["score"]):
                    best[t] = cand

    # Hitung gain% SEKALI per saham unik (dipakai bareng oleh Rank 1 & Rank 2, biar selalu sinkron).
    measured = []  # semua saham yg gain%-nya bisa diukur (harga sinyal & harga terakhir valid)
    for t, cand in best.items():
        last = _f(last_close.get(t))
        entry_price = cand["price"]
        if last <= 0 or entry_price <= 0:
            continue
        gain = (last / entry_price - 1) * 100
        measured.append({**cand, "t": t, "gain": gain})

    passing = [m for m in measured if m["gain"] >= min_gain_pct]

    rows = []
    for m in passing:
        rows.append({
            "ticker": m["t"], "screener_key": m["screener"], "screener_name": screener_names.get(m["screener"], m["screener"]),
            "signal_date": m["date"], "signal_price": m["price"], "last_price": _f(last_close.get(m["t"])),
            "gain_pct": m["gain"], "is_new": m["date"] == keys[-1],
        })
    rows.sort(key=lambda r: -r["gain_pct"])
    rows = rows[:top_n]
    for i, r in enumerate(rows, start=1):
        r["rank"] = i

    # Rank 2 disinkronkan ke filter min_gain_pct yang sama (bukan top_n) -- jadi kalau min_gain_pct
    # dinaikkan, n_in_top/win_rate tiap screener ikut menyusut sesuai apa yg sebenernya lolos filter,
    # dan di 0% hampir semua saham yg kepantau (measured) ikut terhitung.
    n_total_by_key, n_pass_by_key, gain_sum_by_key = {}, {}, {}
    for m in measured:
        k = m["screener"]
        n_total_by_key[k] = n_total_by_key.get(k, 0) + 1
        gain_sum_by_key[k] = gain_sum_by_key.get(k, 0.0) + m["gain"]
        if m["gain"] >= min_gain_pct:
            n_pass_by_key[k] = n_pass_by_key.get(k, 0) + 1

    stats = []
    for key, name in RC.SCREENERS:
        n_sig = all_hits_count.get(key, 0)
        n_total = n_total_by_key.get(key, 0)
        n_pass = n_pass_by_key.get(key, 0)
        if n_sig == 0 and n_total == 0:
            continue
        win_rate = (n_pass / n_total * 100) if n_total else None
        avg_edge = (gain_sum_by_key.get(key, 0.0) / n_total) if n_total else None
        stats.append({
            "key": key, "name": name, "n_in_top": n_pass, "n_signals": n_sig, "n_total": n_total,
            "win_rate": win_rate, "avg_edge": avg_edge,
            "streak_days": _screener_streak(history, key),
        })
    stats.sort(key=lambda s: (-s["n_in_top"], -(s["win_rate"] or 0)))

    return {
        "dates": keys, "range_label": range_label, "rows": rows, "screener_stats": stats,
        "n_candidates": len(best), "min_gain_pct": min_gain_pct, "top_n": top_n,
    }
