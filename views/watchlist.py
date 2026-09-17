import streamlit as st
import pandas as pd
import yfinance as yf

@st.cache_data(ttl=60)
def fetch_stock_quote(ticker_symbol):
    """Mengambil harga terakhir dan % change dari Yahoo Finance"""
    try:
        symbol = ticker_symbol if ticker_symbol.endswith(".JK") else f"{ticker_symbol}.JK"
        stock = yf.Ticker(symbol)
        fast_info = stock.fast_info
        
        last_price = fast_info.last_price
        prev_close = fast_info.previous_close
        
        if last_price and prev_close:
            pct_change = ((last_price - prev_close) / prev_close) * 100
            return float(last_price), float(pct_change)
    except Exception:
        pass
    return None, None

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

    if "watchlist" in st.session_state and st.session_state["watchlist"]:
        existing_tickers = [item["Ticker"] for item in st.session_state["watchlist_data"]]
        for t in st.session_state["watchlist"]:
            formatted_t = t if t.endswith(".JK") else f"{t}.JK"
            if formatted_t not in existing_tickers and len(st.session_state["watchlist_data"]) < 50:
                st.session_state["watchlist_data"].append({
                    "Ticker": formatted_t,
                    "Notes": "Added from Trade Planner",
                    "Target Price": 0
                })

    if "search_filter" not in st.session_state:
        st.session_state["search_filter"] = ""
    if "sort_filter" not in st.session_state:
        st.session_state["sort_filter"] = "Default"

    # Fetch Real-time Data untuk Card
    for item in st.session_state["watchlist_data"]:
        lp, chg = fetch_stock_quote(item["Ticker"])
        item["Last Price"] = lp if lp is not None else item.get("Last Price", 0.0)
        item["Change Pct"] = chg if chg is not None else item.get("Change Pct", 0.0)

    # 3. Layout Utama
    col_left, col_right = st.columns([1.2, 2.3])

    # ==========================================
    # KIRI: DAFTAR SAHAM (CARDS + SCROLL + HEADER FILTER/ADD)
    # ==========================================
    with col_left:
        total_items = len(st.session_state["watchlist_data"])
        
        # Header Row: Judul, (+) Add Button, Filter Button, Badge Counter
        h_col1, h_col2, h_col3, h_col4 = st.columns([2.2, 0.6, 0.6, 1])
        
        with h_col1:
            st.markdown("<span style='font-weight: 800; color: #00F3FF; font-size: 13px;'>📋 DAFTAR SAHAM</span>", unsafe_allow_html=True)
            
        with h_col2:
            # Popover untuk Quick Add (+)
            with st.popover("➕", help="Tambah Saham"):
                st.markdown("**Tambah Saham Quick**")
                quick_ticker = st.text_input("Kode Saham", placeholder="e.g. BBRI").strip().upper()
                if st.button("Simpan", key="btn_quick_add", use_container_width=True):
                    if len(st.session_state["watchlist_data"]) >= 50:
                        st.error("Watchlist penuh (Max 50)!")
                    elif quick_ticker:
                        formatted = quick_ticker if quick_ticker.endswith(".JK") else f"{quick_ticker}.JK"
                        st.session_state["watchlist_data"].append({
                            "Ticker": formatted,
                            "Notes": "Quick Added",
                            "Target Price": 0
                        })
                        st.rerun()

        with h_col3:
            # Popover Filter & Search
            with st.popover("🔍", help="Filter & Search"):
                st.markdown("**Filter Watchlist**")
                st.session_state["search_filter"] = st.text_input("Cari Ticker", value=st.session_state["search_filter"]).strip().upper()
                st.session_state["sort_filter"] = st.selectbox(
                    "Urutkan", 
                    ["Default", "Gainers (% High)", "Losers (% Low)", "Price High", "Price Low"]
                )

        with h_col4:
            st.markdown(f"<div style='text-align: right;'><span style='font-size: 10px; color: #8B949E; background: #21262D; padding: 2px 6px; border-radius: 8px;'>{total_items}/50</span></div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        # Processing Filter Data
        display_list = list(st.session_state["watchlist_data"])
        if st.session_state["search_filter"]:
            display_list = [x for x in display_list if st.session_state["search_filter"] in x["Ticker"]]

        if st.session_state["sort_filter"] == "Gainers (% High)":
            display_list.sort(key=lambda x: x.get("Change Pct", 0), reverse=True)
        elif st.session_state["sort_filter"] == "Losers (% Low)":
            display_list.sort(key=lambda x: x.get("Change Pct", 0))
        elif st.session_state["sort_filter"] == "Price High":
            display_list.sort(key=lambda x: x.get("Last Price", 0), reverse=True)
        elif st.session_state["sort_filter"] == "Price Low":
            display_list.sort(key=lambda x: x.get("Last Price", 0))

        # Container Panjang Fixed (420px) + Internal ScrollBar
        with st.container(height=420):
            if display_list:
                for idx, item in enumerate(display_list):
                    ticker_raw = item["Ticker"]
                    clean_ticker = ticker_raw.replace(".JK", "").upper()
                    last_price = item.get("Last Price", 0.0)
                    pct_change = item.get("Change Pct", 0.0)

                    # Tentukan warna status persentase
                    if pct_change > 0:
                        chg_color = "#00E676"
                        chg_prefix = "+"
                    elif pct_change < 0:
                        chg_color = "#FF5252"
                        chg_prefix = ""
                    else:
                        chg_color = "#8B949E"
                        chg_prefix = ""

                    price_str = f"{int(last_price):,}" if last_price else "-"
                    pct_str = f"{chg_prefix}{pct_change:.2f}%" if last_price else "-"

                    # Render UI Card Saham
                    c_card, c_del = st.columns([3.3, 0.7])
                    with c_card:
                        card_html = f"""
                        <div style="background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 8px 12px; margin-bottom: 6px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 13px; font-weight: 800; color: #F0F6FC;">{clean_ticker}</span>
                                <span style="font-size: 13px; font-weight: 700; color: #E6EDF3;">{price_str}</span>
                            </div>
                            <div style="display: flex; justify-content: flex-end; align-items: center; margin-top: 2px;">
                                <span style="font-size: 11px; font-weight: 700; color: {chg_color};">{pct_str}</span>
                            </div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                    
                    with c_del:
                        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_card_{clean_ticker}_{idx}", help=f"Hapus {clean_ticker}"):
                            st.session_state["watchlist_data"] = [
                                x for x in st.session_state["watchlist_data"] if x["Ticker"] != ticker_raw
                            ]
                            if "watchlist" in st.session_state and clean_ticker in st.session_state["watchlist"]:
                                st.session_state["watchlist"].remove(clean_ticker)
                            st.rerun()
            else:
                st.caption("Tidak ada saham yang sesuai.")

    # ==========================================
    # KANAN: FORM DETAIL & TABEL UTAMA
    # ==========================================
    with col_right:
        with st.expander("➕ Tambah Detail Saham & Catatan", expanded=False):
            with st.form(key="add_watchlist_form_full"):
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
                        formatted_t = new_ticker if new_ticker.endswith(".JK") else f"{new_ticker}.JK"
                        st.session_state["watchlist_data"].append({
                            "Ticker": formatted_t,
                            "Notes": new_notes,
                            "Target Price": new_target
                        })
                        st.success(f"{formatted_t} berhasil ditambahkan!")
                        st.rerun()
                    else:
                        st.warning("Kode Ticker tidak boleh kosong.")

        if st.session_state["watchlist_data"]:
            df_watchlist = pd.DataFrame(st.session_state["watchlist_data"])
            
            # Reorder Kolom
            cols_show = ["Ticker", "Last Price", "Change Pct", "Target Price", "Notes"]
            existing_cols = [c for c in cols_show if c in df_watchlist.columns]
            df_display = df_watchlist[existing_cols]

            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
            
            if st.button("🗑️ Hapus Semua Watchlist", type="secondary"):
                st.session_state["watchlist_data"] = []
                st.session_state["watchlist"] = []
                st.rerun()
        else:
            st.info("Watchlist Anda masih kosong. Tambahkan saham menggunakan tombol (+) atau form di atas.")
