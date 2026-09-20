"""Kalender bursa IDX dan data harian bersama untuk semua screener.

Modul ini sengaja tidak memakai streamlit, jadi bisa dipakai juga oleh
skrip harian (GitHub Actions) dan oleh engine.
"""
import io
import json
import os
import re
import urllib.request
from datetime import date, datetime, time, timedelta, timezone

import pandas as pd

WIB = timezone(timedelta(hours=7))

# ----------------------------------------------------------------------
# PENGATURAN
# ----------------------------------------------------------------------
# Isi dengan "namaGitHub/zio-quant" (tanpa https://github.com/).
# Boleh juga lewat environment variable MARKET_DATA_REPO.
DATA_REPO = ""
DATA_BRANCH = "data"
DATA_FILE = "market_data.csv.gz"
META_FILE = "market_data_meta.json"

# Hari bursa buka (Senin-Jumat, bukan libur): jam ini data diambil langsung dari web.
LIVE_START = time(9, 0)
LIVE_END = time(17, 40)
# Setelah jam ini candle hari itu dianggap final.
CANDLE_FINAL_TIME = time(16, 15)

# Kalender libur bursa (BEI). Isi ulang tiap tahun. Weekend tidak perlu ditulis.
# 2026: sumber pengumuman BEI No. Peng-00171/BEI.POP/09-2025 (239 hari bursa).
IDX_HOLIDAYS = frozenset(
    date.fromisoformat(d)
    for d in (
        # 2026
        "2026-01-01",  # Tahun Baru
        "2026-01-16",  # Isra Mikraj
        "2026-02-16",  # Cuti bersama Imlek
        "2026-02-17",  # Imlek
        "2026-03-18",  # Cuti bersama Nyepi
        "2026-03-19",  # Nyepi
        "2026-03-20",  # Cuti bersama Idulfitri
        "2026-03-23",  # Cuti bersama Idulfitri
        "2026-03-24",  # Cuti bersama Idulfitri
        "2026-04-03",  # Wafat Yesus Kristus
        "2026-05-01",  # Hari Buruh
        "2026-05-14",  # Kenaikan Yesus Kristus
        "2026-05-15",  # Cuti bersama Kenaikan Yesus Kristus
        "2026-05-27",  # Iduladha
        "2026-05-28",  # Cuti bersama Iduladha
        "2026-06-01",  # Hari Lahir Pancasila
        "2026-06-16",  # Tahun Baru Islam
        "2026-08-17",  # Proklamasi Kemerdekaan
        "2026-08-25",  # Maulid Nabi
        "2026-12-24",  # Cuti bersama Natal
        "2026-12-25",  # Natal
        "2026-12-31",  # Libur bursa akhir tahun
    )
)
# Tahun yang kalendernya sudah diisi (untuk peringatan kalau lupa update).
IDX_HOLIDAY_YEARS = frozenset({2026})


# ----------------------------------------------------------------------
# KALENDER & JAM BURSA
# ----------------------------------------------------------------------
def now_wib():
    return datetime.now(WIB)


def _as_date(d):
    if isinstance(d, str):
        return date.fromisoformat(d.strip()[:10])
    if isinstance(d, datetime):
        return d.date()
    return d


def calendar_is_covered(d):
    """False jika daftar libur untuk tahun itu belum diisi."""
    return _as_date(d).year in IDX_HOLIDAY_YEARS


def is_trading_day(d):
    d = _as_date(d)
    return d.weekday() < 5 and d not in IDX_HOLIDAYS


def previous_trading_day(d, include_self=False):
    d = _as_date(d)
    if include_self and is_trading_day(d):
        return d
    for _ in range(40):
        d -= timedelta(days=1)
        if is_trading_day(d):
            return d
    return d


def expected_last_candle_date(now=None):
    """Tanggal candle final terbaru yang seharusnya sudah ada di data."""
    now = now or now_wib()
    today = now.date()
    if is_trading_day(today) and now.time() >= CANDLE_FINAL_TIME:
        return today
    return previous_trading_day(today)


def is_live_window(now=None):
    """Hari bursa buka (Senin-Jumat, bukan libur), jam 09:00 sampai 17:40 WIB."""
    now = now or now_wib()
    return is_trading_day(now.date()) and LIVE_START <= now.time() <= LIVE_END


def candle_is_final(last_candle_date, now=None):
    """Candle terakhir belum final hanya jika itu candle hari ini, hari bursa, sebelum 16:15 WIB."""
    now = now or now_wib()
    last = _as_date(last_candle_date)
    return not (
        last == now.date()
        and is_trading_day(now.date())
        and now.time() < CANDLE_FINAL_TIME
    )


def fmt_date_id(d):
    return _as_date(d).strftime("%d %b %Y")


# ----------------------------------------------------------------------
# PEMILIHAN SUMBER DATA (BATCH)
# ----------------------------------------------------------------------
def choose_source(now, meta):
    """Kembalikan ("live" | "file", alasan).

    live: hari bursa 09:00-17:40 WIB, atau file harian belum ada / belum terbaru.
    file: di luar jam itu dan file harian sudah memuat candle final terbaru.
    """
    if is_live_window(now):
        return "live", "jam bursa (09:00-17:40 WIB), data diambil langsung"
    if not meta:
        return "live", "file data harian belum tersedia, data diambil langsung"
    try:
        last = date.fromisoformat(str(meta["last_candle_date"]))
    except Exception:
        return "live", "file data harian tidak terbaca, data diambil langsung"
    expected = expected_last_candle_date(now)
    if last < expected:
        return (
            "live",
            f"file harian belum diperbarui (data per {fmt_date_id(last)}), data diambil langsung",
        )
    return "file", "file data harian"


# ----------------------------------------------------------------------
# FILE DATA HARIAN (dibaca web dari cabang "data" di GitHub)
# ----------------------------------------------------------------------
def normalize_ticker(t):
    t = str(t).strip().upper()
    return t if t.endswith(".JK") else f"{t}.JK"


def _parse_git_remote(text):
    m = re.search(r"url\s*=\s*\S*github\.com[:/]+([^/\s]+)/([^/\s]+?)(?:\.git)?\s*$", text, re.M)
    return f"{m.group(1)}/{m.group(2)}" if m else ""


def resolve_repo():
    env = os.environ.get("MARKET_DATA_REPO", "").strip()
    if env:
        return env
    if DATA_REPO.strip():
        return DATA_REPO.strip()
    for path in (".git/config", "/mount/src/zio-quant/.git/config"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                repo = _parse_git_remote(f.read())
            if repo:
                return repo
        except Exception:
            continue
    return ""


def data_url(repo, name):
    return f"https://raw.githubusercontent.com/{repo}/{DATA_BRANCH}/{name}"


def http_get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "zio-quant"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def load_market_file(repo, timeout=25):
    """Baca file harian. Melempar error jika gagal. Return (DataFrame long, meta)."""
    meta = json.loads(http_get(data_url(repo, META_FILE), timeout).decode("utf-8"))
    raw = http_get(data_url(repo, DATA_FILE), timeout)
    df = pd.read_csv(io.BytesIO(raw), compression="gzip", parse_dates=["Date"])
    need = {"Ticker", "Date", "Open", "High", "Low", "Close", "Volume"}
    if not need.issubset(df.columns) or df.empty:
        raise ValueError("Format file data harian tidak sesuai")
    # tanggal candle terakhir diambil dari isi data itu sendiri (bukan hanya dari meta)
    meta["last_candle_date"] = pd.Timestamp(df["Date"].max()).date().isoformat()
    return df, meta


def build_ticker_map(df):
    return {
        str(t): g.drop(columns=["Ticker"]).reset_index(drop=True)
        for t, g in df.groupby("Ticker", sort=False)
    }
