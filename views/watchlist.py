import json
import os
import pandas as pd
import streamlit as st
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
    st.markdown(
        f"""
        <div class="live-plan-header" style="padding: 8px 12px; margin-bottom: 10px;">
            <div class="live-plan-title" style="font-size: 14px;">
                📊 LIVE TRADE PLAN: <span class="live-plan-ticker">{ticker_symbol}</span>
            </div>
            <div style="font-size: 11px; color: #8B949E; font-weight: 600;">
                SYSTEM STATUS: <span style="color: #00E676;">ONLINE</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    period_selected = "3mo"

    with st.spinner(f"⚡ Menganalisis Trade Plan {ticker_symbol}..."):
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
                st.markdown(
                    '<div class="section-title" style="font-size: 13px; margin-bottom: 8px;">🎯 TRADE PLAN RECOMMENDATION</div>',
                    unsafe_allow_html=True,
                )

                for idx, row in df_plan.iterrows():
                    plan_no = idx + 1
                    plan_type = row.get("Type", row.get("Strategy", f"Plan #{plan_no}"))
                    score = row.get("Score", 0)
                    grade = row.get("Grade", "N/A")
                    posisi = row.get("Posisi Harga", row.get("Status", "-"))

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

                    posisi_color = "#10B981" if "Buy Zone" in str(posisi) else "#F59E0B"

                    card_html = f"""
                    <div style="background: linear-gradient(135deg, #161B22 0%, #0D1117 100%); border: 1px solid #30363D; border-left: 4px solid #00E676; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #21262D; padding-bottom: 8px; margin-bottom: 10px;">
                            <div>
                                <span style="background: linear-gradient(90deg, #00E676 0%, #38BDF8 100%); color: #0E1117; font-weight: 900; font-size: 11px; padding: 2px 8px; border-radius: 4px;">#{plan_no} {plan_type}</span>
                                <span style="font-size: 12px; font-weight: 700; color: #E6EDF3; margin-left: 6px;">{grade}</span>
                            </div>
                            <div style="background: rgba(168, 85, 247, 0.15); border: 1px solid #A855F7; color: #F3E8FF; font-weight: 800; padding: 2px 10px; border-radius: 12px; font-size: 11px;">
                                SCORE: {score}
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 10px; text-align: center;">
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 8px; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.2);">
                                <div style="font-size: 9px; color: #38BDF8; font-weight: 800;">Area Buy</div>
                                <div style="font-size: 13px; font-weight: 800; color: #38BDF8; margin-top: 2px;">{area_buy}</div>
                            </div>
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 8px; border-radius: 6px; border: 1px solid rgba(255, 82, 82, 0.2);">
                                <div style="font-size: 9px; color: #FF5252; font-weight: 800;">Stop Loss</div>
                                <div style="font-size: 13px; font-weight: 800; color: #FF5252; margin-top: 2px;">{stop_loss}</div>
                            </div>
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 8px; border-radius: 6px; border: 1px solid rgba(0, 230, 118, 0.2);">
                                <div style="font-size: 9px; color: #00E676; font-weight: 800;">Target 1</div>
                                <div style="font-size: 13px; font-weight: 800; color: #00E676; margin-top: 2px;">{tp1}</div>
                            </div>
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 8px; border-radius: 6px; border: 1px solid rgba(0, 230, 118, 0.2);">
                                <div style="font-size: 9px; color: #00E676; font-weight: 800;">Target 2</div>
                                <div style="font-size: 13px; font-weight: 800; color: #00E676; margin-top: 2px;">{tp2}</div>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 11px; background-color: #0E1117; padding: 6px 10px; border-radius: 6px; border: 1px solid #21262D;">
                            <span style="color: #8B949E; font-weight: 600;">Posisi Harga Saat Ini:</span>
                            <span style="font-weight: 800; color: {posisi_color};">{posisi}</span>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

                    rr_tp1_val, rr_tp2_val = calculate_rr_ratios(row)
                    with st.expander(
                        f"⚙️ Parameter Lengkap & Rasio R:R #{plan_no} ({plan_type})",
                        expanded=False,
                    ):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.metric(label="R:R ( Target 1 )", value=rr_tp1_val)
                        with c2:
                            st.metric(label="R:R ( Target 2 )", value=rr_tp2_val)

        except Exception as e:
            st.error(f"Gagal memuat Trade Plan: {e}")


# ==========================================
# MAIN RENDER FUNCTION
# ==========================================
def render_page_watchlist():
    # Session State Initialization
    if "watchlist_data" not in st.session_state:
        st.session_state["watchlist_data"] = load_watchlist_from_file()

    # Dynamic Sync with Global "watchlist" State
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

    # Additional Session State Variables
    defaults = {
        "add_form_version": 0,
        "sort_filter": "Default",
        "selected_cards": set(),
        "quick_add_count": 1,
        "input_search_ticker_field": "",
        "selected_watchlist_ticker": None,
        "batch_del_version": 0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # Fetch Real-time Market Data
    for item in st.session_state["watchlist_data"]:
        lp, chg = fetch_stock_quote(item["Ticker"])
        if lp is not None:
            item["Last Price"] = lp
            item["Change Pct"] = chg

    st.markdown(
        "<h4 style='margin-bottom: 12px; font-weight: 700; color: #E6EDF3;'>WATCHLIST</h4>",
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1.2, 1.8], gap="medium")

    # ==========================================
    # LEFT COLUMN: WATCHLIST CARDS
    # ==========================================
    with col_left:
        h_col1, h_col2, h_col3 = st.columns([1, 1, 1])

        # 1. Quick Add Popover
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
                    if st.button("＋ Baris", key="btn_add_more_field", use_container_width=True):
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
                            st.toast(f"{added_count} Saham ditambahkan!", icon="🚀")
                            st.rerun()

        # 2. Batch Delete Popover
        with h_col2:
            with st.popover("🗑️ Kelola", use_container_width=True):
                st.caption("Batch Delete")
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
                            st.toast("Saham berhasil dihapus!", icon="🗑️")
                            st.rerun()

        # 3. Sort Popover
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

        # Search Bar UI
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

        # Filter & Sort Data Display
        display_list = list(st.session_state["watchlist_data"])
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

        # Scrollable Cards View
        with st.container(height=580):
            if display_list:
                if not st.session_state["selected_watchlist_ticker"]:
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
                        with st.container(border=True):
                            col_info, col_price = st.columns([1.3, 1])

                            with col_info:
                                st.markdown(
                                    f"<div style='font-size: 15px; font-weight: 800; color: #E6EDF3;'>{clean_ticker}</div>",
                                    unsafe_allow_html=True,
                                )
                                st.caption(f"🔹 {notes_tag}")

                            with col_price:
                                st.markdown(
                                    f"<div style='text-align: right; font-size: 13px; font-weight: 700;'>{price_str}</div>",
                                    unsafe_allow_html=True,
                                )
                                color_code = (
                                    "#00C853" if pct_change and pct_change > 0
                                    else "#D50000" if pct_change and pct_change < 0
                                    else "#757575"
                                )
                                st.markdown(
                                    f"<div style='text-align: right; font-size: 11px; color: {color_code}; font-weight: 700;'>{pct_str}</div>",
                                    unsafe_allow_html=True,
                                )

                            is_active = st.session_state["selected_watchlist_ticker"] == ticker_raw
                            btn_label = "📍 Aktif Dilihat" if is_active else f"📊 Trade Plan {clean_ticker}"

                            if st.button(
                                btn_label,
                                key=f"btn_select_{clean_ticker}_{idx}",
                                use_container_width=True,
                                type="primary" if is_active else "secondary",
                            ):
                                st.session_state["selected_watchlist_ticker"] = ticker_raw
                                st.rerun()
            else:
                st.caption("Tidak ada saham yang ditemukan.")

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
