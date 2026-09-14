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
# 0. FUNGSI GENERATE TRADE PLAN LENGKAP (COLAB VERSION)
# ==========================================
def generate_full_trade_plan(ticker, budget=10000000, risk_pct=0.03):
    """Menghitung Trade Plan lengkap sesuai logika Google Colab"""
    try:
        formatted_ticker = ticker.upper() + ".JK" if not ticker.endswith(".JK") else ticker.upper()
        clean_ticker = formatted_ticker.replace(".JK", "")

        df = yf.download(formatted_ticker, period="6mo", interval="1d", progress=False)
        
        if len(df) < 30:
            st.error("❌ Data tidak cukup untuk membuat analisis Trade Plan.")
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 1. Parameter Utama
        curr_price = int(df['Close'].iloc[-1])
        df['Turnover'] = df['Close'] * df['Volume']
        avg_turnover = df['Turnover'].tail(20).mean()
        
        # 2. Moving Averages
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()
        ma20_val = df['MA20'].iloc[-1]
        ma50_val = df['MA50'].iloc[-1]
        
        if curr_price > ma20_val > ma50_val:
            trend_status = "STRONG UPTREND 🚀"
        elif curr_price > ma20_val:
            trend_status = "UPTREND (MA20) 📈"
        elif curr_price < ma20_val < ma50_val:
            trend_status = "STRONG DOWNTREND 📉"
        else:
            trend_status = "SIDEWAYS / CONSOLIDATION ⚖️"

        # 3. Dynamic Stop Loss & Target Price
        swing_low_30d = float(df['Low'].tail(30).min())
        sl_swing = round(swing_low_30d * 0.98) # 2% di bawah swing low
        
        sl_pct_option = round(curr_price * (1 - risk_pct))
        stop_loss = max(sl_swing, sl_pct_option)
        
        if stop_loss >= curr_price:
            stop_loss = round(curr_price * 0.95)

        risk_per_share = curr_price - stop_loss
        sl_percent = round(((curr_price - stop_loss) / curr_price) * 100, 2)

        tp1 = round(curr_price + (1.5 * risk_per_share))
        tp2 = round(curr_price + (2.5 * risk_per_share))
        tp3 = round(curr_price + (3.5 * risk_per_share))

        tp1_pct = round(((tp1 - curr_price) / curr_price) * 100, 1)
        tp2_pct = round(((tp2 - curr_price) / curr_price) * 100, 1)
        tp3_pct = round(((tp3 - curr_price) / curr_price) * 100, 1)

        rrr = round((tp1 - curr_price) / risk_per_share, 2)

        # 4. Money Management (Position Sizing)
        max_loss_allowed = budget * 0.02 # Batas toleransi rugi 2% dari total modal
        shares_to_buy = int(max_loss_allowed / risk_per_share)
        lots_to_buy = max(1, shares_to_buy // 100)
        total_allocation = lots_to_buy * 100 * curr_price

        # --- DISPLAY STREAMLIT ---
        st.markdown(f"## 📋 Trade Plan Lengkap: **{clean_ticker}**")
        st.caption(f"Status Tren: **{trend_status}** | Rata-rata Turnover (20H): **Rp {avg_turnover/1e9:.2f} Miliar**")
        
        # Operational Warning
        if avg_turnover < 1_000_000_000:
            st.error("⚠️ **WARNING LIKUIDITAS LOW:** Saham ini memiliki transaksi harian rata-rata di bawah Rp 1 Miliar. Hati-hati risiko sulit jualan (illiquid).")

        # Metric Cards
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Area Buy / Entry", f"Rp {curr_price:,.0f}")
        col2.metric("Stop Loss (Cut Loss)", f"Rp {stop_loss:,.0f}", f"-{sl_percent}%", delta_color="inverse")
        col3.metric("Target 1 (TP1)", f"Rp {tp1:,.0f}", f"+{tp1_pct}%")
        col4.metric("Target 2 (TP2)", f"Rp {tp2:,.0f}", f"+{tp2_pct}%")
        col5.metric("Risk Reward Ratio", f"1 : {rrr}")

        # Detail Table & Money Management
        st.markdown("### 💰 Money Management & Sizing Position")
        mm_col1, mm_col2 = st.columns(2)
        
        with mm_col1:
            st.markdown(f"""
            - **Modal Maksimal Disimulasikan:** Rp {budget:,.0f}
            - **Max Risk Per Trade (2% Modal):** Rp {max_loss_allowed:,.0f}
            - **Rekomendasi Pembelian:** **{lots_to_buy} Lot** ({lots_to_buy * 100:,} lembar)
            - **Total Investasi:** Rp {total_allocation:,.0f} ({round((total_allocation/budget)*100, 1)}% dari modal)
            """)

        with mm_col2:
            st.markdown(f"""
            - **Target 3 (TP3 - Extension):** Rp {tp3:,.0f} (+{tp3_pct}%)
            - **Swing Low (30 Hari):** Rp {swing_low_30d:,.0f}
            - **Moving Average 20:** Rp {ma20_val:,.0f}
            - **Moving Average 50:** Rp {ma50_val:,.0f}
            """)

        st.markdown("### 📌 Catatan Eksekusi & Strategy Notes")
        st.info(f"""
        1. **Entry Strategy:** Pembelian bertahap di area Rp {curr_price:,.0f}.
        2. **Profit Taking:** Lakukan *Scale-Out* (Jual 50% di TP1 Rp {tp1:,.0f}, sisa 50% letakkan trailing stop hingga TP2/TP3).
        3. **Disciplined Exit:** Jika harga menembus ke bawah **Rp {stop_loss:,.0f}** pada penutupan candle daily, wajib lakukan **Cut Loss** tanpa kompromi.
        """)

        # Chart Tampilan
        st.line_chart(df[['Close', 'MA20', 'MA50']].tail(60))

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
        
        curr = data.iloc[-1]
        stoch_gc = (stoch_k.iloc[-2] <= stoch_d.iloc[-2]) and (stoch_k.iloc[-1] > stoch_d.iloc[-1]) and (stoch_k.iloc[-1] <= 40)
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
    st.subheader("🎯 Generator Trade Plan Manual")
    st.caption("Masukkan kode saham tanpa '.JK' (contoh: BBCA, TLKM, ADRO) beserta estimasi modal Anda.")
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        user_ticker = st.text_input("Kode Saham (Ticker):", value="BBCA").strip()
    with col_input2:
        user_budget = st.number_input("Total Modal (Rp):", value=10000000, step=1000000)

    if st.button("Hitung Trade Plan") or user_ticker:
        if user_ticker:
            generate_full_trade_plan(user_ticker, budget=user_budget)


# ----------------------------------------------------
# FITUR 2: SCREENER RSI DIVERGENCE
# ----------------------------------------------------
elif menu == "2. Screener RSI Divergence":
    st.subheader("🔍 Screener RSI Divergence & Golden Cross")
    
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
        st.markdown("#### 💡 Klik/Pilih Saham Hasil Screener untuk Lihat Trade Plan Lengkap:")
        selected_ticker = st.selectbox("Pilih Saham:", df_res['Ticker'].tolist(), key="select_rsi")
        if selected_ticker:
            generate_full_trade_plan(selected_ticker)


# ----------------------------------------------------
# FITUR 3: SCREENER STOCHASTIC + PSAR
# ----------------------------------------------------
elif menu == "3. Screener Stochastic + PSAR":
    st.subheader("🔍 Screener Stochastic + Parabolic SAR")
    
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
        st.markdown("#### 💡 Klik/Pilih Saham Hasil Screener untuk Lihat Trade Plan Lengkap:")
        selected_ticker = st.selectbox("Pilih Saham:", df_res['Ticker'].tolist(), key="select_stoch")
        if selected_ticker:
            generate_full_trade_plan(selected_ticker)
