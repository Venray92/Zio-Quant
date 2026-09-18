import os
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from engines.trade_planner import TradePlanner

STORAGE_FILE = "watchlist_storage.json"
CSS_FILE = os.path.join("assets", "style-watchlist.css")


# ==========================================
# CYBERPUNK CUSTOM CSS LOADER
# ==========================================
def inject_cyberpunk_css():
    """Membaca dan menerapkan styling dari file CSS eksternal di folder assets."""
    if os.path.exists(CSS_FILE):
        with open(CSS_FILE, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"[SYS_WARN] File '{CSS_FILE}' tidak ditemukan. Pastikan folder 'assets' sudah dibuat.")


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
        st.error(f"[SYSTEM_ERROR] Gagal menyimpan data: {e}")


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


def sanitize_pink_colors(html_content):
    """Mengganti string warna magenta/pink/purple bawaan ke warna Cyan & Theme-friendly."""
    if not isinstance(html_content, str):
        return html_content

    color_map = {
        "#FF007F": "#00F0FF",
        "#ff007f": "#00F0FF",
        "#9D00FF": "#00F0FF",
        "#9d00ff": "#00F0FF",
        "#E2B6FF": "#00F0FF",
        "#e2b6ff": "#00F0FF",
        "rgba(255, 0, 127": "rgba(0, 240, 255",
        "rgba(157, 0, 255": "rgba(0, 240, 255",
    }
    for old_color, new_color in color_map.items():
        html_content = html_content.replace(old_color, new_color)

    return html_content


def render_trade_plan_only(ticker_symbol, key_suffix):
    """Renders the Trade Plan Recommendation component for the selected ticker."""
    st.markdown(
        f"""
        <div style="background: #0A0E1A; border: 1px solid #00F0FF; box-shadow: 0 0 10px rgba(0, 240, 255, 0.3); padding: 10px 14px; margin-bottom: 12px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 14px; font-weight: 800; color: #00F0FF; text-shadow: 0 0 5px #00F0FF;">
                ⚡ LIVE_TRADE_PLAN // <span style="color: #00F0FF; text-shadow: 0 0 5px #00F0FF;">{ticker_symbol}</span>
            </div>
            <div style="font-size: 11px; color: #8B949E; font-weight: 700;">
                SYS_STATUS: <span style="color: #00FF66; text-shadow: 0 0 5px #00FF66;">[ONLINE]</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. EMBED TRADINGVIEW CHART DALAM EXPANDER (DEFAULT DITUTUP / COLLAPSED)
    clean_ticker = (
        ticker_symbol.replace(".JK", "").replace("IDX:", "").strip().upper()
    )
    safe_container_id = clean_ticker.replace(".", "_")
    tv_symbol = f"IDX:{clean_ticker}"

    with st.expander(f"📈 TradingView Chart: {ticker_symbol}", expanded=False):
        tv_html = f"""
        <div class="tradingview-widget-container" style="height:500px; width:100%; border-radius:4px; overflow:hidden; border: 1px solid #00F0FF; margin-top: 5px; margin-bottom: 8px;">
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
                "toolbar_bg": "#0A0E1A",
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
        st.markdown(
            "<div style='font-size: 11px; color: #6C7A9C; margin-bottom: 8px; font-weight: 500;'>"
            "💡 *Lakukan screenshot jika Anda membuat tarikan garis/analisa visual.*"
            "</div>",
            unsafe_allow_html=True,
        )

    period_selected = "3mo"

    with st.spinner(f"🌐 FETCHING CYBER MATRIX FOR {ticker_symbol}..."):
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
                    '<div style="font-size: 12px; font-weight: 800; color: #00F0FF; text-shadow: 0 0 5px #00F0FF; margin-top: 14px; margin-bottom: 10px; letter-spacing: 1px;">🎯 TRADE PLAN RECOMMENDATION</div>',
                    unsafe_allow_html=True,
                )

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

                    posisi_color = "#00FF66" if "Buy Zone" in posisi and "Below" not in posisi else "#00F0FF"

                    is_suggestion = (idx == 0)
                    prefix_label = "Trade Plan Suggestion" if is_suggestion else "Trade Plan Other"
                    expander_title = f"🎯 {prefix_label} #{plan_no} {plan_type} ({ticker_symbol}) - Score: {score}"

                    copyable_text = f"=== TRADE PLAN: {ticker_symbol} ===\\nStrategy: {plan_type}\\nGrade: {grade}\\nScore: {score}/100\\nArea Buy: {area_buy}\\nStop Loss: {stop_loss}\\nTarget 1 (TP1): {tp1}\\nTarget 2 (TP2): {tp2}\\nStatus Posisi: {posisi}\\n==============================="

                    with st.expander(expander_title, expanded=False):
                        unique_btn_id = f"copy_btn_wl_{key_suffix}_{idx}"
                        
                        copy_btn_component = f"""
                        <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 8px;">
                            <button id="{unique_btn_id}" style="background: linear-gradient(135deg, #A855F7 0%, #00F0FF 100%); color: #050811; border: none; padding: 4px 10px; border-radius: 4px; font-weight: 800; font-size: 10px; cursor: pointer; box-shadow: 0 0 8px rgba(0, 240, 255, 0.4); transition: all 0.2s;">
                                📋 COPY PLAN
                            </button>
                        </div>
                        <script>
                        const textToCopy_{unique_btn_id} = `{copyable_text}`;
                        const btn_{unique_btn_id} = document.getElementById("{unique_btn_id}");
                        btn_{unique_btn_id}.onclick = function() {{
                            navigator.clipboard.writeText(textToCopy_{unique_btn_id}).then(function() {{
                                btn_{unique_btn_id}.innerText = "✅ COPIED!";
                                btn_{unique_btn_id}.style.background = "#00FF66";
                                setTimeout(function() {{
                                    btn_{unique_btn_id}.innerText = "📋 COPY PLAN";
                                    btn_{unique_btn_id}.style.background = "linear-gradient(135deg, #A855F7 0%, #00F0FF 100%)";
                                }}, 2000);
                            }}).catch(function(err) {{
                                console.error('Gagal menyalin text: ', err);
                            }});
                        }};
                        </script>
                        """
                        components.html(copy_btn_component, height=35)

                        card_html = f"""
                        <div style="background: #060913; border: 1px solid #00F0FF; border-left: 4px solid #00F0FF; box-shadow: 0 0 8px rgba(0, 240, 255, 0.3); border-radius: 4px; padding: 12px; margin-top: 4px; margin-bottom: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #2A2F45; padding-bottom: 8px; margin-bottom: 10px;">
                                <div>
                                    <span style="background: #00F0FF; color: #050811; font-weight: 900; font-size: 10px; padding: 3px 8px; border-radius: 2px; text-shadow: none;">#{plan_no} {plan_type}</span>
                                    <span style="font-size: 12px; font-weight: 700; color: #FFFFFF; margin-left: 8px;">GRADE: {grade}</span>
                                </div>
                                <div style="background: rgba(0, 240, 255, 0.1); border: 1px solid #00F0FF; color: #00F0FF; font-weight: 800; padding: 2px 10px; border-radius: 10px; font-size: 10px; text-shadow: 0 0 4px #00F0FF;">
                                    SCORE: {score}
                                </div>
                            </div>
                            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 10px; text-align: center;">
                                <div style="background: #0A0E1A; padding: 8px 4px; border-radius: 2px; border: 1px solid rgba(0, 240, 255, 0.4);">
                                    <div style="font-size: 9px; color: #00F0FF; font-weight: 700;">BUY AREA</div>
                                    <div style="font-size: 12px; font-weight: 800; color: #FFFFFF; margin-top: 2px;">{area_buy}</div>
                                </div>
                                <div style="background: #0A0E1A; padding: 8px 4px; border-radius: 2px; border: 1px solid rgba(0, 240, 255, 0.4);">
                                    <div style="font-size: 9px; color: #00F0FF; font-weight: 700;">STOP LOSS</div>
                                    <div style="font-size: 12px; font-weight: 800; color: #00F0FF; margin-top: 2px;">{stop_loss}</div>
                                </div>
                                <div style="background: #0A0E1A; padding: 8px 4px; border-radius: 2px; border: 1px solid rgba(0, 255, 102, 0.4);">
                                    <div style="font-size: 9px; color: #00FF66; font-weight: 700;">TARGET 1</div>
                                    <div style="font-size: 12px; font-weight: 800; color: #00FF66; margin-top: 2px;">{tp1}</div>
                                </div>
                                <div style="background: #0A0E1A; padding: 8px 4px; border-radius: 2px; border: 1px solid rgba(0, 255, 102, 0.4);">
                                    <div style="font-size: 9px; color: #00FF66; font-weight: 700;">TARGET 2</div>
                                    <div style="font-size: 12px; font-weight: 800; color: #00FF66; margin-top: 2px;">{tp2}</div>
                                </div>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 10px; background-color: #03050B; padding: 6px 10px; border-radius: 2px; border: 1px solid #1A1F35;">
                                <span style="color: #6C7A9C; font-weight: 600;">POSISI HARGA SAAT INI:</span>
                                <span style="font-weight: 800; color: {posisi_color}; text-shadow: 0 0 5px {posisi_color};">{posisi}</span>
                            </div>
                        </div>
                        """

                        card_html = sanitize_pink_colors(card_html)
                        st.markdown(card_html, unsafe_allow_html=True)

                        rr_tp1_val, rr_tp2_val = calculate_rr_ratios(row)
                        with st.expander(
                            f"⚙️ PARAMETERS & R:R RATIO #{plan_no} ({plan_type})",
                            expanded=False,
                        ):
                            c1, c2 = st.columns(2)
                            with c1:
                                st.metric(label="R:R ( Target 1 )", value=rr_tp1_val)
                            with c2:
                                st.metric(label="R:R ( Target 2 )", value=rr_tp2_val)

        except Exception as e:
            st.error(f"[SYSTEM_FAILURE] Gagal memuat Trade Plan: {e}")


# ==========================================
# MAIN RENDER FUNCTION
# ==========================================
def render_page_watchlist():
    inject_cyberpunk_css()

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
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    for item in st.session_state["watchlist_data"]:
        lp, chg = fetch_stock_quote(item["Ticker"])
        if lp is not None:
            item["Last Price"] = lp
            item["Change Pct"] = chg

    st.markdown(
        "<h3 style='margin-bottom: 14px;'>📡 WATCHLIST // TERMINAL</h3>",
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1.2, 1.8], gap="medium")

    # ==========================================
    # LEFT COLUMN: WATCHLIST CARDS
    # ==========================================
    with col_left:
        h_col1, h_col2, h_col3 = st.columns([1, 1, 1])

        with h_col1:
            with st.popover("➕ Tambah", use_container_width=True):
                st.caption("SYSTEM // QUICK ADD")
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
                            st.toast(f"{added_count} Ticker Diinjeksi!", icon="🚀")
                            st.rerun()

        with h_col2:
            with st.popover("🗑️ Kelola", use_container_width=True):
                st.caption("SYSTEM // PURGE DATA")
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
                            st.toast("Data Berhasil Dihapus!", icon="🗑️")
                            st.rerun()

        with h_col3:
            with st.popover("⚡ Sort", use_container_width=True):
                st.caption("SYSTEM // SORTING")
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
                placeholder="🔍 FILTER_TICKER...",
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
                    label="📥",
                    data=csv_data,
                    file_name="watchlist_export.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Export Watchlist to CSV"
                )
            else:
                st.button("📥", disabled=True, use_container_width=True, help="Data kosong")

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
                        is_active = st.session_state["selected_watchlist_ticker"] == ticker_raw
                        
                        card_border = "#00F0FF" if is_active else "#1A1F35"
                        glow_effect = "box-shadow: 0 0 10px rgba(0, 240, 255, 0.4);" if is_active else ""
                        bg_card = "#0A0E1A" if is_active else "#060913"

                        pct_color = "#00FF66" if pct_change and pct_change > 0 else "#FF4D4D" if pct_change and pct_change < 0 else "#8B949E"

                        st.markdown(
                            f"""
                            <div style="background: {bg_card}; border: 1px solid {card_border}; {glow_effect} border-radius: 4px; padding: 10px; margin-bottom: 8px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="font-size: 15px; font-weight: 800; color: #FFFFFF;">{clean_ticker}</div>
                                        <div style="font-size: 10px; color: #6C7A9C;">🔹 {notes_tag}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 13px; font-weight: 800; color: #00F0FF;">{price_str}</div>
                                        <div style="font-size: 11px; font-weight: 800; color: {pct_color}; text-shadow: 0 0 4px {pct_color};">
                                            {pct_str}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        btn_label = "⚡ ACTIVE_VIEW" if is_active else f"📊 PLAN {clean_ticker}"

                        if st.button(
                            btn_label,
                            key=f"btn_select_{clean_ticker}_{idx}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary",
                        ):
                            st.session_state["selected_watchlist_ticker"] = ticker_raw
                            st.rerun()
            else:
                st.caption("NO_DATA_FOUND // Tidak ada saham yang ditemukan.")

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
            st.info("SELECT_TARGET // Pilih salah satu saham dari daftar pantauan di sebelah kiri.")
