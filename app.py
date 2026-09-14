import streamlit as st
import pandas as pd

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN STREAMLIT
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Trade Plan & Technical Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Technical Analysis & Automated Trade Plan Dashboard")
st.markdown("---")

# -----------------------------------------------------------------------------
# 2. RAW DATA SWING POINTS (30 DATA REKAPITULASI)
# -----------------------------------------------------------------------------
raw_data = [
    {"No": 1,  "Date": "2026-09-10", "Open": 146.00, "High": 148.00, "Low": 137.00, "Close": 137.00, "Swing Type": "Swing High", "Metpoint Level": "146.0"},
    {"No": 2,  "Date": "2026-08-21", "Open": 104.00, "High": 107.00, "Low": 102.00, "Close": 103.00, "Swing Type": "Swing High", "Metpoint Level": "104.0"},
    {"No": 3,  "Date": "2026-08-06", "Open": 112.00, "High": 113.00, "Low": 106.00, "Close": 108.00, "Swing Type": "Swing High", "Metpoint Level": "-"},
    {"No": 4,  "Date": "2026-07-23", "Open": 135.00, "High": 155.00, "Low": 134.00, "Close": 141.00, "Swing Type": "Swing High", "Metpoint Level": "135.0"},
    {"No": 5,  "Date": "2026-07-09", "Open": 212.00, "High": 216.00, "Low": 166.00, "Close": 173.00, "Swing Type": "Swing High", "Metpoint Level": "212.0, 216.0"},
    {"No": 6,  "Date": "2026-06-24", "Open": 193.00, "High": 212.00, "Low": 175.00, "Close": 179.00, "Swing Type": "Swing High", "Metpoint Level": "212.0"},
    {"No": 7,  "Date": "2026-06-12", "Open": 176.00, "High": 218.00, "Low": 168.00, "Close": 194.00, "Swing Type": "Swing High", "Metpoint Level": "218.0"},
    {"No": 8,  "Date": "2026-05-29", "Open": 236.00, "High": 266.00, "Low": 236.00, "Close": 248.00, "Swing Type": "Swing High", "Metpoint Level": "-"},
    {"No": 9,  "Date": "2026-05-07", "Open": 372.00, "High": 402.00, "Low": 360.00, "Close": 372.00, "Swing Type": "Swing High", "Metpoint Level": "402.0"},
    {"No": 10, "Date": "2026-04-23", "Open": 530.00, "High": 570.00, "Low": 442.00, "Close": 444.00, "Swing Type": "Swing High", "Metpoint Level": "-"},
    {"No": 11, "Date": "2026-04-15", "Open": 450.00, "High": 460.00, "Low": 418.00, "Close": 428.00, "Swing Type": "Swing High", "Metpoint Level": "-"},
    {"No": 12, "Date": "2026-04-02", "Open": 400.00, "High": 400.00, "Low": 314.00, "Close": 314.00, "Swing Type": "Swing High", "Metpoint Level": "400.0"},
    {"No": 13, "Date": "2026-09-11", "Open": 132.00, "High": 135.00, "Low": 125.00, "Close": 131.00, "Swing Type": "Swing Low",  "Metpoint Level": "125.0"},
    {"No": 14, "Date": "2026-08-27", "Open": 97.00,  "High": 101.00, "Low": 96.00,  "Close": 100.00, "Swing Type": "Swing Low",  "Metpoint Level": "96.0, 100.0"},
    {"No": 15, "Date": "2026-08-19", "Open": 100.00, "High": 100.00, "Low": 96.00,  "Close": 98.00,  "Swing Type": "Swing Low",  "Metpoint Level": "96.0, 98.0"},
    {"No": 16, "Date": "2026-08-12", "Open": 101.00, "High": 103.00, "Low": 98.00,  "Close": 102.00, "Swing Type": "Swing Low",  "Metpoint Level": "98.0, 102.0"},
    {"No": 17, "Date": "2026-08-03", "Open": 109.00, "High": 111.00, "Low": 100.00, "Close": 103.00, "Swing Type": "Swing Low",  "Metpoint Level": "100.0, 103.0"},
    {"No": 18, "Date": "2026-07-16", "Open": 128.00, "High": 138.00, "Low": 125.00, "Close": 133.00, "Swing Type": "Swing Low",  "Metpoint Level": "125.0"},
    {"No": 19, "Date": "2026-07-01", "Open": 73.44,  "High": 98.68,  "Low": 66.55,  "Close": 98.68,  "Swing Type": "Swing Low",  "Metpoint Level": "98.68"},
    {"No": 20, "Date": "2026-06-08", "Open": 159.00, "High": 169.00, "Low": 145.00, "Close": 158.00, "Swing Type": "Swing Low",  "Metpoint Level": "145.0"},
    {"No": 21, "Date": "2026-05-22", "Open": 224.00, "High": 256.00, "Low": 210.00, "Close": 252.00, "Swing Type": "Swing Low",  "Metpoint Level": "210.0"},
    {"No": 22, "Date": "2026-05-12", "Open": 348.00, "High": 356.00, "Low": 306.00, "Close": 334.00, "Swing Type": "Swing Low",  "Metpoint Level": "-"},
    {"No": 23, "Date": "2026-04-30", "Open": 342.00, "High": 344.00, "Low": 300.00, "Close": 320.00, "Swing Type": "Swing Low",  "Metpoint Level": "-"},
    {"No": 24, "Date": "2026-04-20", "Open": 410.00, "High": 436.00, "Low": 402.00, "Close": 420.00, "Swing Type": "Swing Low",  "Metpoint Level": "402.0"},
    {"No": 25, "Date": "2026-04-06", "Open": 300.00, "High": 330.00, "Low": 292.00, "Close": 314.00, "Swing Type": "Swing Low",  "Metpoint Level": "292.0"},
    {"No": 26, "Date": "2026-03-16", "Open": 290.00, "High": 300.00, "Low": 290.00, "Close": 294.00, "Swing Type": "Swing Low",  "Metpoint Level": "290.0, 294.0"},
]

df = pd.DataFrame(raw_data)

# -----------------------------------------------------------------------------
# 3. PERHITUNGAN PARAMETER UTAMA
# -----------------------------------------------------------------------------
swing_high = 148.0
swing_low = 125.0
equilibrium = (swing_high + swing_low) / 2  # 136.5
last_close = 134.0
direction = "BOW (Buy On Weakness)" if last_close < equilibrium else "Sell / Wait"

# -----------------------------------------------------------------------------
# 4. MONITOR RINGKASAN ARAH PASAR (DIRECTION ANALYSIS)
# -----------------------------------------------------------------------------
st.subheader("1. Ringkasan Arah Pasar (Direction Analysis)")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Swing High Terupdate", f"{swing_high}")
col2.metric("Swing Low Terupdate", f"{swing_low}")
col3.metric("Level Equilibrium (50%)", f"{equilibrium}")
col4.metric("Harga Penutupan Terakhir", f"{last_close}")
col5.metric("Arah Utama Pasar", direction)

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. PETA SUPPORT & RESISTANCE UTAMA
# -----------------------------------------------------------------------------
st.subheader("2. Peta Support & Resistance Utama")
res_col, sup_col = st.columns(2)

with res_col:
    st.write("### 🔴 Strong Resistance")
    st.write("**1st Rank (Utama):** High **216.0** / Body Top **212.0** *(09 Jul 2026)*")
    st.write("**2nd Rank (Kedua):** High **155.0** / Body Top **141.0** *(23 Jul 2026)*")

with sup_col:
    st.write("### 🟢 Strong Support")
    st.write("**1st Rank (Terdekat):** Low **125.0** / Body Bottom **131.0** *(11 Sep 2026)*")
    st.write("**2nd Rank (Kedua):** Low **96.0** / Body Bottom **97.0** *(27 Aug 2026)*")

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. SKENARIO TRADE PLAN (BOW & BOB)
# -----------------------------------------------------------------------------
st.subheader("3. Eksekusi Trade Plan & Skenario Masuk")

tab1, tab2 = st.columns(2)

with tab1:
    st.info("### 📌 Skenario 1: Buy On Weakness (BOW) — Utama")
    st.markdown("""
    - **Range Area Beli:** `125.0 – 131.0`
    - **Stop Loss:** `122.0` *(Di bawah support terdekat)*
    - **Target Profit 1 (TP 1):** `155.0`
    - **Target Profit 2 (TP 2):** `216.0`
    - **Risk to Reward Ratio:** **1 : 10.0**
    - **Konfirmasi Candlestick:** *Bullish Engulfing*
    
    > **💡 Catatan & Sinyal:** Pembeli mulai mengambil alih kontrol pasar. Sinyal pembalikan arah naik valid di area support terdekat.
    """)

with tab2:
    st.success("### 🚀 Skenario 2: Buy On Breakout (BOB) — Lanjutan")
    st.markdown("""
    - **Range Area Beli:** `155.0 – 158.0` *(Breakout Resistance 155.0)*
    - **Stop Loss:** `152.0`
    - **Target Profit 1 (TP 1):** `216.0`
    - **Target Profit 2 (TP 2):** `218.0`
    - **Risk to Reward Ratio:** **1 : 20.3**
    - **Konfirmasi Candlestick:** *Bullish Engulfing*
    
    > **💡 Catatan & Sinyal:** Validasi penguatan berlanjut menuju area resistance utama jika 155.0 berhasil ditembus dengan volume tinggi.
    """)

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. TABEL DATA SWING POINTS (30 DATA)
# -----------------------------------------------------------------------------
st.subheader("4. Tabel Rekapitulasi Swing Points")
st.dataframe(df, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# 8. MANAJEMEN RISIKO
# -----------------------------------------------------------------------------
st.subheader("5. Manajemen Risiko & Prosedur Eksekusi")
st.warning("""
1. **Disiplin Stop Loss:** Jika harga ditutup di bawah **122.0** pada akhir sesi, lakukan *cut loss* untuk menjaga modal.
2. **Pengaturan Portofolio:** Gunakan alokasi lot bertahap pada area `125.0 - 131.0` untuk mendapatkan harga rata-rata terbaik.
3. **Trailing Stop:** Saat harga menembus TP 1 (**155.0**), naikkan Stop Loss ke harga modal (*BEP*) untuk mengamankan keuntungan menuju TP 2 (**216.0**).
""")
