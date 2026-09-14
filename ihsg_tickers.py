import os
import pandas as pd
import streamlit as st

@st.cache_data(ttl=86400)
def get_all_ihsg_tickers(file_path="daftar_saham.txt"):
    """
    Membaca seluruh ticker saham IHSG langsung dari daftar_saham.txt.
    Mendukung berbagai format separator (koma, tab, dll) dan otomatis menambahkan '.JK'.
    """
    # Fallback jika file tidak ditemukan
    if not os.path.exists(file_path):
        st.error(f"File '{file_path}' tidak ditemukan di directory Streamlit!")
        return []

    try:
        # Membaca file dengan pemisah otomatis
        df = pd.read_csv(file_path, sep=None, engine='python')
        
        # Cari kolom yang berisi 'kode' atau 'ticker' (case-insensitive)
        target_col = None
        for col in df.columns:
            if 'kode' in str(col).lower() or 'ticker' in str(col).lower():
                target_col = col
                break

        # Jika tidak ditemukan nama kolom spesifik, gunakan kolom pertama
        if target_col is None:
            target_col = df.columns[0]

        formatted_tickers = []
        for raw_code in df[target_col]:
            if pd.notna(raw_code):
                t_clean = str(raw_code).strip().upper()
                if t_clean and t_clean != "KODE":  # Abaikan baris header jika terbaca ulang
                    if not t_clean.endswith(".JK"):
                        t_clean += ".JK"
                    formatted_tickers.append(t_clean)

        # Hapus duplikat dan urutkan abjad
        return sorted(list(set(formatted_tickers)))

    except Exception as e:
        st.error(f"Gagal membaca {file_path}: {e}")
        return []
