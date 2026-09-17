import json
import os
import pandas as pd
import streamlit as st
import yfinance as yf
from engines.trade_planner import TradePlanner

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
# HELPER UNTUK TRADE PLAN (TANPA CHART)
# ==========================================
def _format_val(val):
    if pd.isna(val) or val is None or val == "" or val == "-":
        return "-"
    try:
        num = float(val)
        return f"{int(num):,}" if num.is_integer() else f"{num:,.2f}"
    except (ValueError, TypeError):
        return str(val)


def _clean_num(val):
    if pd.isna(val) or val is None or val == "" or val == "-":
        return None
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return float(val)
    except Exception:
        return None


def calculate_rr_ratios(row):
    buy_val = _clean_num(
        row.get("Range Buy Max", row.get("Buy Max", row.get("Buy Min", None)))
    )
    sl_val = _clean_num(row.get("Stop Loss", row.get("SL", None)))
    tp1_val = _clean_num(
        row.get("TP 1", row.get("TP1", row.get("Target 1", None)))
    )
    tp2_val = _clean_num(
        row.get("TP 2", row.get("TP2", row.get("Target 2", None)))
    )

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
    """Merender Trade Plan Recommendation tanpa Chart TradingView"""
    st.markdown("---")

    st.markdown(
        f"""
        <div class="live-plan-header">
            <div class="live-plan-title">
                📊 LIVE TRADE PLAN: <span class="live-plan-ticker">{ticker_symbol}</span>
            </div>
            <div style="font-size: 12px; color: #8B949E; font-weight: 600;">
                SYSTEM STATUS: <span style="color: #00E676;">ONLINE</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    period_selected = st.selectbox(
        "⏱️ Periode Data Analysis",
        options=["3mo", "6mo", "1y", "2y"],
        index=0,
        key=f"period_{key_suffix}",
    )

    with st.spinner(f"⚡ Menganalisis Trade Plan {ticker_symbol}..."):
        try:
            planner = TradePlanner(
                ticker=ticker_symbol.upper(), period=period_selected
            )
            if hasattr(planner, "fetch_and_prepare_data"):
                planner.fetch_and_prepare_data()

            df_plan = (
                planner.generate_trade_plan()
                if hasattr(planner, "generate_trade_plan")
                else None
            )

            if df_plan is not None and not df_plan.empty:
                st.markdown(
                    '<div class="section-title">🎯 Trade Plan'
                    " Recommendation</div>",
                    unsafe_allow_html=True,
                )

                for idx, row in df_plan.iterrows():
                    plan_no = idx + 1
                    plan_type = row.get(
                        "Type", row.get("Strategy", f"Plan #{plan_no}")
                    )
                    score = row.get("Score", 0)
                    grade = row.get("Grade", "N/A")
                    posisi = row.get("Posisi Harga", row.get("Status", "-"))

                    range_min = _format_val(
                        row.get("Range Buy Min", row.get("Buy Min", "-"))
                    )
                    range_max = _format_val(
                        row.get("Range Buy Max", row.get("Buy Max", "-"))
                    )
                    area_buy = (
                        f"{range_min} - {range_max}"
                        if range_min != "-" and range_max != "-"
                        else range_min
                    )

                    stop_loss = _format_val(
                        row.get("Stop Loss", row.get("SL", "-"))
                    )
                    tp1 = _format_val(row.get("TP 1", row.get("TP1", "-")))
                    tp2 = _format_val(row.get("TP 2", row.get("TP2", "-")))

                    posisi_color = (
                        "#10B981" if "Buy Zone" in str(posisi) else "#F59E0B"
                    )

                    card_html = f"""
                    <div style="background: linear-gradient(135deg, #161B22 0%, #0D1117 100%); border: 1px solid #30363D; border-left: 5px solid #00E676; border-radius: 12px; padding: 18px; margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #21262D; padding-bottom: 12px; margin-bottom: 14px;">
                            <div>
                                <span style="background: linear-gradient(90deg, #00E676 0%, #38BDF8 100%); color: #0E1117; font-weight: 900; font-size: 13px; padding: 4px 12px; border-radius: 6px;">#{plan_no} {plan_type}</span>
                                <span style="font-size: 13px; font-weight: 700; color: #E6EDF3; margin-left: 8px;">{grade}</span>
                            </div>
                            <div style="background: rgba(168, 85, 247, 0.15); border: 1px solid #A855F7; color: #F3E8FF; font-weight: 800; padding: 4px 14px; border-radius: 20px; font-size: 12px;">
                                SCORE: {score}
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 14px; text-align: center;">
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.2);">
                                <div style="font-size: 10px; color: #38BDF8; font-weight: 800;">Area Buy</div>
                                <div style="font-size: 15px; font-weight: 800; color: #38BDF8; margin-top: 4px;">{area_buy}</div>
                            </div>
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(255, 82, 82, 0.2);">
                                <div style="font-size: 10px; color: #FF5252; font-weight: 800;">Stop Loss</div>
                                <div style="font-size: 15px; font-weight: 800; color: #FF5252; margin-top: 4px;">{stop_loss}</div>
                            </div>
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 230, 118, 0.2);">
                                <div style="font-size: 10px; color: #00E676; font-weight: 800;">Target 1</div>
                                <div style="font-size: 15px; font-weight: 800; color: #00E676; margin-top: 4px;">{tp1}</div>
                            </div>
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 230, 118, 0.2);">
                                <div style="font-size: 10px; color: #00E676; font-weight: 800;">Target 2</div>
                                <div style="font-size: 15px; font-weight: 800; color: #00E676; margin-top: 4px;">{tp2}</div>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 12px; background-color: #0E1117; padding: 10px 14px; border-radius: 8px; border: 1px solid #21262D;">
                            <span style="color: #8B949E; font-weight: 600;">Posisi Harga Saat Ini:</span>
                            <span style="font-weight: 800; color: {posisi_color};">{posisi}</span>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

                    rr_tp1_val, rr_tp2_val = calculate_rr_ratios(row)
                    with st.expander(
                        f"⚙️ Parameter Lengkap & Rasio R:R #{plan_no}"
                        f" ({plan_type})",
                        expanded=True,
                    ):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.metric(
                                label="R:R ( Target 1 )", value=rr_tp1_val
                            )
                        with c2:
                            st.metric(
                                label="R:R ( Target 2 )", value=rr_tp2_val
                            )

        except Exception as e:
            st.error(f"Gagal memuat Trade Plan: {e}")


# ==========================================
# MAIN RENDER FUNCTION
# ==========================================
def render_page_watchlist():
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
    if "selected_watchlist_ticker" not in st.session_state:
        st.session_state["selected_watchlist_ticker"] = None

    # Safe reset flag untuk Mode Hapus pasca-delete
    if "reset_batch_del" not in st.session_state:
        st.session_state["reset_batch_del"] = False

    if st.session_state["reset_batch_del"]:
        st.session_state["enable_batch_delete"] = False
        st.session_state["reset_batch_del"] = False

    # Fetch Real-time Data
    for item in st.session_state["watchlist_data"]:
        lp, chg = fetch_stock_quote(item["Ticker"])
        item["Last Price"] = (
            lp if lp is not None else item.get("Last Price", 0.0)
        )
        item["Change Pct"] = (
            chg if chg is not None else item.get("Change Pct", 0.0)
        )

    st.title("📈 Watchlist Saham Pro")

    col_left, col_right = st.columns([1.2, 1.8], gap="large")

    # ==========================================
    # KIRI: DAFTAR KARTU SAHAM
    # ==========================================
    with col_left:
        st.subheader("Daftar Pantauan")

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
                    key="chk_mode_hapus_state",
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

                            # Set flag untuk hilangkan centang setelah rerun
                            st.session_state["reset_batch_del"] = True

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

        with st.container(height=550):
            if display_list:
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
                        # RENDER KARTU SAHAM HTML
                        st.markdown(
                            f"""
                            <div style="
                                border: 1px solid #30363D; 
                                border-left: 5px solid {color_code}; 
                                border-radius: 8px 8px 0px 0px; 
                                padding: 10px 14px; 
                                display: flex; 
                                justify-content: space-between; 
                                align-items: center;
                                background-color: #161B22;">
                                <div>
                                    <span style="font-weight: bold; font-size: 16px; color: #E6EDF3;">{clean_ticker}</span>
                                    <span style="font-size: 10px; color: #8B949E; margin-left: 5px;">IDX</span>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-weight: bold; font-size: 14px; color: #E6EDF3;">{price_str}</div>
                                    <div style="
                                        font-size: 11px; 
                                        font-weight: bold; 
                                        color: {color_code}; 
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

                        # TOMBOL TRADE PLAN
                        is_active = (
                            st.session_state["selected_watchlist_ticker"]
                            == ticker_raw
                        )
                        btn_label = (
                            "📍 Aktif Dilihat"
                            if is_active
                            else f"📊 Trade Plan {clean_ticker}"
                        )

                        if st.button(
                            btn_label,
                            key=f"btn_select_{clean_ticker}_{idx}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary",
                        ):
                            st.session_state["selected_watchlist_ticker"] = (
                                ticker_raw
                            )
                            st.rerun()

                        st.write("")
            else:
                st.caption("Tidak ada saham yang ditemukan.")

    # ==========================================
    # KANAN: TRADE PLAN RECOMMENDATION ONLY
    # ==========================================
    with col_right:
        selected_ticker = st.session_state.get("selected_watchlist_ticker")

        if selected_ticker:
            render_trade_plan_only(
                ticker_symbol=selected_ticker,
                key_suffix=f"wl_{selected_ticker.replace('.', '_')}",
            )
        else:
            st.info(
                "Pilih salah satu saham dari daftar pantauan di sebelah kiri."
            )
