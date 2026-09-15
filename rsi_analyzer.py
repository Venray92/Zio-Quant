import os
import pandas as pd
import pandas_ta as ta
import yfinance as yf


def load_stock_list(filepath="daftar_saham.txt"):
    """Membaca daftar saham dari file txt"""
    if not os.path.exists(filepath):
        # Jika file tidak ada, pakai contoh fallback
        return ["BBRI.JK", "BBCA.JK", "BMRI.JK", "TLKM.JK", "ASII.JK"]

    with open(filepath, "r") as f:
        stocks = [line.strip().upper() for line in f if line.strip()]

    # Format ticker agar sesuai dengan yfinance (.JK)
    formatted_stocks = []
    for s in stocks:
        if not s.endswith(".JK") and "." not in s:
            s += ".JK"
        formatted_stocks.append(s)
    return formatted_stocks


def extract_swings(df_in, series, left=2, right=2):
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


def analyze_single_ticker(ticker):
    """Menganalisis 1 saham untuk menentukan status Bullish / Bearish / Neutral"""
    try:
        df = yf.download(
            ticker, period="6mo", interval="1d", auto_adjust=False, progress=False
        )
        if df.empty or len(df) < 30:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Hitung RSI 10 & EMA 10
        df["RSI_10"] = df.ta.rsi(close=df["Close"], length=10)
        df["RSI_EMA10"] = df.ta.ema(close=df["RSI_10"], length=10)

        latest_close = df["Close"].iloc[-1]
        latest_rsi = df["RSI_10"].iloc[-1]
        latest_ema = df["RSI_EMA10"].iloc[-1]

        # Logika Sederhana Bullish vs Bearish Divergence / Signal
        is_gc = latest_rsi > latest_ema
        is_dc = latest_rsi < latest_ema

        # Cek Swing Low (Potensi Bullish)
        swings_low_price = extract_swings(df, df["Low"])
        swings_low_rsi = extract_swings(df, df["RSI_10"])

        status = "NEUTRAL"
        signal_desc = "-"

        if not swings_low_price.empty and not swings_low_rsi.empty:
            p_lows = swings_low_price[
                swings_low_price["Type"] == "SWING LOW"
            ].tail(2)
            r_lows = swings_low_rsi[swings_low_rsi["Type"] == "SWING LOW"].tail(
                2
            )

            if len(p_lows) == 2 and len(r_lows) == 2:
                # Regular Bullish Divergence
                if (
                    p_lows.iloc[1]["Nilai"] < p_lows.iloc[0]["Nilai"]
                    and r_lows.iloc[1]["Nilai"] > r_lows.iloc[0]["Nilai"]
                ):
                    status = "BULLISH"
                    signal_desc = "Bullish Divergence"
                # Hidden Bullish Divergence
                elif (
                    p_lows.iloc[1]["Nilai"] > p_lows.iloc[0]["Nilai"]
                    and r_lows.iloc[1]["Nilai"] < r_lows.iloc[0]["Nilai"]
                ):
                    status = "BULLISH"
                    signal_desc = "Hidden Bullish Divergence"

        # Cek Swing High (Potensi Bearish) jika belum set Bullish
        if status == "NEUTRAL":
            swings_high_price = extract_swings(df, df["High"])
            swings_high_rsi = extract_swings(df, df["RSI_10"])

            if not swings_high_price.empty and not swings_high_rsi.empty:
                p_highs = swings_high_price[
                    swings_high_price["Type"] == "SWING HIGH"
                ].tail(2)
                r_highs = swings_high_rsi[
                    swings_high_rsi["Type"] == "SWING HIGH"
                ].tail(2)

                if len(p_highs) == 2 and len(r_highs) == 2:
                    # Regular Bearish Divergence
                    if (
                        p_highs.iloc[1]["Nilai"] > p_highs.iloc[0]["Nilai"]
                        and r_highs.iloc[1]["Nilai"] < r_highs.iloc[0]["Nilai"]
                    ):
                        status = "BEARISH"
                        signal_desc = "Bearish Divergence"

        # Cross Signal Tambahan jika belum terdeteksi Divergence
        if status == "NEUTRAL":
            if is_gc and latest_rsi < 40:
                status = "BULLISH"
                signal_desc = "RSI Golden Cross (Oversold Area)"
            elif is_dc and latest_rsi > 60:
                status = "BEARISH"
                signal_desc = "RSI Dead Cross (Overbought Area)"

        if status != "NEUTRAL":
            return {
                "Ticker": ticker.replace(".JK", ""),
                "Harga Close": f"Rp {latest_close:,.0f}",
                "RSI 10": round(latest_rsi, 2),
                "Signal": signal_desc,
                "Category": status,
            }
        return None

    except Exception:
        return None


def run_full_scan(filepath="daftar_saham.txt"):
    """Fungsi utama untuk memindai seluruh file daftar saham"""
    stocks = load_stock_list(filepath)
    bullish_list = []
    bearish_list = []

    for s in stocks:
        res = analyze_single_ticker(s)
        if res:
            if res["Category"] == "BULLISH":
                bullish_list.append(res)
            elif res["Category"] == "BEARISH":
                bearish_list.append(res)

    df_bullish = pd.DataFrame(bullish_list)
    df_bearish = pd.DataFrame(bearish_list)

    # Rapikan kolom untuk output
    if not df_bullish.empty:
        df_bullish = df_bullish.drop(columns=["Category"])
    if not df_bearish.empty:
        df_bearish = df_bearish.drop(columns=["Category"])

    return df_bullish, df_bearish
