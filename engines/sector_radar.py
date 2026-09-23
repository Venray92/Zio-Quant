"""Sector Radar: sektor mana yang lagi "menyala" hari ini (dana ramai masuk), berdasarkan data
harga & volume saham anggotanya -- BUKAN prediksi, murni deskriptif (mirip Arah Pasar di Home).

Konsep: dibandingkan ke kebiasaan SEKTOR ITU SENDIRI (bukan angka mutlak), supaya sektor kecil yang
biasanya sepi tidak dibandingkan mentah dengan sektor besar yang biasanya ramai. Perlu bertahan
beberapa hari (streak) sebelum dianggap "menyala", bukan cuma satu hari yang bisa berisik.
"""
import pandas as pd

from engines.market_view import atr_pct
from engines.sector_map import load_sector_map
from engines.trade_planner import HIGH_VOL_ATR_PCT

# ---------------------------------------------------------------- PARAMETER
MIN_PRICE = 50
MIN_VALUE_RP = 1_000_000_000      # likuiditas per saham: rata-rata nilai transaksi 20 hari
MIN_MEMBERS = 3                   # sektor dgn saham likuid < ini tidak dianalisis (terlalu sedikit sampel)
LOOKBACK = 60                     # jendela "kebiasaan sektor sendiri"
RVOL_HIGH = 1.5                   # volume relatif dianggap tinggi
HOT_VALUE_PERCENTILE = 80         # nilai transaksi hari itu masuk 20% teratas kebiasaan 60 hari sendiri
HOT_PCT_UP = 55.0                 # mayoritas saham naik
MAX_CONCENTRATION_PCT = 70.0      # kalau 1 saham dominasi > ini, sektor dianggap tidak "kompak"


def _prep(df):
    if df is None or len(df) < 25:
        return None
    d = df.copy()
    if "Date" not in d.columns:
        d = d.reset_index().rename(columns={d.reset_index().columns[0]: "Date"})
    d["Date"] = pd.to_datetime(d["Date"])
    need = {"Date", "Close", "Volume"}
    if not need.issubset(d.columns):
        return None
    d["Close"] = pd.to_numeric(d["Close"], errors="coerce")
    d["Volume"] = pd.to_numeric(d["Volume"], errors="coerce")
    d = d.dropna(subset=["Close"]).sort_values("Date").drop_duplicates("Date", keep="last")
    d["Volume"] = d["Volume"].fillna(0.0)
    return d.set_index("Date")[["Close", "Volume"]] if len(d) else None


def _qualifies(d):
    avg_value = float((d["Close"] * d["Volume"]).rolling(20).mean().iloc[-1])
    return float(d["Close"].iloc[-1]) > MIN_PRICE and avg_value >= MIN_VALUE_RP


def group_by_sector(data_map, sector_map=None):
    """{sektor: [ticker, ...]} dari data_map yang punya pemetaan sektor."""
    sm = sector_map if sector_map is not None else load_sector_map()
    out = {}
    for t in data_map:
        code = str(t).upper().replace(".JK", "")
        info = sm.get(code)
        if info:
            out.setdefault(info["sector"], []).append(t)
    return out


def _sector_matrices(tickers, data_map, lookback):
    """Kembalikan (close_matrix, volume_matrix, rvol_matrix) index=Date, kolom=ticker yang lolos likuiditas."""
    prepped = {}
    for t in tickers:
        d = _prep(data_map.get(t))
        if d is None or not _qualifies(d):
            continue
        prepped[t] = d
    if len(prepped) < MIN_MEMBERS:
        return None, None, None, []
    close = pd.concat({t: d["Close"] for t, d in prepped.items()}, axis=1).sort_index()
    vol = pd.concat({t: d["Volume"] for t, d in prepped.items()}, axis=1).sort_index()
    vol_ma20 = vol.rolling(20, min_periods=1).mean().shift(1)
    rvol = vol / vol_ma20.replace(0, pd.NA)
    keep = close.tail(lookback + 1).index
    return close.loc[keep], vol.loc[keep], rvol.loc[keep], sorted(prepped)


def compute_sector_radar(data_map, sector_map=None, lookback=LOOKBACK, min_members=MIN_MEMBERS):
    """Ringkasan tiap sektor pada candle terakhir yang tersedia. Return DataFrame (bisa kosong)."""
    groups = group_by_sector(data_map, sector_map)
    rows = []
    for sector, tickers in groups.items():
        close, vol, rvol, members = _sector_matrices(tickers, data_map, lookback)
        if close is None or len(members) < min_members or len(close) < 2:
            continue

        ret = close.pct_change() * 100
        n_traded = ret.notna().sum(axis=1)
        pct_up_series = (ret > 0).sum(axis=1) / n_traded.replace(0, pd.NA) * 100
        value = (close * vol).where(close.notna() & vol.notna())
        value_series = value.sum(axis=1, min_count=1).fillna(0.0)
        high_vol_series = (rvol >= RVOL_HIGH).sum(axis=1) / n_traded.replace(0, pd.NA) * 100

        last = close.index[-1]
        pct_up = float(pct_up_series.loc[last]) if pd.notna(pct_up_series.loc[last]) else 0.0
        pct_high_vol = float(high_vol_series.loc[last]) if pd.notna(high_vol_series.loc[last]) else 0.0
        median_return = float(ret.loc[last].median()) if ret.loc[last].notna().any() else 0.0
        value_today = float(value_series.loc[last])

        hist = value_series.iloc[:-1] if len(value_series) > 1 else value_series
        value_threshold = float(hist.quantile(HOT_VALUE_PERCENTILE / 100)) if len(hist) else value_today
        value_percentile = float((hist <= value_today).mean() * 100) if len(hist) else 100.0

        val_today_row = value.loc[last]
        top_ticker, top_val = (val_today_row.idxmax(), float(val_today_row.max())) if val_today_row.notna().any() else (None, 0.0)
        concentration_pct = (top_val / value_today * 100) if value_today > 0 else 0.0

        hot_day = (value_series >= value_threshold) & (pct_up_series >= HOT_PCT_UP)
        streak = 0
        for v in hot_day.iloc[::-1]:
            if not bool(v) if pd.notna(v) else True:
                break
            streak += 1

        is_hot = bool(hot_day.loc[last]) and concentration_pct <= MAX_CONCENTRATION_PCT
        rows.append({
            "Sector": sector, "N Members": len(members),
            "Pct Up": round(pct_up, 1), "Pct High Vol": round(pct_high_vol, 1), "Median Return (%)": round(median_return, 2),
            "Value Today (Rp)": value_today, "Value Percentile": round(value_percentile, 0),
            "Top Ticker": top_ticker, "Concentration (%)": round(concentration_pct, 1),
            "Streak Days": int(streak), "Is Hot": is_hot, "Members": members,
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["Is Hot", "Value Percentile", "Streak Days"], ascending=[False, False, False], kind="stable").reset_index(drop=True)
    return df


def _stock_volatility(data_map, ticker):
    """ATR% candle terakhir + status 'saham liar' (>HIGH_VOL_ATR_PCT). Satu definisi dgn Trade Planner,
    RSI Reversal, dan Trend Scanner. Catatan saja, tidak memotong RVOL/urutan apa pun."""
    df = data_map.get(ticker)
    if df is None or len(df) < 15 or not {"High", "Low", "Close"}.issubset(df.columns):
        return None, False
    v = float(atr_pct(df.dropna(subset=["High", "Low", "Close"])).iloc[-1])
    return round(v, 1), bool(v > HIGH_VOL_ATR_PCT)


# ---------------------------------------------------------------- histori harian (heatmap kalender)
SECTOR_KEEP_DAYS = 90  # heatmap butuh histori lebih panjang dari rekap sinyal (recap.py pakai 40)


def hot_summary(df):
    """Ringkas hasil compute_sector_radar jadi {sektor: True/False}, siap disimpan harian."""
    if df is None or df.empty:
        return {}
    return {str(row["Sector"]): bool(row["Is Hot"]) for _, row in df.iterrows()}


def add_day(history, date, summary, updated_at_wib="", keep_days=SECTOR_KEEP_DAYS):
    """Tambah/timpa satu hari, buang yang lebih lama dari keep_days. Pola sama seperti engines.recap.add_day."""
    days = dict((history or {}).get("days") or {})
    days[str(date)[:10]] = {str(k): bool(v) for k, v in (summary or {}).items()}
    kept = dict(sorted(days.items())[-keep_days:])
    return {"version": 1, "updated_at_wib": str(updated_at_wib), "days": kept}


def clean_history(raw):
    """Bersihkan riwayat dari sumber luar (file JSON) sebelum dipakai -- jangan percaya isinya mentah-mentah."""
    raw = raw if isinstance(raw, dict) else {}
    days = raw.get("days")
    out = {}
    if isinstance(days, dict):
        for d, entries in days.items():
            if not isinstance(entries, dict) or pd.isna(pd.to_datetime(str(d), errors="coerce")):
                continue
            out[str(d)[:10]] = {str(k): bool(v) for k, v in entries.items() if isinstance(k, str)}
    return {"version": 1, "updated_at_wib": str(raw.get("updated_at_wib", "")), "days": dict(sorted(out.items()))}


def heatmap_data(history, days=SECTOR_KEEP_DAYS):
    """(dates, sectors, matrix) siap dipakai UI. matrix[sector][date] -> True/False/None (None = tidak ada data)."""
    all_days = (history or {}).get("days") or {}
    dates = sorted(all_days)[-days:]
    sectors = sorted({s for d in dates for s in all_days[d]})
    matrix = {s: {d: all_days[d].get(s) for d in dates} for s in sectors}
    return dates, sectors, matrix


def sector_detail(sector, data_map, sector_map=None, lookback=LOOKBACK):
    """Baris per-saham utk drill-down satu sektor, diurutkan volume relatif tertinggi dulu."""
    sm = sector_map if sector_map is not None else load_sector_map()
    tickers = [t for t in data_map if (sm.get(str(t).upper().replace(".JK", "")) or {}).get("sector") == sector]
    close, vol, rvol, members = _sector_matrices(tickers, data_map, lookback)
    if close is None:
        return pd.DataFrame()
    last = close.index[-1]
    rows = []
    for t in members:
        c, c_prev = close[t].loc[last], close[t].iloc[-2] if len(close) > 1 else None
        rv = rvol[t].loc[last]
        atr_now, is_volatile = _stock_volatility(data_map, t)
        rows.append({
            "Ticker": t, "Saham": str(t).replace(".JK", ""),
            "Close": float(c), "Change (%)": round(float((c / c_prev - 1) * 100), 2) if c_prev and c_prev > 0 else 0.0,
            "RVOL": round(float(rv), 2) if pd.notna(rv) else None,
            "ATR % Now": atr_now, "Volatile Tinggi": is_volatile,
        })
    out = pd.DataFrame(rows)
    return out.sort_values("RVOL", ascending=False, na_position="last", kind="stable").reset_index(drop=True) if not out.empty else out
