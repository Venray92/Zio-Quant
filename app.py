import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go

# ==========================================
# 1. KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="ZioQuant - Pro IDX Swing & Trade Plan Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Dark Theme & UI Tweaks
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 12px;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ ZioQuant - Swing & Trade Plan Analytics")
st.caption("Aplikasi Analisis Swing High/Low, Support/Resistance, Pola Candlestick & Trade Plan Presisi Tick IDX")
st.markdown("---")

# ==========================================
# 2. SIDEBAR KONTROL
# ==========================================
st.sidebar.header("⚙️ Parameter Saham")
ticker_symbol = st.sidebar.text_input("Kode Saham IDX", value="INCO.JK")
time_period = st.sidebar.selectbox("Periode Data", ["3mo", "6mo", "1y"], index=1)

# ==========================================
# 3. FUNGSI UTILITAS & TICK IDX
# ==========================================
def get_tick_size(price):
    if price < 200:
        return 1
    elif price <= 500:
        return 2
    elif price < 2000:
        return 5
    elif price < 5000:
        return 10
    else:
        return 25

def add_ticks(price, n_ticks):
    p = price
    for _ in range(n_ticks):
        p += get_tick_size(p)
    return round(p, 2)

def sub_ticks(price, n_ticks):
    p = price
    for _ in range(n_ticks):
        tick = get_tick_size(p)
        p -= tick
        if p < 1:
            p = 1
    return round(p, 2)

def round_to_nearest_tick(price):
    tick = get_tick_size(price)
    return round(round(price / tick) * tick, 2)

def filter_overlapping_levels(df_levels, col1, col2):
    accepted_rows = []
    accepted_ranges = []
    for _, row in df_levels.iterrows():
        r_min = min(row[col1], row[col2])
        r_max = max(row[col1], row[col2])
        overlap = False
        for a_min, a_max in accepted_ranges:
            if max(r_min, a_min) <= min(r_max, a_max):
                overlap = True
                break
        if not overlap:
            accepted_rows.append(row)
            accepted_ranges.append((r_min, r_max))
    return pd.DataFrame(accepted_rows)

# ==========================================
# 4. LOGIKA CANDLESTICK CLASSIFICATION
# ==========================================
def get_props(row):
    high = row["High"]
    low = row["Low"]
    open_p = row["Open"]
    close = row["Close"]
    body_top = max(open_p, close)
    body_bottom = min(open_p, close)
    body_size = body_top - body_bottom
    total_range = high - low
    if total_range == 0:
        total_range = 0.0001
    return {
        "high": high, "low": low, "open": open_p, "close": close,
        "body_top": body_top, "body_bottom": body_bottom,
        "body_size": body_size, "total_range": total_range,
        "upper_shadow": high - body_top, "lower_shadow": body_bottom - low,
        "is_green": close > open_p, "is_red": close < open_p,
    }

def classify_candle(df_all):
    if len(df_all) < 3:
        return "Standard Doji", "ℹ️ Info: Kekuatan pembeli dan penjual seimbang. Pasar sedang ragu, wait and see."

    r3, r2, r1 = df_all.iloc[-3], df_all.iloc[-2], df_all.iloc[-1]
    p3, p2, p1 = get_props(r3), get_props(r2), get_props(r1)

    if p3["is_green"] and p2["is_green"] and p1["is_green"] and p1["close"] > p2["close"] and p2["close"] > p3["close"]:
        return "Three White Soldiers", "💡 Sinyal: Pembeli dominan berturut-turut. Momentum naik sangat kuat."
    if p3["is_red"] and p3["body_size"] >= 0.4 * p3["total_range"] and p2["body_size"] <= 0.3 * p2["total_range"] and p1["is_green"] and p1["close"] >= (p3["open"] + p3["close"]) / 2:
        return "Morning Star", "💡 Sinyal: Fase penurunan berakhir. Pola pembalikan arah naik berakurasi tinggi."
    if p3["is_green"] and p3["body_size"] >= 0.4 * p3["total_range"] and p2["body_size"] <= 0.3 * p2["total_range"] and p1["is_red"] and p1["close"] <= (p3["open"] + p3["close"]) / 2:
        return "Evening Star", "⚠️ Warning: Tren naik resmi patah. Persiapkan strategi exit atau Stop Loss."
    if p1["is_green"] and p2["is_red"] and p1["body_top"] >= p2["body_top"] and p1["body_bottom"] <= p2["body_bottom"]:
        return "Bullish Engulfing", "💡 Sinyal: Pembeli mengambil alih. Sinyal pembalikan arah naik cukup valid."
    if p1["is_red"] and p2["is_green"] and p1["body_bottom"] <= p2["body_bottom"] and p1["body_top"] >= p2["body_top"]:
        return "Bearish Engulfing", "⚠️ Warning: Penjual menguasai pasar secara agresif. Waspada koreksi tajam."
    if p1["is_green"] and p2["is_red"] and p1["close"] >= (p2["open"] + p2["close"]) / 2 and p1["open"] <= p2["close"]:
        return "Piercing Line", "💡 Sinyal: Perlawanan pembeli menembus pertengahan candle merah. Sinyal pembalikan arah."
    if p1["is_red"] and p2["is_green"] and p1["close"] <= (p2["open"] + p2["close"]) / 2 and p1["open"] >= p2["close"]:
        return "Dark Cloud Cover", "⚠️ Warning: Penjual menekan balik hingga melewati separuh candle hijau. Amankan profit!"
    if p1["body_size"] <= 0.15 * p1["total_range"] and p1["lower_shadow"] >= 0.6 * p1["total_range"] and p1["upper_shadow"] <= 0.1 * p1["total_range"]:
        return "Dragonfly Doji", "💡 Sinyal: Penolakan bawah sangat kuat. Area support valid, siap-siap berburu entry."
    if p1["body_size"] <= 0.15 * p1["total_range"] and p1["upper_shadow"] >= 0.6 * p1["total_range"] and p1["lower_shadow"] <= 0.1 * p1["total_range"]:
        return "Gravestone Doji", "⚠️ Warning: Penolakan atas sangat masif. Pasokan melimpah, rawan dump."
    if p1["body_size"] <= 0.2 * p1["total_range"] and p1["upper_shadow"] >= 0.35 * p1["total_range"] and p1["lower_shadow"] >= 0.35 * p1["total_range"]:
        return "Long-Legged Doji", "ℹ️ Info: Volatilitas ekstrem tetapi berakhir imbang. Tunggu penentuan arah break."
    if p1["body_size"] <= 0.2 * p1["total_range"]:
        if p1["upper_shadow"] <= 0.1 and p1["lower_shadow"] <= 0.1:
            return "Standard Doji", "ℹ️ Info: Kekuatan pembeli dan penjual seimbang. Pasar sedang ragu, wait and see."
        else:
            return "Spinning Top", "ℹ️ Info: Konsolidasi tipis. Momentum melambat, bersiap untuk pergerakan berikutnya."
    if p1["is_green"] and p1["upper_shadow"] <= 0.05 * p1["total_range"] and p1["lower_shadow"] <= 0.05 * p1["total_range"]:
        return "Marubozu Hijau", "💡 Sinyal: Pembeli dominan penuh. Momentum naik sangat kuat, siap lanjut rally."
    if p1["is_red"] and p1["upper_shadow"] <= 0.05 * p1["total_range"] and p1["lower_shadow"] <= 0.05 * p1["total_range"]:
        return "Marubozu Merah", "⚠️ Warning: Tekanan jual sangat deras (falling knife). Hindari beli, tunggu konfirmasi pantulan!"
    if p1["upper_shadow"] >= 0.66 * p1["total_range"] or p1["lower_shadow"] >= 0.66 * p1["total_range"]:
        return "Pinbar", "💡 / ⚠️ Sinyal: Terjadi liquidity sweep / penolakan ekor panjang. Ikuti arah ekor penolakannya."
    if p1["is_green"]:
        if p1["lower_shadow"] >= 2 * p1["body_size"]:
            return "Hammer", "💡 Sinyal: Tekanan jual ditolak kuat di bawah. Potensi bounce (pantulan naik)."
        elif p1["upper_shadow"] >= 2 * p1["body_size"]:
            return "Inverted Hammer", "💡 Sinyal: Pembeli mulai merangsek naik. Tunggu konfirmasi candle hijau berikutnya."
        else:
            return "Marubozu Hijau", "💡 Sinyal: Pembeli dominan penuh. Momentum naik sangat kuat, siap lanjut rally."
    else:
        if p1["upper_shadow"] >= 2 * p1["body_size"]:
            return "Shooting Star", "⚠️ Warning: Kenaikan harga ditolak keras di atas. Potensi longsor dari puncak."
        elif p1["lower_shadow"] >= 2 * p1["body_size"]:
            return "Hanging Man", "⚠️ Warning: Sinyal bahaya di area atas. Pembeli mulai kehilangan tenaga."
        else:
            return "Marubozu Merah", "⚠️ Warning: Tekanan jual sangat deras (falling knife). Hindari beli, tunggu konfirmasi pantulan!"

# ==========================================
# 5. EKSEKUSI DATA & PEMROSESAN
# ==========================================
@st.cache_data(ttl=1800)
def fetch_and_process_data(ticker, period):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval="1d").reset_index()
    if df.empty:
        return None, None, None, None, None, None, None, None

    # Normalisasi timezone jika ada
    if pd.api.types.is_datetime64tz_dtype(df["Date"]):
        df["Date"] = df["Date"].dt.tz_localize(None)

    df["Body_Top"] = df[["Open", "Close"]].max(axis=1)
    df["Body_Bottom"] = df[["Open", "Close"]].min(axis=1)
    df["Prev_Close"] = df["Close"].shift(1)
    df["TR"] = np.maximum(
        df["High"] - df["Low"],
        np.maximum(abs(df["High"] - df["Prev_Close"]), abs(df["Low"] - df["Prev_Close"]))
    )
    atr_14 = df["TR"].rolling(window=14).mean().iloc[-1]

    # Swing Detection
    order = 3
    high_idx = argrelextrema(df["High"].values, np.greater_equal, order=order)[0]
    low_idx = argrelextrema(df["Low"].values, np.less_equal, order=order)[0]

    df["Swing_Type"] = ""
    df.iloc[high_idx, df.columns.get_loc("Swing_Type")] = "Swing High"
    df.iloc[low_idx, df.columns.get_loc("Swing_Type")] = "Swing Low"

    highs_15 = df[df["Swing_Type"] == "Swing High"].sort_values(by="Date", ascending=False).head(15)
    lows_15 = df[df["Swing_Type"] == "Swing Low"].sort_values(by="Date", ascending=False).head(15)
    highs_5 = highs_15.head(5)

    # Direction
    latest_high_row = highs_5.sort_values(by="Date", ascending=False).iloc[0]
    latest_low_row = lows_15.head(5).sort_values(by="Date", ascending=False).iloc[0]
    latest_high_val = latest_high_row["High"]
    latest_low_val = latest_low_row["Low"]
    last_market_close = df.iloc[-1]["Close"]
    midpoint_50 = (latest_high_val + latest_low_val) / 2
    direction_result = "BOB" if last_market_close >= midpoint_50 else "BOW"

    direction_df = pd.DataFrame([{
        "Swing High Terupdate": round(latest_high_val, 2),
        "Swing Low Terupdate": round(latest_low_val, 2),
        "Level 50%": round(midpoint_50, 2),
        "Last Close Market": round(last_market_close, 2),
        "Direction": direction_result,
    }])

    # Strong Resistance
    sorted_swings_res = highs_5.sort_values(by="High", ascending=False).iloc[:3]
    res_results = []
    ranks_res = ["1st Highest (Utama)", "2nd Highest (Kedua)", "3rd Highest (Ketiga)"]
    for rank_label, (_, row) in zip(ranks_res, sorted_swings_res.iterrows()):
        idx = row.name
        body_tops = [row["Body_Top"]]
        if idx > 0: body_tops.append(df.loc[idx - 1, "Body_Top"])
        if idx < len(df) - 1: body_tops.append(df.loc[idx + 1, "Body_Top"])
        res_results.append({
            "Date": row["Date"].strftime("%Y-%m-%d"),
            "Rank": rank_label,
            "Body_Top": round(max(body_tops), 2),
            "High": round(row["High"], 2),
        })
    strong_resistance = filter_overlapping_levels(pd.DataFrame(res_results), "Body_Top", "High")

    # Strong Support
    recent_lows_sup = lows_15.sort_values(by="Date", ascending=False).head(3)
    sup_results = []
    ranks_sup = ["1st Support (Terdekat)", "2nd Support", "3rd Support (Terjauh)"]
    for rank_label, (_, row) in zip(ranks_sup, recent_lows_sup.iterrows()):
        idx = row.name
        body_bottoms = [row["Body_Bottom"]]
        if idx > 0: body_bottoms.append(df.loc[idx - 1, "Body_Bottom"])
        if idx < len(df) - 1: body_bottoms.append(df.loc[idx + 1, "Body_Bottom"])
        sup_results.append({
            "Date": row["Date"].strftime("%Y-%m-%d"),
            "Rank": rank_label,
            "Low": round(row["Low"], 2),
            "Body_Bottom": round(min(body_bottoms), 2),
        })
    strong_support = filter_overlapping_levels(pd.DataFrame(sup_results), "Body_Bottom", "Low")

    # Trade Plan
    def find_target_1(min_val):
        valid_res = sorted([p for p in strong_resistance["High"].values if p > min_val])
        if valid_res: return round_to_nearest_tick(valid_res[0])
        sh_valid = highs_15.sort_values(by="Date", ascending=False)
        sh_valid = sh_valid[sh_valid["High"] > min_val]
        if not sh_valid.empty: return round_to_nearest_tick(sh_valid.iloc[0]["High"])
        return round_to_nearest_tick(min_val)

    def find_target_2(target_1):
        valid_res = sorted([p for p in strong_resistance["High"].values if p > target_1])
        if valid_res: return round_to_nearest_tick(valid_res[0])
        sh_valid = highs_15.sort_values(by="Date", ascending=False)
        sh_valid = sh_valid[sh_valid["High"] > target_1]
        if not sh_valid.empty: return round_to_nearest_tick(sh_valid.iloc[0]["High"])
        return round_to_nearest_tick(target_1 + (1.5 * atr_14))

    candle_name, current_warning = classify_candle(df)

    # BOW
    sup_row = strong_support.iloc[0]
    s_low, s_bb = sup_row["Low"], sup_row["Body_Bottom"]
    rb_bow_min, rb_bow_max = min(s_low, s_bb), max(s_low, s_bb)
    range_buy_bow = f"{rb_bow_min} - {rb_bow_max}"
    stop_loss_bow = sub_ticks(rb_bow_min, 3)
    target_1_bow = find_target_1(rb_bow_max)
    target_2_bow = find_target_2(target_1_bow)
    risk_bow = rb_bow_min - stop_loss_bow
    reward_bow = target_1_bow - rb_bow_min
    ratio_bow = f"1 : {round(reward_bow / risk_bow, 1)}" if risk_bow > 0 else "-"

    # BOB
    res_sorted_by_date = strong_resistance.sort_values(by="Date", ascending=False)
    latest_res_row = res_sorted_by_date.iloc[0]
    base_bob_high = latest_res_row["High"]
    upper_bob_high = add_ticks(base_bob_high, 3)
    range_buy_bob = f"{base_bob_high} - {upper_bob_high}"
    stop_loss_bob = sub_ticks(base_bob_high, 3)
    target_1_bob = find_target_1(upper_bob_high)
    target_2_bob = find_target_2(target_1_bob)
    risk_bob = base_bob_high - stop_loss_bob
    reward_bob = target_1_bob - base_bob_high
    ratio_bob = f"1 : {round(reward_bob / risk_bob, 1)}" if risk_bob > 0 else "-"

    trade_plan_df = pd.DataFrame([
        {"No": 1, "Type": "BOW", "Range Buy": range_buy_bow, "Stop Loss": stop_loss_bow, "Target 1": target_1_bow, "Target 2": target_2_bow, "Rasio (R:R)": ratio_bow, "Status Candle": candle_name, "Warning": current_warning},
        {"No": 2, "Type": "BOB", "Range Buy": range_buy_bob, "Stop Loss": stop_loss_bob, "Target 1": target_1_bob, "Target 2": target_2_bob, "Rasio (R:R)": ratio_bob, "Status Candle": candle_name, "Warning": current_warning}
    ])

    # Swing Points & Metpoint
    swing_points = pd.concat([highs_15, lows_15]).copy()
    swing_points = swing_points.sort_values(by=["Swing_Type", "Date"], ascending=[True, False])
    swing_points["No"] = range(1, len(swing_points) + 1)

    TOLERANCE_PCT = 0.015
    def find_metpoints(row, df_all):
        no_curr = row["No"]
        stype_curr = row["Swing_Type"]
        prices_curr = [row["Low"], row["Close"]] if stype_curr == "Swing Low" else [row["High"], row["Open"]]
        matched_prices = set()
        for _, other_row in df_all.iterrows():
            if no_curr == other_row["No"]: continue
            stype_other = other_row["Swing_Type"]
            prices_other = [other_row["Low"], other_row["Close"]] if stype_other == "Swing Low" else [other_row["High"], other_row["Open"]]
            for p1 in prices_curr:
                for p2 in prices_other:
                    if abs(p1 - p2) / p1 <= TOLERANCE_PCT:
                        matched_prices.add(round(p1, 2))
        return ", ".join(map(str, sorted(matched_prices))) if matched_prices else "-"

    swing_points["metpoint"] = swing_points.apply(lambda r: find_metpoints(r, swing_points), axis=1)
    swing_points["Date_Str"] = swing_points["Date"].dt.strftime("%Y-%m-%d")
    swing_points = swing_points[["No", "Date_Str", "Open", "High", "Low", "Close", "Swing_Type", "metpoint"]]
    swing_points[["Open", "High", "Low", "Close"]] = swing_points[["Open", "High", "Low", "Close"]].round(2)

    return df, direction_df, strong_resistance, strong_support, trade_plan_df, swing_points, candle_name, current_warning

# ==========================================
# 6. TAMPILAN DASHBOARD
# ==========================================
with st.spinner(f"Menganalisis data teknikal {ticker_symbol}..."):
    try:
        df, dir_df, st_res, st_sup, trade_plan, swings, candle_status, warning_msg = fetch_and_process_data(ticker_symbol, time_period)

        if df is None:
            st.error(f"Data {ticker_symbol} tidak ditemukan. Pastikan ticker benar (contoh: INCO.JK, BBCA.JK).")
        else:
            # Metric Cards Top
            last_close = df.iloc[-1]["Close"]
            prev_close = df.iloc[-2]["Close"]
            chg = last_close - prev_close
            pct_chg = (chg / prev_close) * 100
            dir_val = dir_df.iloc[0]["Direction"]

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Harga Penutupan", f"Rp {last_close:,.0f}", f"{chg:+,.0f} ({pct_chg:+.2f}%)")
            col2.metric("Arah Strategi (Direction)", dir_val, delta="Buy On Weakness" if dir_val == "BOW" else "Buy On Breakout", delta_color="normal")
            col3.metric("Pola Candle Terakhir", candle_status)
            col4.metric("Midpoint (50%)", f"Rp {dir_df.iloc[0]['Level 50%']:,.0f}")

            # Warning Box
            if "⚠️" in warning_msg:
                st.warning(warning_msg)
            else:
                st.info(warning_msg)

            st.markdown("---")

            # Chart Interaktif Plotly
            st.subheader(f"📈 Grafik Candlestick & Key Levels - {ticker_symbol}")
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candlestick"
            ))

            # Plot Support & Resistance Lines
            for _, r in st_res.iterrows():
                fig.add_hline(y=r["High"], line_dash="dash", line_color="red", annotation_text=f"Resist: {r['High']}")
            for _, s in st_sup.iterrows():
                fig.add_hline(y=s["Low"], line_dash="dash", line_color="green", annotation_text=f"Support: {s['Low']}")

            fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

            # Tab Output
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Trade Plan", "🛡️ Support & Resistance", "🧭 Direction Matrix", "🎯 30 Swing Points"])

            with tab1:
                st.subheader("🎯 Trade Plan Presisi Tick IDX")
                st.dataframe(trade_plan, use_container_width=True, hide_index=True)

            with tab2:
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("🔴 Strong Resistance")
                    st.dataframe(st_res, use_container_width=True, hide_index=True)
                with c2:
                    st.subheader("🟢 Strong Support")
                    st.dataframe(st_sup, use_container_width=True, hide_index=True)

            with tab3:
                st.subheader("🧭 Direction Calculation Matrix")
                st.dataframe(dir_df, use_container_width=True, hide_index=True)

            with tab4:
                st.subheader("📌 30 Swing Points (15 High & 15 Low) & Metpoint")
                st.dataframe(swings, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")
