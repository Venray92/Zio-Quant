import os
import pandas as pd
import streamlit as st
from trade_planner import TradePlanner


def inject_custom_css():
    """Injects Cyber-Futuristic Dark Trading UI into Streamlit."""
    custom_css = """
    <style>
    /* Global App Background */
    .stApp {
        background-color: #0B0E14 !important;
        color: #E6EDF3 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Section Header Card */
    .indicator-header {
        background: linear-gradient(135deg, #161B22 0%, #0D1117 100%);
        border-left: 5px solid #00E676;
        border: 1px solid #30363D;
        border-left-width: 5px;
        padding: 16px 20px;
        border-radius: 12px;
        margin-top: 15px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .indicator-title {
        font-size: 18px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: 0.8px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .indicator-badge {
        background: rgba(0, 230, 118, 0.15);
        color: #00E676;
        border: 1px solid rgba(0, 230, 118, 0.3);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
    }

    /* Subheader Section */
    .section-title {
        font-size: 14px;
        font-weight: 800;
        color: #38BDF8;
        margin-top: 20px;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* --- STYLED SCREENING BUTTONS --- */
    /* Run Screening Button (Green Glow) */
    div.stButton > button[key="btn_run"] {
        background: linear-gradient(135deg, #00E676 0%, #00B0FF 100%) !important;
        color: #0B0E14 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 900 !important;
        font-size: 14px !important;
        letter-spacing: 0.8px !important;
        padding: 12px 24px !important;
        width: 100% !important;
        box-shadow: 0 0 15px rgba(0, 230, 118, 0.4) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
    }

    div.stButton > button[key="btn_run"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 25px rgba(0, 230, 118, 0.7) !important;
    }

    /* Stop Button (Red Alert Glow) */
    div.stButton > button[key="btn_stop"] {
        background: linear-gradient(135deg, #FF5252 0%, #FF1744 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 900 !important;
        font-size: 14px !important;
        letter-spacing: 0.8px !important;
        padding: 12px 24px !important;
        width: 100% !important;
        box-shadow: 0 0 15px rgba(255, 82, 82, 0.4) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
    }

    div.stButton > button[key="btn_stop"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 25px rgba(255, 82, 82, 0.7) !important;
    }

    /* --- RADIO BUTTON STYLING (SIGNAL MODE) --- */
    div[data-testid="stRadio"] > label {
        color: #8B949E !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] {
        background: #161B22;
        border: 1px solid #30363D;
        padding: 6px;
        border-radius: 10px;
        display: flex;
        gap: 10px;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label {
        background: #0D1117;
        border: 1px solid #21262D;
        border-radius: 8px;
        padding: 8px 16px;
        color: #C9D1D9 !important;
        font-weight: 700 !important;
        cursor: pointer;
        transition: all 0.2s ease;
        flex: 1;
        text-align: center;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
        border-color: #38BDF8;
        color: #38BDF8 !important;
    }

    /* Dropdown & Selectbox Styling */
    div[data-baseweb="select"] > div {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
        color: #E6EDF3 !important;
    }

    /* Metric Cards in Expander */
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

    /* Expander Styling */
    div[data-testid="stExpander"] {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 10px !important;
        margin-top: 10px;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_screening_controls():
    """Renders the styled indicator header, signal mode selector, and screening control buttons."""
    # 1. Indicator Title Banner
    st.markdown(
        '''
        <div class="indicator-header">
            <div class="indicator-title">
                📈 STOCHASTIC & PARABOLIC SAR
            </div>
            <div class="indicator-badge">
                STRATEGY SCANNER
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    # 2. Choose Signal Mode Section
    st.markdown('<div class="section-title">🎯 Choose Signal Mode</div>', unsafe_allow_html=True)
    
    signal_mode = st.radio(
        label="Signal Selection",
        options=["GOLDEN CROSS", "DEAD CROSS"],
        index=0,
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    # 3. Action Control Buttons (RUN & STOP)
    col_run, col_stop = st.columns(2)
    
    with col_run:
        run_pressed = st.button("▶ RUNNING SCREENING", key="btn_run")
        
    with col_stop:
        stop_pressed = st.button("⏹ STOP", key="btn_stop")

    return signal_mode, run_pressed, stop_pressed


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


def render_inline_trade_planner(ticker_symbol, key_suffix):
    st.markdown("---")
    
    # 1. LIVE TRADE PLAN HEADER
    st.markdown(
        f'''
        <div class="indicator-header">
            <div class="indicator-title">
                📊 LIVE TRADE PLAN: <span style="color: #00E676; background: rgba(0,230,118,0.1); padding: 2px 8px; border-radius: 6px;">{ticker_symbol}</span>
            </div>
            <div style="font-size: 12px; color: #8B949E; font-weight: 600;">
                SYSTEM STATUS: <span style="color: #00E676;">ONLINE</span>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    col_select, col_space = st.columns([1, 2])
    with col_select:
        period_selected = st.selectbox(
            "⏱️ Data Analysis Period",
            options=["3mo", "6mo", "1y", "2y"],
            index=0,
            key=f"period_{key_suffix}",
        )

    with st.spinner(f"⚡ Analyzing & Calculating Trade Plan for {ticker_symbol}..."):
        try:
            planner = TradePlanner(ticker=ticker_symbol.upper(), period=period_selected)
            if hasattr(planner, "fetch_and_prepare_data"):
                planner.fetch_and_prepare_data()

            df_plan = planner.generate_trade_plan() if hasattr(planner, "generate_trade_plan") else None

            if df_plan is not None and not (hasattr(df_plan, "empty") and df_plan.empty):
                st.markdown('<div class="section-title">🎯 Trade Plan Recommendation</div>', unsafe_allow_html=True)

                for idx, row in df_plan.iterrows():
                    plan_no = idx + 1
                    plan_type = row.get("Type", row.get("Strategy", f"Plan #{plan_no}"))
                    score = row.get("Score", 0)
                    grade = row.get("Grade", "N/A")
                    posisi = row.get("Posisi Harga", row.get("Status", "-"))

                    # Range calculation
                    range_min = _format_val(row.get("Range Buy Min", row.get("Buy Min", "-")))
                    range_max = _format_val(row.get("Range Buy Max", row.get("Buy Max", "-")))
                    area_buy = row.get("Area Buy", None)
                    if not area_buy or area_buy == "-":
                        area_buy = f"{range_min} - {range_max}" if range_min != "-" and range_max != "-" else (range_min if range_min != "-" else range_max)

                    stop_loss = _format_val(row.get("Stop Loss", row.get("SL", "-")))
                    tp1 = _format_val(row.get("TP 1", row.get("TP1", row.get("Target 1", "-"))))
                    tp2 = _format_val(row.get("TP 2", row.get("TP2", row.get("Target 2", "-"))))

                    grade_badge = "🟢" if "A" in str(grade) else ("🟡" if "B" in str(grade) else "⚪")
                    posisi_color = "#10B981" if "Buy Zone" in str(posisi) else "#F59E0B"

                    # CARD COMPONENT
                    card_html = f'''
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
                                <div style="font-size: 10px; color: #38BDF8; font-weight: 800; text-transform: uppercase;">Buy Area</div>
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
                            <span style="color: #8B949E; font-weight: 600;">Current Price Position:</span>
                            <span style="font-weight: 800; color: {posisi_color};">{posisi}</span>
                        </div>
                    </div>
                    '''
                    st.markdown(card_html, unsafe_allow_html=True)

                    # R:R Calculation
                    rr_tp1_val, rr_tp2_val = calculate_rr_ratios(row)

                    # EXPANDER
                    with st.expander(f"⚙️ Detailed Parameters & R:R Ratios #{plan_no} ({plan_type})", expanded=True):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.metric(label="R:R ( Target 1 )", value=rr_tp1_val)
                        with c2:
                            st.metric(label="R:R ( Target 2 )", value=rr_tp2_val)

                        skip_cols = [
                            "No", "no", "index", "RR_Val", "rr_val", "Rasio (R:R)", "R:R", "RR",
                            "Type", "Strategy", "Score", "Grade", "Posisi Harga", "Status",
                            "Range Buy Min", "Buy Min", "Range Buy Max", "Buy Max", "Area Buy",
                            "Stop Loss", "SL", "TP 1", "TP1", "Target 1", "TP 2", "TP2", "Target 2",
                            "Warning", "Status Candle"
                        ]
                        extra_cols = [c for c in df_plan.columns if c not in skip_cols]

                        if extra_cols:
                            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                            cols_per_row = 3
                            for i in range(0, len(extra_cols), cols_per_row):
                                chunk_cols = extra_cols[i:i + cols_per_row]
                                ui_cols = st.columns(len(chunk_cols))
                                for col_idx, c_name in enumerate(chunk_cols):
                                    val = _format_val(row[c_name])
                                    ui_cols[col_idx].metric(label=c_name, value=val)

        except Exception as e:
            st.error(f"Failed to load Trade Plan: {e}")
