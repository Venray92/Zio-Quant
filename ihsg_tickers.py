import os
import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=86400)  # Cache 24 jam
def get_all_ihsg_tickers():
  """Mengambil daftar seluruh ticker saham IHSG dari Wikipedia / IDX.

  Returns a list of tickers with '.JK' suffix.
  """
  try:
    # Ambil daftar ticker saham Indonesia dari Wikipedia
    url = "https://id.wikipedia.org/wiki/Daftar_perusahaan_yang_tercatat_di_Bursa_Efek_Indonesia"
    tables = pd.read_html(url)

    tickers = []
    for table in tables:
      # Cari kolom Kode / Ticker / Simbol
      for col in ["Kode", "Kode Saham", "Ticker", "Symbol"]:
        if col in table.columns:
          raw_codes = table[col].dropna().astype(str).tolist()
          for code in raw_codes:
            code = code.strip().upper()
            if len(code) == 4 and code.isalpha():
              tickers.append(f"{code}.JK")
          break

    tickers = sorted(list(set(tickers)))

    # Jika berhasil dan mendapat > 100 ticker
    if len(tickers) > 100:
      return tickers

  except Exception as e:
    pass

  # Fallback daftar lengkap top saham aktif IHSG jika scraping gagal
  fallback_tickers = [
      "ACES.JK",
      "ADRO.JK",
      "AKRA.JK",
      "AMRT.JK",
      "ANTM.JK",
      "ASII.JK",
      "BBCA.JK",
      "BBNI.JK",
      "BBRI.JK",
      "BBTN.JK",
      "BMRI.JK",
      "BRPT.JK",
      "BUKA.JK",
      "CPIN.JK",
      "EMTK.JK",
      "EXCL.JK",
      "GOTO.JK",
      "ICBP.JK",
      "INCO.JK",
      "INDF.JK",
      "INKP.JK",
      "INTP.JK",
      "ITMG.JK",
      "KLBF.JK",
      "MAPI.JK",
      "MBMA.JK",
      "MDKA.JK",
      "MEDC.JK",
      "MIKA.JK",
      "MNCN.JK",
      "PGAS.JK",
      "PTBA.JK",
      "PTPP.JK",
      "SCMA.JK",
      "SGRG.JK",
      "SMGR.JK",
      "TBIG.JK",
      "TLKM.JK",
      "TPIA.JK",
      "UNVR.JK",
  ]
  return sorted(list(set(fallback_tickers)))
