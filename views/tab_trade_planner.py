import concurrent.futures
import time
import pandas as pd
import requests
import streamlit as st

# ==========================================
# 1. STREAMLIT CONFIG & STYLING (CYBERPUNK)
# ==========================================
st.set_page_config(
    page_title="Stock Screener PRO",
    page_icon="⚡",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Dark Cyberpunk Theme */
    .stApp {
        background-color: #0b0e14;
        color: #c5c6c7;
    }
    h1, h2, h3 {
        color: #00f2fe !important;
        font-family: 'Trebuchet MS', sans-serif;
    }
    .stButton>button {
        background: linear-gradient(45deg, #00c6ff, #0072ff);
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(45deg, #0072ff, #00c6ff);
        box-shadow: 0 0 10px #00c6ff;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("⚡ Stock Screener PRO")
st.caption("Fast multi-threaded data fetching with custom indicator analysis.")

# ==========================================
# 2. HELPER & DATA FETCHING FUNCTIONS
# ==========================================

# Simulasi API Call per Ticker (Ganti dengan API/Logika Rekomendasi Kamu)
def process_single_ticker(symbol):
    try:
        # Dummy delay untuk simulasi kerumitan perhitungan/fetching
        time.sleep(0.1)

        # Contoh data dummy hasil analisis
        return {
            "Symbol": symbol,
            "Price": round(100 + (hash(symbol) % 500), 2),
            "Change (%)": round((hash(symbol) % 10) - 4.5, 2),
            "RSI": round(30 + (hash(symbol) % 50), 1),
            "Signal": "BUY" if (hash(symbol) % 2 == 0) else "HOLD",
        }
    except Exception as e:
        return {"Symbol": symbol, "Error": str(e)}


# Fetching Data Parallel dengan ThreadPoolExecutor
def fetch_all_tickers(ticker_list, max_workers=10):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    total = len(ticker_list)

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:
        future_to_ticker = {
            executor.submit(process_single_ticker, ticker): ticker
            for ticker in ticker_list
        }

        for i, future in enumerate(
            concurrent.futures.as_completed(future_to_ticker)
        ):
            ticker = future_to_ticker[future]
            try:
                data = future.result()
                results.append(data)
            except Exception as exc:
                results.append({"Symbol": ticker, "Error": str(exc)})

            # Update progress UI
            progress = (i + 1) / total
            progress_bar.progress(progress)
            status_text.text(f"Processing ({i + 1}/{total}): {ticker}")

    status_text.empty()
    progress_bar.empty()
    return pd.DataFrame(results)


# ==========================================
# 3. CONTROLS & SIDEBAR
# ==========================================
st.sidebar.header("⚙️ Configuration")
raw_tickers = st.sidebar.text_area(
    "Masukkan Ticker (Pisahkan dengan koma/baris baru):",
    value="BBCA, BBRI, BMRI, TLKM, ASII, UNVR, GOTO, ICBP, ADRO, PTBA",
    height=150,
)

# Clean up ticker input
ticker_list = [
    t.strip().upper()
    for t in raw_tickers.replace("\n", ",").split(",")
    if t.strip()
]

run_button = st.sidebar.button("🚀 Run Screener")

# ==========================================
# 4. MAIN WORKFLOW & SESSION STATE
# ==========================================
if "screener_df" not in st.session_state:
    st.session_state.screener_df = None

if run_button:
    if not ticker_list:
        st.warning("Silakan masukkan minimal satu ticker.")
    else:
        with st.spinner("Fetching & Analyzing Data..."):
            df_result = fetch_all_tickers(ticker_list)
            st.session_state.screener_df = df_result

# Menampilkan Tabel jika Data Sudah Tersedia
if st.session_state.screener_df is not None:
    df = st.session_state.screener_df.copy()

    # Tambahkan kolom checkbox 'Select' jika belum ada
    if "Select" not in df.columns:
        df.insert(0, "Select", False)

    st.subheader("📊 Screening Results")

    # Data Editor untuk Checkbox UI
    edited_df = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Pilih",
                help="Pilih saham untuk analisis lanjutan",
                default=False,
            )
        },
        disabled=[col for col in df.columns if col != "Select"],
    )

    # PERBAIKAN BUG: Ambil baris terpilih berdasarkan indeks yang valid
    selected_indices = edited_df[edited_df["Select"] == True].index
    df_selected_full = df.loc[selected_indices]

    # Display statistik saham terpilih
    if not df_selected_full.empty:
        st.markdown("---")
        st.subheader("🎯 Selected Tickers Summary")
        st.dataframe(
            df_selected_full.drop(columns=["Select"]),
            use_container_width=True,
        )

        selected_symbols = df_selected_full["Symbol"].tolist()
        st.success(f"Saham terpilih: {', '.join(selected_symbols)}")
    else:
        st.info("Centang kotak 'Select' pada tabel di atas untuk memilih saham.")
