import warnings
import concurrent.futures
import pandas as pd
import ta
import yfinance as yf

# Mengabaikan warning bawaan dari library
warnings.filterwarnings("ignore")


def _process_single_ticker(ticker):
    """Fungsi pembantu untuk memproses 1 saham"""
    try:
        df = yf.download(ticker, period="90d", interval="1d", progress=False)
        if df.empty or len(df) < 30:
            return None, None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        c0 = df["Close"].iloc[-1]
        v0 = df["Volume"].iloc[-1]
        l0 = df["Low"].iloc[-1]
        h0 = df["High"].iloc[-1]
        val0 = c0 * v0

        # Filter likuiditas dasar
        if c0 <= 50 or val0 < 1_000_000_000:
            return None, None

        df["vol_ma20"] = df["Volume"].rolling(window=20).mean()

        low_min10 = df["Low"].rolling(window=10).min()
        high_max10 = df["High"].rolling(window=10).max()
        fast_k = 100 * ((df["Close"] - low_min10) / (high_max10 - low_min10))

        df["stoch_k"] = fast_k.rolling(window=5).mean()
        df["stoch_d"] = df["stoch_k"].rolling(window=5).mean()

        try:
            psar_ind = ta.trend.PSARIndicator(
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                step=0.02,
                max_step=0.2,
            )
            df["psar"] = psar_ind.psar()
        except Exception:
            df["psar"] = df["Close"]

        k0, d0 = df["stoch_k"].iloc[-1], df["stoch_d"].iloc[-1]
        k1, d1 = df["stoch_k"].iloc[-2], df["stoch_d"].iloc[-2]
        k2, d2 = df["stoch_k"].iloc[-3], df["stoch_d"].iloc[-3]
        k3, d3 = df["stoch_k"].iloc[-4], df["stoch_d"].iloc[-4]
        k4, d4 = df["stoch_k"].iloc[-5], df["stoch_d"].iloc[-5]
        psar0 = df["psar"].iloc[-1]

        # Pengecekan Volume > MA20
        vol_spike_h0 = v0 > df["vol_ma20"].iloc[-1]
        vol_spike_h1_h3 = (
            (df["Volume"].iloc[-2] > df["vol_ma20"].iloc[-2])
            or (df["Volume"].iloc[-3] > df["vol_ma20"].iloc[-3])
            or (df["Volume"].iloc[-4] > df["vol_ma20"].iloc[-4])
        )

        res_gc = None
        res_dc = None

        # 1. LOGIKA BULLISH / GC (Stoch %K < 30)
        if k0 < 30:
            gc_today = (k1 < d1) and (k0 >= d0)
            gc_yesterday = (k2 < d2) and (k1 >= d1) and (k0 >= d0)
            gc_2days_ago = (k3 < d3) and (k2 >= d2) and (k1 >= d1) and (k0 >= d0)
            gc_3days_ago = (
                (k4 < d4)
                and (k3 >= d3)
                and (k2 >= d2)
                and (k1 >= d1)
                and (k0 >= d0)
            )
            is_almost_gc = (k0 <= d0) and ((d0 - k0) <= 3.0)

            stoch_signal = None
            if gc_today:
                stoch_signal = {"type": "GC Hari Ini (H-0)", "score": 70, "code": "H0"}
            elif gc_yesterday:
                stoch_signal = {"type": "GC Kemarin (H-1)", "score": 70, "code": "H1"}
            elif gc_2days_ago:
                stoch_signal = {"type": "GC 2 Hari Lalu (H-2)", "score": 60, "code": "H2"}
            elif gc_3days_ago:
                stoch_signal = {"type": "GC 3 Hari Lalu (H-3)", "score": 60, "code": "H3"}
            elif is_almost_gc:
                stoch_signal = {"type": "Early Signal (Merapat)", "score": 50, "code": "EARLY"}

            if stoch_signal:
                score = stoch_signal["score"]
                notes = [stoch_signal["type"]]

                if psar0 < l0:
                    score += 20
                    notes.append("PSAR Bullish (+20)")
                else:
                    notes.append("PSAR Bearish (+0)")

                has_vol_bonus = False
                if stoch_signal["code"] == "H0" and vol_spike_h0:
                    has_vol_bonus = True
                elif stoch_signal["code"] in ["H1", "H2", "H3", "EARLY"] and vol_spike_h1_h3:
                    has_vol_bonus = True

                if has_vol_bonus:
                    score += 5
                    notes.append("Vol > MA20 (+5)")

                res_gc = {
                    "Ticker": ticker.replace(".JK", ""),
                    "Harga": int(c0),
                    "Value (M)": round(val0 / 1_000_000_000, 2),
                    "Stoch %K": round(k0, 1),
                    "Stoch %D": round(d0, 1),
                    "Score": score,
                    "Action": "BELI / WATCHLIST",
                    "Detail Signal": " | ".join(notes),
                }

        # 2. LOGIKA BEARISH / DC (Stoch %K > 70)
        if k0 >= 70:
            dc_today = (k1 > d1) and (k0 <= d0)
            dc_yesterday = (k2 > d2) and (k1 <= d1) and (k0 <= d0)
            dc_2days_ago = (k3 > d3) and (k2 >= d2) and (k1 <= d1) and (k0 <= d0)
            dc_3days_ago = (
                (k4 < d4)
                and (k3 >= d3)
                and (k2 >= d2)
                and (k1 <= d1)
                and (k0 <= d0)
            )
            is_almost_dc = (k0 >= d0) and ((k0 - d0) <= 3.0)

            dc_signal = None
            if dc_today:
                dc_signal = {"type": "DC Hari Ini (H-0)", "score": -70, "code": "H0"}
            elif dc_yesterday:
                dc_signal = {"type": "DC Kemarin (H-1)", "score": -70, "code": "H1"}
            elif dc_2days_ago:
                dc_signal = {"type": "DC 2 Hari Lalu (H-2)", "score": -60, "code": "H2"}
            elif dc_3days_ago:
                dc_signal = {"type": "DC 3 Hari Lalu (H-3)", "score": -60, "code": "H3"}
            elif is_almost_dc:
                dc_signal = {"type": "Early DC Signal (Merapat)", "score": -50, "code": "EARLY"}

            if dc_signal:
                score = dc_signal["score"]
                notes = [dc_signal["type"]]

                if psar0 > h0:
                    score -= 20
                    notes.append("PSAR Bearish (-20)")
                else:
                    notes.append("PSAR Bullish (0)")

                has_vol_penalty = False
                if dc_signal["code"] == "H0" and vol_spike_h0:
                    has_vol_penalty = True
                elif dc_signal["code"] in ["H1", "H2", "H3", "EARLY"] and vol_spike_h1_h3:
                    has_vol_penalty = True

                if has_vol_penalty:
                    score -= 5
                    notes.append("High Vol Sell (-5)")

                res_dc = {
                    "Ticker": ticker.replace(".JK", ""),
                    "Harga": int(c0),
                    "Value (M)": round(val0 / 1_000_000_000, 2),
                    "Stoch %K": round(k0, 1),
                    "Stoch %D": round(d0, 1),
                    "Score": score,
                    "Action": "JUAL / EXIT",
                    "Detail Signal": " | ".join(notes),
                }

        return res_gc, res_dc

    except Exception:
        return None, None


# =========================================================================
# FUNGSI UTAMA (Dipanggil oleh app.py)
# =========================================================================
def run_stoch_psar_screener(tickers, max_workers=10):
    """
    Menjalankan screener Stochastic + PSAR secara paralel.
    Mengembalikan tuple: (df_bullish, df_bearish)
    """
    # Pastikan suffix .JK ada
    formatted_tickers = [
        t if t.endswith(".JK") else f"{t}.JK" for t in tickers
    ]

    gc_results = []
    dc_results = []

    # ThreadPoolExecutor aman digunakan di Streamlit Cloud
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_process_single_ticker, ticker)
            for ticker in formatted_tickers
        ]

        for future in concurrent.futures.as_completed(futures):
            res_gc, res_dc = future.result()
            if res_gc:
                gc_results.append(res_gc)
            if res_dc:
                dc_results.append(res_dc)

    # Convert ke DataFrame
    df_gc = pd.DataFrame(gc_results)
    df_dc = pd.DataFrame(dc_results)

    # Urutkan berdasarkan Score tertinggi
    if not df_gc.empty:
        df_gc = df_gc.sort_values(by="Score", ascending=False).reset_index(drop=True)
    if not df_dc.empty:
        df_dc = df_dc.sort_values(by="Score", ascending=True).reset_index(drop=True)

    return df_gc, df_dc
