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
    # CSS Custom untuk merapatkan gap layout & styling checkbox
    st.markdown(
        """
        <style>
        /* Hilangkan gap margin bawaan streamlit antar elemen kiri */
        div[data-testid="stVerticalBlock"] > div {
            gap: 0.3rem !important;
        }
        /* Style Icon Popover / Button Header minimalis */
        div[data-testid="stPopover"] > button, .top-header-btn > button {
            border: none !important;
            background: transparent !important;
            padding: 2px 4px !important;
            color: #9ECBFF !important;
            font-size: 16px !important;
            box-shadow: none !important;
        }
        div[data-testid="stPopover"] > button:hover, .top-header-btn > button:hover {
            color: #00E676 !important;
            background: rgba(255,255,255,0.05) !important;
        }
        /* Merapatkan margin input search */
        div[data-testid="stTextInput"] {
            margin-top: -6px !important;
            margin-bottom: 4px !important;
        }
        /* Merapatkan checkbox di dalam card */
        div[data-testid="stCheckbox"] {
            margin: 0px !important;
            padding: 0px !important;
        }
        div[data-testid="stCheckbox"] label {
            padding-left: 0px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 1. Header Halaman Watchlist
    st.markdown("### 📌 Stock Watchlist")
    st.caption("Pantau daftar saham pilihan Anda secara real-time.")

    # 2. Inisialisasi Session State
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

    if "search_kw" not in st.session_state:
        st.session_state["search_kw"] = ""
    if "sort_filter" not in st.session_state:
        st.session_state["sort_filter"] = "Default"
    if "selected_cards" not in st.session_state:
        st.session_state["selected_cards"] = set()

    # Fetch Real-time Data
    for item in st.session_state["watchlist_data"]:
        lp, chg = fetch_stock_quote(item["Ticker"])
        item["Last Price"] = lp if lp is not None else item.get("Last Price", 0.0)
        item["Change Pct"] = chg if chg is not None else item.get("Change Pct", 0.0)

    # 3. Layout Utama
    col_left, col_right = st.columns([1.2, 2.3])

    # ==========================================
    # KIRI: DAFTAR SAHAM (BATCH DELETE & NO GAP)
    # ==========================================
    with col_left:
        # Header Row: Badge "Watchlist", (+) Add, (🗑️) Batch Delete, (🎛️) Filter
        h_col1, h_col2, h_col3, h_col4 = st.columns([2.1, 0.4, 0.4, 0.4])
        
        with h_col1:
            st.markdown(
                """
                <span style="background: #064E3B; color: #00E676; border: 1px solid #10B981; 
                             padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700;">
                    Watchlist
                </span>
                """,
                unsafe_allow_html=True,
            )
            
        with h_col2:
            # Popover Icon Tambah (+)
            with st.popover("＋", help="Tambah Saham"):
                st.markdown("**Tambah Saham Quick**")
                quick_ticker = st.text_input("Kode Saham", placeholder="Contoh: BBRI").strip().upper()
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
            # Button Hapus Terpilih (🗑️) di Header Atas
            if st.button("🗑️", key="btn_batch_delete", help="Hapus Saham Tercentang"):
                if st.session_state["selected_cards"]:
                    to_remove = list(st.session_state["selected_cards"])
                    st.session_state["watchlist_data"] = [
                        x for x in st.session_state["watchlist_data"] if x["Ticker"] not in to_remove
                    ]
                    if "watchlist" in st.session_state:
                        st.session_state["watchlist"] = [
                            x for x in st.session_state["watchlist"] 
                            if f"{x}.JK" not in to_remove and x not in to_remove
                        ]
                    st.session_state["selected_cards"].clear()
                    st.toast("Saham terpilih berhasil dihapus!", icon="🗑️")
                    st.rerun()
                else:
                    st.toast("Pilih/centang saham yang ingin dihapus terlebih dahulu.", icon="⚠️")

        with h_col4:
            # Popover Icon Filter (🎛️)
            with st.popover("🎛️", help="Filter & Urutkan"):
                st.markdown("**Filter & Urutkan**")
                st.session_state["sort_filter"] = st.selectbox(
                    "Urutkan", 
                    ["Default", "Gainers (% High)", "Losers (% Low)", "Price High", "Price Low"]
                )

        # Search Bar Tanpa Gap & Auto-Reset saat Kosong
        search_input = st.text_input(
            "Cari", 
            value=st.session_state["search_kw"], 
            placeholder="🔍 Cari kode atau nama saham...", 
            label_visibility="collapsed",
            key="input_search_ticker"
        )
        # Update state keyword pencarian secara otomatis
        st.session_state["search_kw"] = search_input.strip().upper()

        # Filtering & Sorting
        display_list = list(st.session_state["watchlist_data"])
        if st.session_state["search_kw"]:
            display_list = [x for x in display_list if st.session_state["search_kw"] in x["Ticker"]]

        if st.session_state["sort_filter"] == "Gainers (% High)":
            display_list.sort(key=lambda x: x.get("Change Pct", 0), reverse=True)
        elif st.session_state["sort_filter"] == "Losers (% Low)":
            display_list.sort(key=lambda x: x.get("Change Pct", 0))
        elif st.session_state["sort_filter"] == "Price High":
            display_list.sort(key=lambda x: x.get("Last Price", 0), reverse=True)
        elif st.session_state["sort_filter"] == "Price Low":
            display_list.sort(key=lambda x: x.get("Last Price", 0))

        # Container Scrollable Fixed Height (420px)
        with st.container(height=420):
            if display_list:
                for idx, item in enumerate(display_list):
                    ticker_raw = item["Ticker"]
                    clean_ticker = ticker_raw.replace(".JK", "").upper()
                    last_price = item.get("Last Price", 0.0)
                    pct_change = item.get("Change Pct", 0.0)

                    # Tentukan warna & panah arah persentase
                    if pct_change > 0:
                        chg_color = "#00E676"
                        arrow_icon = "📈 "
                        chg_prefix = "+"
                    elif pct_change < 0:
                        chg_color = "#FF5252"
                        arrow_icon = "📉 "
                        chg_prefix = ""
                    else:
                        chg_color = "#8B949E"
                        arrow_icon = ""
                        chg_prefix = ""

                    price_str = f"{int(last_price):,}" if last_price else "-"
                    pct_str = f"{arrow_icon}{chg_prefix}{pct_change:.2f}%" if last_price else "-"

                    # Grid Card: Checkbox di Kiri + Card Info Saham
                    c_chk, c_card = st.columns([0.4, 3.6])
                    
                    with c_chk:
                        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                        is_checked = st.checkbox(
                            "", 
                            key=f"chk_{clean_ticker}_{idx}",
                            value=ticker_raw in st.session_state["selected_cards"]
                        )
                        if is_checked:
                            st.session_state["selected_cards"].add(ticker_raw)
                        else:
                            st.session_state["selected_cards"].discard(ticker_raw)

                    with c_card:
                        card_html = f"""
                        <div style="display: flex; align-items: center; justify-content: space-between; 
                                    background: #0D1117; padding: 8px 10px; border-radius: 8px; 
                                    margin-bottom: 4px; border-bottom: 1px solid #21262D;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <div style="background: rgba(56, 189, 248, 0.15); color: #38BDF8; 
                                            font-size: 9px; font-weight: 800; padding: 4px 6px; 
                                            border-radius: 4px; border: 1px solid rgba(56, 189, 248, 0.3);">
                                    IDX
                                </div>
                                <div>
                                    <div style="font-size: 13px; font-weight: 800; color: #F0F6FC;">{clean_ticker}</div>
                                    <div style="font-size: 9px; color: #8B949E; margin-top: -2px;">Indonesia Stock</div>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 13px; font-weight: 800; color: #F0F6FC;">{price_str}</div>
                                <div style="font-size: 10px; font-weight: 700; color: {chg_color};">{pct_str}</div>
                            </div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.caption("Tidak ada saham yang ditemukan.")

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
                st.session_state["selected_cards"].clear()
                st.rerun()
        else:
            st.info("Watchlist Anda masih kosong. Tambahkan saham menggunakan tombol (+) atau form di atas.")
