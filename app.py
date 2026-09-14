import concurrent.futures
import pandas as pd
import streamlit as st

# 1. Import modul yang ada di repositori kamu
from screener_rsi_divergence import (
    TICKERS as RSI_TICKERS,
    detect_rsi_patterns_and_score,
)
from screener_stoch_psar import run_stoch_psar_screener
from trade_planner import TradePlanner  # Import Class TradePlanner langsung

# 2. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="ZIO QUANT - Screener & Trade Planner",
    page_icon="📈",
    layout="wide",
)

st.title("📈 ZIO QUANT Dashboard")
st.markdown(
    "Aplikasi screening saham berbasis **RSI Divergence**, **Stochastic & Parabolic SAR**, serta kalkulator **Trade Planner**."
)

# 3. Membuat Tab Navigasi
tab1, tab2, tab3 = st.tabs(
    [
        "🔄 RSI Divergence",
        "⚡ Stochastic & Parabolic SAR",
        "🎯 Trade Planner",
    ]
)

# ==========================================
# TAB 1: RSI DIVERGENCE (Safety Fix Applied)
# ==========================================
with tab1:
    st.header("Screener RSI Divergence & Patterns")
    st.caption(
        "Deteksi pola RSI Divergence (Bullish/Bearish) dan scoring kekuatan tren."
    )

    if st.button("Jalankan Screener RSI", key="btn_rsi"):
        with st.spinner(
            f"Menganalisis {len(RSI_TICKERS)} saham menggunakan multi-threading..."
        ):
            results_rsi = []
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=10
            ) as executor:
                futures = [
                    executor.submit(detect_rsi_patterns_and_score, ticker)
                    for ticker in RSI_TICKERS
                ]
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    if res is not None:
                        results_rsi.append(res)

            if results_rsi:
                df_rsi = pd.DataFrame(results_rsi)

                # Cek fleksibel untuk kolom Score / score
                score_col = None
                for col in ["Score", "score", "total_score", "RSI_Score"]:
                    if col in df_rsi.columns:
                        score_col = col
                        break

                if score_col:
                    df_rsi = df_rsi.sort_values(
                        by=score_col, ascending=False
                    ).reset_index(drop=True)

                st.success(
                    f"Screening selesai! Ditemukan {len(df_rsi)} hasil."
                )

                # Menampilkan DataFrame dengan format yang aman (hanya format kolom yang ada)
                format_dict = {}
                if "Price" in df_rsi.columns:
                    format_dict["Price"] = "{:,.0f}"
                if "RSI" in df_rsi.columns:
                    format_dict["RSI"] = "{:,.2f}"
                if "RSI MA" in df_rsi.columns:
                    format_dict["RSI MA"] = "{:,.2f}"
                if score_col:
                    format_dict[score_col] = "{:.0f}"

                if format_dict:
                    st.dataframe(
                        df_rsi.style.format(format_dict),
                        use_container_width=True,
                    )
                else:
                    st.dataframe(df_rsi, use_container_width=True)
            else:
                st.warning(
                    "Tidak ada signal RSI Divergence yang terdeteksi saat ini."
                )

# ==========================================
# TAB 2: STOCHASTIC & PARABOLIC SAR
# ==========================================
with tab2:
    st.header("Screener Stochastic & Parabolic SAR")
    st.caption(
        "Mencari signal Golden Cross (Oversold) dan Dead Cross (Overbought) yang dikonfirmasi Parabolic SAR."
    )

    if st.button("Jalankan Screener Stoch & PSAR", key="btn_stoch"):
        with st.spinner(
            "Menganalisis signal Stochastic & Parabolic SAR..."
        ):
            try:
                df_gc, df_dc = run_stoch_psar_screener()

                col_gc, col_dc = st.columns(2)

                with col_gc:
                    st.subheader("🟢 Signal Beli / Watchlist (Golden Cross)")
                    if not df_gc.empty:
                        # Format aman untuk Golden Cross
                        fmt_gc = {
                            col: "{:,.0f}"
                            if col in ["Harga", "Score"]
                            else "{:,.2f}"
                            for col in df_gc.columns
                            if col in ["Harga", "Value (M)", "Stoch %K", "Stoch %D", "Score"]
                        }
                        st.dataframe(
                            df_gc.style.format(fmt_gc),
                            use_container_width=True,
                        )
                    else:
                        st.info("Tidak ada signal Golden Cross.")

                with col_dc:
                    st.subheader("🔴 Signal Jual / Exit (Dead Cross)")
                    if not df_dc.empty:
                        # Format aman untuk Dead Cross
                        fmt_dc = {
                            col: "{:,.0f}"
                            if col in ["Harga", "Score"]
                            else "{:,.2f}"
                            for col in df_dc.columns
                            if col in ["Harga", "Value (M)", "Stoch %K", "Stoch %D", "Score"]
                        }
                        st.dataframe(
                            df_dc.style.format(fmt_dc),
                            use_container_width=True,
                        )
                    else:
                        st.info("Tidak ada signal Dead Cross.")

            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")

# ==========================================
# TAB 3: TRADE PLANNER (Menggunakan Class TradePlanner)
# ==========================================
with tab3:
    st.header("Trade Planner Calculator")
    st.caption(
        "Analisis Swing Point, Support/Resistance Kuat, Arah Tren (Direction), dan Rencana Trading (BOW/BOB)."
    )

    col_input1, col_input2 = st.columns([2, 1])

    with col_input1:
        ticker_input = st.text_input(
            "Masukkan Ticker Saham (Gunakan suffix .JK untuk saham Indonesia)",
            value="INCO.JK",
        )

    with col_input2:
        period_input = st.selectbox(
            "Pilih Periode Data",
            options=["3mo", "6mo", "1y", "2y"],
            index=1,
        )

    if st.button("Generate Trade Plan", key="btn_planner"):
        with st.spinner(f"Mengambil data {ticker_input} dan menghitung rencana..."):
            try:
                # Inisialisasi dan ambil data menggunakan class TradePlanner
                planner = TradePlanner(
                    ticker=ticker_input.upper(), period=period_input
                )
                planner.fetch_and_prepare_data()

                # 1. Direction Market
                st.subheader("📌 Direction Market")
                df_dir = planner.get_direction()
                st.dataframe(df_dir, use_container_width=True)

                # Highlight Direction Status
                direction_val = df_dir["Direction"].iloc[0]
                if direction_val == "BOB":
                    st.success("Analisis Arah: **BOB (Breakout Buy)**")
                else:
                    st.info("Analisis Arah: **BOW (Buy on Weakness)**")

                # 2. Strategy Trade Plan (BOW & BOB)
                st.subheader("🎯 Trade Plan Recommendation (BOW & BOB)")
                df_plan = planner.generate_trade_plan()
                st.dataframe(df_plan, use_container_width=True)

                # Show Candle Warning
                warning_msg = df_plan["Warning"].iloc[0]
                candle_type = df_plan["Status Candle"].iloc[0]
                st.warning(f"**Pola Candle Terdeteksi:** {candle_type} — {warning_msg}")

                # 3. Support & Resistance Levels
                col_sup, col_res = st.columns(2)

                with col_sup:
                    st.subheader("🛡️ Strong Support Levels")
                    df_sup = planner.get_strong_support()
                    st.dataframe(df_sup, use_container_width=True)

                with col_res:
                    st.subheader("🧱 Strong Resistance Levels")
                    df_res = planner.get_strong_resistance()
                    st.dataframe(df_res, use_container_width=True)

                # 4. Swing Points & Metpoint
                st.subheader("📍 Swing Points & Metpoints")
                df_swings = planner.get_swing_points()
                st.dataframe(df_swings, use_container_width=True)

            except Exception as e:
                st.error(
                    f"Gagal memproses data untuk ticker **{ticker_input}**. Pastikan kode ticker benar dan jaringan stabil. Detail Error: {e}"
                )
