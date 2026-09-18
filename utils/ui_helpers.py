import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from engines.trade_planner import TradePlanner



def inject_custom_css():
    css_file_path = "assets/styleupdate.css"
    try:
        with open(css_file_path, "r") as f:
            css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"File CSS tidak ditemukan di: {css_file_path}")


def inject_custom_css():
    css_path = os.path.join("assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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


def render_inline_trade_planner(ticker_symbol, key_suffix, screener_name="Screener"):
    st.markdown("---")

    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = []

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

    col_select, _, col_btn = st.columns([1, 2, 1], vertical_alignment="bottom")

    with col_select:
        period_selected = st.selectbox(
            "⏱️ Periode Data Analysis",
            options=["3mo", "6mo", "1y", "2y"],
            index=0,
            key=f"period_{key_suffix}",
        )

    with col_btn:
        clean_ticker_code = ticker_symbol.upper().strip()
        existing_list = [
            x.get("Ticker", x) if isinstance(x, dict) else str(x)
            for x in st.session_state["watchlist"]
        ]
        is_in_watchlist = clean_ticker_code in existing_list

        if is_in_watchlist:
            st.button(
                "✅ In Watchlist",
                key=f"btn_add_wl_{key_suffix}",
                disabled=True,
                use_container_width=True,
            )
        else:
            if st.button(
                "➕ Add to Watchlist",
                key=f"btn_add_wl_{key_suffix}",
                use_container_width=True,
            ):
                active_source = screener_name
                if active_source == "Screener" and "active_screener_name" in st.session_state:
                    active_source = st.session_state.get("active_screener_name", "Screener")

                st.session_state["watchlist"].append(
                    {"Ticker": clean_ticker_code, "Notes": active_source}
                )
                st.toast(
                    f"🚀 **{clean_ticker_code}** ({active_source}) berhasil ditambahkan ke Watchlist!",
                    icon="📌",
                )
                st.rerun()

    clean_ticker = (
        ticker_symbol.replace(".JK", "").replace("IDX:", "").strip().upper()
    )
    safe_container_id = clean_ticker.replace(".", "_")
    tv_symbol = f"IDX:{clean_ticker}"

    with st.expander(f"📈 TradingView Chart: {ticker_symbol}", expanded=False):
        tv_html = f"""
        <div class="tradingview-widget-container" style="height:550px; width:100%; border-radius:10px; overflow:hidden; border: 1px solid #30363D; margin-top: 5px; margin-bottom: 8px;">
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
                "toolbar_bg": "#1A1A1A",
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
        components.html(tv_html, height=560)
        st.markdown(
            "<div style='font-size: 11px; color: #8B949E; margin-bottom: 10px; font-weight: 500;'>"
            "💡 *Harap lakukan screenshot chart jika Anda membuat tarikan garis/analisa visual.*"
            "</div>",
            unsafe_allow_html=True,
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

                    is_suggestion = (idx == 0)
                    prefix_label = "Trade Plan Suggestion" if is_suggestion else "Trade Plan Other"
                    expander_title = f"🎯 {prefix_label} #{plan_no} {plan_type} ({ticker_symbol}) - Score: {score}"

                    # Teks format bersih untuk disalin
                    copyable_text = f"=== TRADE PLAN: {ticker_symbol} ===\\nStrategy: {plan_type}\\nGrade: {grade}\\nScore: {score}/100\\nArea Buy: {area_buy}\\nStop Loss: {stop_loss}\\nTarget 1 (TP1): {tp1}\\nTarget 2 (TP2): {tp2}\\nStatus Posisi: {posisi}\\n==============================="

                    with st.expander(expander_title, expanded=False):
                        unique_btn_id = f"copy_btn_{key_suffix}_{idx}"
                        
                        # Menggunakan komponen widget kecil HTML/JS terisolasi agar tombol pas di sebelah score dan langsung copy ke clipboard
                        copy_btn_component = f"""
                        <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 8px;">
                            <button id="{unique_btn_id}" style="background: linear-gradient(135deg, #A855F7 0%, #38BDF8 100%); color: #0E1117; border: none; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 10px; cursor: pointer; box-shadow: 0 0 8px rgba(168, 85, 247, 0.4); transition: all 0.2s;">
                                📋 COPY PLAN
                            </button>
                        </div>
                        <script>
                        const textToCopy_{unique_btn_id} = `{copyable_text}`;
                        const btn_{unique_btn_id} = document.getElementById("{unique_btn_id}");
                        btn_{unique_btn_id}.onclick = function() {{
                            navigator.clipboard.writeText(textToCopy_{unique_btn_id}).then(function() {{
                                btn_{unique_btn_id}.innerText = "✅ COPIED!";
                                btn_{unique_btn_id}.style.background = "#00E676";
                                setTimeout(function() {{
                                    btn_{unique_btn_id}.innerText = "📋 COPY PLAN";
                                    btn_{unique_btn_id}.style.background = "linear-gradient(135deg, #A855F7 0%, #38BDF8 100%)";
                                }}, 2000);
                            }}).catch(function(err) {{
                                console.error('Gagal menyalin text: ', err);
                            }});
                        }};
                        </script>
                        """
                        components.html(copy_btn_component, height=35)

                        card_html = f"""
                        <div style="background: linear-gradient(135deg, #161B22 0%, #0D1117 100%); border: 1px solid #30363D; border-left: 5px solid #00E676; border-radius: 12px; padding: 18px; margin-top: 4px; margin-bottom: 16px;">
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
                            f"⚙️ Parameter Lengkap & Rasio R:R #{plan_no} ({plan_type})",
                            expanded=False,
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
            else:
                st.info(f"Tidak ada Trade Plan yang tersedia untuk **{ticker_symbol}** pada periode ini.")

        except Exception as e:
            st.error(f"Gagal memuat Trade Plan: {e}")
