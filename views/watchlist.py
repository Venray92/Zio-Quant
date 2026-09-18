import pandas as pd
import streamlit as st
import yfinance as yf

# Impor pustaka & fungsi lokal pendukung dari struktur proyek Anda
from engines.trade_planner import TradePlanner
from utils.storage import load_watchlist, save_watchlist

# ==========================================
# 1. HELPER & OPTIMIZED FETCH FUNCTIONS
# ==========================================


def ensure_jk_ticker(ticker: str) -> str:
    """Memastikan ticker berakhiran .JK untuk pasar saham Indonesia."""
    ticker = str(ticker).strip().upper()
    if not ticker:
        return ""
    if not ticker.endswith(".JK") and "." not in ticker:
        return f"{ticker}.JK"
    return ticker


def _format_val(val):
    """Format angka sesuai standar Indonesia (pemisah ribuan menggunakan titik)."""
    if pd.isna(val) or val is None or val in ["", "-"]:
        return "-"
    try:
        num = float(val)
        if num.is_integer():
            return f"{int(num):,}".replace(",", ".")
        # Format desimal: koma sebagai pemisah desimal, titik sebagai ribuan
        formatted = f"{num:,.2f}"
        return (
            formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        )
    except (ValueError, TypeError):
        return str(val)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_stock_quotes_batch(tickers_list: list[str]) -> dict:
    """Mengambil data harga (Last Price & Change %) untuk banyak saham sekaligus (Batch).

    Jauh lebih cepat daripada loop satu per satu.
    """
    if not tickers_list:
        return {}

    clean_tickers = [ensure_jk_ticker(t) for t in tickers_list if t]
    results = {}

    try:
        # Menarik data batch dalam 1 HTTP Request
        tickers_obj = yf.Tickers(" ".join(clean_tickers))

        for full_ticker in clean_tickers:
            raw_ticker = full_ticker.replace(".JK", "")
            try:
                t = tickers_obj.tickers.get(full_ticker)
                if not t:
                    results[raw_ticker] = (None, None)
                    continue

                fast = t.fast_info
                lp = fast.last_price
                prev_close = fast.previous_close

                if lp is not None and prev_close:
                    chg = ((lp - prev_close) / prev_close) * 100
                    results[raw_ticker] = (float(lp), float(chg))
                elif lp is not None:
                    results[raw_ticker] = (float(lp), 0.0)
                else:
                    results[raw_ticker] = (None, None)
            except Exception:
                results[raw_ticker] = (None, None)

    except Exception:
        # Fallback jika batch request gagal total
        for t in tickers_list:
            results[t.replace(".JK", "")] = (None, None)

    return results


# ==========================================
# 2. MAIN WATCHLIST VIEW
# ==========================================


def render_watchlist_page():
    st.title("📋 Watchlist & Live Trade Plan")

    # Inisialisasi Session State
    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = load_watchlist()

    if "delete_mode" not in st.session_state:
        st.session_state["delete_mode"] = False

    if "selected_cards" not in st.session_state:
        st.session_state["selected_cards"] = set()

    if "del_version" not in st.session_state:
        st.session_state["del_version"] = 0

    # Synchronization Check
    current_wl = load_watchlist()
    if set(current_wl) != set(st.session_state["watchlist"]):
        st.session_state["watchlist"] = current_wl

    # Top Control Bar (Search, Add, Batch Delete)
    col_search, col_add, col_del = st.columns([3, 1.5, 1.5])

    with col_search:
        search_query = st.text_input(
            "🔎 Cari Ticker",
            placeholder="Ketik kode saham (misal: BBCA)...",
            label_visibility="collapsed",
        ).upper()

    with col_add:
        with st.popover("➕ Tambah Saham", use_container_width=True):
            st.markdown("**Tambah Ticker Baru**")
            new_ticker = st.text_input(
                "Kode Saham",
                placeholder="misal: TLKM",
                key="input_new_ticker",
            ).upper()
            if st.button("Simpan", use_container_width=True):
                clean_t = new_ticker.replace(".JK", "").strip()
                if clean_t:
                    if clean_t not in st.session_state["watchlist"]:
                        st.session_state["watchlist"].append(clean_t)
                        save_watchlist(st.session_state["watchlist"])
                        st.toast(
                            f"✅ {clean_t} berhasil ditambahkan!", icon="🎉"
                        )
                        st.rerun()
                    else:
                        st.warning(f"{clean_t} sudah ada di Watchlist.")

    with col_del:
        toggle_label = (
            "❌ Batal Hapus"
            if st.session_state["delete_mode"]
            else "🗑️ Mode Hapus"
        )
        if st.button(
            toggle_label,
            use_container_width=True,
            type="secondary" if st.session_state["delete_mode"] else "default",
        ):
            st.session_state["delete_mode"] = not st.session_state[
                "delete_mode"
            ]
            st.session_state["selected_cards"].clear()  # Clear state saat toggle
            st.rerun()

    # Action Bar jika dalam Mode Hapus
    if st.session_state["delete_mode"]:
        st.warning("⚠️ **Mode Hapus Aktif**: Pilih saham yang ingin dihapus.")
        col_act1, col_act2 = st.columns([2, 1])
        with col_act1:
            st.write(
                f"Saham terpilih: **{len(st.session_state['selected_cards'])}**"
            )
        with col_act2:
            if st.button(
                "🔥 Hapus Terpilih",
                type="primary",
                use_container_width=True,
                disabled=len(st.session_state["selected_cards"]) == 0,
            ):
                st.session_state["watchlist"] = [
                    t
                    for t in st.session_state["watchlist"]
                    if t not in st.session_state["selected_cards"]
                ]
                save_watchlist(st.session_state["watchlist"])
                st.session_state["selected_cards"].clear()
                st.session_state["delete_mode"] = False
                st.session_state["del_version"] += 1
                st.toast("Daftar saham berhasil diperbarui!", icon="🗑️")
                st.rerun()
        st.divider()

    # Empty State
    if not st.session_state["watchlist"]:
        st.info("Watchlist Anda masih kosong. Silakan tambah saham baru.")
        return

    # Filter berdasarkan kata kunci pencarian
    filtered_watchlist = [
        t for t in st.session_state["watchlist"] if search_query in t
    ]

    if not filtered_watchlist:
        st.warning(f"Tidak ada saham yang cocok dengan pencarian '{search_query}'.")
        return

    # OPTIMATED: Batch fetch semua data harga secara bersamaan
    with st.spinner("Mengambil harga pasar live..."):
        market_data_map = fetch_stock_quotes_batch(filtered_watchlist)

    # Susun Data List
    watchlist_cards = []
    for ticker_raw in filtered_watchlist:
        lp, chg = market_data_map.get(ticker_raw, (None, None))
        watchlist_cards.append(
            {
                "Ticker": ticker_raw,
                "Last Price": lp,
                "Change Pct": chg,
            }
        )

    # Sorting Toolbar
    col_sort, col_order = st.columns([3, 2])
    with col_sort:
        sort_by = st.selectbox(
            "Urutkan Berdasarkan:",
            ["Ticker", "Gainers (%)", "Losers (%)", "Harga Tertinggi", "Harga Terendah"],
            label_visibility="collapsed",
        )

    # Logic Sorting
    if sort_by == "Gainers (%)":
        watchlist_cards.sort(
            key=lambda x: x["Change Pct"] if x["Change Pct"] is not None else -999,
            reverse=True,
        )
    elif sort_by == "Losers (%)":
        watchlist_cards.sort(
            key=lambda x: x["Change Pct"] if x["Change Pct"] is not None else 999
        )
    elif sort_by == "Harga Tertinggi":
        watchlist_cards.sort(
            key=lambda x: x["Last Price"] if x["Last Price"] is not None else -1,
            reverse=True,
        )
    elif sort_by == "Harga Terendah":
        watchlist_cards.sort(
            key=lambda x: x["Last Price"] if x["Last Price"] is not None else 999999
        )
    else:
        watchlist_cards.sort(key=lambda x: x["Ticker"])

    st.write("")  # Spacing

    # Render Cards Loop
    del_ver = st.session_state["del_version"]
    for idx, item in enumerate(watchlist_cards):
        ticker_raw = item["Ticker"]
        lp = item["Last Price"]
        chg = item["Change Pct"]

        # Container Card Style
        with st.container(border=True):
            head_col1, head_col2 = st.columns([4, 1])

            with head_col1:
                # Price Change Badge Color
                if chg is not None:
                    chg_color = "green" if chg >= 0 else "red"
                    chg_str = f":{chg_color}[({chg:+.2f}%)]"
                    lp_str = f"RP {_format_val(lp)}"
                else:
                    chg_str = ""
                    lp_str = "Loading/N/A"

                st.subheader(f"{ticker_raw}  `{lp_str}` {chg_str}")

            with head_col2:
                if st.session_state["delete_mode"]:
                    is_checked = st.checkbox(
                        "Pilih",
                        key=f"card_chk_{ticker_raw}_{idx}_v{del_ver}",
                        value=ticker_raw in st.session_state["selected_cards"],
                    )
                    if is_checked:
                        st.session_state["selected_cards"].add(ticker_raw)
                    else:
                        st.session_state["selected_cards"].discard(ticker_raw)

            # Render Trade Plan Detail menggunakan TradePlanner Engine
            try:
                planner = TradePlanner(ensure_jk_ticker(ticker_raw))
                # Mengasumsikan modul Anda punya method render/get_plan
                planner.render_trade_plan_only()
            except Exception as e:
                st.caption(f"⚠️ Gagal memuat analisis Trade Plan: {e}")
