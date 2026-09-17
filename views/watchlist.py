import streamlit as st
import pandas as pd

def render_page_watchlist():
    # 1. Header Halaman Watchlist
    st.markdown("### 📌 Stock Watchlist")
    st.caption("Pantau daftar saham pilihan Anda secara real-time.")

    # 2. Inisialisasi Session State untuk Data Watchlist
    if "watchlist_data" not in st.session_state:
        st.session_state["watchlist_data"] = [
            {"Ticker": "BBCA.JK", "Notes": "Pantau area support 9800", "Target Price": 10500},
            {"Ticker": "TLKM.JK", "Notes": "Tunggu konfirmasi breakout", "Target Price": 3200},
        ]

    # 3. Form Input Saham Baru
    with st.expander("➕ Tambah Saham ke Watchlist", expanded=False):
        with st.form(key="add_watchlist_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_ticker = st.text_input("Kode Ticker (Contoh: BBNI.JK)", value="").strip().upper()
            with col2:
                new_target = st.number_input("Target Price", min_value=0, step=50)
            
            new_notes = st.text_area("Catatan Strategi", value="")
            submit_button = st.form_submit_button(label="Simpan ke Watchlist", use_container_width=True)

            if submit_button:
                if new_ticker:
                    st.session_state["watchlist_data"].append({
                        "Ticker": new_ticker,
                        "Notes": new_notes,
                        "Target Price": new_target
                    })
                    st.success(f"{new_ticker} berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.warning("Kode Ticker tidak boleh kosong.")

    # 4. Tampilan Tabel Watchlist
    if st.session_state["watchlist_data"]:
        df_watchlist = pd.DataFrame(st.session_state["watchlist_data"])
        
        st.dataframe(
            df_watchlist,
            use_container_width=True,
            hide_index=True
        )
        
        # Tombol Clear All Data
        if st.button("🗑️ Hapus Semua Watchlist", type="secondary"):
            st.session_state["watchlist_data"] = []
            st.rerun()
    else:
        st.info("Watchlist Anda masih kosong. Tambahkan saham menggunakan form di atas.")