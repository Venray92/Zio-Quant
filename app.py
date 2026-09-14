import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

# Config Tampilan
st.set_page_config(
    page_title="Screener Saham IHSG",
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
        actual_rsi = df.iloc[x]['RSI']
        if actual_rsi < expected_rsi - 3:
            return False
    return True

def calculate_candlestick_bonus(curr_bar):
    open_p = curr_bar['Open']
    close_p = curr_bar['Close']
    low_p = curr_bar['Low']
    body = abs(close_p - open_p)
    lower_wick = min(open_p, close_p) - low_p
    
    if (body > 0 and lower_wick >= 2 * body) or (body == 0 and lower_wick > 0):
        return 20
    elif close_p > open_p:
        return 10
    return 0

def scan_rsi_divergence(ticker):
    try:
        data = yf.download(ticker, period="4mo", interval="1d", progress=False)
        if len(data) < 30:
            return None
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        df = calculate_rsi_tradingview(data)
        
        avg_turnover = df['Turnover'].rolling(window=20).mean().iloc[-1]
        if pd.isna(avg_turnover) or avg_turnover < 1_000_000_000:
            return None

        valleys = find_rsi_swings_optimized(df)
        if len(valleys) < 2:
            return None
            
        latest_idx = len(df) - 1
        
        for i in range(len(valleys)-1, -1, -1):
            idx2 = valleys[i]
            age_bars = latest_idx - idx2
            
            if age_bars > 10:
                continue

            for j in range(i-1, -1, -1):
                idx1 = valleys[j]
                gap = idx2 - idx1
                
                if 6 <= gap <= 25:
                    if not (is_local_price_low(df, idx1) and is_local_price_low(df, idx2)):
                        continue

                    if not check_line_penetration(df, idx1, idx2):
                        continue

                    price_low1, price_low2 = df.iloc[idx1]['Low'], df.iloc[idx2]['Low']
                    rsi_v1, rsi_v2 = df.iloc[idx1]['RSI'], df.iloc[idx2]['RSI']
                    
                    price_diff_pct = (price_low2 - price_low1) / price_low1

                    pattern_name = None
                    base_score = 0

                    if price_diff_pct <= -0.01 and rsi_v2 > rsi_v1 and (rsi_v2 - rsi_v1 >= 1.0):
                        if 5 <= rsi_v2 < 30:
                            pattern_name = "Regular Bullish"
                            base_score = 70
                        elif 30 <= rsi_v2 <= 40:
                            pattern_name = "Regular Bullish"
                            base_score = 50

                    elif price_diff_pct >= 0.01 and rsi_v2 < rsi_v1 and (rsi_v1 - rsi_v2 >= 1.0):
                        if 50 <= rsi_v2 <= 60:
                            pattern_name = "Hidden Bullish"
                            base_score = 65
                        elif 40 <= rsi_v2 < 50:
                            pattern_name = "Hidden Bullish"
                            base_score = 45

                    elif -0.01 < price_diff_pct < 0.01 and rsi_v2 > rsi_v1 and (rsi_v2 - rsi_v1 >= 1.0):
                        if 30 <= rsi_v2 < 40:
                            pattern_name = "Medium Bullish"
                            base_score = 60
                        elif 40 <= rsi_v2 <= 50:
                            pattern_name = "Medium Bullish"
                            base_score = 40

                    if pattern_name and base_score > 0:
                        curr_bar = df.iloc[latest_idx]
                        prev_bar = df.iloc[latest_idx - 1]
                        date1 = df.index[idx1].strftime('%Y-%m-%d')
                        date2 = df.index[idx2].strftime('%Y-%m-%d')

                        is_gc = False
                        for idx in range(idx2, latest_idx + 1):
                            if idx > 0 and df.iloc[idx - 1]['RSI'] <= df.iloc[idx - 1]['RSI_EMA'] and df.iloc[idx]['RSI'] > df.iloc[idx]['RSI_EMA']:
                                is_gc = True
                                break
                                
                        gc_score = 15 if is_gc else 0
                        
                        vol_score = 0
                        if is_gc:
                            if curr_bar['Volume'] > 2 * curr_bar['Vol_MA20']:
                                vol_score = 15
                            elif curr_bar['Volume'] > 1 * curr_bar['Vol_MA20']:
                                vol_score = 10
                        else:
                            if curr_bar['Volume'] > prev_bar['Volume']:
                                vol_score = 5

                        candle_score = calculate_candlestick_bonus(curr_bar)
                        
                        if age_bars <= 3:
                            age_penalty = 0
                        elif age_bars <= 7:
                            age_penalty = 10
                        else:
                            age_penalty = 20

                        total_score = base_score + gc_score + vol_score + candle_score - age_penalty

                        return {
                            "Ticker": ticker.replace(".JK", ""),
                            "Price": int(curr_bar['Close']),
                            "Pattern": pattern_name,
                            "Tgl V1": date1,
                            "Tgl V2": date2,
                            "Gap": f"{gap} bar",
                            "RSI V1": round(rsi_v1, 2),
                            "RSI V2": round(rsi_v2, 2),
                            "Age": f"H+{age_bars}",
                            "Status GC": "GC CONFIRMED" if is_gc else "WATCHLIST",
                            "TOTAL SCORE": total_score
                        }
        return None
    except Exception:
        return None


# ==========================================
# 2. MODUL LOGIKA: STOCHASTIC + PSAR
# ==========================================
def calculate_stochastic(df, k_period=14, d_period=3, slowing=3):
    low_min = df['Low'].rolling(window=k_period).min()
    high_max = df['High'].rolling(window=k_period).max()
    
    stoch_k = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    df['Stoch_K'] = stoch_k.rolling(window=slowing).mean()
    df['Stoch_D'] = df['Stoch_K'].rolling(window=d_period).mean()
    return df

def calculate_psar(df, af_start=0.02, af_inc=0.02, af_max=0.2):
    high = df['High'].values
    low = df['Low'].values
    
    psar = np.zeros(len(df))
    bull = True
    af = af_start
    ep = low[0]
    psar[0] = high[0]
    
    for i in range(1, len(df)):
        prior_psar = psar[i-1]
        
        if bull:
            current_psar = prior_psar + af * (ep - prior_psar)
            current_psar = min(current_psar, low[i-1], low[max(0, i-2)])
            
            if low[i] < current_psar:
                bull = False
                current_psar = ep
                ep = low[i]
                af = af_start
            else:
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + af_inc, af_max)
        else:
            current_psar = prior_psar + af * (ep - prior_psar)
            current_psar = max(current_psar, high[i-1], high[max(0, i-2)])
            
            if high[i] > current_psar:
                bull = True
                current_psar = ep
                ep = high[i]
                af = af_start
            else:
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + af_inc, af_max)
                    
        psar[i] = current_psar
        
    df['PSAR'] = psar
    df['PSAR_Bullish'] = df['Close'] > df['PSAR']
    return df

def scan_stoch_psar(ticker):
    try:
        data = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if len(data) < 20:
            return None
            
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        df = calculate_stochastic(data)
        df = calculate_psar(df)
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        stoch_gc = (prev['Stoch_K'] <= prev['Stoch_D']) and (curr['Stoch_K'] > curr['Stoch_D']) and (curr['Stoch_K'] <= 40)
        psar_flip = (not prev['PSAR_Bullish']) and curr['PSAR_Bullish']
        
        if stoch_gc and curr['PSAR_Bullish']:
            return {
                "Ticker": ticker.replace(".JK", ""),
                "Price": int(curr['Close']),
                "Stoch K": round(curr['Stoch_K'], 2),
                "Stoch D": round(curr['Stoch_D'], 2),
                "PSAR Status": "BARU FLIP" if psar_flip else "BULLISH",
                "Signal": "STRONG BUY" if psar_flip else "BUY ON DIP"
            }
        return None
    except Exception:
        return None


# ==========================================
# 3. STREAMLIT INTERFACE (UI)
# ==========================================
st.title("📊 Master Screener Saham IHSG")
st.markdown("Pilih strategi analisis teknikal dari sidebar untuk memulai *scanning*.")

# Menu Sidebar
st.sidebar.header("⚙️ Pengaturan Screener")
strategy = st.sidebar.radio(
    "Pilih Strategi:",
    ("RSI Divergence", "Stochastic + Parabolic SAR")
)

st.sidebar.markdown("---")
st.sidebar.write("Jumlah Ticker Terdaftar:", len(TICKERS))

# --- TAMPILAN 1: RSI DIVERGENCE ---
if strategy == "RSI Divergence":
    st.subheader("🔍 Screener RSI Divergence & Golden Cross")
    st.caption("Deteksi pola Bullish Divergence pada RSI serta konfirmasi Golden Cross.")
    
    if st.button("Jalankan Screener RSI"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, ticker in enumerate(TICKERS):
            status_text.text(f"Scanning ({idx+1}/{len(TICKERS)}): {ticker}")
            res = scan_rsi_divergence(ticker)
            if res:
                results.append(res)
            progress_bar.progress((idx + 1) / len(TICKERS))
            
        status_text.empty()
        progress_bar.empty()
        
        df_res = pd.DataFrame(results)
        if not df_res.empty:
            df_res = df_res.sort_values(by="TOTAL SCORE", ascending=False).reset_index(drop=True)
            st.success(f"Ditemukan **{len(df_res)}** saham yang memenuhi kriteria!")
            st.dataframe(df_res, use_container_width=True)
        else:
            st.warning("Tidak ada saham yang memenuhi kriteria RSI Divergence saat ini.")

# --- TAMPILAN 2: STOCHASTIC + PSAR ---
elif strategy == "Stochastic + Parabolic SAR":
    st.subheader("🔍 Screener Stochastic Oversold + Parabolic SAR")
    st.caption("Deteksi Golden Cross Stochastic dari area oversold bersamaan dengan tren Bullish PSAR.")
    
    if st.button("Jalankan Screener Stoch + PSAR"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, ticker in enumerate(TICKERS):
            status_text.text(f"Scanning ({idx+1}/{len(TICKERS)}): {ticker}")
            res = scan_stoch_psar(ticker)
            if res:
                results.append(res)
            progress_bar.progress((idx + 1) / len(TICKERS))
            
        status_text.empty()
        progress_bar.empty()
        
        df_res = pd.DataFrame(results)
        if not df_res.empty:
            st.success(f"Ditemukan **{len(df_res)}** saham yang memenuhi kriteria!")
            st.dataframe(df_res, use_container_width=True)
        else:
            st.warning("Tidak ada saham yang memenuhi kriteria Stochastic + PSAR saat ini.")
