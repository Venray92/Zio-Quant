import os
import pandas as pd
import pandas_ta as ta
import yfinance as yf


def load_stock_list(filepath="daftar_saham.txt"):
    """Membaca daftar saham dari file txt"""
    if not os.path.exists(filepath):
        return ["BBRI.JK", "BBCA.JK", "BMRI.JK", "TLKM.JK", "ASII.JK"]

    with open(filepath, "r") as f:
        stocks = [line.strip().upper() for line in f if line.strip()]

    formatted_stocks = []
    for s in stocks:
        if not s.endswith(".JK") and "." not in s:
            s += ".JK"
        formatted_stocks.append(s)
    return formatted_stocks


def extract_swings(df_in, series, left=2, right=2):
    """Fungsi Swing Point dari kode baru"""
    swings = []
    n = len(series)

    for i in range(left, n):
        current_val = series.iloc[i]
        left_vals = series.iloc[i - left : i]
        remaining_right = n - 1 - i

        if remaining_right >= right:
            right_vals = series.iloc[i + 1 : i + 1 + right]
            if all(current_val >= val for val in left_vals) and all(
                current_val > val for val in right_vals
            ):
                swings.append({
                    "Tanggal": series.index[i],
                    "Nilai": current_val,
                    "Harga Close": df_in["Close"].iloc[i],
                    "Type": "SWING HIGH",
                })
            elif all(current_val <= val for val in left_vals) and all(
                current_val < val for val in right_vals
            ):
                swings.append({
                    "Tanggal": series.index[i],
                    "Nilai": current_val,
                    "Harga Close": df_in["Close"].iloc[i],
                    "Type": "SWING LOW",
                })
    return pd.DataFrame(swings)


def analyze_single_ticker_new(ticker):
    """Menggunakan logika deteksi Divergence RSI 10 persis dari kode baru"""
    try:
        df = yf.download(
            ticker, period="1y", interval="1d", auto_adjust=False, progress=False
        )
        if df.empty or len(df) < 30:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Hitung RSI 10 & EMA 10 sesuai kode baru
        df["RSI_10"] = df.ta.rsi(close=df["Close"], length=10)
        df["RSI_EMA10"] = df.ta.ema(close=df["RSI_10"], length=10)

        latest_close = df["Close"].iloc[-1]
        latest_rsi = df["RSI_10"].iloc[-1]
        latest_ema = df["RSI_EMA10"].iloc[-1]

        is_gc = latest_rsi > latest_ema
        is_dc = latest_rsi < latest_ema

        max_date = df.index.max()
        cutoff_scan = max_date - pd.Timedelta(days=30)
        cutoff_fresh = max_date - pd.Timedelta(days=4)

        min_rsi_diff = 3.0
        min_price_diff_pct = 0.015

        # 1. DETEKSI BULLISH DIVERGENCE
        p_swings_low = extract_swings(df, df["Low"])
        rsi_swings_low = extract_swings(df, df["RSI_10"])

        if not p_swings_low.empty and not rsi_swings_low.empty:
            p_lows = (
                p_swings_low[p_swings_low["Type"] == "SWING LOW"]
                .sort_values("Tanggal", ascending=False)
                .reset_index(drop=True)
            )
            r_lows = (
                rsi_swings_low[rsi_swings_low["Type"] == "SWING LOW"]
                .sort_values("Tanggal", ascending=False)
                .reset_index(drop=True)
            )

            for i in range(len(p_lows) - 1):
                right_p = p_lows.iloc[i]
                if (
                    right_p["Tanggal"] < cutoff_scan
                    or right_p["Tanggal"] < cutoff_fresh
                ):
                    continue

                for j in range(i + 1, len(p_lows)):
                    left_p = p_lows.iloc[j]
                    days_gap = (right_p["Tanggal"] - left_p["Tanggal"]).days
                    if not (4 <= days_gap <= 60):
                        continue

                    rsi_right = r_lows[
                        (
                            r_lows["Tanggal"]
                            >= right_p["Tanggal"] - pd.Timedelta(days=5)
                        )
                        & (
                            r_lows["Tanggal"]
                            <= right_p["Tanggal"] + pd.Timedelta(days=5)
                        )
                    ]
                    rsi_left = r_lows[
                        (
                            r_lows["Tanggal"]
                            >= left_p["Tanggal"] - pd.Timedelta(days=5)
                        )
                        & (
                            r_lows["Tanggal"]
                            <= left_p["Tanggal"] + pd.Timedelta(days=5)
                        )
                    ]

                    if not rsi_right.empty and not rsi_left.empty:
                        val_r = rsi_right.iloc[0]["Nilai"]
                        val_l = rsi_left.iloc[0]["Nilai"]
                        price_diff = (
                            abs(right_p["Nilai"] - left_p["Nilai"])
                            / left_p["Nilai"]
                        )
                        rsi_diff = abs(val_r - val_l)
                        status_bull = (
                            "Valid (GC)" if is_gc else "Potensial (Wait GC)"
                        )

                        rsi_in_between = df.loc[
                            left_p["Tanggal"] : right_p["Tanggal"], "RSI_10"
                        ]

                        # Regular Bullish
                        if (
                            (right_p["Nilai"] < left_p["Nilai"])
                            and (val_r > val_l)
                            and (val_r < 30)
                            and (rsi_in_between <= 30).all()
                            and price_diff >= min_price_diff_pct
                            and rsi_diff >= min_rsi_diff
                        ):
                            return {
                                "Ticker": ticker.replace(".JK", ""),
                                "Harga Close": f"Rp {latest_close:,.0f}",
                                "RSI 10": round(latest_rsi, 2),
                                "Signal": f"Regular Bullish ({status_bull})",
                                "Category": "BULLISH",
                            }
                        # Hidden Bullish
                        elif (
                            (right_p["Nilai"] >= left_p["Nilai"])
                            and (val_r < val_l)
                            and (35 <= val_r <= 65)
                            and price_diff >= min_price_diff_pct
                            and rsi_diff >= min_rsi_diff
                        ):
                            return {
                                "Ticker": ticker.replace(".JK", ""),
                                "Harga Close": f"Rp {latest_close:,.0f}",
                                "RSI 10": round(latest_rsi, 2),
                                "Signal": f"Hidden Bullish ({status_bull})",
                                "Category": "BULLISH",
                            }

        # 2. DETEKSI BEARISH DIVERGENCE
        p_swings_high = extract_swings(df, df["High"])
        rsi_swings_high = extract_swings(df, df["RSI_10"])

        if not p_swings_high.empty and not rsi_swings_high.empty:
            p_highs = (
                p_swings_high[p_swings_high["Type"] == "SWING HIGH"]
                .sort_values("Tanggal", ascending=False)
                .reset_index(drop=True)
            )
            r_highs = (
                rsi_swings_high[rsi_swings_high["Type"] == "SWING HIGH"]
                .sort_values("Tanggal", ascending=False)
                .reset_index(drop=True)
            )

            for i in range(len(p_highs) - 1):
                right_p = p_highs.iloc[i]
                if (
                    right_p["Tanggal"] < cutoff_scan
                    or right_p["Tanggal"] < cutoff_fresh
                ):
                    continue

                for j in range(i + 1, len(p_highs)):
                    left_p = p_highs.iloc[j]
                    days_gap = (right_p["Tanggal"] - left_p["Tanggal"]).days
                    if not (4 <= days_gap <= 60):
                        continue

                    rsi_right = r_highs[
                        (
                            r_highs["Tanggal"]
                            >= right_p["Tanggal"] - pd.Timedelta(days=5)
                        )
                        & (
                            r_highs["Tanggal"]
                            <= right_p["Tanggal"] + pd.Timedelta(days=5)
                        )
                    ]
                    rsi_left = r_highs[
                        (
                            r_highs["Tanggal"]
                            >= left_p["Tanggal"] - pd.Timedelta(days=5)
                        )
                        & (
                            r_highs["Tanggal"]
                            <= left_p["Tanggal"] + pd.Timedelta(days=5)
                        )
                    ]

                    if not rsi_right.empty and not rsi_left.empty:
                        val_r = rsi_right.iloc[0]["Nilai"]
                        val_l = rsi_left.iloc[0]["Nilai"]
                        price_diff = (
                            abs(right_p["Nilai"] - left_p["Nilai"])
                            / left_p["Nilai"]
                        )
                        rsi_diff = abs(val_r - val_l)
                        status_bear = (
                            "Valid (DC)" if is_dc else "Potensial (Wait DC)"
                        )

                        rsi_in_between = df.loc[
                            left_p["Tanggal"] : right_p["Tanggal"], "RSI_10"
                        ]

                        # Regular Bearish
                        if (
                            (right_p["Nilai"] > left_p["Nilai"])
                            and (val_r < val_l)
                            and (val_r > 80)
                            and (rsi_in_between >= 80).all()
                            and price_diff >= min_price_diff_pct
                            and rsi_diff >= min_rsi_diff
                        ):
                            return {
                                "Ticker": ticker.replace(".JK", ""),
                                "Harga Close": f"Rp {latest_close:,.0f}",
                                "RSI 10": round(latest_rsi, 2),
                                "Signal": f"Regular Bearish ({status_bear})",
                                "Category": "BEARISH",
                            }
                        # Hidden Bearish
                        elif (
                            (right_p["Nilai"] <= left_p["Nilai"])
                            and (val_r > val_l)
                            and (45 <= val_r <= 75)
                            and price_diff >= min_price_diff_pct
                            and rsi_diff >= min_rsi_diff
                        ):
                            return {
                                "Ticker": ticker.replace(".JK", ""),
                                "Harga Close": f"Rp {latest_close:,.0f}",
                                "RSI 10": round(latest_rsi, 2),
                                "Signal": f"Hidden Bearish ({status_bear})",
                                "Category": "BEARISH",
                            }

        # Backup Signal: Cross di Extreme Area
        if is_gc and latest_rsi < 40:
            return {
                "Ticker": ticker.replace(".JK", ""),
                "Harga Close": f"Rp {latest_close:,.0f}",
                "RSI 10": round(latest_rsi, 2),
                "Signal": "RSI Golden Cross (< 40)",
                "Category": "BULLISH",
            }
        elif is_dc and latest_rsi > 60:
            return {
                "Ticker": ticker.replace(".JK", ""),
                "Harga Close": f"Rp {latest_close:,.0f}",
                "RSI 10": round(latest_rsi, 2),
                "Signal": "RSI Dead Cross (> 60)",
                "Category": "BEARISH",
            }

        return None

    except Exception:
        return None


def run_full_rsi_scan(filepath="daftar_saham.txt"):
    """Fungsi pembacaan massal"""
    stocks = load_stock_list(filepath)
    bullish_list = []
    bearish_list = []

    for s in stocks:
        res = analyze_single_ticker_new(s)
        if res:
            if res["Category"] == "BULLISH":
                bullish_list.append(res)
            elif res["Category"] == "BEARISH":
                bearish_list.append(res)

    df_bullish = pd.DataFrame(bullish_list)
    df_bearish = pd.DataFrame(bearish_list)

    if not df_bullish.empty:
        df_bullish = df_bullish.drop(columns=["Category"])
    if not df_bearish.empty:
        df_bearish = df_bearish.drop(columns=["Category"])

    return df_bullish, df_bearish
