import os
import streamlit as st
from trade_planner import TradePlanner


def inject_custom_css():
    """Injects Dark Trading / TradingView-style custom CSS into Streamlit."""
    custom_css = """
    <style>
    /* 1. Global Dark Backgrounds */
    .stApp {
        background-color: #0E1117 !important;
        color: #E6EDF3 !important;
    }
    
    /* 2. Custom Top Header Bar */
    .zio-header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: #161B22;
        padding: 12px 20px;
        border-radius: 8px;
        border: 1px solid #30363D;
        margin-bottom: 20px;
    }
    
    .zio-brand {
        font-size: 20px;
        font-weight: 700;
        color: #00E676;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* 3. Status Badges & Pills */
    .badge-green {
        background-color: #0D2B1D;
        color: #00E676;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid #00E676;
        display: inline-block;
    }
    
    .badge-red {
        background-color: #2D1215;
        color: #FF5252;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid #FF5252;
        display: inline-block;
    }
    
    .badge-info {
        background-color: #161B22;
        color: #58A6FF;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        border: 1px solid #30363D;
        display: inline-block;
    }

    /* 4. Indicator Info Banner (TradingView style) */
    .indicator-banner {
        background-color: #0D2B1D;
        border: 1px solid #00E676;
        border-radius: 6px;
        padding: 10px 16px;
        color: #00E676;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* 5. Streamlit Component Styling Overrides */
    div[data-testid="stMetricValue"] {
        color: #00E676 !important;
        font-weight: 700;
    }
    
    .stButton > button {
        background-color: #238636 !important;
        color: #FFFFFF !important;
        border: 1px solid #2EA043 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #2EA043 !important;
        border-color: #3FB950 !important;
        box-shadow: 0 0 8px rgba(46, 160, 67, 0.4);
    }

    /* Dataframe Table Styling */
    div[data-testid="stDataFrame"] {
        border: 1px solid #30363D;
        border-radius: 6px;
        background-color: #161B22;
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
    """Helper function untuk merender detail Trade Planner di bawah tabel dengan styling TradingView."""
    st.markdown("---")

    # Banner Info Saham
    st.markdown(
        f"""
        <div class="indicator-banner">
            <span>📈 LIVE TRADE PLAN ANALYSIS: <strong>{ticker_symbol}</strong></span>
            <span class="badge-green">REAL-TIME</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
