import concurrent.futures
import warnings
import pandas as pd
import ta
import yfinance as yf

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
  try:
    # 1. Penyesuaian format ticker
    formatted_ticker = ticker.strip().upper()
    if not formatted_ticker.endswith(".JK"):
      formatted_ticker = f"{formatted_ticker}.JK"

    df = yf.download(
        formatted_ticker, period="90d", interval="1d", progress=False
    )
    if df.empty or len(df) < 30:
      return None, None

    # 2. Penanganan MultiIndex yfinance
    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    c0 = df["Close"].iloc[-1]
    v0 = df["Volume"].iloc[-1]
    l0 = df["Low"].iloc[-1]
    h0 = df["High"].iloc[-1]
    val0 = c0 * v0

    # Filter dasar
    if c0 <= 50 or val0 < 100_000_000:
      return None, None

    # Indikator Volume MA20
    df["vol_ma20"] = df["Volume"].rolling(window=20).mean()
    vol_ma20_0 = df["vol_ma20"].iloc[-1]

    # Indikator Stochastic
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
    k4, d4 = df["stoch_k"].iloc[-5], df["stoch_d"].iloc[-5]
    psar0 = df["psar"].iloc[-1]

    res_gc = None
    res_dc = None

    # --- 1. GOLDEN CROSS (REVISI: STOCHASTIC %K < 30) ---
    if k0 < 30:
      gc_today = (k1 < d1) and (k0 >= d0)
      gc_yesterday = (k2 < d2) and (k1 >= d1) and (k0 >= d0)
      gc_2days_ago = (k3 < d3) and (k2 >= d2) and (k1 >= d1) and (k0 >= d0)
      gc_3days_ago = (
          (k4 < d4) and (k3 >= d3) and (k2 >= d2) and (k1 >= d1) and (k0 >= d0)
      )
      is_almost_gc = (k0 <= d0) and ((d0 - k0) <= 3.0)

      stoch_signal = None
      if gc_today:
        stoch_signal = {"type": "GC Hari Ini (H-0)", "score": 70, "code": "H0"}
      elif gc_yesterday:
        stoch_signal = {"type": "GC Kemarin (H-1)", "score": 70, "code": "H1"}
      elif gc_2days_ago:
        stoch_signal = {
            "type": "GC 2 Hari Lalu (H-2)",
            "score": 60,
            "code": "H2",
        }
      elif gc_3days_ago:
        stoch_signal = {
            "type": "GC 3 Hari Lalu (H-3)",
            "score": 60,
            "code": "H3",
        }
      elif is_almost_gc:
        stoch_signal = {
            "type": "Early Signal (Merapat)",
            "score": 50,
            "code": "EARLY",
        }

      if stoch_signal:
        score = stoch_signal["score"]
        notes = [stoch_signal["type"]]

        # PSAR Bullish Bonus (+20)
        if psar0 < l0:
          score += 20
          notes.append("PSAR Bullish (+20)")

        # Pengecekan Volume MA20 (+5)
        vol_hist_match = False
        if stoch_signal["code"] == "H0":
          vol_hist_match = v0 > vol_ma20_0
        else:
          vol_ma20_series = df["vol_ma20"]
          vol_series = df["Volume"]
          vol_hist_match = (
              (vol_series.iloc[-2] > vol_ma20_series.iloc[-2])
              or (vol_series.iloc[-3] > vol_ma20_series.iloc[-3])
              or (vol_series.iloc[-4] > vol_ma20_series.iloc[-4])
          )

        if vol_hist_match:
          score += 5
          notes.append("Vol > MA20 (+5)")

        # Pembatasan Maksimal Skor 100
        score = min(100, score)

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

    # --- 2. DEAD CROSS (REVISI: STOCHASTIC %K > 70) ---
    if k0 > 70:
      dc_today = (k1 > d1) and (k0 <= d0)
      dc_yesterday = (k2 > d2) and (k1 <= d1) and (k0 <= d0)
      dc_2days_ago = (k3 > d3) and (k2 >= d2) and (k1 <= d1) and (k0 <= d0)
      dc_3days_ago = (
          (k4 < d4) and (k3 >= d3) and (k2 >= d2) and (k1 >= d1) and (k0 <= d0)
      )
      is_almost_dc = (k0 >= d0) and ((k0 - d0) <= 3.0)

      dc_signal = None
      if dc_today:
        dc_signal = {"type": "DC Hari Ini (H-0)", "score": -70, "code": "H0"}
      elif dc_yesterday:
        dc_signal = {"type": "DC Kemarin (H-1)", "score": -70, "code": "H1"}
      elif dc_2days_ago:
        dc_signal = {
            "type": "DC 2 Hari Lalu (H-2)",
            "score": -60,
            "code": "H2",
        }
      elif dc_3days_ago:
        dc_signal = {
            "type": "DC 3 Hari Lalu (H-3)",
            "score": -60,
            "code": "H3",
        }
      elif is_almost_dc:
        dc_signal = {
            "type": "Early DC Signal (Merapat)",
            "score": -50,
            "code": "EARLY",
        }

      if dc_signal:
        score = dc_signal["score"]
        notes = [dc_signal["type"]]

        # PSAR Bearish Penalti (-20)
        if psar0 > h0:
          score -= 20
          notes.append("PSAR Bearish (-20)")

        # Pengecekan Volume MA20 (-5)
        vol_hist_match = False
        if dc_signal["code"] == "H0":
          vol_hist_match = v0 > vol_ma20_0
        else:
          vol_ma20_series = df["vol_ma20"]
          vol_series = df["Volume"]
          vol_hist_match = (
              (vol_series.iloc[-2] > vol_ma20_series.iloc[-2])
              or (vol_series.iloc[-3] > vol_ma20_series.iloc[-3])
              or (vol_series.iloc[-4] > vol_ma20_series.iloc[-4])
          )

        if vol_hist_match:
          score -= 5
          notes.append("High Vol Sell (-5)")

        # Pembatasan Minimal Skor -100
        score = max(-100, score)

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


def run_stoch_psar_screener(tickers=None, progress_callback=None):
  """Fungsi utama screener."""
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

  df_gc = (
      pd.DataFrame(results_gc)
      if results_gc
      else pd.DataFrame(
          columns=[
              "Ticker",
              "Harga",
              "Value (M)",
              "Stoch %K",
              "Stoch %D",
              "Score",
              "Action",
              "Detail Signal",
          ]
      )
  )
  df_dc = (
      pd.DataFrame(results_dc)
      if results_dc
      else pd.DataFrame(
          columns=[
              "Ticker",
              "Harga",
              "Value (M)",
              "Stoch %K",
              "Stoch %D",
              "Score",
              "Action",
              "Detail Signal",
          ]
      )
  )

  if not df_gc.empty and "Score" in df_gc.columns:
    df_gc = df_gc.sort_values(by="Score", ascending=False).reset_index(
        drop=True
    )
  if not df_dc.empty and "Score" in df_dc.columns:
    df_dc = df_dc.sort_values(by="Score", ascending=True).reset_index(drop=True)

  return df_gc, df_dc
