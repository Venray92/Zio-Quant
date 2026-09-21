"""Sumber data bersama untuk halaman Streamlit (batch Trade Planner, screener RSI dan Stoch, panel Trade Plan).

Aturan: hari bursa buka jam 09:00-17:40 WIB = ambil langsung (live). Di luar itu = file harian,
selama file sudah memuat candle final terbaru. Kalau file belum ada / basi = otomatis live.
"""
import streamlit as st

from engines.market_data import (
    build_ticker_map,
    calendar_is_covered,
    choose_source,
    fmt_date_id,
    is_live_window,
    load_market_file,
    normalize_ticker,
    now_wib,
    resolve_repo,
)


@st.cache_resource(ttl=300, show_spinner=False)
def _load_shared_file(repo):
    df, meta = load_market_file(repo)
    return build_ticker_map(df), meta


def load_shared_file():
    """Return (peta ticker -> DataFrame, meta) atau (None, None) jika tidak tersedia."""
    repo = resolve_repo()
    if not repo:
        return None, None
    try:
        return _load_shared_file(repo)
    except Exception:
        return None, None


def prepare_batch_source(now=None):
    """Tentukan sumber data untuk scan banyak saham. Return (data_map atau None, teks sumber)."""
    now = now or now_wib()
    data_map, meta = (None, None)
    if not is_live_window(now):
        data_map, meta = load_shared_file()
    source, reason = choose_source(now, meta)
    note = ""
    if not calendar_is_covered(now.date()):
        note = f" · kalender libur bursa {now.year} belum diisi"
    if source == "file":
        updated = str(meta.get("updated_at_wib", "")).strip()
        upd = f" · diperbarui {updated} WIB" if updated else ""
        return (
            data_map,
            f"Sumber data: file harian · Data per {fmt_date_id(meta['last_candle_date'])}{upd}{note}",
        )
    return None, f"Sumber data: live (Yahoo) · diambil {now.strftime('%H:%M')} WIB · {reason}{note}"


def get_shared_history(symbol, now=None):
    """DataFrame harian satu saham dari file bersama, atau None kalau harus ambil langsung."""
    now = now or now_wib()
    if is_live_window(now):
        return None
    data_map, meta = load_shared_file()
    source, _ = choose_source(now, meta)
    if source != "file" or not data_map:
        return None
    return data_map.get(normalize_ticker(symbol))
