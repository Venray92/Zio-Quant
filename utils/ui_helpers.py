import os
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
        font-size: 20px !important;
        font-weight: 700 !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #8B949E !important;
        font-size: 12px !important;
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
                st.dataframe(df_plan, use_container_width=True)

                if hasattr(df_plan, "columns") and len(df_plan) > 0:
                    warning_msg = df_plan["Warning"].iloc[0] if "Warning" in df_plan.columns else "-"
                    candle_type = df_plan["Status Candle"].iloc[0] if "Status Candle" in df_plan.columns else "-"
                    
                    if candle_type != "-" or warning_msg != "-":
                        st.warning(
                            f"**Pola Candle Terdeteksi:** {candle_type} — {warning_msg}"
                        )

            # 2. Support & Resistance Levels (Tampil jika ada data)
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
