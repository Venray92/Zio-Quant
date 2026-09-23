"""Alert harga per saham (per profil): 'kasih tau kalau <ticker> tembus <harga>'. Dicek tiap kali
Home/lonceng dibuka (bukan notifikasi push -- app ini tidak punya jalur push, lihat PROJECT_NOTES).
Pola sama seperti watchlist_store.py."""
import re

from utils import storage
from utils.profile import user_id
from utils.watchlist_store import normalize_ticker

KIND = "alerts"
MAX_ITEMS = 100
_DIRECTIONS = {"above", "below"}
_ID_RE = re.compile(r"^[a-f0-9]{8}$")


def _new_id(existing):
    import secrets

    ids = {x.get("Id") for x in existing}
    while True:
        i = secrets.token_hex(4)
        if i not in ids:
            return i


def _clean_item(x):
    if not isinstance(x, dict):
        return None
    ticker = normalize_ticker(x.get("Ticker"))
    if not ticker:
        return None
    try:
        price = float(x.get("Price", 0) or 0)
    except (TypeError, ValueError):
        return None
    if not (price > 0) or price > 1e12:
        return None
    direction = str(x.get("Direction", "")).strip().lower()
    if direction not in _DIRECTIONS:
        return None
    item_id = str(x.get("Id", "")).strip().lower()
    return {
        "Id": item_id if _ID_RE.match(item_id) else None,
        "Ticker": ticker, "Price": price, "Direction": direction,
        "Created": str(x.get("Created", "") or "")[:10],
        "Fired": bool(x.get("Fired", False)), "Fired At": str(x.get("Fired At", "") or "")[:10],
    }


def clean_items(raw):
    seen, out = set(), []
    for x in raw if isinstance(raw, list) else []:
        item = _clean_item(x)
        if not item:
            continue
        if not item["Id"] or item["Id"] in seen:
            item["Id"] = _new_id(out)
        seen.add(item["Id"])
        out.append(item)
    return out[:MAX_ITEMS]


def load_alerts():
    return clean_items(storage.load(user_id(), KIND, []))


def save_alerts(items):
    return storage.save(user_id(), KIND, clean_items(items))


def add_alert(ticker, price, direction, today_iso):
    t = normalize_ticker(ticker)
    if not t or not (price and price > 0) or direction not in _DIRECTIONS:
        return False
    items = load_alerts()
    if len(items) >= MAX_ITEMS:
        return False
    items.append({"Id": None, "Ticker": t, "Price": float(price), "Direction": direction,
                   "Created": today_iso, "Fired": False, "Fired At": ""})
    save_alerts(items)
    return True


def remove_alert(alert_id):
    items = load_alerts()
    kept = [x for x in items if x["Id"] != alert_id]
    if len(kept) != len(items):
        save_alerts(kept)
    return len(items) - len(kept)


def alerts_for(ticker):
    t = normalize_ticker(ticker)
    return [x for x in load_alerts() if x["Ticker"] == t]


def check_alerts(last_close, today_iso):
    """last_close: {ticker: harga terakhir}. Tandai alert yang kena (Fired=True) & simpan.
    Return list alert yang BARU kena kali ini (belum Fired sebelumnya)."""
    items = load_alerts()
    newly = []
    changed = False
    for x in items:
        if x["Fired"]:
            continue
        price = last_close.get(x["Ticker"])
        if price is None:
            continue
        hit = price >= x["Price"] if x["Direction"] == "above" else price <= x["Price"]
        if hit:
            x["Fired"], x["Fired At"] = True, today_iso
            changed = True
            newly.append(dict(x))
    if changed:
        save_alerts(items)
    return newly
