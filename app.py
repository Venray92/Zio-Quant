import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

# Config Tampilan
st.set_page_config(
    page_title="Master Screener & Trade Plan IHSG",
    page_icon="📈",
    layout="wide"
)

# List Ticker IHSG Default
TICKERS = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "ASII.JK", "GOTO.JK", "UNVR.JK", "ICBP.JK", "INDF.JK",
    "KLBF.JK", "UNTR.JK", "ADRO.JK", "PTBA.JK", "ANTM.JK", "INCO.JK", "MDKA.JK", "PGAS.JK", "SMGR.JK", "INTP.JK",
    "CPIN.JK", "BRIS.JK", "ARTO.JK", "BUMI.JK", "ENRG.JK", "MEDC.JK", "ELSA.JK", "HRUM.JK", "ITMG.JK", "BRPT.JK",
    "TPIA.JK", "AMRT.JK", "MAPI.JK", "ERAA.JK", "ACES.JK", "MAPA.JK", "MYOR.JK", "GGRM.JK", "HMSP.JK", "SIDO.JK",
    "JPFA.JK", "MAIN.JK", "CMRY.JK", "ULTJ.JK", "MIKA.JK", "HEAL.JK", "SILO.JK", "BIRD.JK", "ASSA.JK", "SMDR.JK"
]

# ==========================================
# 0. FUNGSI GENERATE TRADE PLAN & CHART
# ==========================================
def generate_trade_plan(ticker):
    """Menghitung Trade Plan otomatis berdasarkan Swing Low dan High terbaru"""
    try:
        formatted_ticker = ticker.upper() + ".JK" if not ticker.endswith(".JK") else ticker.upper()
        data = yf.download(formatted_ticker, period="6mo", interval="1d", progress=False)
        
        if len(data) < 30:
            st.error("Data historis tidak cukup untuk membuat Trade Plan.")
            return

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        curr_price = float(data['Close'].iloc[-1])
        low_30d = float(data['Low'].tail(30).min())
        high_30d = float(data['High'].tail(30).max())
        
        # Kalkulasi Trade Plan
        entry_price = curr_price
        stop_loss = round(low_30d * 0.98) # 2% di bawah swing low
        risk = entry_price - stop_loss
        
        if risk <= 0:
            risk = entry_price * 0.03 # Default risk 3% jika Swing Low sama/di atas harga saat ini
            stop_loss = round(entry_price - risk)

        tp1 = round(entry_price + (1.5 * risk))
        tp2 = round(entry_price + (2.5 * risk))
        rrr = round((tp1 - entry_price) / (entry_price - stop_loss), 2)

        # Tampilan Hasil Trade Plan
        st.markdown(f"### 📋 Trade Plan: **{formatted_ticker.replace('.JK', '')}**")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Current / Entry", f"Rp {entry_price:,.0f}")
        col2.metric("Stop Loss (SL)", f"Rp {stop_loss:,.0f}", f"-{((entry_price-stop_loss)/entry_price)*100:.1f}%")
        col3.metric("Target 1 (TP1)", f"Rp {tp1:,.0f}", f"+{((tp1-entry_price)/entry_price)*100:.1f}%")
        col4.metric("Target 2 (TP2)", f"Rp {tp2:,.0f}", f"+{((tp2-entry_price)/entry_price)*100:.1f}%")
        col5.metric("Risk Reward Ratio", f"1 : {rrr}")

        st.line_chart(data['Close'].tail(60))

    except Exception as e:
        st.error(f"Gagal memuat Trade Plan untuk {ticker}: {e}")


# ==========================================
# 1. MODUL LOGIKA: RSI DIVERGENCE
# ==========================================
def calculate_rsi_tradingview(df, rsi_period=10, ema_period=10):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/rsi_period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI_EMA'] = df['RSI'].ewm(span=ema_period, adjust=False).mean()
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
    df['Turnover'] = df['Close'] * df['Volume']
    return df

def find_rsi_swings_optimized(df):
    rsi_vals = -df['RSI'].values
    valleys, _ = find_peaks(rsi_vals, distance=8, prominence=2.5)
    return valleys

def is_local_price_low(df, idx, window=2):
    start = max(0, idx - window)
    end = min(len(df) - 1, idx + window)
    return df.iloc[idx]['Low'] == df.iloc[start:end+1]['Low'].min()

def check_line_penetration(df, idx1, idx2):
    rsi_v1 = df.iloc[idx1]['RSI']
    rsi_v2 = df.iloc[idx2]['RSI']
    for x in range(idx1 + 1, idx2):
        expected_rsi = rsi_v1 + (rsi_v2 - rsi_v1) * (x - idx1) / (idx2 - idx1)
        if df.iloc[x]['RSI'] < expected_rsi - 3:
            return False
    return True

def scan_rsi_divergence(ticker):
    try:
        data = yf.download(ticker, period="4mo", interval="1d", progress=False)
        if len(data) < 30: return None
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

        df = calculate_rsi_tradingview(data)
        if df['Turnover'].rolling(20).mean().iloc[-1] < 1_000_000_000: return None

        valleys = find_rsi_swings_optimized(df)
        if len(valleys) < 2: return None
            
        latest_idx = len(df) - 1
        for i in range(len(valleys)-1, -1, -1):
            idx2 = valleys[i]
            age_bars = latest_idx - idx2
            if age_bars > 10: continue

            for j in range(i-1, -1, -1):
                idx1 = valleys[j]
                gap = idx2 - idx1
                if 6 <= gap <= 25:
                    if not (is_local_price_low(df, idx1) and is_local_price_low(df, idx2)): continue
                    if not check_line_penetration(df, idx1, idx2): continue

                    price_low1, price_low2 = df.iloc[idx1]['Low'], df.iloc[idx2]['Low']
                    rsi_v1, rsi_v2 = df.iloc[idx1]['RSI'], df.iloc[idx2]['RSI']
                    price_diff_pct = (price_low2 - price_low1) / price_low1

                    pattern_name, base_score = None, 0
                    if price_diff_pct <= -0.01 and rsi_v2 > rsi_v1 and (rsi_v2 - rsi_v1 >= 1.0):
                        pattern_name = "Regular Bullish"
                        base_score = 70 if rsi_v2 < 30 else 50
                    elif price_diff_pct >= 0.01 and rsi_v2 < rsi_v1 and (rsi_v1 - rsi_v2 >= 1.0):
                        pattern_name = "Hidden Bullish"
                        base_score = 65 if rsi_v2 <= 60 else 45

                    if pattern_name and base_score > 0:
                        curr_bar = df.iloc[latest_idx]
                        is_gc = any(df.iloc[idx-1]['RSI'] <= df.iloc[idx-1]['RSI_EMA'] and df.iloc[idx]['RSI'] > df.iloc[idx]['RSI_EMA'] for idx in range(idx2, latest_idx + 1))
                        
                        gc_score = 15 if is_gc else 0
                        age_penalty = 0 if age_bars <= 3 else (10 if age_bars <= 7 else 20)
                        total_score = base_score + gc_score - age_penalty

                        return {
                            "Ticker": ticker.replace(".JK", ""),
                            "Price": int(curr_bar['Close']),
                            "Pattern": pattern_name,
                            "RSI V1": round(rsi_v1, 2),
                            "RSI V2": round(rsi_v2, 2),
                            "Age": f"H+{age_bars}",
                            "Status GC": "GC CONFIRMED" if is_gc else "WATCHLIST",
                            "TOTAL SCORE": total_score
                        }
        return None
    except Exception: return None


# ==========================================
# 2. MODUL LOGIKA: STOCHASTIC + PSAR
# ==========================================
def scan_stoch_psar(ticker):
    try:
        data = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if len(data) < 20: return None
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

        # Stoch
        low_min = data['Low'].rolling(14).min()
        high_max = data['High'].rolling(14).max()
        stoch_k = (100 * ((data['Close'] - low_min) / (high_max - low_min))).rolling(3).mean()
        stoch_d = stoch_k.rolling(3).mean()
        
        curr, prev = data.iloc[-1], data.iloc[-2]
        stoch_gc = (stoch_k.iloc[-2] <= stoch_d.iloc[-2]) and (stoch_k.iloc[-1] > stoch_d.iloc[-1]) and (stoch_k.iloc[-1] <= 40)
        
        # Simple PSAR Check (Close > Low 5 hari terakhir sebagai proxy sederhana)
        psar_bullish = curr['Close'] > data['Low'].tail(5).min()

        if stoch_gc and psar_bullish:
            return {
                "Ticker": ticker.replace(".JK", ""),
                "Price": int(curr['Close']),
                "Stoch K": round(stoch_k.iloc[-1], 2),
                "Stoch D": round(stoch_d.iloc[-1], 2),
                "Signal": "BUY ON DIP"
            }
        return None
    except Exception: return None


# ==========================================
# 3. STREAMLIT INTERFACE (UI)
# ==========================================
st.title("📊 Master Screener & Trade Plan IHSG")

# Sidebar Menu
st.sidebar.header("⚙️ Navigasi Modul")
menu = st.sidebar.radio(
    "Pilih Fitur:",
    ("1. Trade Plan (Manual Input)", "2. Screener RSI Divergence", "3. Screener Stochastic + PSAR")
)

# ----------------------------------------------------
# FITUR 1: TRADE PLAN (MANUAL INPUT TICKER)
# ----------------------------------------------------
if menu == "1. Trade Plan (Manual Input)":
    st.subheader("🎯 Bikin Trade Plan Sendiri")
    st.caption("Masukkan kode saham tanpa '.JK' (contoh: BBCA, TLKM, ADRO) untuk membuat analisa Trade Plan secara instan.")
    
    user_ticker = st.text_input("Kode Saham (Ticker):", value="BBCA").strip()
    
    if st.button("Hitung Trade Plan") or user_ticker:
        if user_ticker:
            generate_trade_plan(user_ticker)


# ----------------------------------------------------
# FITUR 2: SCREENER RSI DIVERGENCE
# ----------------------------------------------------
elif menu == "2. Screener RSI Divergence":
    st.subheader("🔍 Screener RSI Divergence")
    
    if st.button("Jalankan Screener RSI"):
        results = []
        progress_bar = st.progress(0)
        
        for idx, ticker in enumerate(TICKERS):
            res = scan_rsi_divergence(ticker)
            if res: results.append(res)
            progress_bar.progress((idx + 1) / len(TICKERS))
            
        progress_bar.empty()
        st.session_state['rsi_results'] = pd.DataFrame(results)

    # Tampilkan Hasil dan Pilihan Trade Plan Otomatis
    if 'rsi_results' in st.session_state and not st.session_state['rsi_results'].empty:
        df_res = st.session_state['rsi_results'].sort_values(by="TOTAL SCORE", ascending=False).reset_index(drop=True)
        st.success(f"Ditemukan **{len(df_res)}** saham yang lolos kriteria!")
        st.dataframe(df_res, use_container_width=True)
        
        st.markdown("---")
        st.markdown("#### 💡 Lihat Trade Plan dari Hasil Screener:")
        selected_ticker = st.selectbox("Pilih Saham Hasil Screener:", df_res['Ticker'].tolist())
        if selected_ticker:
            generate_trade_plan(selected_ticker)


# ----------------------------------------------------
# FITUR 3: SCREENER STOCHASTIC + PSAR
# ----------------------------------------------------
elif menu == "3. Screener Stochastic + PSAR":
    st.subheader("🔍 Screener Stochastic + PSAR")
    
    if st.button("Jalankan Screener Stoch + PSAR"):
        results = []
        progress_bar = st.progress(0)
        
        for idx, ticker in enumerate(TICKERS):
            res = scan_stoch_psar(ticker)
            if res: results.append(res)
            progress_bar.progress((idx + 1) / len(TICKERS))
            
        progress_bar.empty()
        st.session_state['stoch_results'] = pd.DataFrame(results)

    # Tampilkan Hasil dan Pilihan Trade Plan Otomatis
    if 'stoch_results' in st.session_state and not st.session_state['stoch_results'].empty:
        df_res = st.session_state['stoch_results']
        st.success(f"Ditemukan **{len(df_res)}** saham yang lolos kriteria!")
        st.dataframe(df_res, use_container_width=True)
        
        st.markdown("---")
        st.markdown("#### 💡 Lihat Trade Plan dari Hasil Screener:")
        selected_ticker = st.selectbox("Pilih Saham Hasil Screener:", df_res['Ticker'].tolist())
        if selected_ticker:
            generate_trade_plan(selected_ticker)
