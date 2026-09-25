#!/usr/bin/env python3
"""Unduh data harian semua saham SEKALI, simpan jadi satu file bersama.

Dijalankan otomatis oleh GitHub Actions (Senin-Jumat sore). Hasilnya dibaca
oleh semua screener di web. Jika data kurang lengkap, file lama TIDAK ditimpa.

File yang dihasilkan (semua masuk ke branch `data`):
  market_data.csv.gz + market_data_meta.json : histori harian semua saham (12 bulan)
  ihsg_history.csv                           : histori harian IHSG (12 bulan)
  screener_history.json                      : hasil harian tiap screener (pengaturan bawaan), 40 hari terakhir
  sector_history.json                        : sektor mana yang "menyala" tiap hari (heatmap Sector Radar), 90 hari terakhir

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

from engines import recap  # noqa: E402
from engines import sector_radar  # noqa: E402
from engines.sector_map import load_sector_map  # noqa: E402
from engines.market_data import (  # noqa: E402
    DATA_FILE,
    IHSG_FILE,
    META_FILE,
    RECAP_FILE,
    SECTOR_HISTORY_FILE,
    build_ticker_map,
    calendar_alert,
    candle_is_final,
    data_url,
    expected_last_candle_date,
    http_get,
    now_wib,
    read_ticker_file,
)

BATCH_SIZE = 50
HISTORY_PERIOD = "1y"        # ~245 sesi: cukup untuk EMA200 dan analisis IHSG
IHSG_SYMBOL = "^JKSE"
MIN_IHSG_ROWS = 100
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
                tickers, period=HISTORY_PERIOD, interval="1d", auto_adjust=False,
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


def carry_forward(out, names):
    """Bawa file lama dari branch data kalau file baru belum dibuat, supaya tidak hilang saat branch ditulis ulang."""
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo:
        return
    for name in names:
        target = out / name
        if target.exists():
            continue
        try:
            target.write_bytes(http_get(data_url(repo, name), 30))
            print(f"File lama {name} dibawa ke hasil baru.")
        except Exception:  # noqa: BLE001
            pass


def fetch_ihsg(now):
    """Riwayat IHSG 12 bulan. Return DataFrame (Date + OHLCV) atau None kalau gagal (bukan kegagalan job)."""
    try:
        raw = yf.download(IHSG_SYMBOL, period=HISTORY_PERIOD, interval="1d", auto_adjust=False, progress=False)
        if raw is None or raw.empty:
            return None
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        d = raw[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Open", "High", "Low", "Close"]).copy()
        idx = pd.to_datetime(d.index)
        if getattr(idx, "tz", None) is not None:
            idx = idx.tz_localize(None)
        d.insert(0, "Date", idx.normalize())
        d = d.reset_index(drop=True)
        if not candle_is_final(now.date(), now):
            d = d[d["Date"].dt.date != now.date()]
        d["Volume"] = d["Volume"].fillna(0).astype("int64")
        d = d.sort_values("Date").drop_duplicates("Date", keep="last").reset_index(drop=True)
        return d if len(d) >= MIN_IHSG_ROWS else None
    except Exception as e:  # noqa: BLE001
        print(f"IHSG gagal diunduh: {e}")
        return None


def run_screeners(df):
    """Jalankan tiap screener dengan pengaturan bawaan pada data yang baru. Kegagalan satu screener tidak menghentikan job."""
    last = pd.Timestamp(df["Date"].max())
    fresh = df[df.groupby("Ticker")["Date"].transform("max") == last]   # saham tanpa candle terbaru tidak ikut (basi/suspensi)
    data_map = build_ticker_map(fresh)
    tickers = list(data_map)
    entries = {}
    try:
        from engines.screener_rsi_divergence import run_rsi_screener

        res, _ = run_rsi_screener(tickers, data=data_map)
        entries["rsi"] = {"hits": recap.hits_from_rsi(res)}
    except Exception as e:  # noqa: BLE001
        entries["rsi"] = {"error": f"{type(e).__name__}: {e}"[:120]}
    try:
        from engines.screener_stoch_psar import run_stoch_psar_screener

        gc, dc = run_stoch_psar_screener(tickers, data=data_map)
        entries["stoch_psar"] = {"hits": recap.hits_from_stoch(gc, dc)}
    except Exception as e:  # noqa: BLE001
        entries["stoch_psar"] = {"error": f"{type(e).__name__}: {e}"[:120]}
    try:
        from engines.screener_trend import run_trend_screener

        df_breakout, df_reset, _df_squeeze, _ = run_trend_screener(tickers, data=data_map)
        entries["breakout_surge"] = {"hits": recap.hits_from_breakout(df_breakout)}
        entries["trend_reset"] = {"hits": recap.hits_from_trend_reset(df_reset)}
    except Exception as e:  # noqa: BLE001
        msg = f"{type(e).__name__}: {e}"[:120]
        entries["breakout_surge"] = {"error": msg}
        entries["trend_reset"] = {"error": msg}
    try:
        from engines.screener_macd import run_macd_screener

        df_gc, df_dc, _ = run_macd_screener(tickers, data=data_map)
        entries["macd"] = {"hits": recap.hits_from_macd(df_gc, df_dc)}
    except Exception as e:  # noqa: BLE001
        entries["macd"] = {"error": f"{type(e).__name__}: {e}"[:120]}
    try:
        from engines.screener_mfi_reversal import run_mfi_screener

        res, _ = run_mfi_screener(tickers, data=data_map)
        entries["mfi"] = {"hits": recap.hits_from_mfi(res)}
    except Exception as e:  # noqa: BLE001
        entries["mfi"] = {"error": f"{type(e).__name__}: {e}"[:120]}
    try:
        from engines.screener_overnight import run_overnight_screener

        df_bsjp, df_bpjs, _ = run_overnight_screener(tickers, data=data_map)
        entries["overnight"] = {"hits": recap.hits_from_overnight(df_bsjp, df_bpjs)}
    except Exception as e:  # noqa: BLE001
        entries["overnight"] = {"error": f"{type(e).__name__}: {e}"[:120]}
    for k, v in entries.items():
        print(f"Screener {k}: " + (f"{len(v['hits'])} sinyal" if "hits" in v else f"GAGAL ({v['error']})"))
    return last.date().isoformat(), entries


def run_sector_radar(df):
    """Hitung sektor mana yang 'menyala' hari ini, utk histori heatmap. Kegagalan tidak menghentikan job."""
    last = pd.Timestamp(df["Date"].max())
    fresh = df[df.groupby("Ticker")["Date"].transform("max") == last]
    data_map = build_ticker_map(fresh)
    df_radar = sector_radar.compute_sector_radar(data_map, load_sector_map())
    summary = sector_radar.hot_summary(df_radar)
    print(f"Sector Radar: {sum(summary.values())}/{len(summary)} sektor menyala")
    return last.date().isoformat(), summary


def previous_sector_history():
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo:
        return {}
    try:
        return sector_radar.clean_history(json.loads(http_get(data_url(repo, SECTOR_HISTORY_FILE), 30).decode("utf-8")))
    except Exception:  # noqa: BLE001
        return {}


def previous_recap():
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo:
        return {}
    try:
        return recap.clean_history(json.loads(http_get(data_url(repo, RECAP_FILE), 30).decode("utf-8")))
    except Exception:  # noqa: BLE001
        return {}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default=str(ROOT / "data" / "daftar_saham.txt"))
    ap.add_argument("--out", default=str(ROOT / "out"))
    ap.add_argument("--force", action="store_true", help="unduh ulang walau data sudah terbaru")
    args = ap.parse_args(argv)

    now = now_wib()
    expected = expected_last_candle_date(now)
    print(f"Sekarang {now:%Y-%m-%d %H:%M} WIB, candle final terbaru yang diharapkan: {expected}")

    alert = calendar_alert(now)
    set_output("calendar_alert", f"{alert['year']}|{alert['level']}" if alert else "")
    if alert:
        print(f"PERINGATAN: kalender libur bursa {alert['year']} belum diisi ({alert['level']}).")

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

    # IHSG dan hasil screener harian: kegagalan di sini TIDAK menggagalkan data utama
    ihsg = fetch_ihsg(now)
    if ihsg is not None:
        ihsg_out = ihsg.copy()
        ihsg_out["Date"] = ihsg_out["Date"].dt.strftime("%Y-%m-%d")
        ihsg_out.to_csv(out / IHSG_FILE, index=False, float_format="%.4f")
        print(f"IHSG: {len(ihsg)} candle, terakhir {ihsg_out['Date'].iloc[-1]}")
    else:
        print("IHSG tidak diperbarui (file lama dipertahankan kalau ada).")
    recap_days = 0
    try:
        recap_date, entries = run_screeners(df)
        history = recap.add_day(previous_recap(), recap_date, entries, f"{now:%Y-%m-%d %H:%M}")
        (out / RECAP_FILE).write_text(json.dumps(history, separators=(",", ":")), encoding="utf-8")
        recap_days = len(history["days"])
    except Exception as e:  # noqa: BLE001
        print(f"Rekap screener gagal, riwayat lama dipertahankan: {type(e).__name__}: {e}")
    try:
        sector_date, sector_summary = run_sector_radar(df)
        sector_hist = sector_radar.add_day(previous_sector_history(), sector_date, sector_summary, f"{now:%Y-%m-%d %H:%M}")
        (out / SECTOR_HISTORY_FILE).write_text(json.dumps(sector_hist, separators=(",", ":")), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        print(f"Sector Radar histori gagal, riwayat lama dipertahankan: {type(e).__name__}: {e}")
    carry_forward(out, [IHSG_FILE, RECAP_FILE, SECTOR_HISTORY_FILE])

    df_out = df.copy()
    df_out["Date"] = df_out["Date"].dt.strftime("%Y-%m-%d")
    df_out.to_csv(out / DATA_FILE, index=False, compression="gzip", float_format="%.4f")
    got = set(df["Ticker"])
    meta = {
        "version": 2,
        "history_period": HISTORY_PERIOD,
        "recap_days": recap_days,
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
