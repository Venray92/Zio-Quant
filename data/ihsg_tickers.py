import os

import streamlit as st

from engines.market_data import find_ticker_file, read_ticker_file


@st.cache_data(ttl=86400)
def get_all_ihsg_tickers(file_name="daftar_saham.txt"):
    """
    Membaca seluruh ticker saham IHSG dari file daftar saham dengan pencarian path otomatis.
    Memakai pembaca yang sama dengan halaman batch dan tugas harian, jadi daftarnya selalu sama.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = find_ticker_file(file_name, extra_dirs=[current_dir])

    if not target_path:
        st.error(
            f"File '{file_name}' tidak ditemukan! "
            f"Lokasi direktori saat ini: `{current_dir}`. "
            f"File yang ada di folder: `{os.listdir(current_dir)}`"
        )
        return []

    try:
        return read_ticker_file(target_path)
    except Exception as e:
        st.error(f"Gagal membaca file {file_name}: {e}")
        return []
