"""Peta saham -> sektor & nama perusahaan, dari data/sector_map.csv (diambil dari daftar sektor resmi IDX
per 22 Sep 2026, 11 sektor / 962 saham). Diperbarui manual sebulan sekali (lihat PROJECT_NOTES / peringatan
GitHub Issue di workflow update_market_data)."""
import csv
from pathlib import Path

CSV_NAME = "sector_map.csv"
SECTORS = (
    "Basic Materials", "Consumer Cyclicals", "Consumer Non-Cyclicals", "Energy", "Financials",
    "Healthcare", "Industrials", "Infrastructures", "Properties & Real Estate", "Technology",
    "Transportation & Logistic",
)

_CACHE = {}


def _csv_path():
    return Path(__file__).resolve().parent.parent / "data" / CSV_NAME


def load_sector_map(path=None):
    """{kode_tanpa_JK: {"sector":.., "name":.., "board":..}}. Cache di memori proses (data statis bulanan)."""
    p = str(path or _csv_path())
    if p in _CACHE:
        return _CACHE[p]
    out = {}
    try:
        with open(p, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                kode = (row.get("Kode") or "").strip().upper()
                if not kode:
                    continue
                out[kode] = {
                    "sector": (row.get("Sektor") or "").strip(),
                    "name": (row.get("Nama Perusahaan") or "").strip(),
                    "board": (row.get("Papan Pencatatan") or "").strip(),
                }
    except OSError:
        return {}
    _CACHE[p] = out
    return out


def _code(ticker):
    return str(ticker).strip().upper().replace(".JK", "")


def get_sector(ticker, path=None):
    row = load_sector_map(path).get(_code(ticker))
    return row["sector"] if row else None


def get_company_name(ticker, path=None):
    row = load_sector_map(path).get(_code(ticker))
    return row["name"] if row else None


def get_board(ticker, path=None):
    row = load_sector_map(path).get(_code(ticker))
    return row["board"] if row else None


def display_name(ticker, path=None):
    """'BBCA' atau 'BBCA - Bank Central Asia Tbk.' kalau nama perusahaan diketahui."""
    code = _code(ticker)
    name = get_company_name(code, path)
    return f"{code} - {name}" if name else code


def sector_tickers(sector, path=None):
    """Daftar kode (tanpa .JK) milik satu sektor."""
    m = load_sector_map(path)
    return sorted(k for k, v in m.items() if v["sector"] == sector)


def coverage_stats(all_tickers, path=None):
    """Berapa dari `all_tickers` (format .JK) yang sudah punya pemetaan sektor -- utk alarm bulanan."""
    m = load_sector_map(path)
    codes = {_code(t) for t in all_tickers}
    known = {c for c in codes if c in m}
    return {"total": len(codes), "mapped": len(known), "unmapped": sorted(codes - known)}
