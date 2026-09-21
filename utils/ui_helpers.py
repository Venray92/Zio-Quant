import os
from html import escape

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from engines.trade_planner import TradePlanner
from utils.card_html import compact_html, emoji_to_icons, strip_emoji
from utils.icons import expander_kwargs, icon_kwargs, svg_icon
from utils.market_source import get_shared_history
from utils import watchlist_store


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


def _js_template_escape(text):
    """Aman dipakai di dalam template literal JavaScript (backtick)."""
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
        .replace("</", "<\\/")
    )


def _history_for_period(symbol, period):
    """Data harian dari file bersama (di luar jam live). None = ambil langsung."""
    if period not in ("3mo", "6mo"):
        return None
    hist = get_shared_history(symbol)
    if hist is None or hist.empty:
        return None
    if period == "3mo":
        cutoff = pd.to_datetime(hist["Date"]).max() - pd.DateOffset(months=3)
        hist = hist[pd.to_datetime(hist["Date"]) >= cutoff]
    return hist


def _rr_text(value):
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "-"
    return f"1 : {v:.1f}" if v > 0 else "-"


def _as_of_text(value, final=True):
    try:
        txt = pd.to_datetime(value).strftime("%d %b %Y")
    except Exception:
        return ""
    return f"Data per {txt}" + ("" if final else " · candle belum final")


_WARN_COLORS = {"ok": "#34d399", "caution": "#fbbf24", "critical": "#ef4444"}


def render_inline_trade_planner(ticker_symbol, key_suffix="default", screener_name="Screener", show_watchlist_button=True):
    st.markdown("---")

    st.markdown(
        f"""
        <div class="live-plan-header">
            <div class="live-plan-title">
                {svg_icon("chart-bar", 22, "currentColor", 2, margin_right=8)}LIVE TRADE PLAN: <span class="live-plan-ticker">{ticker_symbol}</span>
            </div>
            <div style="font-size: 12px; color: #8B949E; font-weight: 600;">
                SYSTEM STATUS: <span style="color: #00F3FF; text-shadow: 0 0 5px #00F3FF;">ONLINE</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_select, _, col_btn = st.columns([1, 2, 1], vertical_alignment="bottom")

    with col_select:
        period_selected = st.selectbox(
            "Analysis Period",
            options=["3mo", "6mo", "1y", "2y"],
            index=1,
            key=f"period_{key_suffix}",
        )

    with col_btn:
        clean_ticker_code = ticker_symbol.upper().strip()
        is_in_watchlist = watchlist_store.is_in_watchlist(clean_ticker_code)

        if not show_watchlist_button:
            pass
        elif is_in_watchlist:
            st.button(
                "In Watchlist",
                key=f"btn_add_wl_{key_suffix}",
                disabled=True,
                use_container_width=True,
                **icon_kwargs("check_circle"),
            )
        else:
            if st.button(
                "Add to Watchlist",
                key=f"btn_add_wl_{key_suffix}",
                use_container_width=True,
                **icon_kwargs("bookmark_add"),
            ):
                active_source = screener_name
                if active_source == "Screener" and "active_screener_name" in st.session_state:
                    active_source = st.session_state.get("active_screener_name", "Screener")

                res = watchlist_store.add_tickers([clean_ticker_code], active_source)
                if res["added"]:
                    st.toast(f"{clean_ticker_code} ({active_source}) berhasil ditambahkan ke Watchlist!")
                elif res["limit"]:
                    st.toast(f"Watchlist penuh (maks {watchlist_store.MAX_ITEMS} saham). Hapus satu dulu.")
                else:
                    st.toast("Saham sudah ada di Watchlist.")
                st.rerun()

    clean_ticker = ticker_symbol.replace(".JK", "").replace("IDX:", "").strip().upper()
    safe_container_id = clean_ticker.replace(".", "_")
    tv_symbol = f"IDX:{clean_ticker}"

    with st.expander(
        f"TradingView Chart: {ticker_symbol}", expanded=False, **expander_kwargs("candlestick_chart")
    ):
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
            f"{svg_icon('bulb', 13, '#E3B341', 2, margin_right=4)}"
            "Harap lakukan screenshot chart jika Anda membuat tarikan garis/analisa visual."
            "</div>",
            unsafe_allow_html=True,
        )

    with st.spinner(f"Analyzing trade plan for {ticker_symbol}..."):
        try:
            planner = TradePlanner(ticker=ticker_symbol.upper(), period=period_selected)
            hist = _history_for_period(ticker_symbol, period_selected)
            planner.fetch_and_prepare_data(data=hist)

            df_plan = planner.generate_trade_plan()

            best_fit = None
            try:
                df_dir = planner.get_direction()
                if df_dir is not None and not df_dir.empty:
                    best_fit = str(df_dir.iloc[0]["Direction"])
            except Exception:
                best_fit = None

            if df_plan is not None and not df_plan.empty:
                # Best Fit (aturan yang sama dengan halaman Trade Planner) tampil paling atas
                if best_fit in ("BOW", "BOB") and "Type" in df_plan.columns:
                    df_plan = pd.concat(
                        [df_plan[df_plan["Type"] == best_fit], df_plan[df_plan["Type"] != best_fit]]
                    ).reset_index(drop=True)

                for idx, row in df_plan.iterrows():
                    plan_no = idx + 1
                    plan_type = str(row.get("Type", row.get("Strategy", f"Plan #{plan_no}")))
                    is_best = best_fit is not None and plan_type == best_fit
                    score = row.get("Score", 0)
                    grade = str(row.get("Grade", "N/A"))
                    grade_short = strip_emoji(grade).replace(" Setup", "")
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
                    tp1_src = str(row.get("TP1 Source", "") or "")
                    tp2_src = str(row.get("TP2 Source", "") or "")
                    rr1, rr2 = _rr_text(row.get("RR_Val")), _rr_text(row.get("RR TP2"))

                    candle_final = bool(row.get("Candle Final", True))
                    as_of = _as_of_text(row.get("Data As Of", ""), candle_final)
                    warn_level = str(row.get("Warning Level", "caution"))
                    warn_color = _WARN_COLORS.get(warn_level, "#fbbf24")
                    warn_items = [w.strip() for w in str(row.get("Warning", "")).split(" | ") if w.strip()]
                    status_level = str(row.get("Status Level", "") or "")
                    candle_name = str(row.get("Pola Candle", "") or "")

                    posisi_color = "#00F3FF" if "Buy Zone" in posisi else "#F59E0B"

                    title_parts = [f"#{plan_no} {plan_type}"]
                    if is_best:
                        title_parts.append("Best Fit")
                    title_parts += [f"{grade_short} {score}", posisi]
                    expander_title = " · ".join(title_parts)

                    copy_lines = [
                        f"=== TRADE PLAN: {ticker_symbol} ===",
                        f"Strategy: {plan_type}{' (Best Fit)' if is_best else ''}",
                        f"Grade: {grade_short}",
                        f"Score: {score}/100",
                        f"Area Buy: {area_buy}",
                        f"Stop Loss: {stop_loss}",
                        f"Target 1 (TP1): {tp1}" + (f" [{tp1_src}]" if tp1_src else ""),
                        f"Target 2 (TP2): {tp2}" + (f" [{tp2_src}]" if tp2_src else ""),
                        f"Risk-Reward: TP1 {rr1}, TP2 {rr2}",
                        f"Status Posisi: {posisi}",
                    ]
                    if as_of:
                        copy_lines.append(as_of)
                    copy_lines.append("===============================")
                    copyable_text = "\n".join(copy_lines)

                    with st.expander(expander_title, expanded=False, **expander_kwargs("target")):
                        unique_btn_id = f"copy_btn_{key_suffix}_{idx}"
                        copy_icon = svg_icon("copy", 13, "#0E1117", 2, margin_right=4)

                        copy_btn_component = f"""
                        <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 8px;">
                            <button id="{unique_btn_id}" style="background: linear-gradient(135deg, #A855F7 0%, #38BDF8 100%); color: #0E1117; border: none; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 10px; cursor: pointer; box-shadow: 0 0 8px rgba(168, 85, 247, 0.4); transition: all 0.2s;">
                                {copy_icon}COPY PLAN
                            </button>
                        </div>
                        <script>
                        const textToCopy_{unique_btn_id} = `{_js_template_escape(copyable_text)}`;
                        const btn_{unique_btn_id} = document.getElementById("{unique_btn_id}");
                        const orig_{unique_btn_id} = btn_{unique_btn_id}.innerHTML;
                        btn_{unique_btn_id}.onclick = function() {{
                            navigator.clipboard.writeText(textToCopy_{unique_btn_id}).then(function() {{
                                btn_{unique_btn_id}.textContent = "COPIED";
                                btn_{unique_btn_id}.style.background = "#00F3FF";
                                setTimeout(function() {{
                                    btn_{unique_btn_id}.innerHTML = orig_{unique_btn_id};
                                    btn_{unique_btn_id}.style.background = "linear-gradient(135deg, #A855F7 0%, #38BDF8 100%)";
                                }}, 2000);
                            }}).catch(function(err) {{
                                console.error('Gagal menyalin text: ', err);
                            }});
                        }};
                        </script>
                        """
                        components.html(copy_btn_component, height=35)

                        best_badge = (
                            '<span style="background: rgba(0,243,255,0.15); border: 1px solid #00F3FF; color: #00F3FF; font-weight: 800; padding: 2px 8px; border-radius: 6px; font-size: 10px; margin-left: 8px;">BEST FIT</span>'
                            if is_best
                            else ""
                        )
                        src1 = f'<div style="font-size: 10px; color: #8B949E; margin-top: 2px;">Sumber: {escape(tp1_src)}</div>' if tp1_src else ""
                        src2 = f'<div style="font-size: 10px; color: #8B949E; margin-top: 2px;">Sumber: {escape(tp2_src)}</div>' if tp2_src else ""
                        warn_html = "".join(
                            f'<div style="font-size: 12px; color: {warn_color}; margin-top: 4px;">{emoji_to_icons(w)}</div>'
                            for w in warn_items
                        )
                        as_of_color = "#8B949E" if candle_final else "#fbbf24"
                        level_html = (
                            f'<div style="font-size: 11px; color: #8B949E; margin-top: 8px;">{escape(status_level)}</div>'
                            if status_level
                            else ""
                        )

                        card_html = f"""
                        <div style="background: linear-gradient(135deg, #161B22 0%, #0D1117 100%); border: 1px solid #30363D; border-left: 5px solid #00F3FF; border-radius: 12px; padding: 18px; margin-top: 4px; margin-bottom: 16px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #21262D; padding-bottom: 12px; margin-bottom: 14px;">
                                <div>
                                    <span style="background: linear-gradient(90deg, #00F3FF 0%, #38BDF8 100%); color: #0E1117; font-weight: 900; font-size: 13px; padding: 4px 12px; border-radius: 6px;">#{plan_no} {escape(plan_type)}</span>
                                    {best_badge}
                                    <span style="font-size: 13px; font-weight: 700; color: #E6EDF3; margin-left: 8px;">{emoji_to_icons(grade)}</span>
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
                                <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 243, 255, 0.2);">
                                    <div style="font-size: 10px; color: #00F3FF; font-weight: 800;">Target 1</div>
                                    <div style="font-size: 15px; font-weight: 800; color: #00F3FF; margin-top: 4px;">{tp1}</div>
                                    {src1}
                                </div>
                                <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 243, 255, 0.2);">
                                    <div style="font-size: 10px; color: #00F3FF; font-weight: 800;">Target 2</div>
                                    <div style="font-size: 15px; font-weight: 800; color: #00F3FF; margin-top: 4px;">{tp2}</div>
                                    {src2}
                                </div>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 12px; background-color: #0E1117; padding: 10px 14px; border-radius: 8px; border: 1px solid #21262D;">
                                <span style="color: #8B949E; font-weight: 600;">Posisi Harga Saat Ini:</span>
                                <span style="font-weight: 800; color: {posisi_color};">{escape(posisi)}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 8px; padding: 0 4px; color: #C9D1D9;">
                                <span>R:R Target 1 <strong style="color: #E6EDF3;">{rr1}</strong></span>
                                <span>R:R Target 2 <strong style="color: #E6EDF3;">{rr2}</strong></span>
                            </div>
                            {level_html}
                            <div style="margin-top: 6px;">{warn_html}</div>
                            <div style="font-size: 11px; color: {as_of_color}; margin-top: 8px;">{escape(as_of)}</div>
                        </div>
                        """
                        st.markdown(compact_html(card_html), unsafe_allow_html=True)

                        with st.expander(
                            f"Score Details & Parameters #{plan_no} ({plan_type})",
                            expanded=False,
                            **expander_kwargs("tune"),
                        ):
                            c1, c2 = st.columns(2)
                            with c1:
                                st.metric(label="R:R (Target 1)", value=rr1)
                            with c2:
                                st.metric(label="R:R (Target 2)", value=rr2)
                            detail_lines = []
                            if row.get("Entry Basis") is not None and pd.notna(row.get("Entry Basis")):
                                detail_lines.append(f"Entry acuan RR: {_format_val(row.get('Entry Basis'))}")
                            if candle_name:
                                detail_lines.append(f"Pola candle: {candle_name}")
                            detail_lines.append(f"Score: {row.get('Score Detail', '-')}")
                            st.caption("  \n".join(detail_lines))
            else:
                st.info(f"Tidak ada Trade Plan yang tersedia untuk **{ticker_symbol}** pada periode ini.")

        except ValueError as e:
            st.warning(f"Trade Plan belum bisa dibuat untuk {ticker_symbol}: {e}")
        except Exception as e:
            st.error(f"Gagal memuat Trade Plan untuk {ticker_symbol}. Coba lagi beberapa saat lagi.")
            with st.expander("Detail teknis", expanded=False):
                st.code(str(e))
