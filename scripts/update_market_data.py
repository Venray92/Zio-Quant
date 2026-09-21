#!/usr/bin/env python3
"""Unduh data harian semua saham SEKALI, simpan jadi satu file bersama.

Dijalankan otomatis oleh GitHub Actions (Senin-Jumat sore). Hasilnya dibaca
oleh semua screener di web. Jika data kurang lengkap, file lama TIDAK ditimpa.

Contoh manual:
    python scripts/update_market_data.py --tickers data/daftar_saham.txt --out out
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
import yfinance as yf  # noqa: E402

from engines.market_data import (  # noqa: E402
    DATA_FILE,
    META_FILE,
    candle_is_final,
    data_url,
    expected_last_candle_date,
    http_get,
    now_wib,
    read_ticker_file,
)

BATCH_SIZE = 50
MIN_ROWS = 20              # minimal candle per saham
MIN_SUCCESS_RATIO = 0.80   # minimal saham berhasil dari daftar
MIN_FRESH_RATIO = 0.50     # minimal saham yang candle terakhirnya sudah terbaru
RETRIES = 2
PAUSE_SECONDS = 1.5


def set_output(key, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def read_tickers(path):
    tickers, ignored = read_ticker_file(path, return_ignored=True)
    if ignored:
        print(f"{len(ignored)} baris daftar saham diabaikan (bukan kode saham): {ignored[:5]}")
    return tickers


def download_batch(tickers):
    raw = None
    for attempt in range(RETRIES + 1):
        try:
            raw = yf.download(
                tickers, period="6mo", interval="1d", auto_adjust=False,
                group_by="ticker", progress=False, threads=True,
            )
            if raw is not None and not raw.empty:
                break
        except Exception as e:  # noqa: BLE001
            print(f"  batch gagal (percobaan {attempt + 1}): {e}")
        time.sleep(PAUSE_SECONDS * (attempt + 1))
    out = {}
    if raw is None or raw.empty:
        return out
    for t in tickers:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                if t not in raw.columns.get_level_values(0):
                    continue
                sub = raw[t]
            else:
                sub = raw
            sub = sub[["Open", "High", "Low", "Close", "Volume"]].dropna(
                subset=["Open", "High", "Low", "Close"]
            )
            if len(sub) >= MIN_ROWS:
                out[t] = sub
        except Exception:  # noqa: BLE001
            continue
    return out


def fetch_all(tickers):
    frames = {}
    for i in range(0, len(tickers), BATCH_SIZE):
        chunk = tickers[i:i + BATCH_SIZE]
        print(f"Unduh {i + 1}-{i + len(chunk)} dari {len(tickers)}")
        frames.update(download_batch(chunk))
        time.sleep(PAUSE_SECONDS)
    return frames


def build_long(frames):
    parts = []
    for t, sub in frames.items():
        d = sub.copy()
        idx = pd.to_datetime(d.index)
        if getattr(idx, "tz", None) is not None:
            idx = idx.tz_localize(None)
        d.insert(0, "Date", idx.normalize())
        d.insert(0, "Ticker", t)
        parts.append(d.reset_index(drop=True))
    if not parts:
        return pd.DataFrame()
    df = pd.concat(parts, ignore_index=True)
    df["Volume"] = df["Volume"].fillna(0).astype("int64")
    return df.sort_values(["Ticker", "Date"]).reset_index(drop=True)


def existing_last_date():
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo:
        return None
    try:
        meta = json.loads(http_get(data_url(repo, META_FILE), 20).decode("utf-8"))
        return str(meta.get("last_candle_date", "")) or None
    except Exception:  # noqa: BLE001
        return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default=str(ROOT / "data" / "daftar_saham.txt"))
    ap.add_argument("--out", default=str(ROOT / "out"))
    ap.add_argument("--force", action="store_true", help="unduh ulang walau data sudah terbaru")
    args = ap.parse_args(argv)

    now = now_wib()
    expected = expected_last_candle_date(now)
    print(f"Sekarang {now:%Y-%m-%d %H:%M} WIB, candle final terbaru yang diharapkan: {expected}")

    if not args.force:
        last = existing_last_date()
        if last and last >= expected.isoformat():
            print(f"Data sudah terbaru (per {last}), tidak ada yang perlu diunduh.")
            set_output("changed", "false")
            return 0

    tickers = read_tickers(args.tickers)
    if not tickers:
        print("GAGAL: daftar saham kosong.")
        set_output("changed", "false")
        return 1

    frames = fetch_all(tickers)
    df = build_long(frames)
    if df.empty:
        print("GAGAL: tidak ada data yang berhasil diunduh. File lama tidak ditimpa.")
        set_output("changed", "false")
        return 1

    # Jangan simpan candle hari ini kalau belum final (misal dijalankan manual saat market buka)
    if not candle_is_final(now.date(), now):
        df = df[df["Date"].dt.date != now.date()]
        frames = {t: g for t, g in frames.items() if t in set(df["Ticker"])}

    ok_ratio = df["Ticker"].nunique() / len(tickers)
    last_dates = df.groupby("Ticker")["Date"].max().dt.date
    fresh_ratio = float((last_dates >= expected).mean())
    print(f"Berhasil {df['Ticker'].nunique()}/{len(tickers)} saham ({ok_ratio:.0%}), "
          f"candle terbaru {fresh_ratio:.0%}")
    if ok_ratio < MIN_SUCCESS_RATIO:
        print("GAGAL: saham yang berhasil terlalu sedikit. File lama tidak ditimpa.")
        set_output("changed", "false")
        return 1
    if fresh_ratio < MIN_FRESH_RATIO:
        print(f"GAGAL: data belum sampai {expected} (Yahoo mungkin belum siap). "
              "File lama tidak ditimpa, coba lagi nanti.")
        set_output("changed", "false")
        return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    df_out = df.copy()
    df_out["Date"] = df_out["Date"].dt.strftime("%Y-%m-%d")
    df_out.to_csv(out / DATA_FILE, index=False, compression="gzip", float_format="%.4f")
    got = set(df["Ticker"])
    meta = {
        "version": 1,
        "updated_at_wib": f"{now:%Y-%m-%d %H:%M}",
        "last_candle_date": pd.Timestamp(df["Date"].max()).date().isoformat(),
        "n_tickers": len(got),
        "n_requested": len(tickers),
        "rows": int(len(df)),
        "failed": sorted(set(tickers) - got)[:300],
    }
    (out / META_FILE).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Selesai. File: {out / DATA_FILE} ({(out / DATA_FILE).stat().st_size / 1024:.0f} KB)")
    set_output("changed", "true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
