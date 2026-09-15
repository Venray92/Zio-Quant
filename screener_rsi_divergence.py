import os
import pandas as pd
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


def calculate_rsi_pure(series, length=10):
    """Menghitung RSI secara manual menggunakan Pandas (Tanpa pandas-ta)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_ema_pure(series, length=10):
    """Menghitung EMA secara manual menggunakan Pandas (Tanpa pandas-ta)"""
    return series.ewm(span=length, adjust=False).mean()


def extract_swings(df_in, series, left=2, right=2):
    """Mencari Swing High dan Swing Low"""
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


def detect_all_divergences(df_data, is_gc, is_dc):
    """Mendeteksi 4 Pola Divergence secara presisi"""
    max_date = df_data.index.max()
    cutoff_scan = max_date - pd.Timedelta(days=30)
    cutoff_fresh = max_date - pd.Timedelta(days=4)

    min_rsi_diff = 3.0
    min_price_diff_pct = 0.015
    div_results = []

    # 1. BULLISH DIVERGENCE (Swing Low)
    p_swings_low = extract_swings(df_data, df_data["Low"])
    rsi_swings_low = extract_swings(df_data, df_data["RSI_10"])

    if not p_swings_low.empty and not rsi_swings_low.empty:
        p_lows = (
            p_swings_low[p_swings_low["Type"] == "SWING LOW"]
            .sort_values("Tanggal", ascending=False)
            .reset_index(drop=True)
        )
        rsi_lows = (
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

                r_match_right = rsi_lows[
                    (
                        rsi_lows["Tanggal"]
                        >= right_p["Tanggal"] - pd.Timedelta(days=5)
                    )
                    & (
                        rsi_lows["Tanggal"]
                        <= right_p["Tanggal"] + pd.Timedelta(days=5)
                    )
                ]
                r_match_left = rsi_lows[
                    (
                        rsi_lows["Tanggal"]
                        >= left_p["Tanggal"] - pd.Timedelta(days=5)
                    )
                    & (
                        rsi_lows["Tanggal"]
                        <= left_p["Tanggal"] + pd.Timedelta(days=5)
                    )
                ]

                if not r_match_right.empty and not r_match_left.empty:
                    val_rsi_right = r_match_right.iloc[0]["Nilai"]
                    val_rsi_left = r_match_left.iloc[0]["Nilai"]

                    price_diff_pct = (
                        abs(right_p["Nilai"] - left_p["Nilai"]) / left_p["Nilai"]
                    )
                    rsi_diff = abs(val_rsi_right - val_rsi_left)
                    status_bull = "Valid (GC)" if is_gc else "Potensial (Wait GC)"

                    rsi_in_between = df_data.loc[
                        left_p["Tanggal"] : right_p["Tanggal"], "RSI_10"
                    ]

                    # Regular Bullish Divergence
                    if (
                        (right_p["Nilai"] < left_p["Nilai"])
                        and (val_rsi_right > val_rsi_left)
                        and (val_rsi_right < 30)
                        and (rsi_in_between <= 30).all()
                        and price_diff_pct >= min_price_diff_pct
                        and rsi_diff >= min_rsi_diff
                    ):
                        div_results.append({
                            "Pattern": f"Regular Bullish ({status_bull})",
                            "Score": 85 if is_gc else 70,
                        })
                        break

                    # Hidden Bullish Divergence
                    elif (
                        (right_p["Nilai"] >= left_p["Nilai"])
                        and (val_rsi_right < val_rsi_left)
                        and (35 <= val_rsi_right <= 65)
                        and price_diff_pct >= min_price_diff_pct
                        and rsi_diff >= min_rsi_diff
                    ):
                        div_results.append({
                            "Pattern": f"Hidden Bullish ({status_bull})",
                            "Score": 80 if is_gc else 65,
                        })
                        break

    # 2. BEARISH DIVERGENCE (Swing High)
    p_swings_high = extract_swings(df_data, df_data["High"])
    rsi_swings_high = extract_swings(df_data, df_data["RSI_10"])

    if not p_swings_high.empty and not rsi_swings_high.empty:
        p_highs = (
            p_swings_high[p_swings_high["Type"] == "SWING HIGH"]
            .sort_values("Tanggal", ascending=False)
            .reset_index(drop=True)
        )
        rsi_highs = (
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

                r_match_right = rsi_highs[
                    (
                        rsi_highs["Tanggal"]
                        >= right_p["Tanggal"] - pd.Timedelta(days=5)
                    )
                    & (
                        rsi_highs["Tanggal"]
                        <= right_p["Tanggal"] + pd.Timedelta(days=5)
                    )
                ]
                r_match_left = rsi_highs[
                    (
                        rsi_highs["Tanggal"]
                        >= left_p["Tanggal"] - pd.Timedelta(days=5)
                    )
                    & (
                        rsi_highs["Tanggal"]
                        <= left_p["Tanggal"] + pd.Timedelta(days=5)
                    )
                ]

                if not r_match_right.empty and not r_match_left.empty:
                    val_rsi_right = r_match_right.iloc[0]["Nilai"]
                    val_rsi_left = r_match_left.iloc[0]["Nilai"]

                    price_diff_pct = (
                        abs(right_p["Nilai"] - left_p["Nilai"]) / left_p["Nilai"]
                    )
                    rsi_diff = abs(val_rsi_right - val_rsi_left)
                    status_bear = "Valid (DC)" if is_dc else "Potensial (Wait DC)"

                    rsi_in_between = df_data.loc[
                        left_p["Tanggal"] : right_p["Tanggal"], "RSI_10"
                    ]

                    # Regular Bearish Divergence
                    if (
                        (right_p["Nilai"] > left_p["Nilai"])
                        and (val_rsi_right < val_rsi_left)
                        and (val_rsi_right > 80)
                        and (rsi_in_between >= 80).all()
                        and price_diff_pct >= min_price_diff_pct
                        and rsi_diff >= min_rsi_diff
                    ):
                        div_results.append({
                            "Pattern": f"Regular Bearish ({status_bear})",
                            "Score": 85 if is_dc else 70,
                        })
                        break

                    # Hidden Bearish Divergence
                    elif (
                        (right_p["Nilai"] <= left_p["Nilai"])
                        and (val_rsi_right > val_rsi_left)
                        and (45 <= val_rsi_right <= 75)
                        and price_diff_pct >= min_price_diff_pct
                        and rsi_diff >= min_rsi_diff
                    ):
                        div_results.append({
                            "Pattern": f"Hidden Bearish ({status_bear})",
                            "Score": 80 if is_dc else 65,
                        })
                        break

    return pd.DataFrame(div_results)


# FUNGSI UTAMA YANG DIPANGGIL OLEH APP.PY
def detect_rsi_patterns_and_score(ticker):
    """Diadaptasi khusus untuk app.py"""
    try:
        df = yf.download(
            ticker, period="1y", interval="1d", auto_adjust=False, progress=False
        )
        if df.empty or len(df) < 30:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Hitung RSI 10 & EMA 10 secara manual (Murni Pandas)
        df["RSI_10"] = calculate_rsi_pure(df["Close"], length=10)
        df["RSI_EMA10"] = calculate_ema_pure(df["RSI_10"], length=10)

        latest_close = df["Close"].iloc[-1]
        latest_rsi = df["RSI_10"].iloc[-1]
        latest_ema = df["RSI_EMA10"].iloc[-1]

        is_gc = latest_rsi > latest_ema
        is_dc = latest_rsi < latest_ema

        # Scan 4 Divergence Pattern
        df_div = detect_all_divergences(df, is_gc, is_dc)

        if not df_div.empty:
            res_pattern = df_div.iloc[0]["Pattern"]
            res_score = df_div.iloc[0]["Score"]
            return {
                "Ticker": ticker.replace(".JK", ""),
                "Harga Close": f"Rp {latest_close:,.0f}",
                "RSI 10": round(latest_rsi, 2),
                "Pattern": res_pattern,
                "TOTAL SCORE": res_score,
            }

        # Sinyal Tambahan (Non-Divergence)
        if is_gc and latest_rsi < 40:
            return {
                "Ticker": ticker.replace(".JK", ""),
                "Harga Close": f"Rp {latest_close:,.0f}",
                "RSI 10": round(latest_rsi, 2),
                "Pattern": "Bullish RSI Golden Cross (<40)",
                "TOTAL SCORE": 60,
            }
        elif is_dc and latest_rsi > 60:
            return {
                "Ticker": ticker.replace(".JK", ""),
                "Harga Close": f"Rp {latest_close:,.0f}",
                "RSI 10": round(latest_rsi, 2),
                "Pattern": "Bearish RSI Dead Cross (>60)",
                "TOTAL SCORE": 60,
            }

        return None

    except Exception:
        return None
