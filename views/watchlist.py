import os
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from engines.trade_planner import TradePlanner

STORAGE_FILE = "watchlist_storage.json"


# ==========================================
# DATA & STORAGE MANAGEMENT
# ==========================================
def load_watchlist_from_file():
    """Memuat data watchlist dari file JSON lokal."""
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r") as f:
                data = json.load(f)
                normalized = []
                for item in data:
                    if isinstance(item, str):
                        normalized.append(
                            {
                                "Ticker": item if item.endswith(".JK") else f"{item}.JK",
                                "Notes": "Watchlist",
                                "Target Price": 0,
                            }
                        )
                    elif isinstance(item, dict):
                        ticker = item.get("Ticker", "")
                        if ticker:
                            item["Ticker"] = ticker if ticker.endswith(".JK") else f"{ticker}.JK"
                            normalized.append(item)
                return normalized
        except Exception:
            pass

    return [
        {"Ticker": "BBCA.JK", "Notes": "Manual Added", "Target Price": 10500},
        {"Ticker": "TLKM.JK", "Notes": "Manual Added", "Target Price": 3200},
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
    """Mengambil harga terbaru dan persentase perubahan dari Yahoo Finance."""
    try:
        symbol = ticker_symbol if ticker_symbol.endswith(".JK") else f"{ticker_symbol}.JK"
        stock = yf.Ticker(symbol)
        fast_info = stock.fast_info

        last_price = fast_info.last_price
        prev_close = fast_info.previous_close

        if last_price and prev_close:
            pct_change = ((last_price - prev_close) / prev_close) * 100
            return float(last_price), float(pct_change)
        elif last_price:
            return float(last_price), 0.0
    except Exception:
        pass
    return None, None


def clear_search_callback():
    st.session_state["input_search_ticker_field"] = ""


# ==========================================
# TRADE PLAN HELPERS
# ==========================================
def _format_val(val):
    if pd.isna(val) or val is None or val in ["", "-"]:
        return "-"
    try:
        num = float(val)
        return f"{int(num):,}" if num.is_integer() else f"{num:,.2f}"
    except (ValueError, TypeError):
        return str(val)


def _clean_num(val):
    if pd.isna(val) or val is None or val in ["", "-"]:
        return None
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return float(val)
    except Exception:
        return None


def calculate_rr_ratios(row):
    """Menghitung rasio Risk to Reward untuk Target 1 & Target 2."""
    buy_val = _clean_num(row.get("Range Buy Max", row.get("Buy Max", row.get("Buy Min", None))))
    sl_val = _clean_num(row.get("Stop Loss", row.get("SL", None)))
    tp1_val = _clean_num(row.get("TP 1", row.get("TP1", row.get("Target 1", None))))
    tp2_val = _clean_num(row.get("TP 2", row.get("TP2", row.get("Target 2", None))))

    rr_tp1_str = "-"
    rr_tp2_str = "-"

    if buy_val and sl_val and (buy_val > sl_val):
        risk = buy_val - sl_val
        if tp1_val and tp1_val > buy_val:
            rr_tp1_str = f"1 : {((tp1_val - buy_val) / risk):.1f}"
        if tp2_val and tp2_val > buy_val:
            rr_tp2_str = f"1 : {((tp2_val - buy_val) / risk):.1f}"

    return rr_tp1_str, rr_tp2_str


def render_trade_plan_only(ticker_symbol, key_suffix):
    """Renders the Trade Plan Recommendation component for the selected ticker."""
    st.write(f"### Live Trade Plan: {ticker_symbol}")

    clean_ticker = (
        ticker_symbol.replace(".JK", "").replace("IDX:", "").strip().upper()
    )
    safe_container_id = clean_ticker.replace(".", "_")
    tv_symbol = f"IDX:{clean_ticker}"

    with st.expander(f"TradingView Chart: {ticker_symbol}", expanded=False):
        tv_html = f"""
        <div class="tradingview-widget-container" style="height:500px; width:100%;">
          <div id="tv_chart_container_{safe_container_id}" style="height:100%; width:100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          if (typeof TradingView !== 'undefined') {{
              new TradingView.widget({{
                "autosize": true,
                "symbol": "{tv_symbol}",
                "interval": "D",
                "timezone": "Asia/Jakarta",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "hide_side_toolbar": false,
                "allow_symbol_change": true,
                "save_image": true,
                "container_id": "tv_chart_container_{safe_container_id}"
              }});
          }}
          </script>
        </div>
        """
        components.html(tv_html, height=510)
        st.caption("Lakukan screenshot jika Anda membuat tarikan garis/analisa visual.")

    period_selected = "3mo"

    with st.spinner(f"Memuat data untuk {ticker_symbol}..."):
        try:
            planner = TradePlanner(ticker=ticker_symbol.upper(), period=period_selected)
            if hasattr(planner, "fetch_and_prepare_data"):
                planner.fetch_and_prepare_data()

            df_plan = (
                planner.generate_trade_plan()
                if hasattr(planner, "generate_trade_plan")
                else None
            )

            if df_plan is not None and not df_plan.empty:
                st.write("#### Trade Plan Recommendation")

                for idx, row in df_plan.iterrows():
                    plan_no = idx + 1
                    plan_type = str(row.get("Type", row.get("Strategy", f"Plan #{plan_no}")))
                    score = str(row.get("Score", 0))
                    grade = str(row.get("Grade", "N/A"))
                    posisi = str(row.get("Posisi Harga", row.get("Status", "-")))

                    range_min = _format_val(row.get("Range Buy Min", row.get("Buy Min", "-")))
                    range_max = _format_val(row.get("Range Buy Max", row.get("Buy Max", "-")))
                    area_buy = (
                        f"{range_min} - {range_max}"
                        if range_min != "-" and range_max != "-"
                        else range_min
                    )

                    stop_loss = _format_val(row.get("Stop Loss", row.get("SL", "-")))
                    tp1 = _format_val(row.get("TP 1", row.get("TP1", "-")))
                    tp2 = _format_val(row.get("TP 2", row.get("TP2", "-")))

                    prefix_label = "Suggestion" if idx == 0 else "Other"
                    expander_title = f"Plan #{plan_no} ({plan_type}) - Grade: {grade} - Score: {score}"

                    with st.expander(expander_title, expanded=False):
                        st.write(f"**Strategi:** {plan_type}")
                        st.write(f"**Grade:** {grade} | **Score:** {score}/100")
                        st.write(f"**Area Buy:** {area_buy}")
                        st.write(f"**Stop Loss:** {stop_loss}")
                        st.write(f"**Target 1 (TP1):** {tp1}")
                        st.write(f"**Target 2 (TP2):** {tp2}")
                        st.write(f"**Posisi Harga:** {posisi}")

                        rr_tp1_val, rr_tp2_val = calculate_rr_ratios(row)
                        c1, c2 = st.columns(2)
                        with c1:
                            st.metric(label="R:R (Target 1)", value=rr_tp1_val)
                        with c2:
                            st.metric(label="R:R (Target 2)", value=rr_tp2_val)

        except Exception as e:
            st.error(f"Gagal memuat Trade Plan: {e}")


# ==========================================
# MAIN RENDER FUNCTION
# ==========================================
def render_page_watchlist():
    # Menghapus paksa border hijau/glow global dari file lain khusus untuk halaman Watchlist
    st.markdown(
        """
        <style>
            .stButton > button, div[data-testid="stPopover"] > button {
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                box-shadow: none !important;
            }
            .stButton > button:hover, div[data-testid="stPopover"] > button:hover {
                border-color: rgba(255, 255, 255, 0.5) !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "watchlist_data" not in st.session_state:
        st.session_state["watchlist_data"] = load_watchlist_from_file()

    if "watchlist" in st.session_state and isinstance(st.session_state["watchlist"], list):
        existing_tickers = {x["Ticker"] for x in st.session_state["watchlist_data"]}
        has_new = False
        active_screener_name = st.session_state.get("active_screener_name", "Screener")

        for item in st.session_state["watchlist"]:
            if isinstance(item, dict):
                ticker_raw = item.get("Ticker", "")
                notes_source = item.get("Notes", item.get("Source", active_screener_name))
            else:
                ticker_raw = str(item)
                notes_source = active_screener_name

            formatted = ticker_raw if ticker_raw.endswith(".JK") else f"{ticker_raw}.JK"

            if formatted and formatted not in existing_tickers:
                st.session_state["watchlist_data"].append(
                    {
                        "Ticker": formatted,
                        "Notes": notes_source,
                        "Target Price": 0,
                    }
                )
                existing_tickers.add(formatted)
                has_new = True

        if has_new:
            save_watchlist_to_file(st.session_state["watchlist_data"])

    defaults = {
        "add_form_version": 0,
        "sort_filter": "Default",
        "selected_cards": set(),
        "quick_add_count": 1,
        "input_search_ticker_field": "",
        "selected_watchlist_ticker": None,
        "batch_del_version": 0,
        "confirm_delete_all": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    for item in st.session_state["watchlist_data"]:
        lp, chg = fetch_stock_quote(item["Ticker"])
        if lp is not None:
            item["Last Price"] = lp
            item["Change Pct"] = chg

    st.title("Watchlist")
    st.markdown("---")

    col_left, col_right = st.columns([1.2, 1.8], gap="medium")

    # ==========================================
    # LEFT COLUMN: WATCHLIST CARDS
    # ==========================================
    with col_left:
        h_col1, h_col2, h_col3 = st.columns([1, 1, 1])

        with h_col1:
            with st.popover("Add Ticker", use_container_width=True):
                st.write("Tambah Ticker Baru")
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
                    if st.button("Tambah Baris", key="btn_add_more_field", use_container_width=True):
                        st.session_state["quick_add_count"] += 1
                        st.rerun()
                with c_save:
                    if st.button("Simpan", key="btn_quick_add_save", type="primary", use_container_width=True):
                        if inputs:
                            added_count = 0
                            existing_tickers = {x["Ticker"] for x in st.session_state["watchlist_data"]}

                            for ticker in inputs:
                                if len(st.session_state["watchlist_data"]) < 50:
                                    formatted = ticker if ticker.endswith(".JK") else f"{ticker}.JK"
                                    if formatted not in existing_tickers:
                                        st.session_state["watchlist_data"].append(
                                            {
                                                "Ticker": formatted,
                                                "Notes": "Quick Added",
                                                "Target Price": 0,
                                            }
                                        )
                                        existing_tickers.add(formatted)
                                        added_count += 1

                            save_watchlist_to_file(st.session_state["watchlist_data"])
                            st.session_state["add_form_version"] += 1
                            st.session_state["quick_add_count"] = 1
                            st.success(f"{added_count} Ticker berhasil ditambahkan!")
                            st.rerun()

        with h_col2:
            with st.popover("Manage", use_container_width=True):
                st.write("Kelola Watchlist")
                del_ver = st.session_state["batch_del_version"]
                enable_batch_delete = st.checkbox(
                    "Mode Hapus",
                    value=False,
                    key=f"chk_mode_hapus_v{del_ver}",
                )

                if enable_batch_delete:
                    if st.button(
                        "Hapus Terpilih",
                        key=f"btn_execute_batch_delete_v{del_ver}",
                        type="primary",
                        use_container_width=True,
                    ):
                        if st.session_state["selected_cards"]:
                            to_remove = set(st.session_state["selected_cards"])

                            st.session_state["watchlist_data"] = [
                                x for x in st.session_state["watchlist_data"]
                                if x["Ticker"] not in to_remove
                            ]

                            if "watchlist" in st.session_state:
                                st.session_state["watchlist"] = [
                                    x for x in st.session_state["watchlist"]
                                    if (isinstance(x, str) and x not in to_remove and f"{x}.JK" not in to_remove)
                                    or (isinstance(x, dict) and x.get("Ticker") not in to_remove and f"{x.get('Ticker')}.JK" not in to_remove)
                                ]

                            save_watchlist_to_file(st.session_state["watchlist_data"])
                            st.session_state["selected_cards"].clear()
                            st.session_state["batch_del_version"] += 1
                            st.success("Data berhasil dihapus!")
                            st.rerun()

                st.markdown("---")
                if not st.session_state["confirm_delete_all"]:
                    if st.button("Hapus Semua Watchlist", key="btn_init_delete_all", use_container_width=True):
                        st.session_state["confirm_delete_all"] = True
                        st.rerun()
                else:
                    st.warning("Yakin ingin menghapus seluruh watchlist?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Ya", key="btn_confirm_del_all_yes", type="primary", use_container_width=True):
                            st.session_state["watchlist_data"] = []
                            if "watchlist" in st.session_state:
                                st.session_state["watchlist"] = []
                            save_watchlist_to_file([])
                            st.session_state["selected_cards"].clear()
                            st.session_state["selected_watchlist_ticker"] = None
                            st.session_state["confirm_delete_all"] = False
                            st.session_state["batch_del_version"] += 1
                            st.success("Semua watchlist dikosongkan!")
                            st.rerun()
                    with col_no:
                        if st.button("Tidak", key="btn_confirm_del_all_no", use_container_width=True):
                            st.session_state["confirm_delete_all"] = False
                            st.rerun()

        with h_col3:
            with st.popover("Sort", use_container_width=True):
                st.write("Urutkan")
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

        col_search, col_export = st.columns([3.2, 0.8], vertical_alignment="bottom")

        with col_search:
            st.text_input(
                "Search",
                placeholder="Cari Ticker...",
                label_visibility="collapsed",
                key="input_search_ticker_field",
            )

        display_list = list(st.session_state["watchlist_data"])
        search_val = st.session_state["input_search_ticker_field"].strip().upper()
        if search_val:
            display_list = [x for x in display_list if search_val in x["Ticker"]]

        sort_key_map = {
            "Gainers (% High)": (lambda x: x.get("Change Pct", 0) or 0, True),
            "Losers (% Low)": (lambda x: x.get("Change Pct", 0) or 0, False),
            "Price High": (lambda x: x.get("Last Price", 0) or 0, True),
            "Price Low": (lambda x: x.get("Last Price", 0) or 0, False),
        }

        if st.session_state["sort_filter"] in sort_key_map:
            key_func, rev = sort_key_map[st.session_state["sort_filter"]]
            display_list.sort(key=key_func, reverse=rev)

        with col_export:
            if display_list:
                df_export = pd.DataFrame(display_list)
                csv_data = df_export.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="CSV",
                    data=csv_data,
                    file_name="watchlist_export.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Export Watchlist to CSV"
                )
            else:
                st.button("CSV", disabled=True, use_container_width=True)

        with st.container(height=580):
            if display_list:
                if not st.session_state["selected_watchlist_ticker"] or not any(x["Ticker"] == st.session_state["selected_watchlist_ticker"] for x in display_list):
                    st.session_state["selected_watchlist_ticker"] = display_list[0]["Ticker"]

                for idx, item in enumerate(display_list):
                    ticker_raw = item["Ticker"]
                    clean_ticker = ticker_raw.replace(".JK", "").upper()
                    notes_tag = item.get("Notes", "Manual Added")
                    last_price = item.get("Last Price")
                    pct_change = item.get("Change Pct")

                    prefix = "+" if (pct_change is not None and pct_change > 0) else ""
                    price_str = f"Rp {int(last_price):,}" if last_price is not None else "-"
                    pct_str = f"{prefix}{pct_change:.2f}%" if pct_change is not None else "-"

                    if enable_batch_delete:
                        c_chk, c_card = st.columns([0.3, 3.7])
                        with c_chk:
                            is_checked = st.checkbox(
                                "",
                                key=f"card_chk_{clean_ticker}_{idx}_v{del_ver}",
                                value=ticker_raw in st.session_state["selected_cards"],
                            )
                            if is_checked:
                                st.session_state["selected_cards"].add(ticker_raw)
                            else:
                                st.session_state["selected_cards"].discard(ticker_raw)
                    else:
                        c_card = st.container()

                    with c_card:
                        is_active = st.session_state["selected_watchlist_ticker"] == ticker_raw
                        
                        st.write(f"**{clean_ticker}** - {notes_tag}")
                        st.write(f"Harga: {price_str} | Perubahan: {pct_str}")

                        btn_label = "Aktif" if is_active else f"Pilih {clean_ticker}"

                        if st.button(
                            btn_label,
                            key=f"btn_select_{clean_ticker}_{idx}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary",
                        ):
                            st.session_state["selected_watchlist_ticker"] = ticker_raw
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Tidak ada saham yang ditemukan.")

    # ==========================================
    # RIGHT COLUMN: TRADE PLAN VIEW
    # ==========================================
    with col_right:
        selected_ticker = st.session_state.get("selected_watchlist_ticker")

        if selected_ticker:
            render_trade_plan_only(
                ticker_symbol=selected_ticker,
                key_suffix=f"wl_{selected_ticker.replace('.', '_')}",
            )
        else:
            st.info("Pilih salah satu saham dari daftar pantauan di sebelah kiri.")
