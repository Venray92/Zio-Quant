import pandas as pd
import requests


def get_all_ihsg_tickers():
  """Mengambil daftar seluruh ticker saham IHSG (berakhiran .JK).

  Menggunakan scraping Wikipedia dengan fallback jika terjadi kendala jaringan.
  """
  try:
    url = "https://id.wikipedia.org/wiki/Daftar_perusahaan_yang_tercatat_di_Bursa_Efek_Indonesia"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
      tables = pd.read_html(response.text)
      ticker_list = []
      for table in tables:
        # Mencari kolom Kode / Kode Saham
        code_col = [
            col
            for col in table.columns
            if "Kode" in str(col) or "Ticker" in str(col)
        ]
        if code_col:
          codes = table[code_col[0]].astype(str).str.strip()
          # Filter hanya yang berbentuk kode saham 4 huruf
          valid_codes = codes[codes.str.len() == 4].tolist()
          ticker_list.extend(valid_codes)

      if len(ticker_list) > 100:
        # Hilangkan duplikat & tambahkan .JK
        unique_tickers = sorted(list(set(ticker_list)))
        return [f"{t.upper()}.JK" for t in unique_tickers]
  except Exception as e:
    print(f"Warning: Gagal scraping data live ({e}), menggunakan fallback list.")

  # Fallback: Daftar saham paling umum / utama jika internet gagal
  fallback_tickers = [
      "BBCA.JK",
      "BBRI.JK",
      "BMRI.JK",
      "TLKM.JK",
      "ASII.JK",
      "INDF.JK",
      "UNVR.JK",
      "ICBP.JK",
      "AMRT.JK",
      "BBNI.JK",
      "GOTO.JK",
      "BRIS.JK",
      "MDKA.JK",
      "ADRO.JK",
      "PGAS.JK",
      "PTBA.JK",
      "ANTM.JK",
      "INCO.JK",
      "MEDC.JK",
      "CPIN.JK",
  ]
  return fallback_tickers


if __name__ == "__main__":
  tickers = get_all_ihsg_tickers()
  print(f"Total Ticker Berhasil Dimuat: {len(tickers)}")
  print("Sampel 10 pertama:", tickers[:10])