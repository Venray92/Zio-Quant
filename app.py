import streamlit as st
import pandas as pd
import yfinance as yf

# 1. Konfigurasi Halaman Wajib Full-Width
st.set_page_config(
    page_title="ZioQuant - IDX Stock Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS untuk Tampilan Modern Dark Mode & Hilangkan Padding Berlebih
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    /* Styling Tabel & Metrik */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Header Utama Aplikasi
st.title("⚡ ZioQuant - IDX Professional Screener")
st.markdown("---")

# 4. Sidebar Kontrol Sederhana
st.sidebar.header("⚙️ Pengaturan Screener")
ticker_input = st.sidebar.text_input("Kode Saham (Contoh: BBCA.JK, BBRI.JK)", value="BBCA.JK")
fetch_btn = st.sidebar.button("Jalankan Analisis", type="primary")

# 5. Area Utama Tampilan
if fetch_btn:
    with st.spinner(f"Menarik data masif untuk {ticker_input}..."):
        try:
            # Contoh tarik data menggunakan yfinance
            df = yf.download(ticker_input, period="6mo", interval="1d", progress=False)
            
            # Meratakan MultiIndex jika ada (penyesuaian yfinance versi terbaru)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            if not df.empty:
                # FIX STRING SYNTAX ERROR DI SINI:
                st.success(f"Berhasil memuat data {ticker_input}!")
                st.subheader("📊 Data Historis Terakhir")
                st.dataframe(df.tail(10), use_container_width=True)
            else:
                st.error("Data tidak ditemukan atau kode saham salah.")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat mengambil data: {e}")
else:
    st.info("👈 Masukkan kode saham di sidebar lalu klik **Jalankan Analisis** untuk memulai.")
