"""Money management: semua perhitungan (murni, tanpa Streamlit) supaya bisa dites ketat.

Konsep:
  - 1 lot = 100 lembar. Harga mengikuti fraksi harga BEI.
  - Modal = total setoran (cashflows). Cash = setoran + laba/rugi terealisasi - biaya beli posisi terbuka.
  - Equity = cash + nilai posisi bersih (harga terakhir dikurangi fee jual). Jadi
    equity - setoran - terealisasi = laba/rugi belum terealisasi (persis).
  - Risiko posisi = kerugian jika stop loss kena, dihitung dari biaya beli (termasuk fee).
    Posisi tanpa stop loss dihitung berisiko sebesar seluruh biayanya (paling konservatif).
  - Hanya posisi beli (long).
"""
import math
from datetime import date, datetime

LOT = 100


# ---------------------------------------------------------------- dasar
def _num(x, default=0.0):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


def _floor(x):
    return int(math.floor(x + 1e-9))


def parse_date(value):
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- fraksi harga BEI
def tick_size(price):
    """Fraksi harga BEI: <200: 1, 200-<500: 2, 500-<2.000: 5, 2.000-<5.000: 10, >=5.000: 25."""
    p = _num(price)
    if p < 200:
        return 1
    if p < 500:
        return 2
    if p < 2000:
        return 5
    if p < 5000:
        return 10
    return 25


def round_to_tick(price, mode="nearest"):
    """Bulatkan ke fraksi harga BEI. mode: 'nearest' | 'down' | 'up'. Harga <= 0 menghasilkan 0."""
    p = _num(price)
    if p <= 0:
        return 0
    t = tick_size(p)
    q = p / t
    if mode == "down":
        r = math.floor(q + 1e-9)
    elif mode == "up":
        r = math.ceil(q - 1e-9)
    else:
        r = math.floor(q + 0.5 + 1e-9)
    return int(r * t)


# ---------------------------------------------------------------- pengaturan
PRESETS = {
    "Scalping": dict(risk_pct=0.5, max_total_risk_pct=4.0, max_positions=10, max_alloc_pct=10.0, min_cash_pct=30.0),
    "Swing": dict(risk_pct=1.0, max_total_risk_pct=6.0, max_positions=5, max_alloc_pct=20.0, min_cash_pct=15.0),
    "Trend Following": dict(risk_pct=1.5, max_total_risk_pct=6.0, max_positions=4, max_alloc_pct=25.0, min_cash_pct=10.0),
    "Investing": dict(risk_pct=2.0, max_total_risk_pct=6.0, max_positions=3, max_alloc_pct=33.0, min_cash_pct=0.0),
}
PRESET_DESC = {
    "Scalping": "Frekuensi tinggi, tahan kurang dari 1 hari. Risiko kecil per trade, cash besar.",
    "Swing": "Tahan 3 hari sampai 3 minggu. Titik awal yang seimbang untuk kebanyakan trader.",
    "Trend Following": "Ikut tren berbulan-bulan sampai tren patah. Posisi lebih sedikit dan lebih besar.",
    "Investing": "Fokus fundamental dan akumulasi bertahap. Posisi paling sedikit dan paling besar.",
}
_BASE = dict(fee_buy_pct=0.15, fee_sell_pct=0.25, partial_pct=50, near_sl_pct=3.0)
DEFAULTS = {"preset": "Swing", **PRESETS["Swing"], **_BASE}
RANGES = {
    "risk_pct": (0.1, 5.0, float),
    "max_total_risk_pct": (0.5, 30.0, float),
    "max_positions": (1, 30, int),
    "max_alloc_pct": (1.0, 100.0, float),
    "min_cash_pct": (0.0, 90.0, float),
    "fee_buy_pct": (0.0, 2.0, float),
    "fee_sell_pct": (0.0, 2.0, float),
    "partial_pct": (10, 90, int),
    "near_sl_pct": (0.5, 10.0, float),
}
_PRESET_KEYS = ("risk_pct", "max_total_risk_pct", "max_positions", "max_alloc_pct", "min_cash_pct")


def _match_preset(s):
    for name, vals in PRESETS.items():
        if all(abs(_num(s[k]) - vals[k]) < 1e-9 for k in _PRESET_KEYS):
            return name
    return "Custom"


def clean_settings(raw):
    """Pengaturan yang aman: tipe dipaksa benar, nilai di luar batas dipangkas, preset dicocokkan."""
    s = dict(DEFAULTS)
    raw = raw if isinstance(raw, dict) else {}
    for key, (lo, hi, cast) in RANGES.items():
        if key in raw:
            v = min(max(_num(raw[key], s[key]), lo), hi)
            s[key] = int(round(v)) if cast is int else float(v)
    p = raw.get("preset")
    if isinstance(p, str) and p in PRESETS and all(abs(s[k] - PRESETS[p][k]) < 1e-9 for k in _PRESET_KEYS):
        s["preset"] = p
    else:
        s["preset"] = _match_preset(s)
    return s


def settings_notes(settings):
    """Catatan konsistensi pengaturan: list (level, kunci, argumen)."""
    s = clean_settings(settings)
    notes = []
    if s["risk_pct"] > s["max_total_risk_pct"]:
        notes.append(("warn", "risk_gt_cap", {}))
    elif s["risk_pct"] * s["max_positions"] > s["max_total_risk_pct"] + 1e-9:
        notes.append(("info", "heat_before_slots", {"n": s["max_positions"], "r": s["risk_pct"], "x": s["risk_pct"] * s["max_positions"], "cap": s["max_total_risk_pct"]}))
    if s["max_alloc_pct"] * s["max_positions"] > 100 - s["min_cash_pct"] + 1e-9:
        notes.append(("info", "cash_limits_slots", {"n": s["max_positions"], "a": s["max_alloc_pct"], "cash": s["min_cash_pct"]}))
    return notes


# ---------------------------------------------------------------- matematika posisi
def buy_cost(lots, price, fee_buy):
    return lots * LOT * price * (1 + fee_buy)


def sell_proceeds(lots, price, fee_sell):
    return lots * LOT * price * (1 - fee_sell)


def loss_per_share_at_sl(avg, sl, fee_buy, fee_sell):
    """Kerugian per lembar jika SL kena (dari biaya beli termasuk fee). Bisa <= 0 jika SL di atas biaya beli."""
    return avg * (1 + fee_buy) - sl * (1 - fee_sell)


def breakeven_price(avg, fee_buy, fee_sell):
    return avg * (1 + fee_buy) / (1 - fee_sell)


def _level(pct, cap, warn_at=0.8):
    if pct > cap + 1e-9:
        return "fail"
    return "warn" if pct >= cap * warn_at - 1e-9 else "ok"


# ---------------------------------------------------------------- ukuran posisi
def size_position(equity, cash, open_risk, n_positions, entry, sl, tp1, tp2, settings, risk_pct=None, partial_pct=None):
    """Hitung ukuran posisi baru. Lot = yang terkecil dari batas risiko, alokasi, cash, dan sisa risiko total."""
    s = clean_settings(settings)
    fb, fs = s["fee_buy_pct"] / 100, s["fee_sell_pct"] / 100
    rp = min(max(_num(risk_pct, s["risk_pct"]), 0.05), 10.0) if risk_pct is not None else s["risk_pct"]
    part = int(min(max(_num(partial_pct, s["partial_pct"]), 0), 100)) if partial_pct is not None else s["partial_pct"]
    equity, cash, open_risk = _num(equity), _num(cash), max(0.0, _num(open_risk))
    out = {"valid": False, "errors": [], "notes": [], "lots": 0, "binding": [], "risk_pct_used": rp}

    e_in, s_in, t1_in, t2_in = _num(entry), _num(sl), _num(tp1), _num(tp2)
    e, sl_r = round_to_tick(e_in, "nearest"), round_to_tick(s_in, "down")
    t1 = round_to_tick(t1_in, "down") if t1_in > 0 else 0
    t2 = round_to_tick(t2_in, "down") if t2_in > 0 else 0
    out.update(entry=e, sl=sl_r, tp1=t1, tp2=t2)
    out["rounded"] = [(n, a, b) for n, a, b in (("entry", e_in, e), ("sl", s_in, sl_r), ("tp1", t1_in, t1), ("tp2", t2_in, t2)) if a > 0 and abs(a - b) > 1e-9]

    if equity <= 0:
        out["errors"].append("equity_zero")
    if e <= 0 or sl_r <= 0:
        out["errors"].append("need_entry_sl")
    elif sl_r >= e:
        out["errors"].append("sl_above_entry")
    if e > 0 and t1 > 0 and t1 <= e:
        out["errors"].append("tp1_below_entry")
    if t1 > 0 and t2 > 0 and t2 < t1:
        out["errors"].append("tp2_below_tp1")
    if t1 == 0 and t2 > 0 and e > 0 and t2 <= e:
        out["errors"].append("tp2_below_entry")
    if out["errors"]:
        return out

    rps = loss_per_share_at_sl(e, sl_r, fb, fs)
    unit_cost = buy_cost(1, e, fb)
    budget = equity * rp / 100
    by = {
        "risk": _floor(budget / rps / LOT),
        "alloc": _floor(equity * s["max_alloc_pct"] / 100 / unit_cost),
        "cash": _floor(max(0.0, cash - equity * s["min_cash_pct"] / 100) / unit_cost),
        "heat": _floor(max(0.0, equity * s["max_total_risk_pct"] / 100 - open_risk) / (rps * LOT)),
    }
    lots = min(by.values())
    binding = [k for k, v in by.items() if v == lots]
    if n_positions >= s["max_positions"]:
        lots, binding = 0, ["slots"]
    out.update(valid=True, lots_by=by, lots=lots, binding=binding, risk_per_share=rps, risk_budget=budget)

    shares = lots * LOT
    cost = buy_cost(lots, e, fb)
    risk_amt = lots * LOT * rps
    out.update(
        shares=shares,
        buy_value=shares * e,
        cost=cost,
        alloc_pct=cost / equity * 100,
        risk_amount=risk_amt,
        risk_pct_equity=risk_amt / equity * 100,
        breakeven=round_to_tick(breakeven_price(e, fb, fs), "up"),
    )

    # rencana ambil untung: jual sebagian di TP1, sisanya di TP2
    if t1 and t2:
        l1 = _floor(lots * part / 100)
        l2 = lots - l1
    elif t1:
        l1, l2 = lots, 0
    elif t2:
        l1, l2 = 0, lots
    else:
        l1 = l2 = 0
    plan = {}
    for name, lk, tp in (("tp1", l1, t1), ("tp2", l2, t2)):
        if lk > 0 and tp > 0:
            plan[name] = {
                "lots": lk,
                "price": tp,
                "profit": sell_proceeds(lk, tp, fs) - buy_cost(lk, e, fb),
                "r": (tp * (1 - fs) - e * (1 + fb)) / rps,
            }
    out["plan"] = plan
    out["total_profit"] = sum(v["profit"] for v in plan.values())
    out["total_r"] = out["total_profit"] / risk_amt if risk_amt > 0 else None

    # dampak ke portofolio
    risk_after = open_risk + risk_amt
    cash_after = cash - cost
    pos_after = n_positions + (1 if lots > 0 else 0)
    out["impact"] = {
        "open_risk_pct": risk_after / equity * 100,
        "cash_pct": cash_after / equity * 100,
        "positions": pos_after,
        "checks": [
            {"key": "total_risk", "level": _level(risk_after / equity * 100, s["max_total_risk_pct"]), "args": {"pct": risk_after / equity * 100, "cap": s["max_total_risk_pct"], "before": open_risk / equity * 100}},
            {"key": "cash", "level": "fail" if cash_after / equity * 100 < s["min_cash_pct"] - 1e-9 else ("warn" if cash_after / equity * 100 < s["min_cash_pct"] + 5 else "ok"), "args": {"pct": cash_after / equity * 100, "min": s["min_cash_pct"], "before": cash / equity * 100}},
            {"key": "slots", "level": "fail" if pos_after > s["max_positions"] else ("warn" if pos_after == s["max_positions"] else "ok"), "args": {"n": pos_after, "max": s["max_positions"]}},
        ],
    }
    return out


# ---------------------------------------------------------------- ringkasan portofolio
def portfolio_summary(positions, prices, settings, cashflows, journal):
    """Ringkasan portofolio. prices: {ticker: harga terakhir}. Posisi tanpa harga dihitung di harga rata-rata."""
    s = clean_settings(settings)
    fb, fs = s["fee_buy_pct"] / 100, s["fee_sell_pct"] / 100
    deposits = sum(_num(c.get("amount")) for c in cashflows)
    realized = sum(_num(t.get("pnl")) for t in journal)
    rows, invested, value_net, open_risk = [], 0.0, 0.0, 0.0
    for p in positions:
        lots, avg = int(p["lots"]), float(p["avg"])
        sl, tp1, tp2 = _num(p.get("sl")), _num(p.get("tp1")), _num(p.get("tp2"))
        last = _num(prices.get(p["ticker"]))
        has_price = last > 0
        if not has_price:
            last = avg
        cost = buy_cost(lots, avg, fb)
        val = sell_proceeds(lots, last, fs)
        denom = loss_per_share_at_sl(avg, sl, fb, fs) if sl > 0 else None
        risk = cost if sl <= 0 else max(0.0, lots * LOT * denom)
        invested += cost
        value_net += val
        open_risk += risk
        r_now = (last * (1 - fs) - avg * (1 + fb)) / denom if (denom is not None and denom > 0) else None
        rows.append({
            **p, "lots": lots, "avg": avg, "sl": sl, "tp1": tp1, "tp2": tp2,
            "last": last, "has_price": has_price, "cost": cost, "value": val, "pnl": val - cost,
            "pnl_pct": (val - cost) / cost * 100 if cost > 0 else 0.0,
            "risk": risk,
            "dist_sl_pct": (last - sl) / last * 100 if sl > 0 else None,
            "r_now": r_now,
            "tp1_progress": (last - avg) / (tp1 - avg) if tp1 > avg else None,
            "risk_free": sl > 0 and denom is not None and denom <= 0,
        })
    cash = deposits + realized - invested
    equity = cash + value_net
    eq = equity if equity > 0 else None
    for r in rows:
        r["weight_pct"] = r["value"] / eq * 100 if eq else 0.0
        r["risk_pct_equity"] = r["risk"] / eq * 100 if eq else 0.0
        flags = []
        if r["sl"] <= 0:
            flags.append("no_sl")
        elif r["last"] <= r["sl"]:
            flags.append("sl_hit")
        elif r["dist_sl_pct"] is not None and r["dist_sl_pct"] <= s["near_sl_pct"]:
            flags.append("near_sl")
        if r["tp2"] > 0 and r["last"] >= r["tp2"]:
            flags.append("tp2_hit")
        elif r["tp1"] > 0 and r["last"] >= r["tp1"]:
            flags.append("tp1_hit")
        if r["weight_pct"] > s["max_alloc_pct"] + 1e-9:
            flags.append("overweight")
        if not r["has_price"]:
            flags.append("no_price")
        r["flags"] = flags
    top = max(rows, key=lambda r: r["weight_pct"]) if rows else None
    return {
        "deposits": deposits, "realized": realized, "invested_cost": invested, "market_value": value_net,
        "cash": cash, "equity": equity, "unrealized": value_net - invested,
        "cash_pct": cash / eq * 100 if eq else 0.0,
        "invested_pct": value_net / eq * 100 if eq else 0.0,
        "open_risk": open_risk, "open_risk_pct": open_risk / eq * 100 if eq else 0.0,
        "positions": rows, "n_positions": len(rows),
        "largest": (top["ticker"], top["weight_pct"]) if top else None,
    }


def scenarios(summary, settings):
    """Perubahan equity jika semua SL kena / semua TP1 kena / semua TP2 kena, plus kapasitas trade baru."""
    s = clean_settings(settings)
    fs = s["fee_sell_pct"] / 100
    eq = summary["equity"]
    d_sl = d_tp1 = d_tp2 = 0.0
    for r in summary["positions"]:
        lots, last = r["lots"], r["last"]
        if r["sl"] > 0:
            d_sl += lots * LOT * (min(r["sl"], last) - last) * (1 - fs)
        if r["tp1"] > 0:
            d_tp1 += lots * LOT * (max(r["tp1"], last) - last) * (1 - fs)
        if r["tp2"] > 0:
            d_tp2 += lots * LOT * (max(r["tp2"], last) - last) * (1 - fs)
    pct = lambda v: v / eq * 100 if eq > 0 else 0.0
    budget = eq * s["risk_pct"] / 100 if eq > 0 else 0.0
    room = max(0.0, eq * s["max_total_risk_pct"] / 100 - summary["open_risk"]) if eq > 0 else 0.0
    by_heat = _floor(room / budget) if budget > 0 else 0
    by_slots = max(0, s["max_positions"] - summary["n_positions"])
    return {
        "sl": d_sl, "sl_pct": pct(d_sl), "tp1": d_tp1, "tp1_pct": pct(d_tp1), "tp2": d_tp2, "tp2_pct": pct(d_tp2),
        "capacity": min(by_heat, by_slots), "risk_room": room, "risk_per_trade": budget,
        "cash_free": max(0.0, summary["cash"] - max(eq, 0) * s["min_cash_pct"] / 100),
    }


def risk_checks(summary, settings):
    """Daftar pemeriksaan risiko: {key, level ok|warn|fail|info, args}."""
    s = clean_settings(settings)
    out = []
    out.append({"key": "total_risk", "level": _level(summary["open_risk_pct"], s["max_total_risk_pct"]), "args": {"pct": summary["open_risk_pct"], "cap": s["max_total_risk_pct"]}})
    cp = summary["cash_pct"]
    out.append({"key": "cash", "level": "fail" if cp < s["min_cash_pct"] - 1e-9 else ("warn" if cp < s["min_cash_pct"] + 5 else "ok"), "args": {"pct": cp, "min": s["min_cash_pct"]}})
    n = summary["n_positions"]
    out.append({"key": "slots", "level": "fail" if n > s["max_positions"] else ("warn" if n == s["max_positions"] else "ok"), "args": {"n": n, "max": s["max_positions"]}})
    if summary["largest"]:
        t, w = summary["largest"]
        lvl = "fail" if w > s["max_alloc_pct"] * 1.5 else ("warn" if w > s["max_alloc_pct"] + 1e-9 else "ok")
        out.append({"key": "concentration", "level": lvl, "args": {"ticker": t, "pct": w, "max": s["max_alloc_pct"]}})
    for r in summary["positions"]:
        f = r["flags"]
        code = r["ticker"].replace(".JK", "")
        if "sl_hit" in f:
            out.append({"key": "sl_hit", "level": "fail", "args": {"ticker": code}})
        if "near_sl" in f:
            out.append({"key": "near_sl", "level": "warn", "args": {"ticker": code, "pct": r["dist_sl_pct"]}})
        if "no_sl" in f:
            out.append({"key": "no_sl", "level": "warn", "args": {"ticker": code}})
        if "no_price" in f:
            out.append({"key": "no_price", "level": "warn", "args": {"ticker": code}})
        if "tp1_hit" in f or "tp2_hit" in f:
            out.append({"key": "tp_hit", "level": "info", "args": {"ticker": code, "tp": "TP2" if "tp2_hit" in f else "TP1"}})
    return out


# ---------------------------------------------------------------- transaksi
def add_position(positions, new, pid):
    """Tambah posisi; kalau saham sudah ada digabung (harga rata-rata tertimbang). Return (posisi_list, posisi, digabung)."""
    positions = [dict(p) for p in positions]
    for p in positions:
        if p["ticker"] == new["ticker"]:
            total = p["lots"] + new["lots"]
            p["avg"] = (p["lots"] * p["avg"] + new["lots"] * new["avg"]) / total
            p["lots"] = total
            for k in ("sl", "tp1", "tp2"):
                if _num(new.get(k)) > 0:
                    p[k] = new[k]
            if new.get("note"):
                p["note"] = new["note"]
            if new.get("strategy"):
                p["strategy"] = new["strategy"]
            od, nd = parse_date(p.get("opened")), parse_date(new.get("opened"))
            if nd and (not od or nd < od):
                p["opened"] = nd.isoformat()
            return positions, p, True
    pos = {"id": pid, "ticker": new["ticker"], "lots": int(new["lots"]), "avg": float(new["avg"]),
           "sl": _num(new.get("sl")), "tp1": _num(new.get("tp1")), "tp2": _num(new.get("tp2")),
           "opened": str(new.get("opened") or ""), "note": str(new.get("note") or ""), "strategy": str(new.get("strategy") or "")}
    positions.append(pos)
    return positions, pos, False


def sell_position(pos, lots_sold, price, settings, closed, reason, note, tid):
    """Jual sebagian/seluruh posisi. Return (posisi_baru atau None, catatan_trade)."""
    s = clean_settings(settings)
    fb, fs = s["fee_buy_pct"] / 100, s["fee_sell_pct"] / 100
    lots_sold = int(lots_sold)
    if lots_sold < 1 or lots_sold > pos["lots"]:
        raise ValueError("lots_out_of_range")
    if _num(price) <= 0:
        raise ValueError("bad_price")
    cost = buy_cost(lots_sold, pos["avg"], fb)
    proceeds = sell_proceeds(lots_sold, price, fs)
    pnl = proceeds - cost
    sl = _num(pos.get("sl"))
    denom = loss_per_share_at_sl(pos["avg"], sl, fb, fs) if sl > 0 else None
    r = pnl / (lots_sold * LOT * denom) if (denom is not None and denom > 0) else None
    trade = {
        "id": tid, "ticker": pos["ticker"], "lots": lots_sold, "entry": pos["avg"], "exit": float(price),
        "opened": pos.get("opened", ""), "closed": str(closed), "pnl": pnl, "pnl_pct": pnl / cost * 100 if cost else 0.0,
        "r": r, "reason": reason, "note": str(note or ""), "fee_buy_pct": s["fee_buy_pct"], "fee_sell_pct": s["fee_sell_pct"],
    }
    remaining = None
    if lots_sold < pos["lots"]:
        remaining = dict(pos)
        remaining["lots"] = pos["lots"] - lots_sold
    return remaining, trade


def delete_position(positions, cashflows, pid):
    """Hapus posisi (batalkan pembelian). Cashflow 'sudah dimiliki' milik posisi itu ikut dihapus."""
    return [p for p in positions if p["id"] != pid], [c for c in cashflows if c.get("pos") != pid]


# ---------------------------------------------------------------- statistik jurnal
def journal_stats(trades, cashflows):
    """Statistik trade tertutup + kurva equity terealisasi."""
    ts = [t for t in trades if isinstance(t, dict)]
    n = len(ts)
    pnls = [_num(t.get("pnl")) for t in ts]
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    gp, gl = sum(wins), -sum(losses)
    rs = [t["r"] for t in ts if t.get("r") is not None and math.isfinite(_num(t.get("r"), float("nan")))]
    holds = []
    for t in ts:
        a, b = parse_date(t.get("opened")), parse_date(t.get("closed"))
        if a and b and b >= a:
            holds.append((b - a).days)
    ordered = sorted(ts, key=lambda t: (str(t.get("closed")), str(t.get("id"))))
    streak = best_streak = 0
    for t in ordered:
        if _num(t.get("pnl")) < 0:
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0

    events = [(str(c.get("date"))[:10], 0, _num(c.get("amount"))) for c in cashflows] + [(str(t.get("closed"))[:10], 1, _num(t.get("pnl"))) for t in ts]
    events.sort(key=lambda e: (e[0], e[1]))
    curve, dep, pl = [], 0.0, 0.0
    peak_pl, max_dd, max_dd_pct = 0.0, 0.0, 0.0
    for d, kind, amt in events:
        if kind == 0:
            dep += amt
        else:
            pl += amt
            peak_pl = max(peak_pl, pl)
            dd = peak_pl - pl
            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd / dep * 100 if dep > 0 else 0.0
        curve.append({"date": d, "equity": dep + pl, "deposits": dep, "realized": pl})
    monthly = {}
    for t in ts:
        m = str(t.get("closed"))[:7]
        monthly[m] = monthly.get(m, 0.0) + _num(t.get("pnl"))
    by_reason = {}
    for t in ts:
        by_reason[t.get("reason") or "Manual"] = by_reason.get(t.get("reason") or "Manual", 0) + 1
    return {
        "n": n, "wins": len(wins), "losses": len(losses), "even": n - len(wins) - len(losses),
        "win_rate": len(wins) / n * 100 if n else None,
        "total_pnl": sum(pnls),
        "avg_win": gp / len(wins) if wins else None,
        "avg_loss": gl / len(losses) if losses else None,
        "payoff": (gp / len(wins)) / (gl / len(losses)) if wins and losses else None,
        "profit_factor": gp / gl if gl > 0 else None,
        "no_losses": bool(wins) and gl == 0,
        "expectancy": sum(pnls) / n if n else None,
        "expectancy_r": sum(rs) / len(rs) if rs else None,
        "best": max(ts, key=lambda t: _num(t.get("pnl"))) if ts else None,
        "worst": min(ts, key=lambda t: _num(t.get("pnl"))) if ts else None,
        "avg_hold_days": sum(holds) / len(holds) if holds else None,
        "max_losing_streak": best_streak,
        "max_drawdown": max_dd, "max_drawdown_pct": max_dd_pct,
        "curve": curve, "monthly": dict(sorted(monthly.items())), "by_reason": by_reason,
    }
