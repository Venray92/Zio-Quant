import json
import os
import pandas as pd
import streamlit as st
import yfinance as yf

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
    # Modern Custom CSS Styling
    st.markdown(
        """
        <style>
        /* Global Font & Background adjustments */
        .stApp {
            background-color: #0B0E14;
        }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #0B0E14;
        }
        ::-webkit-scrollbar-thumb {
            background: #1F2937;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #374151;
        }

        /* Glassmorphism Cards */
        .stock-card {
            background: rgba(17, 24, 39, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 8px;
            transition: all 0.2s ease-in-out;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .stock-card:hover {
            border-color: rgba(0, 230, 118, 0.4);
            transform: translateY(-1px);
            background: rgba(31, 41, 55, 0.8);
        }

        /* Popover Styling */
        div[data-testid="stPopover"] > button {
            background: #1F2937 !important;
            border: 1px solid #374151 !important;
            border-radius: 8px !important;
            color: #E5E7EB !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stPopover"] > button:hover {
            border-color: #00E676 !important;
            color: #00E676 !important;
            box-shadow: 0 0 10px rgba(0, 230, 118, 0.2);
        }
        
        /* Remove popover arrow */
        div[data-testid="stPopover"] div[aria-expanded="false"] svg,
        div[data-testid="stPopover"] div[aria-expanded="true"] svg {
            display: none !important;
        }

        /* Input Custom Styling */
        div[data-testid="stTextInput"] input {
            background-color: #111827 !important;
            border: 1px solid #374151 !important;
            border-radius: 8px !important;
            color: #F3F4F6 !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #00E676 !important;
            box-shadow: 0 0 8px rgba(0, 230, 118, 0.3) !important;
        }

        /* Badge Styling */
        .idx-badge {
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(56, 189, 248, 0.05));
            color: #38BDF8;
            font-size: 10px;
            font-weight: 800;
            padding: 3px 6px;
            border-radius: 4px;
            border: 1px solid rgba(56, 189, 248, 0.3);
            letter-spacing: 0.5px;
        }
        
        /* Metric Box */
        .metric-container {
            background: #111827;
            border: 1px solid #1F2937;
            border-radius: 10px;
            padding: 12px 16px;
            text-align: left;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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

    # Fetch Real-time Data
    for item in st.session_state["watchlist_data"]:
        lp, chg = fetch_stock_quote(item["Ticker"])
        item["Last Price"] = (
            lp if lp is not None else item.get("Last Price", 0.0)
        )
        item["Change Pct"] = (
            chg if chg is not None else item.get("Change Pct", 0.0)
        )

    # 1. Header Section
    st.markdown("### 📊 Market Watchlist Pro")

    # Metrics Summary Row
    if st.session_state["watchlist_data"]:
        valid_items = [
            x
            for x in st.session_state["watchlist_data"]
            if x.get("Last Price", 0) > 0
        ]
        total_items = len(st.session_state["watchlist_data"])

        top_gainer = (
            max(valid_items, key=lambda x: x.get("Change Pct", -999))
            if valid_items
            else None
        )
        top_loser = (
            min(valid_items, key=lambda x: x.get("Change Pct", 999))
            if valid_items
            else None
        )

        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div style="font-size: 11px; color: #9CA3AF; font-weight: 600;">TOTAL WATCHLIST</div>
                    <div style="font-size: 18px; color: #F3F4F6; font-weight: 700; margin-top:2px;">{total_items} <span style="font-size:12px; color:#6B7280;">/ 50</span></div>
                </div>
            """,
                unsafe_allow_html=True,
            )
        with m2:
            g_ticker = (
                top_gainer["Ticker"].replace(".JK", "") if top_gainer else "-"
            )
            g_pct = top_gainer.get("Change Pct", 0.0) if top_gainer else 0.0
            st.markdown(
                f"""
                <div class="metric-container">
                    <div style="font-size: 11px; color: #9CA3AF; font-weight: 600;">TOP GAINER</div>
                    <div style="font-size: 18px; color: #00E676; font-weight: 700; margin-top:2px;">{g_ticker} <span style="font-size:13px;">(+{g_pct:.2f}%)</span></div>
                </div>
            """,
                unsafe_allow_html=True,
            )
        with m3:
            l_ticker = (
                top_loser["Ticker"].replace(".JK", "") if top_loser else "-"
            )
            l_pct = top_loser.get("Change Pct", 0.0) if top_loser else 0.0
            st.markdown(
                f"""
                <div class="metric-container">
                    <div style="font-size: 11px; color: #9CA3AF; font-weight: 600;">TOP LOSER</div>
                    <div style="font-size: 18px; color: #FF5252; font-weight: 700; margin-top:2px;">{l_ticker} <span style="font-size:13px;">({l_pct:.2f}%)</span></div>
                </div>
            """,
                unsafe_allow_html=True,
            )

    st.write("")

    # 2. Main Layout Split
    col_left, col_right = st.columns([1.1, 1.9], gap="medium")

    # ==========================================
    # KIRI: DAFTAR KARTU SAHAM
    # ==========================================
    with col_left:
        # Action Toolbar
        h_col1, h_col2, h_col3 = st.columns([1, 1, 1])

        with h_col1:
            with st.popover("➕ Tambah", use_container_width=True):
                st.markdown(
                    "<div style='text-align:center; padding-bottom:8px;'><b>Quick Add</b></div>",
                    unsafe_allow_html=True,
                )
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
                st.markdown(
                    "<div style='text-align:center; padding-bottom:8px;'><b>Batch Delete</b></div>",
                    unsafe_allow_html=True,
                )
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
                st.markdown(
                    "<div style='text-align:center; padding-bottom:8px;'><b>Urutkan</b></div>",
                    unsafe_allow_html=True,
                )
                st.session_state["sort_filter"] = st.selectbox(
                    "Berdasarkan",
                    [
                        "Default",
                        "Gainers (% High)",
                        "Losers (% Low)",
                        "Price High",
                        "Price Low",
                    ],
                    label_visibility="collapsed",
                )

        # Search Bar Row
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

        # Apply Filtering & Sorting
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

        # Cards Scroll Container
        with st.container(height=430):
            if display_list:
                for idx, item in enumerate(display_list):
                    ticker_raw = item["Ticker"]
                    clean_ticker = ticker_raw.replace(".JK", "").upper()
                    last_price = item.get("Last Price", 0.0)
                    pct_change = item.get("Change Pct", 0.0)

                    if pct_change > 0:
                        chg_color = "#00E676"
                        bg_badge = "rgba(0, 230, 118, 0.1)"
                        chg_prefix = "+"
                        icon = "▲ "
                    elif pct_change < 0:
                        chg_color = "#FF5252"
                        bg_badge = "rgba(255, 82, 82, 0.1)"
                        chg_prefix = ""
                        icon = "▼ "
                    else:
                        chg_color = "#9CA3AF"
                        bg_badge = "rgba(156, 163, 175, 0.1)"
                        chg_prefix = ""
                        icon = ""

                    price_str = f"{int(last_price):,}" if last_price else "-"
                    pct_str = (
                        f"{icon}{chg_prefix}{pct_change:.2f}%"
                        if last_price
                        else "-"
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
                            <div class="stock-card">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span class="idx-badge">IDX</span>
                                    <div>
                                        <div style="font-size: 14px; font-weight: 700; color: #F9FAFB;">{clean_ticker}</div>
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 13px; font-weight: 700; color: #F3F4F6;">{price_str}</div>
                                    <div style="font-size: 11px; font-weight: 700; color: {chg_color}; background: {bg_badge}; padding: 1px 6px; border-radius: 4px; display: inline-block; margin-top: 2px;">
                                        {pct_str}
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            else:
                st.caption("Tidak ada saham yang cocok.")

    # ==========================================
    # KANAN: FORM DETAIL & DATA TABEL PRO
    # ==========================================
    with col_right:
        with st.expander("➕ Tambah Saham Lengkap & Catatan Strategi"):
            with st.form(key="add_watchlist_form_full", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    new_ticker = (
                        st.text_input("Kode Ticker", placeholder="Contoh: BBNI")
                        .strip()
                        .upper()
                    )
                with c2:
                    new_target = st.number_input(
                        "Target Price (Rp)", min_value=0, step=50
                    )

                new_notes = st.text_area(
                    "Catatan Strategi & Technical Setup",
                    placeholder="Contoh: Entry area breakout 5200...",
                    height=80,
                )
                submit_button = st.form_submit_button(
                    label="Simpan ke Watchlist",
                    use_container_width=True,
                    type="primary",
                )

                if submit_button:
                    if len(st.session_state["watchlist_data"]) >= 50:
                        st.error("Gagal! Kuota Watchlist penuh (Maksimal 50).")
                    elif new_ticker:
                        formatted_t = (
                            new_ticker
                            if new_ticker.endswith(".JK")
                            else f"{new_ticker}.JK"
                        )
                        st.session_state["watchlist_data"].append({
                            "Ticker": formatted_t,
                            "Notes": new_notes,
                            "Target Price": new_target,
                        })
                        save_watchlist_to_file(
                            st.session_state["watchlist_data"]
                        )
                        st.toast(
                            f"{formatted_t} berhasil ditambahkan!", icon="✅"
                        )
                        st.rerun()
                    else:
                        st.warning("Kode Ticker wajib diisi.")

        # Table Display
        if st.session_state["watchlist_data"]:
            df_watchlist = pd.DataFrame(st.session_state["watchlist_data"])

            # Clean Up Ticker Display Name
            df_watchlist["Ticker"] = df_watchlist["Ticker"].str.replace(
                ".JK", ""
            )

            cols_show = [
                "Ticker",
                "Last Price",
                "Change Pct",
                "Target Price",
                "Notes",
            ]
            existing_cols = [
                c for c in cols_show if c in df_watchlist.columns
            ]
            df_display = df_watchlist[existing_cols]

            # Streamlit Interactive Dataframe dengan Formatting Canggih
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Ticker": st.column_config.TextColumn(
                        "Kode", help="Kode saham IDX", width="medium"
                    ),
                    "Last Price": st.column_config.NumberColumn(
                        "Harga Terakhir", format="Rp %'d"
                    ),
                    "Change Pct": st.column_config.NumberColumn(
                        "Perubahan (%)", format="%.2f%%"
                    ),
                    "Target Price": st.column_config.NumberColumn(
                        "Target Price", format="Rp %'d"
                    ),
                    "Notes": st.column_config.TextColumn(
                        "Catatan Strategi", width="large"
                    ),
                },
            )

            st.write("")
            if st.button(
                "🗑️ Hapus Semua Data Watchlist",
                type="secondary",
                use_container_width=True,
            ):
                st.session_state["watchlist_data"] = []
                save_watchlist_to_file([])
                st.session_state["selected_cards"].clear()
                st.toast("Watchlist dibersihkan!", icon="🧹")
                st.rerun()
        else:
            st.info(
                "Watchlist Anda masih kosong. Tambahkan saham untuk memulai."
            )
