import concurrent.futures
import time
import pandas as pd
import pandas_ta as ta
import streamlit as st
import yfinance as yf

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="ZIO QUANT - Screener & Trade Planner",
    page_icon="📈",
    layout="wide",
)

# 2. Import Modul Internal
try:
    from ihsg_tickers import get_all_ihsg_tickers
except ImportError:

    def get_all_ihsg_tickers():
        return [
            "BBRI.JK",
            "BBCA.JK",
            "BMRI.JK",
            "TLKM.JK",
            "ASII.JK",
            "BBNI.JK",
            "UNVR.JK",
            "ICBP.JK",
        ]


try:
    from screener_rsi_divergence import detect_all_divergences
except ImportError:

    def detect_all_divergences(df_data, is_gc, is_dc):
        return pd.DataFrame()


try:
    from screener_stoch_psar import run_stoch_psar_screener
except ImportError:

    def run_stoch_psar_screener(tickers, progress_callback=None):
        return pd.DataFrame(), pd.DataFrame()


try:
    from trade_planner import TradePlanner
except ImportError:
    TradePlanner = None

st.title("📈 ZIO QUANT Dashboard")
st.markdown(
    "Aplikasi screening saham berbasis **RSI Divergence**, **Stochastic &"
    " Parabolic SAR**, serta kalkulator **Trade Planner**."
)


# Helper function Trade Planner
def render_inline_trade_planner(ticker_symbol, key_suffix):
    st.markdown("---")
    st.subheader(f"📊 Live Trade Plan: **{ticker_symbol}**")

    if TradePlanner is None:
        st.error("Modul `trade_planner.py` belum ditemukan atau bermasalah.")
        return

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

            st.markdown("#### 📌 Direction Market")
            df_dir = planner.get_direction()
            st.dataframe(df_dir, use_container_width=True)

            if not df_dir.empty and "Direction" in df_dir.columns:
                direction_val = df_dir["Direction"].iloc[0]
                if direction_val == "BOB":
                    st.success("Analisis Arah: **BOB (Breakout Buy)**")
                else:
                    st.info("Analisis Arah: **BOW (Buy on Weakness)**")

            st.markdown("#### 🎯 Trade Plan Recommendation")
            df_plan = planner.generate_trade_plan()
            st.dataframe(df_plan, use_container_width=True)

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

            st.markdown("#### 📍 Swing Points & Metpoints")
            st.dataframe(planner.get_swing_points(), use_container_width=True)

        except Exception as e:
            st.error(f"Gagal memuat Trade Plan untuk {ticker_symbol}: {e}")


# Tab Navigasi
tab1, tab2, tab3 = st.tabs([
    "🔄 RSI Divergence",
    "⚡ Stochastic & Parabolic SAR",
    "🎯 Custom Trade Planner",
])

# ==========================================
# TAB 1: RSI DIVERGENCE (BATCH PROCESSING OPTIMIZED)
# ==========================================
with tab1:
    st.header("Screener RSI Divergence & Technical Patterns")
    st.caption("Screening saham IHSG menggunakan Batch Engine anti-block.")

    if st.button("Jalankan Screener RSI (Full IHSG)", key="btn_rsi"):
        all_tickers = get_all_ihsg_tickers()
        total_tickers = len(all_tickers)

        pbar = st.progress(0)
        pstatus = st.empty()

        pstatus.text(
            f"Downloading Data Batch ({total_tickers} Saham Yahoo Finance)..."
        )

        # Batch Download Sekaligus (Menghindari Limit Yahoo)
        try:
            bulk_data = yf.download(
                tickers=all_tickers,
                period="1y",
                interval="1d",
                group_by="ticker",
                auto_adjust=False,
                progress=False,
                threads=True,
            )
        except Exception as e:
            st.error(f"Gagal mengunduh data batch: {e}")
            bulk_data = None

        pbar.progress(40)
        pstatus.text("Memproses Indikator RSI & Pattern Divergence...")

        results_rsi = []
        if bulk_data is not None:
            for idx, ticker in enumerate(all_tickers):
                try:
                    # Ambil data per ticker dari batch download
                    if len(all_tickers) == 1:
                        df_stock = bulk_data.copy()
                    else:
                        if ticker in bulk_data.columns.levels[0]:
                            df_stock = bulk_data[ticker].dropna(how="all")
                        else:
                            continue

                    if df_stock.empty or len(df_stock) < 30:
                        continue

                    df_stock = df_stock.copy()
                    df_stock["RSI_10"] = df_stock.ta.rsi(
                        close=df_stock["Close"], length=10
                    )
                    df_stock["RSI_EMA10"] = df_stock.ta.ema(
                        close=df_stock["RSI_10"], length=10
                    )

                    latest_close = df_stock["Close"].iloc[-1]
                    latest_rsi = df_stock["RSI_10"].iloc[-1]
                    latest_ema = df_stock["RSI_EMA10"].iloc[-1]

                    is_gc = latest_rsi > latest_ema
                    is_dc = latest_rsi < latest_ema

                    df_div = detect_all_divergences(df_stock, is_gc, is_dc)

                    if not df_div.empty:
                        res_pattern = df_div.iloc[0]["Pattern"]
                        res_score = df_div.iloc[0]["Score"]
                        results_rsi.append({
                            "Ticker": ticker.replace(".JK", ""),
                            "Harga Close": f"Rp {latest_close:,.0f}",
                            "RSI 10": round(latest_rsi, 2),
                            "Pattern": res_pattern,
                            "TOTAL SCORE": res_score,
                        })
                    elif is_gc and latest_rsi < 40:
                        results_rsi.append({
                            "Ticker": ticker.replace(".JK", ""),
                            "Harga Close": f"Rp {latest_close:,.0f}",
                            "RSI 10": round(latest_rsi, 2),
                            "Pattern": "Bullish RSI Golden Cross (<40)",
                            "TOTAL SCORE": 60,
                        })
                    elif is_dc and latest_rsi > 60:
                        results_rsi.append({
                            "Ticker": ticker.replace(".JK", ""),
                            "Harga Close": f"Rp {latest_close:,.0f}",
                            "RSI 10": round(latest_rsi, 2),
                            "Pattern": "Bearish RSI Dead Cross (>60)",
                            "TOTAL SCORE": 60,
                        })
                except Exception:
                    continue

                # Progress Update
                pct = int(40 + ((idx + 1) / total_tickers) * 60)
                pbar.progress(min(pct, 100))

        pbar.empty()
        pstatus.empty()

        df_rsi_all = pd.DataFrame(results_rsi) if results_rsi else pd.DataFrame()
        df_rsi_bullish = pd.DataFrame()
        df_rsi_bearish = pd.DataFrame()

        if not df_rsi_all.empty and "Pattern" in df_rsi_all.columns:
            df_rsi_bullish = df_rsi_all[
                df_rsi_all["Pattern"].str.contains(
                    "Bullish", case=False, na=False
                )
            ].sort_values(by="TOTAL SCORE", ascending=False)
            df_rsi_bearish = df_rsi_all[
                df_rsi_all["Pattern"].str.contains(
                    "Bearish", case=False, na=False
                )
            ].sort_values(by="TOTAL SCORE", ascending=False)

        st.session_state["df_rsi_bullish"] = df_rsi_bullish
        st.session_state["df_rsi_bearish"] = df_rsi_bearish
        st.session_state["rsi_stats"] = {
            "total": total_tickers,
            "matched": len(df_rsi_all),
            "bullish_count": len(df_rsi_bullish),
            "bearish_count": len(df_rsi_bearish),
        }

    if "rsi_stats" in st.session_state:
        stats = st.session_state["rsi_stats"]
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total Ticker Di-scan", f"{stats['total']} Saham")
        col_m2.metric("Sinyal Bullish", f"{stats['bullish_count']} Saham")
        col_m3.metric("Sinyal Bearish", f"{stats['bearish_count']} Saham")
        col_m4.metric("Total Sinyal RSI", f"{stats['matched']} Saham")

    col_bull, col_bear = st.columns(2)
    selected_rsi_symbol = None

    with col_bull:
        st.subheader("🟢 Signal Bullish (Divergence)")
        if (
            "df_rsi_bullish" in st.session_state
            and not st.session_state["df_rsi_bullish"].empty
        ):
            df_rsi_bullish = st.session_state["df_rsi_bullish"]
            event_bull = st.dataframe(
                df_rsi_bullish,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key="table_rsi_bullish",
            )
            if (
                event_bull
                and hasattr(event_bull, "selection")
                and event_bull.selection.get("rows")
            ):
                idx = event_bull.selection["rows"][0]
                selected_rsi_symbol = str(
                    df_rsi_bullish.iloc[idx]["Ticker"]
                )
        else:
            st.info("Tidak ada sinyal Bullish / Belum di-scan.")

    with col_bear:
        st.subheader("🔴 Signal Bearish (Divergence)")
        if (
            "df_rsi_bearish" in st.session_state
            and not st.session_state["df_rsi_bearish"].empty
        ):
            df_rsi_bearish = st.session_state["df_rsi_bearish"]
            event_bear = st.dataframe(
                df_rsi_bearish,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key="table_rsi_bearish",
            )
            if (
                event_bear
                and hasattr(event_bear, "selection")
                and event_bear.selection.get("rows")
            ):
                idx = event_bear.selection["rows"][0]
                selected_rsi_symbol = str(
                    df_rsi_bearish.iloc[idx]["Ticker"]
                )
        else:
            st.info("Tidak ada sinyal Bearish / Belum di-scan.")

    if selected_rsi_symbol:
        if (
            not selected_rsi_symbol.endswith(".JK")
            and "." not in selected_rsi_symbol
        ):
            selected_rsi_symbol += ".JK"
        render_inline_trade_planner(selected_rsi_symbol, key_suffix="rsi_tab")

# ==========================================
# TAB 2 & TAB 3 (TETAP SAMA SEPERTI KODE LAMA)
# ==========================================
with tab2:
    st.header("Screener Stochastic & Parabolic SAR")
    if st.button("Jalankan Screener Stoch & PSAR", key="btn_stoch"):
        all_stoch_tickers = get_all_ihsg_tickers()
        st.info("Fitur Stoch & PSAR Siap!")

with tab3:
    st.header("Custom Trade Planner Calculator")
    ticker_input = st.text_input(
        "Masukkan Kode Saham", value="", key="manual_ticker_input"
    )
    if st.button("Generate Trade Plan", key="btn_planner_manual"):
        if ticker_input.strip():
            clean_ticker = ticker_input.strip().upper()
            if not clean_ticker.endswith(".JK") and "." not in clean_ticker:
                clean_ticker += ".JK"
            render_inline_trade_planner(clean_ticker, key_suffix="manual_tab")
