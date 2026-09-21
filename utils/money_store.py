"""Penyimpanan dan aksi Money Management per pengguna. Perhitungan ada di engines/money.py.

Dua dokumen per pengguna:
  mm_settings   : pengaturan risiko dan fee
  mm_portfolio  : {positions, journal, cashflows}, satu dokumen supaya jual/beli tersimpan sekaligus (atomik)
Semua aksi mengembalikan (berhasil, kode, info). View yang menerjemahkan kode menjadi pesan.
"""
import math
import uuid

from engines import money as M
from engines.market_data import now_wib
from utils import storage
from utils.profile import user_id
from utils.watchlist_store import normalize_ticker

KIND_SETTINGS = "mm_settings"
KIND_PORTFOLIO = "mm_portfolio"
MAX_POSITIONS, MAX_JOURNAL, MAX_CASHFLOWS = 50, 2000, 500
REASONS = ("Manual", "TP1", "TP2", "SL")


def _id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def today():
    return now_wib().date().isoformat()


def _num(x, default=0.0):
    return M._num(x, default)


def _date(x, default=""):
    d = M.parse_date(x)
    return d.isoformat() if d else default


# ---------------------------------------------------------------- pembersihan data
def clean_position(x):
    if not isinstance(x, dict):
        return None
    t = normalize_ticker(x.get("ticker") or x.get("Ticker"))
    lots, avg = int(_num(x.get("lots"))), _num(x.get("avg"))
    if not t or lots < 1 or lots > 10**7 or not (0 < avg <= 10**7):
        return None
    return {
        "id": str(x.get("id") or _id("p"))[:24], "ticker": t, "lots": lots, "avg": avg,
        "sl": min(max(0.0, _num(x.get("sl"))), 10**7), "tp1": min(max(0.0, _num(x.get("tp1"))), 10**7), "tp2": min(max(0.0, _num(x.get("tp2"))), 10**7),
        "opened": _date(x.get("opened")), "note": str(x.get("note") or "")[:120], "strategy": str(x.get("strategy") or "")[:8],
    }


def clean_trade(x):
    if not isinstance(x, dict):
        return None
    t = normalize_ticker(x.get("ticker"))
    lots, exit_p = int(_num(x.get("lots"))), _num(x.get("exit"))
    pnl = _num(x.get("pnl"), None) if x.get("pnl") is not None else None
    if not t or lots < 1 or exit_p <= 0 or pnl is None or not math.isfinite(pnl):
        return None
    r = x.get("r")
    r = float(r) if isinstance(r, (int, float)) and math.isfinite(r) else None
    reason = x.get("reason") if x.get("reason") in REASONS else "Manual"
    return {
        "id": str(x.get("id") or _id("t"))[:24], "ticker": t, "lots": lots, "entry": _num(x.get("entry")), "exit": exit_p,
        "opened": _date(x.get("opened")), "closed": _date(x.get("closed"), today()), "pnl": pnl, "pnl_pct": _num(x.get("pnl_pct")),
        "r": r, "reason": reason, "note": str(x.get("note") or "")[:120],
        "fee_buy_pct": _num(x.get("fee_buy_pct")), "fee_sell_pct": _num(x.get("fee_sell_pct")),
    }


def clean_cashflow(x):
    if not isinstance(x, dict):
        return None
    amt = _num(x.get("amount"))
    if amt == 0 or abs(amt) > 1e13:
        return None
    out = {"id": str(x.get("id") or _id("c"))[:24], "date": _date(x.get("date"), today()), "amount": amt, "note": str(x.get("note") or "")[:80]}
    if x.get("pos"):
        out["pos"] = str(x["pos"])[:24]
    return out


def clean_portfolio(raw):
    raw = raw if isinstance(raw, dict) else {}
    seen, positions = set(), []
    for x in raw.get("positions") if isinstance(raw.get("positions"), list) else []:
        p = clean_position(x)
        if p and p["ticker"] not in seen:
            seen.add(p["ticker"])
            positions.append(p)
    journal = [t for t in (clean_trade(x) for x in (raw.get("journal") if isinstance(raw.get("journal"), list) else [])) if t]
    cashflows = [c for c in (clean_cashflow(x) for x in (raw.get("cashflows") if isinstance(raw.get("cashflows"), list) else [])) if c]
    return {"positions": positions[:MAX_POSITIONS], "journal": journal[-MAX_JOURNAL:], "cashflows": cashflows[-MAX_CASHFLOWS:]}


# ---------------------------------------------------------------- baca/tulis
def load_settings():
    return M.clean_settings(storage.load(user_id(), KIND_SETTINGS, {}))


def save_settings(settings):
    s = M.clean_settings(settings)
    storage.save(user_id(), KIND_SETTINGS, s)
    return s


def load_portfolio():
    return clean_portfolio(storage.load(user_id(), KIND_PORTFOLIO, {}))


def save_portfolio(doc):
    return storage.save(user_id(), KIND_PORTFOLIO, clean_portfolio(doc))


def cash_now(doc, settings):
    return M.portfolio_summary(doc["positions"], {}, settings, doc["cashflows"], doc["journal"])["cash"]


# ---------------------------------------------------------------- validasi harga
def _levels_error(price, sl, tp1, tp2):
    if price <= 0:
        return "bad_price"
    if sl and sl >= price:
        return "sl_above_price"
    if tp1 and tp1 <= price:
        return "tp1_below_price"
    if tp1 and tp2 and tp2 < tp1:
        return "tp2_below_tp1"
    if not tp1 and tp2 and tp2 <= price:
        return "tp2_below_price"
    return None


# ---------------------------------------------------------------- aksi
def _apply_add(doc, s, ticker, lots, price, sl, tp1, tp2, opened, note, strategy, owned):
    t = normalize_ticker(ticker)
    lots = int(_num(lots))
    if not t:
        return False, "bad_ticker", {}
    if lots < 1:
        return False, "bad_lots", {}
    err = _levels_error(price, sl, tp1, tp2)
    if err:
        return False, err, {}
    if len(doc["positions"]) >= MAX_POSITIONS and all(p["ticker"] != t for p in doc["positions"]):
        return False, "too_many", {"max": MAX_POSITIONS}
    cost = M.buy_cost(lots, price, s["fee_buy_pct"] / 100)
    if not owned:
        cash = cash_now(doc, s)
        if cost > cash + 1e-6:
            return False, "cash_short", {"short": cost - cash, "cost": cost, "cash": cash}
    positions, pos, merged = M.add_position(
        doc["positions"],
        {"ticker": t, "lots": lots, "avg": float(price), "sl": sl, "tp1": tp1, "tp2": tp2, "opened": opened or today(), "note": note, "strategy": strategy},
        _id("p"),
    )
    doc["positions"] = positions
    if owned:
        doc["cashflows"].append({"id": _id("c"), "date": _date(opened, today()), "amount": cost, "note": f"In-kind: {t.replace('.JK', '')}", "pos": pos["id"]})
    return True, "merged" if merged else "added", {"ticker": t.replace(".JK", ""), "lots": lots, "cost": cost}


def add_position(ticker, lots, price, sl=0, tp1=0, tp2=0, opened="", note="", strategy="", owned=False):
    doc, s = load_portfolio(), load_settings()
    ok, code, info = _apply_add(doc, s, ticker, lots, _num(price), _num(sl), _num(tp1), _num(tp2), opened, str(note or "")[:120], strategy, owned)
    if ok:
        info["saved"] = save_portfolio(doc)
    return ok, code, info


def import_positions(rows, owned=False):
    """rows: list dict (ticker, lots, avg, sl, tp1, tp2, opened, note). Return (ok, 'imported', ringkasan)."""
    doc, s = load_portfolio(), load_settings()
    res = {"added": 0, "merged": 0, "errors": []}
    for i, r in enumerate(rows, 1):
        ok, code, info = _apply_add(doc, s, r.get("ticker"), r.get("lots"), _num(r.get("avg")), _num(r.get("sl")), _num(r.get("tp1")), _num(r.get("tp2")),
                                    r.get("opened") or "", str(r.get("note") or "")[:120], "", owned)
        if ok:
            res["merged" if code == "merged" else "added"] += 1
        else:
            res["errors"].append((i, code))
    if res["added"] or res["merged"]:
        save_portfolio(doc)
    return True, "imported", res


def sell(pos_id, lots, price, reason="Manual", note="", date_=""):
    doc, s = load_portfolio(), load_settings()
    pos = next((p for p in doc["positions"] if p["id"] == pos_id), None)
    if not pos:
        return False, "not_found", {}
    try:
        remaining, trade = M.sell_position(pos, lots, price, s, date_ or today(), reason if reason in REASONS else "Manual", note, _id("t"))
    except ValueError as e:
        return False, str(e), {}
    doc["positions"] = [remaining if p["id"] == pos_id else p for p in doc["positions"] if p["id"] != pos_id or remaining]
    doc["journal"].append(trade)
    saved = save_portfolio(doc)
    return True, "sold", {"trade": trade, "closed": remaining is None, "saved": saved}


def edit_position(pos_id, sl, tp1, tp2, note):
    doc = load_portfolio()
    pos = next((p for p in doc["positions"] if p["id"] == pos_id), None)
    if not pos:
        return False, "not_found", {}
    sl, tp1, tp2 = _num(sl), _num(tp1), _num(tp2)
    if tp1 and tp2 and tp2 < tp1:
        return False, "tp2_below_tp1", {}
    pos.update(sl=max(0.0, sl), tp1=max(0.0, tp1), tp2=max(0.0, tp2), note=str(note or "")[:120])
    return True, "edited", {"saved": save_portfolio(doc)}


def delete_position(pos_id):
    doc = load_portfolio()
    if not any(p["id"] == pos_id for p in doc["positions"]):
        return False, "not_found", {}
    doc["positions"], doc["cashflows"] = M.delete_position(doc["positions"], doc["cashflows"], pos_id)
    return True, "deleted", {"saved": save_portfolio(doc)}


def add_cashflow(amount, note="", date_=""):
    doc, s = load_portfolio(), load_settings()
    amount = _num(amount)
    if amount == 0 or abs(amount) > 1e13:
        return False, "bad_amount", {}
    if amount < 0 and -amount > cash_now(doc, s) + 1e-6:
        return False, "cash_short", {"cash": cash_now(doc, s)}
    doc["cashflows"].append({"id": _id("c"), "date": _date(date_, today()), "amount": amount, "note": str(note or "")[:80]})
    return True, "deposit" if amount > 0 else "withdraw", {"saved": save_portfolio(doc)}


def remove_cashflow(cf_id):
    doc, s = load_portfolio(), load_settings()
    cf = next((c for c in doc["cashflows"] if c["id"] == cf_id), None)
    if not cf:
        return False, "not_found", {}
    doc["cashflows"] = [c for c in doc["cashflows"] if c["id"] != cf_id]
    if cash_now(doc, s) < -1e-6:
        return False, "would_go_negative", {}
    return True, "removed", {"saved": save_portfolio(doc)}


def delete_trade(trade_id):
    doc = load_portfolio()
    if not any(t["id"] == trade_id for t in doc["journal"]):
        return False, "not_found", {}
    doc["journal"] = [t for t in doc["journal"] if t["id"] != trade_id]
    return True, "deleted", {"saved": save_portfolio(doc)}


def reset_portfolio():
    return True, "reset", {"saved": save_portfolio({"positions": [], "journal": [], "cashflows": []})}
