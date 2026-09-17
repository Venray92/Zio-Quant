import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from engines.trade_planner import TradePlanner


def inject_custom_css():
    """Injects Cyber-Futuristic Dark Trading UI & Custom CSS into Streamlit safely."""
    css_file_path = "rsi.css"

    # 1. Prioritaskan membaca file rsi.css jika tersedia
    if os.path.exists(css_file_path):
        with open(css_file_path, "r", encoding="utf-8") as f:
            custom_css = f"<style>\n{f.read()}\n</style>"
    else:
        # 2. Fallback CSS dengan selector yang aman (tanpa merusak layout global)
        custom_css = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

        /* Global Font & Background */
        .stApp {
            background-color: #0d1117 !important;
            color: #C0C5D0 !important;
            font-family: 'Share Tech Mono', monospace !important;
        }

        /* Header Bar Styling */
        .brand-link {
            display: inline-flex;
            align-items: center;
            gap: 14px;
            text-decoration: none !important;
            cursor: pointer;
        }

        .brand-logo-img {
            width: 48px;
            height: 48px;
            border-radius: 8px;
            object-fit: cover;
            border: 1.5px solid #00F3FF;
            box-shadow: 0 0 12px rgba(0, 243, 255, 0.4);
        }

        .brand-title-text {
            color: #00F3FF;
            font-size: 22px;
            font-weight: 900;
            letter-spacing: 1px;
            text-shadow: 0 0 10px rgba(0, 243, 255, 0.6);
            font-family: 'Share Tech Mono', monospace;
        }

        /* Trade Plan Header Card */
        .live-plan-header {
            background: linear-gradient(90deg, rgba(0, 230, 118, 0.15) 0%, rgba(56, 189, 248, 0.05) 100%);
            border-left: 5px solid #00E676;
            padding: 12px 18px;
            border-radius: 8px;
            margin-top: 10px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .live-plan-title {
            font-size: 18px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 0.5px;
        }

        .live-plan-ticker {
            color: #00E676;
            background: rgba(0, 230, 118, 0.1);
            padding: 2px 10px;
            border-radius: 6px;
            border: 1px solid rgba(0, 230, 118, 0.3);
        }

        .section-title {
            font-size: 16px;
            font-weight: 700;
            color: #38BDF8;
            margin-top: 15px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Metric Box Styling */
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #161B22 0%, #0D1117 100%);
            border: 1px solid #21262D;
            padding: 12px 16px;
            border-radius: 10px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }

        div[data-testid="stMetricValue"] {
            color: #00E676 !important;
            font-size: 20px !important;
            font-weight: 800 !important;
        }

        div[data-testid="stMetricLabel"] {
            color: #8B949E !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
        }

        div[data-testid="stExpander"] {
            background-color: #161B22 !important;
            border: 1px solid #30363D !important;
            border-radius: 10px !important;
            margin-top: 10px;
        }
        </style>
        """

    st.markdown(custom_css, unsafe_allow_html=True)


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
        row.get(
            "Range Buy Max", row.get("Buy Max", row.get("Buy Min", None))
        )
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


def render_inline_trade_planner(ticker_symbol, key_suffix):
    st.markdown("---")

    # 1. HEADER LIVE TRADE PLAN
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

    # 2. DROPDOWN PERIODE
    col_select, col_space = st.columns([1, 2])
    with col_select:
        period_selected = st.selectbox(
            "⏱️ Periode Data Analysis",
            options=["3mo", "6mo", "1y", "2y"],
            index=0,
            key=f"period_{key_suffix}",
        )

    # 3. TRADINGVIEW WIDGET
    clean_ticker = (
        ticker_symbol.replace(".JK", "").replace("IDX:", "").strip().upper()
    )
    tv_symbol = f"IDX:{clean_ticker}"

    tv_html = f"""
    <div class="tradingview-widget-container" style="height:550px; width:100%; border-radius:10px; overflow:hidden; border: 1px solid #30363D; margin-top: 10px; margin-bottom: 8px;">
      <div id="tv_chart_container_{clean_ticker}" style="height:100%; width:100%;"></div>
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
            "container_id": "tv_chart_container_{clean_ticker}"
          }});
      }}
      </script>
    </div>
    """
    components.html(tv_html, height=560)

    st.markdown(
        "<div style='font-size: 11px; color: #8B949E; margin-bottom: 20px; font-weight: 500;'>"
        "*Harap lakukan screenshot chart jika Anda membuat tarikan garis/analisa visual, karena sistem tidak menyimpan tarikan garis secara otomatis saat Anda berpindah saham."
        "</div>",
        unsafe_allow_html=True,
    )

    # 4. TRADE PLAN RECOMMENDATION
    with st.spinner(
        f"⚡ Menganalisis & Mengkalkulasi Trade Plan {ticker_symbol}..."
    ):
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

            if df_plan is not None and not (
                hasattr(df_plan, "empty") and df_plan.empty
            ):
                st.markdown(
                    '<div class="section-title">🎯 Trade Plan Recommendation</div>',
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
                    area_buy = row.get("Area Buy", None)
                    if not area_buy or area_buy == "-":
                        area_buy = (
                            f"{range_min} - {range_max}"
                            if range_min != "-" and range_max != "-"
                            else (range_min if range_min != "-" else range_max)
                        )

                    stop_loss = _format_val(
                        row.get("Stop Loss", row.get("SL", "-"))
                    )
                    tp1 = _format_val(
                        row.get(
                            "TP 1", row.get("TP1", row.get("Target 1", "-"))
                        )
                    )
                    tp2 = _format_val(
                        row.get(
                            "TP 2", row.get("TP2", row.get("Target 2", "-"))
                        )
                    )

                    grade_badge = (
                        "🟢"
                        if "A" in str(grade)
                        else ("🟡" if "B" in str(grade) else "⚪")
                    )
                    posisi_color = (
                        "#10B981" if "Buy Zone" in str(posisi) else "#F59E0B"
                    )

                    card_html = f"""
                    <div style="background: linear-gradient(135deg, #161B22 0%, #0D1117 100%); border: 1px solid #30363D; border-left: 5px solid #00E676; border-radius: 12px; padding: 18px; margin-bottom: 16px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #21262D; padding-bottom: 12px; margin-bottom: 14px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="background: linear-gradient(90deg, #00E676 0%, #38BDF8 100%); color: #0E1117; font-weight: 900; font-size: 13px; padding: 4px 12px; border-radius: 6px; text-transform: uppercase;">#{plan_no} {plan_type}</span>
                                <span style="font-size: 13px; font-weight: 700; color: #E6EDF3;">{grade_badge} {grade}</span>
                            </div>
                            <div style="background: rgba(168, 85, 247, 0.15); border: 1px solid #A855F7; color: #F3E8FF; font-weight: 800; padding: 4px 14px; border-radius: 20px; font-size: 12px; box-shadow: 0 0 12px rgba(168, 85, 247, 0.25);">
                                SCORE: {score}
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 14px; text-align: center;">
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.2);">
                                <div style="font-size: 10px; color: #38BDF8; font-weight: 800; text-transform: uppercase;">Area Buy</div>
                                <div style="font-size: 15px; font-weight: 800; color: #38BDF8; margin-top: 4px;">{area_buy}</div>
                            </div>
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(255, 82, 82, 0.2);">
                                <div style="font-size: 10px; color: #FF5252; font-weight: 800; text-transform: uppercase;">Stop Loss</div>
                                <div style="font-size: 15px; font-weight: 800; color: #FF5252; margin-top: 4px;">{stop_loss}</div>
                            </div>
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 230, 118, 0.2);">
                                <div style="font-size: 10px; color: #00E676; font-weight: 800; text-transform: uppercase;">Target 1 (TP 1)</div>
                                <div style="font-size: 15px; font-weight: 800; color: #00E676; margin-top: 4px;">{tp1}</div>
                            </div>
                            <div style="background: rgba(14, 17, 23, 0.9); padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 230, 118, 0.2);">
                                <div style="font-size: 10px; color: #00E676; font-weight: 800; text-transform: uppercase;">Target 2 (TP 2)</div>
                                <div style="font-size: 15px; font-weight: 800; color: #00E676; margin-top: 4px;">{tp2}</div>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; background-color: #0E1117; padding: 10px 14px; border-radius: 8px; border: 1px solid #21262D;">
                            <span style="color: #8B949E; font-weight: 600;">Posisi Harga Saat Ini:</span>
                            <span style="font-weight: 800; color: {posisi_color};">{posisi}</span>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

                    rr_tp1_val, rr_tp2_val = calculate_rr_ratios(row)

                    with st.expander(
                        f"⚙️ Parameter Lengkap & Rasio R:R #{plan_no} ({plan_type})",
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
