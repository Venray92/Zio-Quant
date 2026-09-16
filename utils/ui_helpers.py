import os
import pandas as pd
import streamlit as st
from trade_planner import TradePlanner


def inject_custom_css():
    """Injects Dark Trading / Stockbit-style custom CSS into Streamlit."""
    custom_css = """
    <style>
    /* Global Background */
    .stApp {
        background-color: #0E1117 !important;
        color: #E6EDF3 !important;
    }
    
    /* Header Bar Minimalis */
    .zio-header-container {
        display: flex;
        align-items: center;
        background-color: #161B22;
        padding: 10px 16px;
        border-radius: 6px;
        border: 1px solid #21262D;
        margin-bottom: 15px;
    }
    
    .zio-brand {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Styling Info Box / Empty State Card */
    div[data-testid="stAlert"] {
        background-color: #161B22 !important;
        color: #8B949E !important;
        border: 1px solid #21262D !important;
        border-radius: 6px !important;
        padding: 12px 16px !important;
    }

    /* Styling Tombol Utama (Green Action Button) */
    .stButton > button {
        background-color: #0D2B1D !important;
        color: #00E676 !important;
        border: 1px solid #00E676 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 6px 16px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #00E676 !important;
        color: #0E1117 !important;
        box-shadow: 0 0 10px rgba(0, 230, 118, 0.3) !important;
    }

    /* Dataframe Table Styling */
    div[data-testid="stDataFrame"] {
        border: 1px solid #21262D;
        border-radius: 6px;
        background-color: #161B22;
    }
    
    /* Metric Card Custom Style */
    div[data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #21262D;
        padding: 10px 15px;
        border-radius: 6px;
    }
    
    div[data-testid="stMetricValue"] {
        color: #00E676 !important;
        font-size: 18px !important;
        font-weight: 700 !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #8B949E !important;
        font-size: 11px !important;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def load_daftar_saham(filepath="daftar_saham.txt"):
    """Helper Robust untuk membaca & membersihkan daftar saham dari file TXT."""
    if not os.path.exists(filepath):
        return []

    tickers = []
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            for line in f:
                item = line.strip().upper()
                if item and item not in ["KODE", "TICKER", "SAHAM"]:
                    clean_t = item.split(",")[0].replace(".JK", "").strip()
                    if clean_t:
                        tickers.append(f"{clean_t}.JK")
        return sorted(list(set(tickers)))
    except Exception as e:
        st.error(f"Gagal membaca `{filepath}`: {e}")
        return []


def _safe_get_method_or_attr(obj, possible_names):
    """Helper internal untuk mengambil data dari objek TradePlanner secara fleksibel."""
    for name in possible_names:
        if hasattr(obj, name):
            attr = getattr(obj, name)
            if callable(attr):
                try:
                    return attr()
                except Exception:
                    continue
            return attr
    return None


def _format_val(val):
    """Helper formatting nilai numerik menjadi pemisah ribuan atau string bersih."""
    if pd.isna(val) or val is None or val == "" or val == "-":
        return "-"
    try:
        num = float(val)
        return f"{int(num):,}" if num.is_integer() else f"{num:,.2f}"
    except (ValueError, TypeError):
        return str(val)


def _clean_num(val):
    """Helper konversi string/angka menjadi float murni."""
    if pd.isna(val) or val is None or val == "" or val == "-":
        return None
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return float(val)
    except Exception:
        return None


def calculate_rr_ratios(row):
    """Menghitung Rasio Risk:Reward (TP1) dan Risk:Reward (TP2) secara matematis."""
    buy_val = _clean_num(row.get("Range Buy Max", row.get("Buy Max", row.get("Buy Min", None))))
    sl_val = _clean_num(row.get("Stop Loss", row.get("SL", None)))
    tp1_val = _clean_num(row.get("TP 1", row.get("TP1", row.get("Target 1", None))))
    tp2_val = _clean_num(row.get("TP 2", row.get("TP2", row.get("Target 2", None))))

    rr_tp1_str = "-"
    rr_tp2_str = "-"

    if buy_val and sl_val and (buy_val > sl_val):
        risk = buy_val - sl_val
        
        # Risk to Reward Target 1
        if tp1_val and tp1_val > buy_val:
            reward1 = tp1_val - buy_val
            rr1 = reward1 / risk
            rr_tp1_str = f"1 : {rr1:.1f}"
            
        # Risk to Reward Target 2
        if tp2_val and tp2_val > buy_val:
            reward2 = tp2_val - buy_val
            rr2 = reward2 / risk
            rr_tp2_str = f"1 : {rr2:.1f}"

    return rr_tp1_str, rr_tp2_str


def render_inline_trade_planner(ticker_symbol, key_suffix):
    """Helper function untuk merender detail Trade Planner di bawah tabel."""
    st.markdown("---")
    st.subheader(f"📊 Live Trade Plan: **{ticker_symbol}**")

    period_selected = st.selectbox(
        "Periode Data Analysis",
        options=["3mo", "6mo", "1y", "2y"],
        index=0,
        key=f"period_{key_suffix}",
    )

    with st.spinner(f"Menghitung Trade Plan untuk {ticker_symbol}..."):
        try:
            planner = TradePlanner(
                ticker=ticker_symbol.upper(), period=period_selected
            )
            
            # Fetch & prepare data
            if hasattr(planner, "fetch_and_prepare_data"):
                planner.fetch_and_prepare_data()

            # 1. Strategy Trade Plan
            df_plan = _safe_get_method_or_attr(planner, ["generate_trade_plan", "get_trade_plan"])
            
            if df_plan is not None and not (hasattr(df_plan, "empty") and df_plan.empty):
                st.markdown("#### 🎯 Trade Plan Recommendation")

                for idx, row in df_plan.iterrows():
                    plan_no = idx + 1
                    plan_type = row.get("Type", row.get("Strategy", f"Plan #{plan_no}"))
                    score = row.get("Score", 0)
                    grade = row.get("Grade", "N/A")
                    posisi = row.get("Posisi Harga", row.get("Status", "-"))
                    
                    # Target harga & range utama
                    range_min = _format_val(row.get("Range Buy Min", row.get("Buy Min", "-")))
                    range_max = _format_val(row.get("Range Buy Max", row.get("Buy Max", "-")))
                    
                    area_buy = row.get("Area Buy", None)
                    if not area_buy or area_buy == "-":
                        if range_min != "-" and range_max != "-":
                            area_buy = f"{range_min} - {range_max}"
                        else:
                            area_buy = range_min if range_min != "-" else range_max

                    stop_loss = _format_val(row.get("Stop Loss", row.get("SL", "-")))
                    tp1 = _format_val(row.get("TP 1", row.get("TP1", row.get("Target 1", "-"))))
                    tp2 = _format_val(row.get("TP 2", row.get("TP2", row.get("Target 2", "-"))))

                    grade_badge = "🟢" if "A" in str(grade) else ("🟡" if "B" in str(grade) else "⚪")
                    posisi_color = "#10B981" if "Buy Zone" in str(posisi) else "#F59E0B"

                    # MAIN CARD FUTURISTIK
                    card_html = (
                        f'<div style="background: linear-gradient(135deg, #161B22 0%, #0D1117 100%); border: 1px solid #30363D; border-left: 4px solid #00E676; border-radius: 12px; padding: 16px; margin-bottom: 15px; box-shadow: 0 8px 24px rgba(0,0,0,0.4);">'
                        f'<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #21262D; padding-bottom: 10px; margin-bottom: 12px;">'
                        f'<div style="display: flex; align-items: center; gap: 10px;">'
                        f'<span style="background: linear-gradient(90deg, #00E676 0%, #38BDF8 100%); color: #0E1117; font-weight: 900; font-size: 13px; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; letter-spacing: 0.5px;">#{plan_no} {plan_type}</span>'
                        f'<span style="font-size: 13px; font-weight: 700; color: #E6EDF3;">{grade_badge} {grade}</span>'
                        f'</div>'
                        f'<div style="background: rgba(139, 92, 246, 0.2); border: 1px solid #A855F7; color: #E9D5FF; font-weight: 800; padding: 3px 12px; border-radius: 20px; font-size: 12px; box-shadow: 0 0 10px rgba(168, 85, 247, 0.3);">'
                        f'SCORE: {score}'
                        f'</div>'
                        f'</div>'
                        f'<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px; text-align: center;">'
                        f'<div style="background-color: rgba(14, 17, 23, 0.8); padding: 10px; border-radius: 8px; border: 1px solid #38BDF833;">'
                        f'<div style="font-size: 10px; color: #38BDF8; font-weight: 700; text-transform: uppercase;">Area Buy</div>'
                        f'<div style="font-size: 14px; font-weight: 800; color: #38BDF8; margin-top: 4px;">{area_buy}</div>'
                        f'</div>'
                        f'<div style="background-color: rgba(14, 17, 23, 0.8); padding: 10px; border-radius: 8px; border: 1px solid #FF525233;">'
                        f'<div style="font-size: 10px; color: #FF5252; font-weight: 700; text-transform: uppercase;">Stop Loss</div>'
                        f'<div style="font-size: 14px; font-weight: 800; color: #FF5252; margin-top: 4px;">{stop_loss}</div>'
                        f'</div>'
                        f'<div style="background-color: rgba(14, 17, 23, 0.8); padding: 10px; border-radius: 8px; border: 1px solid #00E67633;">'
                        f'<div style="font-size: 10px; color: #00E676; font-weight: 700; text-transform: uppercase;">TP 1</div>'
                        f'<div style="font-size: 14px; font-weight: 800; color: #00E676; margin-top: 4px;">{tp1}</div>'
                        f'</div>'
                        f'<div style="background-color: rgba(14, 17, 23, 0.8); padding: 10px; border-radius: 8px; border: 1px solid #00E67633;">'
                        f'<div style="font-size: 10px; color: #00E676; font-weight: 700; text-transform: uppercase;">TP 2</div>'
                        f'<div style="font-size: 14px; font-weight: 800; color: #00E676; margin-top: 4px;">{tp2}</div>'
                        f'</div>'
                        f'</div>'
                        f'<div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; background-color: #0E1117; padding: 8px 12px; border-radius: 6px; border: 1px solid #21262D;">'
                        f'<span style="color: #8B949E; font-weight: 600;">Posisi Harga Saat Ini:</span>'
                        f'<span style="font-weight: 800; color: {posisi_color};">{posisi}</span>'
                        f'</div>'
                        f'</div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)

                    # Kalkulasi R:R untuk TP1 dan TP2 secara presisi
                    rr_tp1_val, rr_tp2_val = calculate_rr_ratios(row)

                    # TAMPILKAN PARAMETER DETAIL (INCL. 2 KOTAK R:R)
                    with st.expander(f"📋 Detail Lengkap Parameter #{plan_no} ({plan_type})", expanded=True):
                        # Row 1: Dua Kotak R:R (Target 1 & Target 2)
                        col_rr1, col_rr2 = st.columns(2)
                        with col_rr1:
                            st.metric(label="R:R ( Target 1 )", value=rr_tp1_val)
                        with col_rr2:
                            st.metric(label="R:R ( Target 2 )", value=rr_tp2_val)

                        # Row 2+: Sisa Parameter Tambahan (Polos dari Kolom Mentah)
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

                # Banner warning jika ada
                if hasattr(df_plan, "columns") and len(df_plan) > 0:
                    warning_msg = df_plan["Warning"].iloc[0] if "Warning" in df_plan.columns else "-"
                    candle_type = df_plan["Status Candle"].iloc[0] if "Status Candle" in df_plan.columns else "-"
                    
                    if candle_type != "-" or warning_msg != "-":
                        st.warning(
                            f"**Pola Candle Terdeteksi:** {candle_type} — {warning_msg}"
                        )

            # 2. Support & Resistance Levels
            df_sup = _safe_get_method_or_attr(
                planner, ["get_strong_support", "get_support_levels", "get_support", "support_levels"]
            )
            df_res = _safe_get_method_or_attr(
                planner, ["get_strong_resistance", "get_resistance_levels", "get_resistance", "resistance_levels"]
            )

            has_sup = df_sup is not None and not (hasattr(df_sup, "empty") and df_sup.empty)
            has_res = df_res is not None and not (hasattr(df_res, "empty") and df_res.empty)

            if has_sup or has_res:
                col_sup, col_res = st.columns(2)
                with col_sup:
                    if has_sup:
                        st.markdown("#### 🛡️ Support Levels")
                        st.dataframe(df_sup, use_container_width=True)

                with col_res:
                    if has_res:
                        st.markdown("#### 🧱 Resistance Levels")
                        st.dataframe(df_res, use_container_width=True)

            # 3. Swing Points
            df_swing = _safe_get_method_or_attr(planner, ["get_swing_points", "swing_points"])
            if df_swing is not None and not (hasattr(df_swing, "empty") and df_swing.empty):
                st.markdown("#### 📍 Swing Points & Metpoints")
                st.dataframe(df_swing, use_container_width=True)

        except Exception as e:
            st.error(f"Gagal memuat Trade Plan untuk {ticker_symbol}: {e}")
