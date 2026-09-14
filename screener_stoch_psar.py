import warnings
import pandas as pd
import ta
import yfinance as yf
import concurrent.futures
import streamlit as st

# Import pengambil daftar 962 saham dari file .txt
from ihsg_tickers import get_all_ihsg_tickers

warnings.filterwarnings("ignore")

DEFAULT_SAHAM_LIST = sorted(
    list(
        set([
            "ISAT.JK",
            "ACES.JK",
            "ADHI.JK",
            "ADRO.JK",
            "AGRO.JK",
            "AALI.JK",
            "AKRA.JK",
            "AMMN.JK",
            "AMRT.JK",
            "ANTM.JK",
            "APLN.JK",
            "ARTO.JK",
            "ASII.JK",
            "ASRI.JK",
            "AUTO.JK",
            "AVIA.JK",
            "BBCA.JK",
            "BBHI.JK",
            "BBNI.JK",
            "BBRI.JK",
            "BBTN.JK",
            "BCIC.JK",
            "BDMN.JK",
            "BELI.JK",
            "BIRD.JK",
            "BJBR.JK",
            "BJTM.JK",
            "BMRI.JK",
            "BMTR.JK",
            "BNGA.JK",
            "BREN.JK",
            "BRIS.JK",
            "BRPT.JK",
            "BSDE.JK",
            "BUKA.JK",
            "BUMI.JK",
            "BYAN.JK",
            "CITA.JK",
            "CLEO.JK",
            "CMRY.JK",
            "CPIN.JK",
            "CTRA.JK",
            "CUAN.JK",
            "DCII.JK",
            "DEWA.JK",
            "DILD.JK",
            "DKFT.JK",
            "DOID.JK",
            "DRMA.JK",
            "DSNG.JK",
            "EAST.JK",
            "EDGE.JK",
            "ELSA.JK",
            "EMTK.JK",
            "ENRG.JK",
            "ESSA.JK",
            "EXCL.JK",
            "FILM.JK",
            "GEMS.JK",
            "GJTL.JK",
            "GOTO.JK",
            "HAIS.JK",
            "HEAL.JK",
            "HRUM.JK",
            "ICBP.JK",
            "INAF.JK",
            "INCO.JK",
            "INDF.JK",
            "INDY.JK",
            "INKP.JK",
            "INTP.JK",
            "IPCC.JK",
            "IPCM.JK",
            "IRRA.JK",
            "ITMG.JK",
            "JKON.JK",
            "JPFA.JK",
            "JSPT.JK",
            "KAEF.JK",
            "KEEN.JK",
            "KIJA.JK",
            "KLBF.JK",
            "LEAD.JK",
            "LSIP.JK",
            "MAIN.JK",
            "MAPA.JK",
            "MAPI.JK",
            "MBAP.JK",
            "MBMA.JK",
            "MCAS.JK",
            "MDKA.JK",
            "MEDC.JK",
            "MEDS.JK",
            "MIKA.JK",
            "MNCN.JK",
            "MPMX.JK",
            "MTDL.JK",
            "MYOR.JK",
            "NCKL.JK",
            "NELY.JK",
            "NRCA.JK",
            "PANI.JK",
            "PANR.JK",
            "PGAS.JK",
            "PGEO.JK",
            "PNBN.JK",
            "POWR.JK",
            "PRDA.JK",
            "PSAB.JK",
            "PSSI.JK",
            "PTBA.JK",
            "PTPP.JK",
            "PWON.JK",
            "RAAM.JK",
            "RALS.JK",
            "SAME.JK",
            "SCMA.JK",
            "SIDO.JK",
            "SILO.JK",
            "SMBR.JK",
            "SMDR.JK",
            "SMGR.JK",
            "SMRA.JK",
            "SMSM.JK",
            "SSIA.JK",
            "SSMS.JK",
            "STAA.JK",
            "TAPG.JK",
            "TBIG.JK",
            "TCPI.JK",
            "TINS.JK",
            "TKIM.JK",
            "TLKM.JK",
            "TMAS.JK",
            "TOBA.JK",
            "TOTL.JK",
            "TOWR.JK",
            "TPIA.JK",
            "TSPC.JK",
            "UNTR.JK",
            "UNVR.JK",
            "WEGE.JK",
            "WIFI.JK",
            "WIKA.JK",
            "WINS.JK",
            "WOOD.JK",
        ])
    )
)


def _process_single_ticker(ticker):
    """Fungsi pembantu untuk menganalisis 1 saham (logika asli kamu)."""
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

        # Filter likuiditas & harga minimal
        if c0 <= 50 or val0 < 1_000_000_000:
            return None, None

        df["vol_ma20"] = df["Volume"].rolling(window=20).mean()
        vol_ma20_0 = df["vol_ma20"].iloc[-1]

        # STOCHASTIC (10,5,5)
        low_min10 = df["Low"].rolling(window=10).min()
        high_max10 = df["High"].rolling(window=10).max()
        fast_k = 100 * ((df["Close"] - low_min10) / (high_max10 - low_min10))

        df["stoch_k"] = fast_k.rolling(window=5).mean()
        df["stoch_d"] = df["stoch_k"].rolling(window=5).mean()

        # PARABOLIC SAR
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

        k0, d0 = df["stoch_k"].iloc[-1], df["stoch_d"].iloc[-1]  # H-0
        k1, d1 = df["stoch_k"].iloc[-2], df["stoch_d"].iloc[-2]  # H-1
        k2, d2 = df["stoch_k"].iloc[-3], df["stoch_d"].iloc[-3]  # H-2
        k3, d3 = df["stoch_k"].iloc[-4], df["stoch_d"].iloc[-4]  # H-3
        k4, d4 = df["stoch_k"].iloc[-5], df["stoch_d"].iloc[-5]  # H-4
        psar0 = df["psar"].iloc[-1]

        res_gc = None
        res_dc = None

        # 1. GOLDEN CROSS (GC) -> OVERSOLD (k0 < 35)
        if k0 < 35:
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
                stoch_signal = {
                    "type": "GC Hari Ini (H-0)",
                    "score": 80,
                    "code": "H0",
                }
            elif gc_yesterday:
                stoch_signal = {
                    "type": "GC Kemarin (H-1)",
                    "score": 70,
                    "code": "H1_H3",
                }
            elif gc_2days_ago:
                stoch_signal = {
                    "type": "GC 2 Hari Lalu (H-2)",
                    "score": 70,
                    "code": "H1_H3",
                }
            elif gc_3days_ago:
                stoch_signal = {
                    "type": "GC 3 Hari Lalu (H-3)",
                    "score": 70,
                    "code": "H1_H3",
                }
            elif is_almost_gc:
                stoch_signal = {
                    "type": "Early Signal (Merapat)",
                    "score": 55,
                    "code": "EARLY",
                }

            if stoch_signal:
                score = stoch_signal["score"]
                notes = [stoch_signal["type"]]

                if psar0 < l0:
                    score += 20
                    notes.append("PSAR Bullish (+20)")
                else:
                    notes.append("PSAR Bearish (+0)")

                if v0 > vol_ma20_0:
                    score += 10 if stoch_signal["code"] == "H0" else 5
                    notes.append("Vol > MA20")

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

        # 2. DEAD CROSS (DC) -> OVERBOUGHT (k0 >= 75)
        if k0 >= 75:
            dc_today = (k1 > d1) and (k0 <= d0)
            dc_yesterday = (k2 > d2) and (k1 <= d1) and (k0 <= d0)
            dc_2days_ago = (k3 > d3) and (k2 >= d2) and (k1 <= d1) and (k0 <= d0)
            dc_3days_ago = (
                (k4 > d4)
                and (k3 >= d3)
                and (k2 >= d2)
                and (k1 <= d1)
                and (k0 <= d0)
            )
            is_almost_dc = (k0 >= d0) and ((k0 - d0) <= 3.0)

            dc_signal = None
            if dc_today:
                dc_signal = {
                    "type": "DC Hari Ini (H-0)",
                    "score": -80,
                    "code": "H0",
                }
            elif dc_yesterday:
                dc_signal = {
                    "type": "DC Kemarin (H-1)",
                    "score": -70,
                    "code": "H1_H3",
                }
            elif dc_2days_ago:
                dc_signal = {
                    "type": "DC 2 Hari Lalu (H-2)",
                    "score": -70,
                    "code": "H1_H3",
                }
            elif dc_3days_ago:
                dc_signal = {
                    "type": "DC 3 Hari Lalu (H-3)",
                    "score": -70,
                    "code": "H1_H3",
                }
            elif is_almost_dc:
                dc_signal = {
                    "type": "Early DC Signal (Merapat)",
                    "score": -55,
                    "code": "EARLY",
                }

            if dc_signal:
                score = dc_signal["score"]
                notes = [dc_signal["type"]]

                if psar0 > h0:
                    score -= 20
                    notes.append("PSAR Bearish (-20)")
                else:
                    notes.append("PSAR Bullish (0)")

                if v0 > vol_ma20_0:
                    penalty = 10 if dc_signal["code"] == "H0" else 5
                    score -= penalty
                    notes.append(f"High Vol Sell (-{penalty})")

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


def run_stoch_psar_screener(tickers=None):
    """Jalankan screening Stochastic + Parabolic SAR secara paralel."""
    # Priority: jika tickers tidak di-pass, ambil dari file daftar_saham.txt via ihsg_tickers.py
    if tickers is None:
        tickers = get_all_ihsg_tickers()
        if not tickers:
            tickers = DEFAULT_SAHAM_LIST

    results_gc = []
    results_dc = []

    total_tickers = len(tickers)
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.info(f"Menganalisis {total_tickers} ticker saham IHSG...")

    completed = 0
    # Multi-threading untuk mempercepat proses scan 962 saham
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(_process_single_ticker, t): t for t in tickers}
        for future in concurrent.futures.as_completed(futures):
            res_gc, res_dc = future.result()
            if res_gc:
                results_gc.append(res_gc)
            if res_dc:
                results_dc.append(res_dc)

            completed += 1
            progress_bar.progress(completed / total_tickers)

    progress_bar.empty()
    status_text.empty()

    df_gc = pd.DataFrame(results_gc)
    df_dc = pd.DataFrame(results_dc)

    if not df_gc.empty:
        df_gc = df_gc.sort_values(by="Score", ascending=False).reset_index(
            drop=True
        )
    if not df_dc.empty:
        df_dc = df_dc.sort_values(by="Score", ascending=True).reset_index(
            drop=True
        )

    return df_gc, df_dc


if __name__ == "__main__":
    # Test jalankan standalone
    print("Running Stochastic - PSAR Screener...")
    gc, dc = run_stoch_psar_screener()
    print("=== GOLDEN CROSS ===")
    print(gc.head() if not gc.empty else "Kosong")
    print("\n=== DEAD CROSS ===")
    print(dc.head() if not dc.empty else "Kosong")
