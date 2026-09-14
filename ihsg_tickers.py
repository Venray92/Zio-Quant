import os
import pandas as pd
import streamlit as st

@st.cache_data(ttl=86400)
def get_all_ihsg_tickers(file_name="daftar_saham.txt"):
    """
    Membaca seluruh ticker saham IHSG dari file txt dengan pencarian path otomatis.
    """
    # 1. Dapatkan lokasi folder saat ini di mana script ihsg_tickers.py berada
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Cari file di folder utama dan beberapa opsi nama file yang mungkin
    possible_paths = [
        os.path.join(current_dir, file_name),
        file_name,
        os.path.join(current_dir, "daftar_saham.txt.txt"), # Mencegah error double extension di Windows
    ]

    target_path = None
    for path in possible_paths:
        if os.path.exists(path):
            target_path = path
            break

    # Jika file tetap tidak ditemukan, tampilkan lokasi direktori untuk debug
    if not target_path:
        st.error(
            f"File '{file_name}' tidak ditemukan! "
            f"Lokasi direktori saat ini: `{current_dir}`. "
            f"File yang ada di folder: `{os.listdir(current_dir)}`"
        )
        return []

    try:
        # Membaca file dengan pandas (pemisah otomatis)
        df = pd.read_csv(target_path, sep=None, engine='python')
        
        # Cari kolom yang berisi kata 'kode' atau 'ticker'
        target_col = None
        for col in df.columns:
            if 'kode' in str(col).lower() or 'ticker' in str(col).lower():
                target_col = col
                break

        if target_col is None:
            target_col = df.columns[0]

        formatted_tickers = []
        for raw_code in df[target_col]:
            if pd.notna(raw_code):
                t_clean = str(raw_code).strip().upper()
                if t_clean and t_clean != "KODE":
                    if not t_clean.endswith(".JK"):
                        t_clean += ".JK"
                    formatted_tickers.append(t_clean)

        return sorted(list(set(formatted_tickers)))

    except Exception as e:
        st.error(f"Gagal membaca file {file_name}: {e}")
        return []
