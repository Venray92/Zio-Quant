import json
import os
import pandas as pd
import streamlit as st
import yfinance as yf

# Import fungsi render dari ui_helpers
from utils.ui_helpers import render_inline_trade_planner

STORAGE_FILE = "watchlist_storage.json"


# ==========================================
# FUNGSIONALITAS DATA & STORAGE
# ==========================================
def load_watchlist_from_file():
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return [
        {
            "Ticker": "BBCA.JK",
            "Notes": "Pantau area support 9800",
            "Target Price": 10500,
        },
        {
            "Ticker": "TLKM.JK",
            "Notes": "Tunggu konfirmasi breakout",
            "Target Price": 3200,
        },
    ]


def save_watchlist_to_file(data):
    try:
        with open(STORAGE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")


@st.cache_data(ttl=60)
def fetch_stock_quote(ticker_symbol):
    try:
        symbol = (
            ticker_symbol
            if ticker_symbol.endswith(".JK")
            else f"{ticker_symbol}.JK"
        )
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
    st.session_state["input_search_ticker_field"] = ""


# ==========================================
# MAIN RENDER FUNCTION
# ==========================================
def render_page_watchlist():
    # Inisialisasi Session State
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
    # Session state untuk menyimpan saham yang aktif dipilih
    if "selected_watchlist_ticker" not in st.session_state:
        st.session_state["selected_watchlist_ticker"] = None

    # Fetch Real-time Data
    for item in st.session_state["watchlist_data"]:
        lp, chg = fetch_stock_quote(item["Ticker"])
        item["Last Price"] = (
            lp if lp is not None else item.get("Last Price", 0.0)
        )
        item["Change Pct"] = (
            chg if chg is not None else item.get("Change Pct", 0.0)
        )

    # Header
    st.title("📈 Watchlist Saham Pro")

    # Main Layout Split
    col_left, col_right = st.columns([1.2, 1.8], gap="large")

    # ==========================================
    # KIRI: DAFTAR KARTU SAHAM
    # ==========================================
    with col_left:
        st.subheader("Daftar Pantauan")

        # Action Toolbar
        h_col1, h_col2, h_col3 = st.columns([1, 1, 1])

        with h_col1:
            with st.popover("➕ Tambah", use_container_width=True):
                st.caption("Quick Add Ticker")
                inputs = []
                ver = st.session_state["add_form_version"]

                for i in range(st.session_state["quick_add_count"]):
                    val = (
                        st.text_input(
                            f"Ticker #{i+1}",
                            key=f"quick_t_{i}_v{ver}",
                            placeholder="BBRI",
                        )
                        .strip()
                        .upper()
                    )
                    if val:
                        inputs.append(val)

                c_add, c_save = st.columns(2)
                with c_add:
                    if st.button(
                        "＋ Baris",
                        key="btn_add_more_field",
                        use_container_width=True,
                    ):
                        st.session_state["quick_add_count"] += 1
                        st.rerun()
                with c_save:
                    if st.button(
                        "Simpan",
                        key="btn_quick_add_save",
                        type="primary",
                        use_container_width=True,
                    ):
                        if inputs:
                            added_count = 0
                            existing_tickers = [
                                x["Ticker"]
                                for x in st.session_state["watchlist_data"]
                            ]
                            for ticker in inputs:
                                if (
                                    len(st.session_state["watchlist_data"])
                                    < 50
                                ):
                                    formatted = (
                                        ticker
                                        if ticker.endswith(".JK")
                                        else f"{ticker}.JK"
                                    )
                                    if formatted not in existing_tickers:
                                        st.session_state[
                                            "watchlist_data"
                                        ].append({
                                            "Ticker": formatted,
                                            "Notes": "Quick Added",
                                            "Target Price": 0,
                                        })
                                        added_count += 1

                            save_watchlist_to_file(
                                st.session_state["watchlist_data"]
                            )
                            st.session_state["add_form_version"] += 1
                            st.session_state["quick_add_count"] = 1
                            st.toast(
                                f"{added_count} Saham ditambahkan!", icon="🚀"
                            )
                            st.rerun()

        with h_col2:
            with st.popover("🗑️ Kelola", use_container_width=True):
                st.caption("Batch Delete")
                st.session_state["enable_batch_delete"] = st.checkbox(
                    "Mode Hapus",
                    value=st.session_state["enable_batch_delete"],
                    key="chk_enable_batch_del",
                )
                if st.session_state["enable_batch_delete"]:
                    if st.button(
                        "Hapus Terpilih",
                        key="btn_execute_batch_delete",
                        type="primary",
                        use_container_width=True,
                    ):
                        if st.session_state["selected_cards"]:
                            to_remove = list(
                                st.session_state["selected_cards"]
                            )
                            st.session_state["watchlist_data"] = [
                                x
                                for x in st.session_state["watchlist_data"]
                                if x["Ticker"] not in to_remove
                            ]
                            save_watchlist_to_file(
                                st.session_state["watchlist_data"]
                            )
                            st.session_state["selected_cards"].clear()
                            st.toast("Saham berhasil dihapus!", icon="🗑️")
                            st.rerun()

        with h_col3:
            with st.popover("⚡ Sort", use_container_width=True):
                st.caption("Urutkan Tampilan")
                st.session_state["sort_filter"] = st.selectbox(
                    "Sort By",
                    [
                        "Default",
                        "Gainers (% High)",
                        "Losers (% Low)",
                        "Price High",
                        "Price Low",
                    ],
                    label_visibility="collapsed",
                )

        # Search Bar
        search_val = st.session_state["input_search_ticker_field"].strip().upper()
        if search_val:
            c_search, c_clear = st.columns([3.2, 0.8])
        else:
            c_search = st.container()
            c_clear = None

        with c_search:
            st.text_input(
                "Search",
                placeholder="🔍 Cari kode saham...",
                label_visibility="collapsed",
                key="input_search_ticker_field",
            )

        if c_clear is not None:
            with c_clear:
                st.button(
                    "✕",
                    key="btn_clear_search_act",
                    use_container_width=True,
                    on_click=clear_search_callback,
                )

        # Filtering & Sorting
        display_list = list(st.session_state["watchlist_data"])
        if search_val:
            display_list = [
                x for x in display_list if search_val in x["Ticker"]
            ]

        if st.session_state["sort_filter"] == "Gainers (% High)":
            display_list.sort(
                key=lambda x: x.get("Change Pct", 0), reverse=True
            )
        elif st.session_state["sort_filter"] == "Losers (% Low)":
            display_list.sort(key=lambda x: x.get("Change Pct", 0))
        elif st.session_state["sort_filter"] == "Price High":
            display_list.sort(key=lambda x: x.get("Last Price", 0), reverse=True)
        elif st.session_state["sort_filter"] == "Price Low":
            display_list.sort(key=lambda x: x.get("Last Price", 0))

        # List Kartu Saham Kustom
        with st.container(height=550):
            if display_list:
                # Pilih saham pertama sebagai default jika belum ada yang dipilih
                if not st.session_state["selected_watchlist_ticker"]:
                    st.session_state["selected_watchlist_ticker"] = display_list[0]["Ticker"]

                for idx, item in enumerate(display_list):
                    ticker_raw = item["Ticker"]
                    clean_ticker = ticker_raw.replace(".JK", "").upper()
                    last_price = item.get("Last Price", 0.0)
                    pct_change = item.get("Change Pct", 0.0)

                    if pct_change > 0:
                        color_code = "#00C853"
                        bg_code = "#E8F5E9"
                        prefix = "+"
                    elif pct_change < 0:
                        color_code = "#D50000"
                        bg_code = "#FFEBEE"
                        prefix = ""
                    else:
                        color_code = "#757575"
                        bg_code = "#F5F5F5"
                        prefix = ""

                    price_str = f"Rp {int(last_price):,}" if last_price else "-"
                    pct_str = (
                        f"{prefix}{pct_change:.2f}%" if last_price else "-"
                    )

                    if st.session_state["enable_batch_delete"]:
                        c_chk, c_card = st.columns([0.4, 3.6])
                        with c_chk:
                            is_checked = st.checkbox(
                                "",
                                key=f"card_chk_{clean_ticker}_{idx}",
                                value=ticker_raw
                                in st.session_state["selected_cards"],
                            )
                            if is_checked:
                                st.session_state["selected_cards"].add(
                                    ticker_raw
                                )
                            else:
                                st.session_state["selected_cards"].discard(
                                    ticker_raw
                                )
                    else:
                        c_card = st.container()

                    with c_card:
                        st.markdown(
                            f"""
                            <div style="
                                border: 1px solid #E0E0E0; 
                                border-left: 5px solid {color_code}; 
                                border-radius: 8px 8px 0px 0px; 
                                padding: 10px 14px; 
                                display: flex; 
                                justify-content: space-between; 
                                align-items: center;
                                background-color: #FFFFFF;">
                                <div>
                                    <span style="font-weight: bold; font-size: 16px; color: #212121;">{clean_ticker}</span>
                                    <span style="font-size: 10px; color: #9E9E9E; margin-left: 5px;">IDX</span>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-weight: bold; font-size: 14px; color: #212121;">{price_str}</div>
                                    <div style="
                                        font-size: 11px; 
                                        font-weight: bold; 
                                        color: {color_code}; 
                                        background-color: {bg_code}; 
                                        padding: 2px 6px; 
                                        border-radius: 4px; 
                                        display: inline-block;">
                                        {pct_str}
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Tombol Klik untuk Membuka Trade Plan di Sebelah Kanan
                        is_active = (st.session_state["selected_watchlist_ticker"] == ticker_raw)
                        btn_label = "📍 Aktif Dilihat" if is_active else "📊 Trade Plan"
                        
                        if st.button(
                            btn_label,
                            key=f"btn_select_{clean_ticker}_{idx}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary",
                        ):
                            st.session_state["selected_watchlist_ticker"] = ticker_raw
                            st.rerun()

                        st.write("") # Margin antar kartu
            else:
                st.caption("Tidak ada saham yang ditemukan.")

    # ==========================================
    # KANAN: LIVE TRADE PLAN SAHAM TERPILIH
    # ==========================================
    with col_right:
        selected_ticker = st.session_state.get("selected_watchlist_ticker")

        if selected_ticker:
            # Panggil fungsi Live Trade Plan dari ui_helpers
            render_inline_trade_planner(
                ticker_symbol=selected_ticker,
                key_suffix=f"wl_{selected_ticker.replace('.', '_')}"
            )
        else:
            st.info("Pilih salah satu saham dari daftar pantauan di sebelah kiri.")
