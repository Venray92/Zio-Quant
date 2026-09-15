import os
import streamlit as st
from trade_planner import TradePlanner


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