import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os

STORAGE_FILE = "watchlist_storage.json"

# ==========================================
# FUNGSIONALITAS SIMPAN & BACA PERMANEN (FILE JSON)
# ==========================================
def load_watchlist_from_file():
    """Membaca data watchlist dari file JSON agar tahan refresh."""
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return [
        {"Ticker": "BBCA.JK", "Notes": "Pantau area support 9800", "Target Price": 10500},
        {"Ticker": "TLKM.JK", "Notes": "Tunggu konfirmasi breakout", "Target Price": 3200},
    ]

def save_watchlist_to_file(data):
    """Menyimpan data watchlist ke file JSON."""
    try:
        with open(STORAGE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")

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


def clear_search_callback():
    """Callback untuk mengosongkan input pencarian"""
    st.session_state["input_search_ticker_field"] = ""


def render_page_watchlist():
    # CSS Custom: Sembunyikan Panah Popover, Rapatkan Tombol ke Kanan
    st.markdown(
        """
        <style>
        /* Hilangkan panah dropdown bawaan popover Streamlit */
        div[data-testid="stPopover"] div[aria-expanded="false"] svg,
        div[data-testid="stPopover"] div[aria-expanded="true"] svg {
            display: none !important;
        }
        
        /* Hilangkan gap bawaan Streamlit */
        [data-testid="stVerticalBlock"] > [data-testid="stBlock"] {
            gap: 0.2rem !important;
            margin-bottom: 0px !important;
        }
        
        /* Styling Popover Header: Rata Tengah & Mentok Kanan */
        div[data-testid="stPopover"] > button {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
            width: 100% !important;
            background: #161B22 !important;
            border: 1px solid #30363D !important;
            padding: 4px 0px !important;
            color: #9ECBFF !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            border-radius: 6px !important;
            box-shadow: none !important;
        }
        
        div[data-testid="stPopover"] > button:hover {
            color: #00E676 !important;
            border-color: #00E676 !important;
            background: #21262D !important;
        }

        /* Layout Input Search & Clear Button */
        div[data-testid="stTextInput"] {
            margin-top: 0px !important;
            margin-bottom: 0px !important;
        }

        /* Checkbox Warna Hijau & Align Tengah */
        div[data-testid="stCheckbox"] {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            margin: 0px auto !important;
            padding-top: 8px !important;
        }
        
        div[data-testid="stCheckbox"] input[type="checkbox"]:checked {
            background-color: #00E676 !important;
            border-color: #00E676 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 1. Header Halaman Watchlist
    st.markdown("### 📌 Stock Watchlist")
    st.caption("Pantau daftar saham pilihan Anda secara real-time.")

    # 2. Inisialisasi Session State & Versi Form
    if "watchlist_data" not in st.session_state:
        st.session_state["watchlist_data"] = load_watchlist_from_file()

    if "add_form_version" not in st.session_state:
        st.session_state["add_form_version"] = 0

    if "sort_filter" not in st.session_state:
        st.session_state["sort_filter"] = "Default"
    if "selected_cards" not in st.session_state:
        st.session_state["selected_cards"] = set()
    if "quick_add_count" not in st.session_state:
        st.session_state["quick_add_count"] = 1
    if "enable_batch_delete" not in st.session_state:
        st.session_state["enable_batch_delete"] = False
    if "input_search_ticker_field" not in st.session_state:
        st.session_state["input_search_ticker_field"] = ""

    # Fetch Real-time Data
    for item in st.session_state["watchlist_data"]:
        lp, chg = fetch_stock_quote(item["Ticker"])
        item["Last Price"] = lp if lp is not None else item.get("Last Price", 0.0)
        item["Change Pct"] = chg if chg is not None else item.get("Change Pct", 0.0)

    # 3. Layout Utama
    col_left, col_right = st.columns([1.2, 2.3])

    # ==========================================
    # KIRI: DAFTAR SAHAM
    # ==========================================
    with col_left:
        # Header Row: Badge "Watchlist" (lebar) + 3 Tombol Dirapatkan ke Kanan
        h_col1, h_col2, h_col3, h_col4 = st.columns([2.5, 0.5, 0.5, 0.5])
        
        with h_col1:
            st.markdown(
                """
                <span style="background: #064E3B; color: #00E676; border: 1px solid #10B981; 
                             padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; display: inline-block;">
                    Watchlist
                </span>
                """,
                unsafe_allow_html=True,
            )
            
        with h_col2:
            # Popover Tombol Tambah (+)
            with st.popover("＋"):
                st.markdown("<div style='text-align:center;'><b>Tambah Saham Quick</b></div>", unsafe_allow_html=True)
                
                inputs = []
                ver = st.session_state["add_form_version"]
                
                for i in range(st.session_state["quick_add_count"]):
                    input_key = f"quick_t_{i}_v{ver}"
                    val = st.text_input(
                        f"Kode Saham #{i+1}", 
                        key=input_key, 
                        placeholder="Contoh: BBRI"
                    ).strip().upper()
                    if val:
                        inputs.append(val)

                col_add_field, col_save = st.columns(2)
                with col_add_field:
                    if st.button("➕ Baris", key="btn_add_more_field", use_container_width=True):
                        st.session_state["quick_add_count"] += 1
                        st.rerun()

                with col_save:
                    if st.button("Simpan", key="btn_quick_add_save", use_container_width=True):
                        if inputs:
                            added_count = 0
                            existing_tickers = [x["Ticker"] for x in st.session_state["watchlist_data"]]
                            
                            for ticker in inputs:
                                if len(st.session_state["watchlist_data"]) < 50:
                                    formatted = ticker if ticker.endswith(".JK") else f"{ticker}.JK"
                                    if formatted not in existing_tickers:
                                        st.session_state["watchlist_data"].append({
                                            "Ticker": formatted,
                                            "Notes": "Quick Added",
                                            "Target Price": 0
                                        })
                                        added_count += 1
                            
                            save_watchlist_to_file(st.session_state["watchlist_data"])
                            st.session_state["add_form_version"] += 1
                            st.session_state["quick_add_count"] = 1
                            st.toast(f"{added_count} Saham berhasil ditambahkan!", icon="🚀")
                            st.rerun()
                        else:
                            st.warning("Masukkan kode saham!")

        with h_col3:
            # Popover Tombol Hapus (✕)
            with st.popover("✕"):
                st.markdown("<div style='text-align:center;'><b>Pengaturan Hapus</b></div>", unsafe_allow_html=True)
                
                st.session_state["enable_batch_delete"] = st.checkbox(
                    "Aktifkan Batch Delete", 
                    value=st.session_state["enable_batch_delete"],
                    key="chk_enable_batch_del"
                )

                if st.session_state["enable_batch_delete"]:
                    if st.button("Hapus Tercentang", key="btn_execute_batch_delete", use_container_width=True):
                        if st.session_state["selected_cards"]:
                            to_remove = list(st.session_state["selected_cards"])
                            st.session_state["watchlist_data"] = [
                                x for x in st.session_state["watchlist_data"] if x["Ticker"] not in to_remove
                            ]
                            save_watchlist_to_file(st.session_state["watchlist_data"])
                            st.session_state["selected_cards"].clear()
                            st.toast("Saham terpilih berhasil dihapus!", icon="🗑️")
                            st.rerun()
                        else:
                            st.warning("Belum ada saham yang dicentang.")

        with h_col4:
            # Popover Tombol Filter Teks
            with st.popover("Filter"):
                st.markdown("<div style='text-align:center;'><b>Filter & Urutkan</b></div>", unsafe_allow_html=True)
                st.session_state["sort_filter"] = st.selectbox(
                    "Urutkan", 
                    ["Default", "Gainers (% High)", "Losers (% Low)", "Price High", "Price Low"]
                )

        # Baris Pencarian Saham & Clear Button (❌)
        search_val = st.session_state["input_search_ticker_field"].strip().upper()

        if search_val:
            c_search, c_clear = st.columns([3.3, 0.7])
        else:
            c_search = st.container()
            c_clear = None

        with c_search:
            st.text_input(
                "Cari Kode", 
                placeholder="🔍 Cari kode saham...", 
                label_visibility="collapsed",
                key="input_search_ticker_field"
            )

        if c_clear is not None:
            with c_clear:
                st.button(
                    "❌", 
                    key="btn_clear_search_act", 
                    help="", 
                    use_container_width=True,
                    on_click=clear_search_callback
                )

        # Filter List Saham
        display_list = list(st.session_state["watchlist_data"])
        if search_val:
            display_list = [x for x in display_list if search_val in x["Ticker"]]

        if st.session_state["sort_filter"] == "Gainers (% High)":
            display_list.sort(key=lambda x: x.get("Change Pct", 0), reverse=True)
        elif st.session_state["sort_filter"] == "Losers (% Low)":
            display_list.sort(key=lambda x: x.get("Change Pct", 0))
        elif st.session_state["sort_filter"] == "Price High":
            display_list.sort(key=lambda x: x.get("Last Price", 0), reverse=True)
        elif st.session_state["sort_filter"] == "Price Low":
            display_list.sort(key=lambda x: x.get("Last Price", 0))

        # Container Scroll Kartu Saham (Fixed Height)
        with st.container(height=420):
            if display_list:
                for idx, item in enumerate(display_list):
                    ticker_raw = item["Ticker"]
                    clean_ticker = ticker_raw.replace(".JK", "").upper()
                    last_price = item.get("Last Price", 0.0)
                    pct_change = item.get("Change Pct", 0.0)

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

                    if st.session_state["enable_batch_delete"]:
                        c_chk, c_card = st.columns([0.4, 3.6])
                        with c_chk:
                            is_checked = st.checkbox(
                                "", 
                                key=f"card_chk_{clean_ticker}_{idx}",
                                value=ticker_raw in st.session_state["selected_cards"]
                            )
                            if is_checked:
                                st.session_state["selected_cards"].add(ticker_raw)
                            else:
                                st.session_state["selected_cards"].discard(ticker_raw)
                    else:
                        c_card = st.container()

                    with c_card:
                        card_html = f"""
                        <div style="display: flex; align-items: center; justify-content: space-between; 
                                    background: #0D1117; padding: 6px 10px; border-radius: 6px; 
                                    margin-bottom: 4px; border-bottom: 1px solid #21262D;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <div style="background: rgba(56, 189, 248, 0.15); color: #38BDF8; 
                                            font-size: 9px; font-weight: 800; padding: 3px 5px; 
                                            border-radius: 4px; border: 1px solid rgba(56, 189, 248, 0.3);">
                                    IDX
                                </div>
                                <div>
                                    <div style="font-size: 13px; font-weight: 800; color: #F0F6FC;">{clean_ticker}</div>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 12px; font-weight: 800; color: #F0F6FC;">{price_str}</div>
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
                        save_watchlist_to_file(st.session_state["watchlist_data"])
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
            
            if st.button("🗑️ Hapus Semua Watchlist", type="secondary", use_container_width=True):
                st.session_state["watchlist_data"] = []
                save_watchlist_to_file([])
                st.session_state["selected_cards"].clear()
                st.rerun()
        else:
            st.info("Watchlist Anda masih kosong. Tambahkan saham menggunakan tombol di atas.")
