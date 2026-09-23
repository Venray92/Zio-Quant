"""Kalender bursa IDX dan data harian bersama untuk semua screener.

Modul ini sengaja tidak memakai streamlit, jadi bisa dipakai juga oleh
skrip harian (GitHub Actions) dan oleh engine.
"""
import io
import json
import os
import re
import urllib.request
from pathlib import Path
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
IHSG_FILE = "ihsg_history.csv"
RECAP_FILE = "screener_history.json"
SECTOR_HISTORY_FILE = "sector_history.json"

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
        # 2027: pengumuman BEI 16 Sep 2026 No. Peng-00169/BEI.POP/09-2026 (diperbarui Peng-00171/BEI.POP/09-2026
        # tanggal 17 Sep 2026, hanya perubahan keterangan 6 Mei). 20 hari libur, 241 hari bursa.
        "2027-01-01",  # Tahun Baru
        "2027-01-05",  # Isra Mikraj
        "2027-02-05",  # Cuti bersama Imlek
        "2027-03-08",  # Nyepi
        "2027-03-09",  # Cuti bersama Idulfitri
        "2027-03-10",  # Idulfitri
        "2027-03-11",  # Idulfitri
        "2027-03-12",  # Cuti bersama Idulfitri
        "2027-03-15",  # Cuti bersama Idulfitri
        "2027-03-25",  # Cuti bersama Wafat Yesus Kristus
        "2027-03-26",  # Wafat Yesus Kristus
        "2027-05-06",  # Kenaikan Yesus Kristus
        "2027-05-17",  # Iduladha
        "2027-05-18",  # Cuti bersama Iduladha
        "2027-05-19",  # Cuti bersama Waisak
        "2027-05-20",  # Waisak
        "2027-06-01",  # Hari Lahir Pancasila
        "2027-08-17",  # Proklamasi Kemerdekaan
        "2027-12-24",  # Cuti bersama Natal
        "2027-12-31",  # Libur bursa akhir tahun
    )
)
# Tahun yang kalendernya sudah diisi (untuk peringatan kalau lupa update).
IDX_HOLIDAY_YEARS = frozenset({2026, 2027})


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


def calendar_alert(now=None):
    """Pengingat mengisi kalender libur. None kalau aman.
    {"year", "level"}: 'warn' mulai 1 Oktober untuk tahun depan; 'urgent' kalau tahun ini sendiri belum diisi
    atau tahun depan belum diisi pada Desember."""
    now = now or now_wib()
    y = now.year
    if y not in IDX_HOLIDAY_YEARS:
        return {"year": y, "level": "urgent"}
    if y + 1 not in IDX_HOLIDAY_YEARS:
        if now.month == 12:
            return {"year": y + 1, "level": "urgent"}
        if now.month >= 10:
            return {"year": y + 1, "level": "warn"}
    return None


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


def load_ihsg_history(repo, timeout=25):
    """Riwayat harian IHSG (Date, Open, High, Low, Close, Volume). Melempar error jika gagal."""
    raw = http_get(data_url(repo, IHSG_FILE), timeout)
    df = pd.read_csv(io.BytesIO(raw), parse_dates=["Date"])
    if not {"Date", "Open", "High", "Low", "Close"}.issubset(df.columns) or df.empty:
        raise ValueError("Format riwayat IHSG tidak sesuai")
    return df


def load_recap_history(repo, timeout=25):
    """Riwayat hasil screener harian (JSON). Melempar error jika gagal."""
    return json.loads(http_get(data_url(repo, RECAP_FILE), timeout).decode("utf-8"))


def load_sector_history(repo, timeout=25):
    """Riwayat harian sektor 'menyala' (JSON), utk heatmap Sector Radar. Melempar error jika gagal."""
    return json.loads(http_get(data_url(repo, SECTOR_HISTORY_FILE), timeout).decode("utf-8"))


def build_ticker_map(df):
    return {
        str(t): g.drop(columns=["Ticker"]).reset_index(drop=True)
        for t, g in df.groupby("Ticker", sort=False)
    }


# ----------------------------------------------------------------------
# DAFTAR SAHAM: satu pembaca untuk semua (screener, batch, tugas harian)
# ----------------------------------------------------------------------
_HEADER_HINTS = ("kode", "ticker", "code", "symbol")
_TICKER_RE = re.compile(r"^[A-Z0-9]{2,6}$")
_SPLIT_RE = re.compile(r"[,;\t|]")


def parse_ticker_lines(lines):
    """Return (tickers, ignored). tickers: unik, terurut, format 'BBCA.JK'.

    Paham file dengan/tanpa baris judul (Kode, Ticker, ...), pemisah koma/titik koma/tab,
    baris kosong dan komentar (#), huruf kecil, dan akhiran .JK."""
    col, first, seen, out, ignored = 0, True, set(), [], []
    for raw in lines:
        line = str(raw).replace("\ufeff", "").strip()
        if not line or line.startswith("#"):
            continue
        cells = [c.strip().strip('"').strip("'") for c in _SPLIT_RE.split(line)]
        if first:
            first = False
            hit = [i for i, c in enumerate(cells) if any(h in c.lower() for h in _HEADER_HINTS)]
            if hit:
                col = hit[0]
                continue
        if col >= len(cells):
            ignored.append(line)
            continue
        code = cells[col].upper().replace("IDX:", "")
        if code.endswith(".JK"):
            code = code[:-3]
        if not _TICKER_RE.match(code):
            ignored.append(line)
            continue
        t = f"{code}.JK"
        if t not in seen:
            seen.add(t)
            out.append(t)
    return sorted(out), ignored


def find_ticker_file(file_name="daftar_saham.txt", extra_dirs=()):
    root = Path(__file__).resolve().parent.parent
    dirs = [*map(Path, extra_dirs), root / "data", root, Path.cwd() / "data", Path.cwd()]
    for d in dirs:
        for name in (file_name, file_name + ".txt"):
            p = d / name
            if p.is_file():
                return str(p)
    return ""


def read_ticker_file(path, return_ignored=False):
    with open(path, "r", encoding="utf-8-sig") as f:
        tickers, ignored = parse_ticker_lines(f.readlines())
    return (tickers, ignored) if return_ignored else tickers


# ----------------------------------------------------------------------
# UNDUH DATA HARIAN PER GRUP (dipakai saat data live dibutuhkan)
# ----------------------------------------------------------------------
def clean_ohlcv(df):
    """Rapikan DataFrame OHLCV (kolom datar, buang baris kosong). None jika tidak layak."""
    if df is None or len(df) == 0:
        return None
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    for col in ("Open", "High", "Low", "Close", "Volume"):
        if col not in df.columns:
            return None
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    df["Volume"] = df["Volume"].fillna(0)
    return df if not df.empty else None


def split_download(raw, tickers):
    """Pecah hasil yf.download(list ticker) jadi {ticker: DataFrame}."""
    out = {}
    if raw is None or len(raw) == 0:
        return out
    if not isinstance(raw.columns, pd.MultiIndex):
        if len(tickers) == 1:
            d = clean_ohlcv(raw)
            if d is not None:
                out[tickers[0]] = d
        return out
    lvl0 = set(raw.columns.get_level_values(0))
    lvl1 = set(raw.columns.get_level_values(1))
    for tk in tickers:
        try:
            if tk in lvl0:
                sub = raw[tk]
            elif tk in lvl1:
                sub = raw.xs(tk, axis=1, level=1)
            else:
                continue
            d = clean_ohlcv(sub)
            if d is not None:
                out[tk] = d
        except Exception:
            continue
    return out


def download_daily_batch(tickers, period="6mo", retries=1):
    """Unduh satu grup ticker sekaligus (panggil per maksimal 50 ticker)."""
    import yfinance as yf

    got = {}
    for _ in range(retries + 1):
        todo = [t for t in tickers if t not in got]
        if not todo:
            break
        try:
            raw = yf.download(
                todo, period=period, interval="1d", group_by="ticker",
                auto_adjust=False, progress=False, threads=True,
            )
            got.update(split_download(raw, todo))
        except Exception:
            pass
    return got
