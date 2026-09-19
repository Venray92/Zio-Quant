import concurrent.futures
import warnings
import pandas as pd
import ta
import yfinance as yf

from data.ihsg_tickers import get_all_ihsg_tickers

warnings.filterwarnings("ignore")

DEFAULT_SAHAM_LIST = sorted(
    list(
        set([
            "ISAT.JK"
        ])
    )
)


def _process_single_ticker(ticker):
    try:
        formatted_ticker = ticker.strip().upper()
        if not formatted_ticker.endswith(".JK"):
            formatted_ticker = f"{formatted_ticker}.JK"

        df = yf.download(
            formatted_ticker, period="90d", interval="1d", progress=False
        )
        if df.empty or len(df) < 30:
            return None, None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        c0 = df["Close"].iloc[-1]
        c1 = df["Close"].iloc[-2]
        v0 = df["Volume"].iloc[-1]
        v1 = df["Volume"].iloc[-2]
        l0 = df["Low"].iloc[-1]
        h0 = df["High"].iloc[-1]
        val0 = c0 * v0

        # Persentase perubahan harga harian
        change_pct = ((c0 - c1) / c1) * 100 if c1 > 0 else 0.0

        # Filter Likuiditas Minimum RP 1 Miliar & Harga > 70
        if c0 <= 70 or val0 < 1_000_000_000:
            return None, None

        # Indikator Volume MA20
        df["vol_ma20"] = df["Volume"].rolling(window=20).mean()
        vol_ma20_0 = df["vol_ma20"].iloc[-1]

        # Indikator Stochastic (Custom 10, 5, 5)
        low_min10 = df["Low"].rolling(window=10).min()
        high_max10 = df["High"].rolling(window=10).max()

        diff = high_max10 - low_min10
        diff = diff.replace(0, 0.001)

        fast_k = 100 * ((df["Close"] - low_min10) / diff)
        df["stoch_k"] = fast_k.rolling(window=5).mean()
        df["stoch_d"] = df["stoch_k"].rolling(window=5).mean()

        # Indikator PSAR
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
        psar0 = df["psar"].iloc[-1]

        res_gc = None
        res_dc = None

        # =========================================================
        # 1. GOLDEN CROSS (BULLISH)
        # =========================================================
        gc_today = (k1 < d1) and (k0 >= d0) and (k0 < 35)
        gc_yesterday = (k2 < d2) and (k1 >= d1) and (k0 >= d0) and (k1 < 35)
        gc_2days_ago = (
            (k3 < d3) and (k2 >= d2) and (k1 >= d1) and (k0 >= d0) and (k2 < 35)
        )
        is_almost_gc = (k0 <= d0) and ((d0 - k0) <= 3.0) and (k0 < 35) and (v0 > v1)

        stoch_signal_gc = None
        if gc_today:
            stoch_signal_gc = {"type": "GC Hari Ini (H-0)", "score": 50, "code": "H0"}
        elif gc_yesterday:
            stoch_signal_gc = {"type": "GC Kemarin (H-1)", "score": 40, "code": "H1"}
        elif gc_2days_ago:
            stoch_signal_gc = {"type": "GC 2 Hari Lalu (H-2)", "score": 30, "code": "H2"}
        elif is_almost_gc:
            stoch_signal_gc = {"type": "Early Signal (Merapat)", "score": 20, "code": "EARLY"}

        if stoch_signal_gc:
            score = stoch_signal_gc["score"]
            notes = [stoch_signal_gc["type"]]

            if psar0 < l0:
                score += 20
                notes.append("PSAR Bullish (+20)")

            if stoch_signal_gc["code"] == "H0":
                if v0 > vol_ma20_0:
                    score += 20
                    notes.append("Vol > MA20 (+20)")
                elif v0 > v1:
                    score += 10
                    notes.append("Vol > Prev Vol (+10)")

                if c0 > c1:
                    score += 10
                    notes.append("Price > Prev (+10)")

            score = min(100, score)

            res_gc = {
                "Ticker": ticker.replace(".JK", ""),
                "Harga": int(c0),
                "Change (%)": round(change_pct, 2),
                "Value (M)": round(val0 / 1_000_000_000, 2),
                "Stoch %K": round(k0, 1),
                "Stoch %D": round(d0, 1),
                "Score": score,
                "Detail Signal": " | ".join(notes),
            }

        # =========================================================
        # 2. DEAD CROSS (BEARISH)
        # =========================================================
        dc_today = (k1 > d1) and (k0 <= d0) and (k0 > 70)
        dc_yesterday = (k2 > d2) and (k1 <= d1) and (k0 <= d0) and (k1 > 70)
        dc_2days_ago = (
            (k3 > d3) and (k2 <= d2) and (k1 <= d1) and (k0 <= d0) and (k2 > 70)
        )
        is_almost_dc = (k0 >= d0) and ((k0 - d0) <= 3.0) and (k0 > 70)

        stoch_signal_dc = None
        if dc_today:
            stoch_signal_dc = {"type": "DC Hari Ini (H-0)", "score": -20, "code": "H0"}
        elif dc_yesterday:
            stoch_signal_dc = {"type": "DC Kemarin (H-1)", "score": -30, "code": "H1"}
        elif dc_2days_ago:
            stoch_signal_dc = {"type": "DC 2 Hari Lalu (H-2)", "score": -40, "code": "H2"}
        elif is_almost_dc:
            stoch_signal_dc = {"type": "Early DC Signal (Merapat)", "score": -10, "code": "EARLY"}

        if stoch_signal_dc:
            score = stoch_signal_dc["score"]
            notes = [stoch_signal_dc["type"]]

            if psar0 > h0:
                score -= 20
                notes.append("PSAR Bearish (-20)")

            if stoch_signal_dc["code"] == "H0":
                if v0 > vol_ma20_0:
                    score -= 20
                    notes.append("Vol > MA20 (-20)")
                elif v0 > v1:
                    score -= 10
                    notes.append("Vol > Prev Vol (-10)")

                if c0 < c1:
                    score -= 10
                    notes.append("Price < Prev (-10)")

            score = max(-100, score)

            res_dc = {
                "Ticker": ticker.replace(".JK", ""),
                "Harga": int(c0),
                "Change (%)": round(change_pct, 2),
                "Value (M)": round(val0 / 1_000_000_000, 2),
                "Stoch %K": round(k0, 1),
                "Stoch %D": round(d0, 1),
                "Score": score,
                "Detail Signal": " | ".join(notes),
            }

        return res_gc, res_dc

    except Exception:
        return None, None


def run_stoch_psar_screener(tickers=None, progress_callback=None):
    if tickers is None:
        try:
            tickers = get_all_ihsg_tickers()
        except Exception:
            tickers = DEFAULT_SAHAM_LIST

        if not tickers:
            tickers = DEFAULT_SAHAM_LIST

    results_gc = []
    results_dc = []
    total_tickers = len(tickers)
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_process_single_ticker, t): t for t in tickers}
        for future in concurrent.futures.as_completed(futures):
            res_gc, res_dc = future.result()
            if res_gc:
                results_gc.append(res_gc)
            if res_dc:
                results_dc.append(res_dc)

            completed += 1
            if progress_callback:
                progress_callback(completed, total_tickers)

    cols = [
        "Ticker",
        "Harga",
        "Change (%)",
        "Value (M)",
        "Stoch %K",
        "Stoch %D",
        "Score",
        "Detail Signal",
    ]

    df_gc = pd.DataFrame(results_gc) if results_gc else pd.DataFrame(columns=cols)
    df_dc = pd.DataFrame(results_dc) if results_dc else pd.DataFrame(columns=cols)

    if not df_gc.empty and "Score" in df_gc.columns:
        df_gc = df_gc.sort_values(by="Score", ascending=False).reset_index(drop=True)
    if not df_dc.empty and "Score" in df_dc.columns:
        df_dc = df_dc.sort_values(by="Score", ascending=True).reset_index(drop=True)

    return df_gc, df_dc
