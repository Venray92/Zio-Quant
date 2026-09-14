import json
import urllib.request
import pandas as pd
import streamlit as st


@st.cache_data(ttl=86400)  # Cache 24 jam
def get_all_ihsg_tickers():
  """Mengambil daftar lengkap seluruh ticker saham IHSG aktif (800+ saham)."""
  # Sumber Data 1: Repository Github Publik Data Saham BEI / IHSG
  try:
    url = "https://raw.githubusercontent.com/datasets/indonesia-stock-exchange/master/data/stock_code.csv"
    df = pd.read_csv(url)
    if "Ticker" in df.columns:
      tickers = [
          f"{str(t).strip().upper()}.JK"
          for t in df["Ticker"]
          if len(str(t).strip()) == 4
      ]
    elif "Code" in df.columns:
      tickers = [
          f"{str(t).strip().upper()}.JK"
          for t in df["Code"]
          if len(str(t).strip()) == 4
      ]

    tickers = sorted(list(set(tickers)))
    if len(tickers) > 200:
      return tickers
  except Exception:
    pass

  # Sumber Data 2 (Backup API GoAPI / IDX Public JSON)
  try:
    url_json = "https://raw.githubusercontent.com/kanisius/indonesia-stock-exchange-data/main/stocks.json"
    req = urllib.request.Request(
        url_json, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req) as response:
      data = json.loads(response.read().decode())
      tickers = [f"{item['code'].upper()}.JK" for item in data if "code" in item]
      tickers = sorted(list(set(tickers)))
      if len(tickers) > 200:
        return tickers
  except Exception:
    pass

  # Fallback Hardcoded 100+ Saham Terpopuler & Teraktif jika koneksi internet terdistorsi
  fallback_tickers = [
      "AALI.JK",
      "ABMM.JK",
      "ACES.JK",
      "ADRO.JK",
      "AGRO.JK",
      "AKRA.JK",
      "AMMN.JK",
      "AMRT.JK",
      "ANTM.JK",
      "APLN.JK",
      "ARTO.JK",
      "ASII.JK",
      "AUTO.JK",
      "BABP.JK",
      "BACA.JK",
      "BBCA.JK",
      "BBHI.JK",
      "BBNI.JK",
      "BBRI.JK",
      "BBTN.JK",
      "BCHP.JK",
      "BDMN.JK",
      "BEST.JK",
      "BFIN.JK",
      "BIRD.JK",
      "BIPP.JK",
      "BKSL.JK",
      "BMRI.JK",
      "BMTR.JK",
      "BNGA.JK",
      "BNII.JK",
      "BNLI.JK",
      "BRIS.JK",
      "BRMS.JK",
      "BRPT.JK",
      "BUKA.JK",
      "BUMI.JK",
      "BYAN.JK",
      "CASA.JK",
      "CLEO.JK",
      "CPIN.JK",
      "CTRA.JK",
      "DLDN.JK",
      "DMAS.JK",
      "DOOH.JK",
      "DSSA.JK",
      "ELSA.JK",
      "EMTK.JK",
      "ERAA.JK",
      "EXCL.JK",
      "FILM.JK",
      "GGRM.JK",
      "GJTL.JK",
      "GOTO.JK",
      "HEAL.JK",
      "HERO.JK",
      "HMSP.JK",
      "IATA.JK",
      "ICBP.JK",
      "INCF.JK",
      "INCO.JK",
      "INDF.JK",
      "INKP.JK",
      "INTP.JK",
      "ISAT.JK",
      "ITMG.JK",
      "JPFA.JK",
      "JRPT.JK",
      "KAEF.JK",
      "KIJA.JK",
      "KLBF.JK",
      "KPIG.JK",
      "LPKR.JK",
      "LPPF.JK",
      "MAPI.JK",
      "MBMA.JK",
      "MDKA.JK",
      "MEDC.JK",
      "MIKA.JK",
      "MNCN.JK",
      "MPMX.JK",
      "MYOR.JK",
      "NCKL.JK",
      "PGAS.JK",
      "PGEO.JK",
      "PNBN.JK",
      "PNBS.JK",
      "PTBA.JK",
      "PTPP.JK",
      "PSSI.JK",
      "PWON.JK",
      "SCMA.JK",
      "SIDO.JK",
      "SMGR.JK",
      "SMRA.JK",
      "SRTG.JK",
      "TBIG.JK",
      "TKIM.JK",
      "TLKM.JK",
      "TPIA.JK",
      "UNVR.JK",
      "WIKA.JK",
      "WOOD.JK",
      "YULE.JK",
  ]
  return sorted(list(set(fallback_tickers)))
