import concurrent.futures
import pandas as pd
import streamlit as st

# Import modul yang BENAR-BENAR ada di repositori kamu
from screener_rsi_divergence import (
    TICKERS as RSI_TICKERS,
    detect_rsi_patterns_and_score,
)
from screener_stoch_psar import run_stoch_psar_screener
from trade_planner import render_trade_planner  # Menyesuaikan file trade_planner.py

# Set konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Stock Screener & Trade Planner", page_icon="📈", layout="wide"
)

st.title("📈 Stock Screener & Trade Planner Dashboard")
st.markdown(
    "Aplikasi screening saham berdasarkan **RSI Divergence**, **Stochastic & Parabolic SAR**, serta kalkulator **Trade Planner**."
)

# Buat Tab sesuai modul yang kamu miliki
tab1, tab2, tab3 = st.tabs(
    [
        "🔄 RSI Divergence",
        "⚡ Stochastic & Parabolic SAR",
        "🎯 Trade Planner",
    ]
)

# ==========================================
# TAB 1: RSI DIVERGENCE
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
                df_rsi = df_rsi.sort_values(
                    by="Score", ascending=False
                ).reset_index(drop=True)

                st.success(
                    f"Screening selesai! Ditemukan {len(df_rsi)} hasil."
                )

                st.dataframe(
                    df_rsi.style.format(
                        {
                            "Price": "{:,.0f}",
                            "RSI": "{:,.2f}",
                            "RSI MA": "{:,.2f}",
                            "Score": "{:.0f}",
                        }
                    ),
                    use_container_width=True,
                )
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
                        st.dataframe(
                            df_gc.style.format(
                                {
                                    "Harga": "{:,.0f}",
                                    "Value (M)": "{:,.2f}",
                                    "Stoch %K": "{:,.1f}",
                                    "Stoch %D": "{:,.1f}",
                                    "Score": "{:.0f}",
                                }
                            ),
                            use_container_width=True,
                        )
                    else:
                        st.info("Tidak ada signal Golden Cross.")

                with col_dc:
                    st.subheader("🔴 Signal Jual / Exit (Dead Cross)")
                    if not df_dc.empty:
                        st.dataframe(
                            df_dc.style.format(
                                {
                                    "Harga": "{:,.0f}",
                                    "Value (M)": "{:,.2f}",
                                    "Stoch %K": "{:,.1f}",
                                    "Stoch %D": "{:,.1f}",
                                    "Score": "{:.0f}",
                                }
                            ),
                            use_container_width=True,
                        )
                    else:
                        st.info("Tidak ada signal Dead Cross.")

            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")

# ==========================================
# TAB 3: TRADE PLANNER
# ==========================================
with tab3:
    st.header("Trade Planner Calculator")
    st.caption("Hitung posisi entry, stop loss, target profit, dan money management.")
    
    # Menjalankan fungsi interface dari trade_planner.py
    try:
        render_trade_planner()
    except AttributeError:
        # Jika trade_planner.py tidak punya fungsi render_trade_planner(), ganti sesuai nama fungsi di dalam file kamu
        st.info("Silakan sesuaikan pemanggilan fungsi utama dari trade_planner.py di baris ini.")
