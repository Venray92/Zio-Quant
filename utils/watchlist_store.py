"""Aturan data watchlist (validasi, tambah, hapus, ubah). Penyimpanan lewat utils.storage."""
import re

import streamlit as st

from engines.market_data import now_wib
from utils import storage
from utils.profile import user_id

KIND = "watchlist"
MAX_ITEMS = 100
_TICKER_RE = re.compile(r"^[A-Z0-9]{2,6}$")


def normalize_ticker(value):
    """'bbca' / 'BBCA.JK' / 'IDX:BBCA' -> 'BBCA.JK'. None kalau bukan kode saham yang valid."""
    t = str(value or "").strip().upper().replace("IDX:", "")
    if t.endswith(".JK"):
        t = t[:-3]
    return f"{t}.JK" if _TICKER_RE.match(t) else None


def _clean_item(x):
    if isinstance(x, str):
        x = {"Ticker": x}
    if not isinstance(x, dict):
        return None
    ticker = normalize_ticker(x.get("Ticker") or x.get("ticker"))
    if not ticker:
        return None
    try:
        target = float(x.get("Target Price", 0) or 0)
    except (TypeError, ValueError):
        target = 0.0
    if not (target >= 0) or target > 1e12:
        target = 0.0
    return {
        "Ticker": ticker,
        "Notes": str(x.get("Notes", "") or "")[:80],
        "Target Price": target,
        "Added": str(x.get("Added", "") or "")[:10],
    }


def clean_items(raw):
    """Bersihkan daftar dari penyimpanan (bentuk lama ikut didukung), buang duplikat dan yang tidak valid."""
    seen, out = set(), []
    for x in raw if isinstance(raw, list) else []:
        item = _clean_item(x)
        if item and item["Ticker"] not in seen:
            seen.add(item["Ticker"])
            out.append(item)
    return out[:MAX_ITEMS]


def load_watchlist():
    items = clean_items(storage.load(user_id(), KIND, []))
    st.session_state["watchlist_data"] = items  # cermin untuk halaman lama (Money Management)
    return items


def save_watchlist(items):
    items = clean_items(items)
    ok = storage.save(user_id(), KIND, items)
    st.session_state["watchlist_data"] = items
    return ok


def tickers():
    return [x["Ticker"] for x in load_watchlist()]


def add_tickers(symbols, source="Manual"):
    """Tambah saham. Return {'added': n, 'exists': n, 'invalid': [...], 'limit': bool}."""
    items = load_watchlist()
    have = {x["Ticker"] for x in items}
    res = {"added": 0, "exists": 0, "invalid": [], "limit": False}
    today = now_wib().date().isoformat()
    for s in symbols or []:
        t = normalize_ticker(s)
        if not t:
            res["invalid"].append(str(s)[:12])
        elif t in have:
            res["exists"] += 1
        elif len(items) >= MAX_ITEMS:
            res["limit"] = True
        else:
            items.append({"Ticker": t, "Notes": str(source or "")[:80], "Target Price": 0.0, "Added": today})
            have.add(t)
            res["added"] += 1
    if res["added"]:
        save_watchlist(items)
    return res


def remove_tickers(symbols):
    drop = {normalize_ticker(s) for s in symbols}
    items = load_watchlist()
    kept = [x for x in items if x["Ticker"] not in drop]
    if len(kept) != len(items):
        save_watchlist(kept)
    return len(items) - len(kept)


def update_item(symbol, notes=None, target=None):
    t = normalize_ticker(symbol)
    items = load_watchlist()
    for x in items:
        if x["Ticker"] == t:
            if notes is not None:
                x["Notes"] = str(notes)[:80]
            if target is not None:
                x["Target Price"] = target
            save_watchlist(items)
            return True
    return False


def clear_all():
    save_watchlist([])


def merge_guest(items):
    """Gabungkan daftar tamu ke daftar profil (dipanggil saat profil baru dipilih)."""
    if not items:
        return 0
    have = load_watchlist()
    before = len(have)
    known = {x["Ticker"] for x in have}
    for x in clean_items(items):
        if x["Ticker"] not in known and len(have) < MAX_ITEMS:
            have.append(x)
            known.add(x["Ticker"])
    if len(have) != before:
        save_watchlist(have)
    return len(have) - before


def is_in_watchlist(symbol):
    t = normalize_ticker(symbol)
    return t in {x["Ticker"] for x in load_watchlist()}
