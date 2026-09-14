import concurrent.futures
import pandas as pd
import streamlit as st

# Import modul screener lokal
from screener_ema_vol import run_screener as run_ema_vol_screener
from screener_rsi_divergence import (
    TICKERS as RSI_TICKERS,
    detect_rsi_patterns_and_score,
)
from screener_stoch_psar import run_stoch_psar_screener

# Set konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Stock Screener Dashboard", page_icon="📈", layout="wide"
)

st.title("📈 Indonesian Stock Screener Dashboard")
st.markdown(
    "Aplikasi screening saham IHSG berdasarkan kriteria **EMA & Volume**, **RSI Divergence**, dan **Stochastic & Parabolic SAR**."
)

# Buat Tab untuk masing-masing screener
tab1, tab2, tab3 = st.tabs(
    [
        "🚀 EMA & Vol Breakout",
        "🔄 RSI Divergence",
        "⚡ Stochastic & Parabolic SAR",
    ]
)

# ==========================================
# TAB 1: EMA & VOLUME BREAKOUT
# ==========================================
with tab1:
    st.header("Screener EMA & Volume Breakout")
    st.caption("Mencari saham dengan potensi breakout EMA dan lonjakan volume.")

    if st.button("Jalankan Screener EMA & Vol", key="btn_ema"):
        with st.spinner("Mengunduh data saham dan menganalisis..."):
            try:
                df_ema = run_ema_vol_screener()
                if not df_ema.empty:
                    st.success(
                        f"Screening selesai! Ditemukan {len(df_ema)} saham."
                    )
                    st.dataframe(
                        df_ema.style.format(
                            {
                                "Harga": "{:,.0f}",
                                "EMA 20": "{:,.2f}",
                                "EMA 50": "{:,.2f}",
                                "EMA 200": "{:,.2f}",
                                "RSI 14": "{:,.2f}",
                                "Vol (xMA20)": "{:,.2f}x",
                                "Val (M)": "{:,.2f}",
                            }
                        ),
                        use_container_width=True,
                    )
                else:
                    st.warning(
                        "Tidak ada saham yang memenuhi kriteria saat ini."
                    )
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")

# ==========================================
# TAB 2: RSI DIVERGENCE
# ==========================================
with tab2:
    st.header("Screener RSI Divergence & Patterns")
    st.caption(
        "Deteksi pola RSI Divergence (Bullish/Bearish) dan scoring kekuatan tren."
    )

    if st.button("Jalankan Screener RSI", key="btn_rsi"):
        with st.spinner(
            f"Menganalisis {len(RSI_TICKERS)} saham menggunakan multi-threading..."
        ):
            results_rsi = []
            # Mempercepat eksekusi per ticker dengan ThreadPoolExecutor
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
# TAB 3: STOCHASTIC & PARABOLIC SAR
# ==========================================
with tab3:
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
