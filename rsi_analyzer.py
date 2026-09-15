import pandas as pd
import pandas_ta as ta
import yfinance as yf


def extract_swings(df_in, series, left=2, right=2):
    swings = []
    n = len(series)
    for i in range(left, n):
        current_val = series.iloc[i]
        left_vals = series.iloc[i - left : i]
        remaining_right = n - 1 - i

        if remaining_right >= right:
            right_vals = series.iloc[i + 1 : i + 1 + right]
            if all(current_val >= val for val in left_vals) and all(
                current_val > val for val in right_vals
            ):
                swings.append({
                    "Tanggal": series.index[i],
                    "Nilai": current_val,
                    "Harga Close": df_in["Close"].iloc[i],
                    "Type": "SWING HIGH",
                    "Status": "Confirmed",
                })
            elif all(current_val <= val for val in left_vals) and all(
                current_val < val for val in right_vals
            ):
                swings.append({
                    "Tanggal": series.index[i],
                    "Nilai": current_val,
                    "Harga Close": df_in["Close"].iloc[i],
                    "Type": "SWING LOW",
                    "Status": "Confirmed",
                })
    return pd.DataFrame(swings)


def get_all_bases(df_source, min_candles=4, max_range_pct=0.10):
    df_b = df_source.copy().reset_index()
    if "Date" in df_b.columns:
        df_b = df_b.rename(columns={"Date": "Tanggal"})
    df_b = df_b.dropna().sort_values("Tanggal").reset_index(drop=True)

    bases = []
    i = len(df_b) - 1
    while i >= min_candles - 1:
        best_base = None
        for length in range(min_candles, 40):
            start_idx = i - length + 1
            if start_idx < 0:
                break
            sub = df_b.iloc[start_idx : i + 1]
            max_h = sub["High"].max()
            min_l = sub["Low"].min()
            range_pct = (max_h - min_l) / min_l if min_l > 0 else 0

            if range_pct <= max_range_pct:
                best_base = {
                    "Tgl Mulai Base": sub["Tanggal"].iloc[0],
                    "Tgl Akhir Base": sub["Tanggal"].iloc[-1],
                    "Jumlah Candle": length,
                    "Base Support (Low)": int(round(min_l)),
                    "Base Resistance (High)": int(round(max_h)),
                    "Range Harga (Rp)": int(round(max_h - min_l)),
                    "Lebar Konsolidasi": f"{round(range_pct * 100, 2)}%",
                    "start_idx": start_idx,
                }
            else:
                break

        if best_base:
            bases.append(best_base)
            i = best_base["start_idx"] - 1
        else:
            i -= 1

    res_df = pd.DataFrame(bases)
    if not res_df.empty:
        res_df = res_df.drop(columns=["start_idx"])
    return res_df


def detect_all_divergences(df_data, is_gc, is_dc):
    max_date = df_data.index.max()
    cutoff_scan = max_date - pd.Timedelta(days=30)
    cutoff_fresh = max_date - pd.Timedelta(days=4)
    min_rsi_diff = 3.0
    min_price_diff_pct = 0.015
    div_results = []

    p_swings_low = extract_swings(df_data, df_data["Low"])
    if p_swings_low.empty:
        return pd.DataFrame()

    p_swings_low = (
        p_swings_low[p_swings_low["Type"] == "SWING LOW"]
        .sort_values("Tanggal", ascending=False)
        .reset_index(drop=True)
    )

    rsi_swings_low = extract_swings(df_data, df_data["RSI_10"])
    if rsi_swings_low.empty:
        return pd.DataFrame()

    rsi_swings_low = (
        rsi_swings_low[rsi_swings_low["Type"] == "SWING LOW"]
        .sort_values("Tanggal", ascending=False)
        .reset_index(drop=True)
    )

    for i in range(len(p_swings_low) - 1):
        right_p = p_swings_low.iloc[i]
        if (
            right_p["Tanggal"] < cutoff_scan
            or right_p["Tanggal"] < cutoff_fresh
        ):
            continue

        for j in range(i + 1, len(p_swings_low)):
            left_p = p_swings_low.iloc[j]
            days_gap = (right_p["Tanggal"] - left_p["Tanggal"]).days
            if not (4 <= days_gap <= 60):
                continue

            rsi_right_match = rsi_swings_low[
                (
                    rsi_swings_low["Tanggal"]
                    >= right_p["Tanggal"] - pd.Timedelta(days=5)
                )
                & (
                    rsi_swings_low["Tanggal"]
                    <= right_p["Tanggal"] + pd.Timedelta(days=5)
                )
            ]
            rsi_left_match = rsi_swings_low[
                (
                    rsi_swings_low["Tanggal"]
                    >= left_p["Tanggal"] - pd.Timedelta(days=5)
                )
                & (
                    rsi_swings_low["Tanggal"]
                    <= left_p["Tanggal"] + pd.Timedelta(days=5)
                )
            ]

            if not rsi_right_match.empty and not rsi_left_match.empty:
                val_rsi_right = rsi_right_match.iloc[0]["Nilai"]
                val_rsi_left = rsi_left_match.iloc[0]["Nilai"]
                price_diff_pct = (
                    abs(right_p["Nilai"] - left_p["Nilai"]) / left_p["Nilai"]
                )
                rsi_diff = abs(val_rsi_right - val_rsi_left)

                status_bull = (
                    "Valid (GC Confirmed)"
                    if is_gc
                    else "Potensial (Menunggu GC)"
                )
                pattern_type = None

                rsi_in_between = df_data.loc[
                    left_p["Tanggal"] : right_p["Tanggal"], "RSI_10"
                ]

                if (
                    (right_p["Nilai"] < left_p["Nilai"])
                    and (val_rsi_right > val_rsi_left)
                    and (val_rsi_right < 30)
                ):
                    if (rsi_in_between <= 30).all():
                        if (
                            price_diff_pct >= min_price_diff_pct
                            and rsi_diff >= min_rsi_diff
                        ):
                            pattern_type = (
                                f"Regular Bullish Divergence {status_bull}"
                            )

                elif (
                    (right_p["Nilai"] >= left_p["Nilai"])
                    and (val_rsi_right < val_rsi_left)
                    and (35 <= val_rsi_right <= 65)
                ):
                    if (
                        price_diff_pct >= min_price_diff_pct
                        and rsi_diff >= min_rsi_diff
                    ):
                        pattern_type = (
                            f"Hidden Bullish Divergence {status_bull}"
                        )

                if pattern_type:
                    div_results.append({
                        "Jenis Divergence": pattern_type,
                        "Tanggal Kiri": left_p["Tanggal"],
                        "Harga Kiri": left_p["Nilai"],
                        "RSI Kiri": val_rsi_left,
                        "Tanggal Kanan": right_p["Tanggal"],
                        "Harga Kanan": right_p["Nilai"],
                        "RSI Kanan": val_rsi_right,
                    })
                    break

    return pd.DataFrame(div_results)


def generate_6_tables(ticker, period="1y"):
    df = yf.download(ticker, period=period, interval="1d", auto_adjust=False)
    if df.empty:
        raise ValueError("Data ticker tidak ditemukan.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df["RSI_10"] = df.ta.rsi(close=df["Close"], length=10)
    df["RSI_EMA10"] = df.ta.ema(close=df["RSI_10"], length=10)

    tabel_4 = get_all_bases(df, min_candles=4, max_range_pct=0.10)

    swings_high_chart = extract_swings(df, df["High"])
    swings_low_chart = extract_swings(df, df["Low"])
    all_chart_swings = pd.concat([
        swings_high_chart[swings_high_chart["Type"] == "SWING HIGH"],
        swings_low_chart[swings_low_chart["Type"] == "SWING LOW"],
    ], ignore_index=True)

    highs_chart = (
        all_chart_swings[all_chart_swings["Type"] == "SWING HIGH"]
        .sort_values("Tanggal", ascending=False)
        .head(5)
    )
    lows_chart = (
        all_chart_swings[all_chart_swings["Type"] == "SWING LOW"]
        .sort_values("Tanggal", ascending=False)
        .head(5)
    )
    tabel_1 = pd.concat([highs_chart, lows_chart], ignore_index=True)

    min_date_tabel_1 = (
        tabel_1["Tanggal"].min() if not tabel_1.empty else df.index.min()
    )
    swings_rsi_all = extract_swings(df, df["RSI_10"])
    swings_rsi_filtered = swings_rsi_all[
        swings_rsi_all["Tanggal"] >= min_date_tabel_1
    ]

    highs_rsi = swings_rsi_filtered[
        swings_rsi_filtered["Type"] == "SWING HIGH"
    ].sort_values("Tanggal", ascending=False)
    lows_rsi = swings_rsi_filtered[
        swings_rsi_filtered["Type"] == "SWING LOW"
    ].sort_values("Tanggal", ascending=False)
    tabel_2 = pd.concat([highs_rsi, lows_rsi], ignore_index=True)

    tabel_3 = tabel_2.copy()
    if not tabel_3.empty:
        tabel_3["Nilai EMA 10"] = tabel_3["Tanggal"].map(df["RSI_EMA10"])

    latest_rsi_daily = df["RSI_10"].iloc[-1]
    latest_ema10_daily = df["RSI_EMA10"].iloc[-1]
    is_golden_cross = latest_rsi_daily > latest_ema10_daily
    is_dead_cross = latest_rsi_daily < latest_ema10_daily

    tabel_5 = detect_all_divergences(df, is_golden_cross, is_dead_cross)

    tabel_6_raw = df.tail(30).copy().reset_index()
    if "Date" in tabel_6_raw.columns:
        tabel_6_raw = tabel_6_raw.rename(columns={"Date": "Tanggal"})

    tabel_6 = tabel_6_raw[["Tanggal", "Close", "RSI_10", "RSI_EMA10"]].copy()
    tabel_6["Tanggal"] = pd.to_datetime(tabel_6["Tanggal"]).dt.strftime(
        "%Y-%m-%d"
    )
    tabel_6["Harga Close"] = tabel_6["Close"].apply(lambda x: f"Rp {x:,.0f}")
    tabel_6["RSI 10 Daily"] = tabel_6["RSI_10"].round(2)
    tabel_6["Smoothing EMA 10 Daily"] = tabel_6["RSI_EMA10"].round(2)
    tabel_6 = tabel_6[[
        "Tanggal",
        "Harga Close",
        "RSI 10 Daily",
        "Smoothing EMA 10 Daily",
    ]].sort_values("Tanggal", ascending=False)

    return tabel_1, tabel_2, tabel_3, tabel_4, tabel_5, tabel_6