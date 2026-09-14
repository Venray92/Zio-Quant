import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

TICKERS = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "ASII.JK", "GOTO.JK", "UNVR.JK", "ICBP.JK", "INDF.JK",
    "KLBF.JK", "UNTR.JK", "ADRO.JK", "PTBA.JK", "ANTM.JK", "INCO.JK", "MDKA.JK", "PGAS.JK", "SMGR.JK", "INTP.JK",
    "CPIN.JK", "BRIS.JK", "ARTO.JK", "BUMI.JK", "ENRG.JK", "MEDC.JK", "ELSA.JK", "HRUM.JK", "ITMG.JK", "BRPT.JK",
    "TPIA.JK", "AMRT.JK", "MAPI.JK", "ERAA.JK", "ACES.JK", "MAPA.JK", "MYOR.JK", "GGRM.JK", "HMSP.JK", "SIDO.JK",
    "JPFA.JK", "MAIN.JK", "CMRY.JK", "ULTJ.JK", "MIKA.JK", "HEAL.JK", "SILO.JK", "BIRD.JK", "ASSA.JK", "SMDR.JK",
    "TMAS.JK", "TPMA.JK", "DOID.JK", "ABMM.JK", "BSSR.JK", "TOBA.JK", "BBTN.JK", "BBYB.JK", "BNGA.JK", "BDMN.JK",
    "PNBN.JK", "NISP.JK", "BBKP.JK", "MAYA.JK", "BABP.JK", "AGRO.JK", "BANK.JK", "BGTG.JK", "NOBU.JK", "INPC.JK",
    "MEGA.JK", "BNII.JK", "BTPN.JK", "BJBR.JK", "BJTM.JK", "BSIM.JK", "BINA.JK", "SDRA.JK", "AMAR.JK", "MASB.JK",
    "AUTO.JK", "GJTL.JK", "SMSM.JK", "DRMA.JK", "IMJS.JK", "IPCC.JK", "IPCM.JK", "WEHA.JK", "JSMR.JK", "CMNP.JK",
    "SCMA.JK", "MNCN.JK", "EMTK.JK", "BELL.JK", "TRIS.JK", "SRIL.JK", "TEBE.JK", "HRTA.JK", "PSAB.JK", "BRMS.JK",
    "DEWA.JK", "INDY.JK", "BYAN.JK", "CUAN.JK", "BREN.JK", "PANI.JK", "AMMN.JK", "ARCI.JK", "ADMF.JK", "CFIN.JK",
    "WOMF.JK", "LIFE.JK", "ASBI.JK", "ASRM.JK", "PWON.JK", "BSDE.JK", "CTRA.JK", "SMRA.JK", "APLN.JK",
    "ASRI.JK", "BEST.JK", "KIJA.JK", "DMAS.JK", "MKPI.JK", "JRPT.JK", "LPPF.JK", "MPPA.JK", "RALS.JK", "HERO.JK",
    "ERTX.JK", "PURA.JK", "STAR.JK", "ESTI.JK", "POLU.JK", "RICY.JK", "TFCO.JK", "FIRE.JK", "MITI.JK", "INDS.JK",
    "WINS.JK", "BULL.JK", "SOCI.JK", "COAL.JK", "PACK.JK", "GTSI.JK", "ADMR.JK", "CLEO.JK", "STAA.JK", "DSNG.JK",
    "AALI.JK", "LSIP.JK", "SIMP.JK", "TAPG.JK", "SGRO.JK", "TBLA.JK", "MGRO.JK", "UNSP.JK", "PALM.JK",
    "SMAR.JK", "GZCO.JK", "PSGO.JK", "BTEK.JK", "GOLL.JK", "SHIP.JK", "PORT.JK", "PEGE.JK", "RIGS.JK", "BESS.JK",
    "BPFI.JK", "TRUS.JK", "VINS.JK", "ASDM.JK", "ASMI.JK", "ABDA.JK", "EDGE.JK", "DGIK.JK", "KOKA.JK",
    "BOAT.JK", "MORA.JK", "PTDU.JK", "GTRA.JK", "RELF.JK", "HAIS.JK", "ALII.JK", "PUDP.JK", "CPRO.JK", "BIKA.JK"
]

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

def detect_rsi_patterns_and_score(ticker):
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
                            "Penalti Usia": f"-{age_penalty} pts",
                            "Status GC": "GC CONFIRMED" if is_gc else "WATCHLIST",
                            "TOTAL SCORE": total_score
                        }
        return None

    except Exception:
        return None

if __name__ == "__main__":
    results = []
    print("--- SCREENER RSI DIVERGENCE ---")
    for idx, t in enumerate(TICKERS):
        res = detect_rsi_patterns_and_score(t)
        if res:
            results.append(res)
        print(f"Progress: {idx+1}/{len(TICKERS)} checked...", end="\r")

    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by="TOTAL SCORE", ascending=False).reset_index(drop=True)
        print(f"\n\nHASIL AKURAT FINAL ({len(df_res)} Saham Lolos):")
        print(df_res.to_string())
    else:
        print("\n\nTidak ada saham yang lolos.")