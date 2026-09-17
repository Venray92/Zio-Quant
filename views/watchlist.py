import streamlit as st
import pandas as pd

def render_page_watchlist():
    # 1. Header Halaman Watchlist
    st.markdown("### 📌 Stock Watchlist")
    st.caption("Pantau daftar saham pilihan Anda secara real-time.")

    # 2. Inisialisasi & Sinkronisasi Session State
    if "watchlist_data" not in st.session_state:
        st.session_state["watchlist_data"] = [
            {"Ticker": "BBCA.JK", "Notes": "Pantau area support 9800", "Target Price": 10500},
            {"Ticker": "TLKM.JK", "Notes": "Tunggu konfirmasi breakout", "Target Price": 3200},
        ]

    # Sinkronkan jika ada saham yang di-add dari ui_helpers.py via st.session_state["watchlist"]
    if "watchlist" in st.session_state and st.session_state["watchlist"]:
        existing_tickers = [item["Ticker"] for item in st.session_state["watchlist_data"]]
        for t in st.session_state["watchlist"]:
            if t not in existing_tickers and len(st.session_state["watchlist_data"]) < 50:
                st.session_state["watchlist_data"].append({
                    "Ticker": t,
                    "Notes": "Added from Trade Planner",
                    "Target Price": 0
                })

    # 3. Layout Utama (Kolom Kiri: Scrollable List, Kolom Kanan: Form & Table)
    col_left, col_right = st.columns([1, 2.5])

    # ==========================================
    # KANAN: FORM INPUT & TABEL DETAIL
    # ==========================================
    with col_right:
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
                    if len(st.session_state["watchlist_data"]) >= 50:
                        st.error("Gagal! Kuota Watchlist sudah penuh (Maksimal 50 saham).")
                    elif new_ticker:
                        st.session_state["watchlist_data"].append({
                            "Ticker": new_ticker,
                            "Notes": new_notes,
                            "Target Price": new_target
                        })
                        st.success(f"{new_ticker} berhasil ditambahkan!")
                        st.rerun()
                    else:
                        st.warning("Kode Ticker tidak boleh kosong.")

        if st.session_state["watchlist_data"]:
            df_watchlist = pd.DataFrame(st.session_state["watchlist_data"])
            st.dataframe(
                df_watchlist,
                use_container_width=True,
                hide_index=True
            )
            
            if st.button("🗑️ Hapus Semua Watchlist", type="secondary"):
                st.session_state["watchlist_data"] = []
                st.session_state["watchlist"] = []
                st.rerun()
        else:
            st.info("Watchlist Anda masih kosong.")

    # ==========================================
    # KIRI: KONTAINER DAFTAR SAHAM (MAX 50 + SCROLL 100PX)
    # ==========================================
    with col_left:
        total_items = len(st.session_state["watchlist_data"])
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 700; color: #00F3FF; font-size: 14px;">📋 DAFTAR SAHAM</span>
                <span style="font-size: 11px; color: #8B949E; background: #21262D; padding: 2px 8px; border-radius: 10px;">{total_items}/50</span>
            </div>
            """, 
            unsafe_allow_html=True
        )

        # Container dengan tinggi 100px + scroll otomatis saat melebihi batas
        with st.container(height=100):
            if st.session_state["watchlist_data"]:
                for idx, item in enumerate(st.session_state["watchlist_data"]):
                    ticker = item["Ticker"]
                    c_txt, c_del = st.columns([3, 1])
                    with c_txt:
                        st.markdown(f"<span style='font-size: 13px; font-weight: 700; color: #E6EDF3;'>• {ticker}</span>", unsafe_allow_html=True)
                    with c_del:
                        if st.button("❌", key=f"del_wl_{idx}_{ticker}", help=f"Hapus {ticker}"):
                            st.session_state["watchlist_data"].pop(idx)
                            if "watchlist" in st.session_state and ticker in st.session_state["watchlist"]:
                                st.session_state["watchlist"].remove(ticker)
                            st.rerun()
            else:
                st.markdown("<div style='font-size: 11px; color: #8B949E;'>Belum ada data</div>", unsafe_allow_html=True)
