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
            planner.fetch_and_prepare_data()

            # Direction Market
            st.markdown("#### 📌 Direction Market")
            df_dir = planner.get_direction()
            st.dataframe(df_dir, use_container_width=True)

            direction_val = df_dir["Direction"].iloc[0]
            if direction_val == "BOB":
                st.success("Analisis Arah: **BOB (Breakout Buy)**")
            else:
                st.info("Analisis Arah: **BOW (Buy on Weakness)**")

            # Strategy Trade Plan
            st.markdown("#### 🎯 Trade Plan Recommendation")
            df_plan = planner.generate_trade_plan()
            st.dataframe(df_plan, use_container_width=True)

            warning_msg = df_plan["Warning"].iloc[0]
            candle_type = df_plan["Status Candle"].iloc[0]
            st.warning(
                f"**Pola Candle Terdeteksi:** {candle_type} — {warning_msg}"
            )

            # Support & Resistance Levels
            col_sup, col_res = st.columns(2)
            with col_sup:
                st.markdown("#### 🛡️ Support Levels")
                st.dataframe(
                    planner.get_strong_support(), use_container_width=True
                )
            with col_res:
                st.markdown("#### 🧱 Resistance Levels")
                st.dataframe(
                    planner.get_strong_resistance(), use_container_width=True
                )

            # Swing Points
            st.markdown("#### 📍 Swing Points & Metpoints")
            st.dataframe(
                planner.get_swing_points(), use_container_width=True
            )

        except Exception as e:
            st.error(f"Gagal memuat Trade Plan untuk {ticker_symbol}: {e}")
