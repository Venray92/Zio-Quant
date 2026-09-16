import concurrent.futures
import warnings
import pandas as pd
import yfinance as yf

from ihsg_tickers import get_all_ihsg_tickers

warnings.filterwarnings("ignore")

DEFAULT_SAHAM_LIST = sorted(
    list(
        set([
            "ISAT.JK", "ACES.JK", "ADHI.JK", "ADRO.JK", "AGRO.JK", "AALI.JK",
            "AKRA.JK", "AMMN.JK", "AMRT.JK", "ANTM.JK", "APLN.JK", "ARTO.JK",
            "ASII.JK", "ASRI.JK", "AUTO.JK", "AVIA.JK", "BBCA.JK", "BBHI.JK",
            "BBNI.JK", "BBRI.JK", "BBTN.JK", "BCIC.JK", "BDMN.JK", "BELI.JK",
            "BIRD.JK", "BJBR.JK", "BJTM.JK", "BMRI.JK", "BMTR.JK", "BNGA.JK",
            "BREN.JK", "BRIS.JK", "BRPT.JK", "BSDE.JK", "BUKA.JK", "BUMI.JK",
            "BYAN.JK", "CITA.JK", "CLEO.JK", "CMRY.JK", "CPIN.JK", "CTRA.JK",
            "CUAN.JK", "DCII.JK", "DEWA.JK", "DILD.JK", "DKFT.JK", "DOID.JK",
            "DRMA.JK", "DSNG.JK", "EAST.JK", "EDGE.JK", "ELSA.JK", "EMTK.JK",
            "ENRG.JK", "ESSA.JK", "EXCL.JK", "FILM.JK", "GEMS.JK", "GJTL.JK",
            "GOTO.JK", "HAIS.JK", "HEAL.JK", "HRUM.JK", "ICBP.JK", "INAF.JK",
            "INCO.JK", "INDF.JK", "INDY.JK", "INKP.JK", "INTP.JK", "IPCC.JK",
            "IPCM.JK", "IRRA.JK", "ITMG.JK", "JKON.JK", "JPFA.JK", "JSPT.JK",
            "KAEF.JK", "KEEN.JK", "KIJA.JK", "KLBF.JK", "LEAD.JK", "LSIP.JK",
            "MAIN.JK", "MAPA.JK", "MAPI.JK", "MBAP.JK", "MBMA.JK", "MCAS.JK",
            "MDKA.JK", "MEDC.JK", "MEDS.JK", "MIKA.JK", "MNCN.JK", "MPMX.JK",
            "MTDL.JK", "MYOR.JK", "NCKL.JK", "NELY.JK", "NRCA.JK", "PANI.JK",
            "PANR.JK", "PGAS.JK", "PGEO.JK", "PNBN.JK", "POWR.JK", "PRDA.JK",
            "PSAB.JK", "PSSI.JK", "PTBA.JK", "PTPP.JK", "PWON.JK", "RAAM.JK",
            "RALS.JK", "SAME.JK", "SCMA.JK", "SIDO.JK", "SILO.JK", "SMBR.JK",
            "SMDR.JK", "SMGR.JK", "SMRA.JK", "SMSM.JK", "SSIA.JK", "SSMS.JK",
            "STAA.JK", "TAPG.JK", "TBIG.JK", "TCPI.JK", "TINS.JK", "TKIM.JK",
            "TLKM.JK", "TMAS.JK", "TOBA.JK", "TOTL.JK", "TOWR.JK", "TPIA.JK",
            "TSPC.JK", "UNTR.JK", "UNVR.JK", "WEGE.JK", "WIFI.JK", "WIKA.JK",
            "WINS.JK", "WOOD.JK",
        ])
    )
)


def calculate_rsi(series, period=10):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).copy()
    loss = (-delta.where(delta < 0, 0)).copy()

    avg_gain = gain.ewm(
        alpha=1 / period, min_periods=period, adjust=False
    ).mean()
    avg_loss = loss.ewm(
        alpha=1 / period, min_periods=period, adjust=False
    ).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_ema(series, period=10):
    return series.ewm(span=period, adjust=False).mean()


def detect_bases(df, min_candles=5, max_width_pct=8.0, window_lookback=60):
    bases = []
    sub_df = df.tail(window_lookback)
    n = len(sub_df)

    i = 0
    while i <= n - min_candles:
        found_base = None
        for length in range(min_candles, min(20, n - i + 1)):
            window = sub_df.iloc[i : i + length]
            base_low = window["Low"].min()
            base_high = window["High"].max()

            if base_low == 0:
                continue

            width_pct = ((base_high - base_low) / base_low) * 100

            if width_pct <= max_width_pct:
                found_base = {
                    "Tgl Mulai Base": window.index[0],
                    "Tgl Akhir Base": window.index[-1],
                    "Jumlah Candle": length,
                    "Base Support": base_low,
                    "Base Resistance": base_high,
                    "Lebar Konsolidasi (%)": round(width_pct, 2),
                }
            else:
                break

        if found_base:
            bases.append(found_base)
            i += found_base["Jumlah Candle"]
        else:
            i += 1

    return pd.DataFrame(bases)


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
                    "Index_Pos": i,
                    "Nilai": current_val,
                    "Type": "SWING HIGH",
                    "Status": "Confirmed",
                })
            elif all(current_val <= val for val in left_vals) and all(
                current_val < val for val in right_vals
            ):
                swings.append({
                    "Tanggal": series.index[i],
                    "Index_Pos": i,
                    "Nilai": current_val,
                    "Type": "SWING LOW",
                    "Status": "Confirmed",
                })

    return pd.DataFrame(swings)


def _process_single_rsi_ticker(ticker):
    try:
        formatted_ticker = ticker.strip().upper()
        if not formatted_ticker.endswith(".JK"):
            formatted_ticker = f"{formatted_ticker}.JK"

        df = yf.download(
            formatted_ticker,
            period="6mo",
            interval="1d",
            progress=False,
            auto_adjust=False,
        )
        if df.empty or len(df) < 30:
            return None, None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        c0 = df["Close"].iloc[-1]
        c1 = df["Close"].iloc[-2]
        v0 = df["Volume"].iloc[-1]
        latest_value = v0 * c0

        # Filter Likuiditas Minimum > 1 Miliar
        if latest_value <= 1_000_000_000:
            return None, None

        chg_pct = round(((c0 - c1) / c1) * 100, 2)

        df["RSI_10"] = calculate_rsi(df["Close"], period=10)
        df["RSI_EMA10"] = calculate_ema(df["RSI_10"], period=10)
        df = df.dropna(subset=["RSI_10", "RSI_EMA10"])

        latest_idx = len(df) - 1
        latest_rsi = df["RSI_10"].iloc[-1]
        latest_ema = df["RSI_EMA10"].iloc[-1]

        is_gc = latest_rsi > latest_ema
        is_dc = latest_rsi < latest_ema

        min_rsi_diff = 2.5
        min_price_diff_pct = 0.02
        clean_symbol = formatted_ticker.replace(".JK", "")

        df_bases = detect_bases(df, min_candles=5, max_width_pct=8.0)

        def evaluate_base_score(tgl_titik_1, tgl_titik_2):
            if df_bases.empty:
                return "Tidak Ada Base", 0

            has_base_t1, has_base_t2 = False, False
            width_t1, width_t2 = 0.0, 0.0

            for _, base in df_bases.iterrows():
                start_t1 = base["Tgl Mulai Base"] - pd.Timedelta(days=5)
                end_t1 = base["Tgl Akhir Base"] + pd.Timedelta(days=5)
                if start_t1 <= tgl_titik_1 <= end_t1:
                    has_base_t1 = True
                    width_t1 = base["Lebar Konsolidasi (%)"]

                if (
                    base["Tgl Mulai Base"] >= tgl_titik_1
                    and base["Tgl Akhir Base"] <= tgl_titik_2
                ):
                    if (tgl_titik_2 - base["Tgl Akhir Base"]).days <= 5:
                        has_base_t2 = True
                        width_t2 = base["Lebar Konsolidasi (%)"]

            if has_base_t1 and has_base_t2:
                return f"Grade A++ (T1: {width_t1}% | T2: {width_t2}%)", 30
            elif has_base_t2:
                return f"Ada Base Sblm Titik 2 ({width_t2}%)", 20
            elif has_base_t1:
                return f"Ada Base Titik 1 ({width_t1}%)", 10
            else:
                return "Tidak Ada Base", 0

        res_bull = None
        res_bear = None

        # ==========================================
        # A. BULLISH DIVERGENCE (SWING LOW)
        # ==========================================
        p_swings_low = extract_swings(df, df["Low"])
        rsi_swings_low = extract_swings(df, df["RSI_10"])

        if not p_swings_low.empty and not rsi_swings_low.empty:
            p_swings_low = p_swings_low[
                p_swings_low["Type"] == "SWING LOW"
            ].sort_values("Index_Pos", ascending=False)
            rsi_swings_low = rsi_swings_low[
                rsi_swings_low["Type"] == "SWING LOW"
            ].sort_values("Index_Pos", ascending=False)

            if len(p_swings_low) >= 2 and len(rsi_swings_low) >= 2:
                for i in range(len(p_swings_low) - 1):
                    right_p = p_swings_low.iloc[i]
                    bars_from_latest = latest_idx - right_p["Index_Pos"]
                    if bars_from_latest > 2:
                        continue

                    for j in range(i + 1, len(p_swings_low)):
                        left_p = p_swings_low.iloc[j]
                        bars_gap = right_p["Index_Pos"] - left_p["Index_Pos"]

                        if not (4 <= bars_gap <= 25):
                            continue

                        between_df = df.iloc[
                            int(left_p["Index_Pos"]) : int(right_p["Index_Pos"]) + 1
                        ]
                        if between_df["Low"].min() < (
                            min(left_p["Nilai"], right_p["Nilai"]) * 0.998
                        ):
                            continue

                        rsi_right_match = rsi_swings_low[
                            abs(rsi_swings_low["Index_Pos"] - right_p["Index_Pos"]) <= 3
                        ]
                        rsi_left_match = rsi_swings_low[
                            abs(rsi_swings_low["Index_Pos"] - left_p["Index_Pos"]) <= 3
                        ]

                        if not rsi_right_match.empty and not rsi_left_match.empty:
                            val_rsi_right = rsi_right_match.iloc[0]["Nilai"]
                            val_rsi_left = rsi_left_match.iloc[0]["Nilai"]
                            price_diff_pct = (
                                abs(right_p["Nilai"] - left_p["Nilai"]) / left_p["Nilai"]
                            )
                            rsi_diff = abs(val_rsi_right - val_rsi_left)

                            pattern_type = None

                            if (
                                (right_p["Nilai"] < left_p["Nilai"])
                                and (val_rsi_right > val_rsi_left)
                                and (val_rsi_right <= 35)
                            ):
                                if (
                                    price_diff_pct >= min_price_diff_pct
                                    and rsi_diff >= min_rsi_diff
                                ):
                                    pattern_type = "Regular Bullish Divergence"

                            elif (
                                (right_p["Nilai"] >= left_p["Nilai"])
                                and (val_rsi_right < val_rsi_left)
                                and (35 <= val_rsi_right <= 65)
                            ):
                                if (
                                    price_diff_pct >= min_price_diff_pct
                                    and rsi_diff >= min_rsi_diff
                                ):
                                    pattern_type = "Hidden Bullish Divergence"

                            if pattern_type:
                                base_desc, base_score = evaluate_base_score(
                                    left_p["Tanggal"], right_p["Tanggal"]
                                )
                                score = 0
                                score += 30 if is_gc else 15
                                score += base_score
                                score += (
                                    20
                                    if (rsi_diff >= 5.0 and price_diff_pct >= 0.03)
                                    else 10
                                )
                                if val_rsi_right <= 30:
                                    score += 20
                                elif val_rsi_right <= 35:
                                    score += 10

                                status_bull = (
                                    "Valid (GC Confirmed)"
                                    if is_gc
                                    else "Potensial (Menunggu GC)"
                                )

                                res_bull = {
                                    "Ticker": clean_symbol,
                                    "Harga": int(c0),
                                    "Change (%)": chg_pct,
                                    "Value (M)": round(latest_value / 1_000_000_000, 2),
                                    "Pattern": f"{pattern_type} {status_bull}",
                                    "Score": score,
                                    "Status Base": base_desc,
                                    "Tgl Kiri": left_p["Tanggal"].strftime("%Y-%m-%d"),
                                    "Harga Kiri": int(left_p["Nilai"]),
                                    "RSI Kiri": round(val_rsi_left, 2),
                                    "Tgl Kanan": right_p["Tanggal"].strftime("%Y-%m-%d"),
                                    "Harga Kanan": int(right_p["Nilai"]),
                                    "RSI Kanan": round(val_rsi_right, 2),
                                    "Signal_Type": "BULLISH",  # <--- FLAG TOGGLE
                                }
                                break

        # ==========================================
        # B. BEARISH DIVERGENCE (SWING HIGH)
        # ==========================================
        p_swings_high = extract_swings(df, df["High"])
        rsi_swings_high = extract_swings(df, df["RSI_10"])

        if not p_swings_high.empty and not rsi_swings_high.empty:
            p_swings_high = p_swings_high[
                p_swings_high["Type"] == "SWING HIGH"
            ].sort_values("Index_Pos", ascending=False)
            rsi_swings_high = rsi_swings_high[
                rsi_swings_high["Type"] == "SWING HIGH"
            ].sort_values("Index_Pos", ascending=False)

            if len(p_swings_high) >= 2 and len(rsi_swings_high) >= 2:
                for i in range(len(p_swings_high) - 1):
                    right_p = p_swings_high.iloc[i]
                    bars_from_latest = latest_idx - right_p["Index_Pos"]
                    if bars_from_latest > 2:
                        continue

                    for j in range(i + 1, len(p_swings_high)):
                        left_p = p_swings_high.iloc[j]
                        bars_gap = right_p["Index_Pos"] - left_p["Index_Pos"]

                        if not (4 <= bars_gap <= 25):
                            continue

                        between_df = df.iloc[
                            int(left_p["Index_Pos"]) : int(right_p["Index_Pos"]) + 1
                        ]
                        if between_df["High"].max() > (
                            max(left_p["Nilai"], right_p["Nilai"]) * 1.002
                        ):
                            continue

                        rsi_right_match = rsi_swings_high[
                            abs(rsi_swings_high["Index_Pos"] - right_p["Index_Pos"]) <= 3
                        ]
                        rsi_left_match = rsi_swings_high[
                            abs(rsi_swings_high["Index_Pos"] - left_p["Index_Pos"]) <= 3
                        ]

                        if not rsi_right_match.empty and not rsi_left_match.empty:
                            val_rsi_right = rsi_right_match.iloc[0]["Nilai"]
                            val_rsi_left = rsi_left_match.iloc[0]["Nilai"]
                            price_diff_pct = (
                                abs(right_p["Nilai"] - left_p["Nilai"]) / left_p["Nilai"]
                            )
                            rsi_diff = abs(val_rsi_right - val_rsi_left)

                            pattern_type = None

                            if (
                                (right_p["Nilai"] > left_p["Nilai"])
                                and (val_rsi_right < val_rsi_left)
                                and (val_rsi_right >= 65)
                            ):
                                if (
                                    price_diff_pct >= min_price_diff_pct
                                    and rsi_diff >= min_rsi_diff
                                ):
                                    pattern_type = "Regular Bearish Divergence"

                            elif (
                                (right_p["Nilai"] <= left_p["Nilai"])
                                and (val_rsi_right > val_rsi_left)
                                and (45 <= val_rsi_right <= 75)
                            ):
                                if (
                                    price_diff_pct >= min_price_diff_pct
                                    and rsi_diff >= min_rsi_diff
                                ):
                                    pattern_type = "Hidden Bearish Divergence"

                            if pattern_type:
                                base_desc, base_score = evaluate_base_score(
                                    left_p["Tanggal"], right_p["Tanggal"]
                                )
                                score = 0
                                score += -30 if is_dc else -15
                                score -= base_score
                                score -= (
                                    20
                                    if (rsi_diff >= 5.0 and price_diff_pct >= 0.03)
                                    else 10
                                )
                                if val_rsi_right >= 70:
                                    score -= 20
                                elif val_rsi_right >= 65:
                                    score -= 10

                                status_bear = (
                                    "Valid (DC Confirmed)"
                                    if is_dc
                                    else "Potensial (Menunggu DC)"
                                )

                                res_bear = {
                                    "Ticker": clean_symbol,
                                    "Harga": int(c0),
                                    "Change (%)": chg_pct,
                                    "Value (M)": round(latest_value / 1_000_000_000, 2),
                                    "Pattern": f"{pattern_type} {status_bear}",
                                    "Score": score,
                                    "Status Base": base_desc,
                                    "Tgl Kiri": left_p["Tanggal"].strftime("%Y-%m-%d"),
                                    "Harga Kiri": int(left_p["Nilai"]),
                                    "RSI Kiri": round(val_rsi_left, 2),
                                    "Tgl Kanan": right_p["Tanggal"].strftime("%Y-%m-%d"),
                                    "Harga Kanan": int(right_p["Nilai"]),
                                    "RSI Kanan": round(val_rsi_right, 2),
                                    "Signal_Type": "BEARISH",  # <--- FLAG TOGGLE
                                }
                                break

        return res_bull, res_bear

    except Exception:
        return None, None


def run_rsi_pattern_screener(tickers=None, progress_callback=None):
    if tickers is None:
        try:
            tickers = get_all_ihsg_tickers()
        except Exception:
            tickers = DEFAULT_SAHAM_LIST

        if not tickers:
            tickers = DEFAULT_SAHAM_LIST

    results_bull = []
    results_bear = []
    total_tickers = len(tickers)
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_process_single_rsi_ticker, t): t for t in tickers}
        for future in concurrent.futures.as_completed(futures):
            res_bull, res_bear = future.result()
            if res_bull:
                results_bull.append(res_bull)
            if res_bear:
                results_bear.append(res_bear)

            completed += 1
            if progress_callback:
                progress_callback(completed, total_tickers)

    df_bull = pd.DataFrame(results_bull) if results_bull else pd.DataFrame()
    df_bear = pd.DataFrame(results_bear) if results_bear else pd.DataFrame()

    if not df_bull.empty and "Score" in df_bull.columns:
        df_bull = df_bull.sort_values(by="Score", ascending=False).reset_index(drop=True)
    if not df_bear.empty and "Score" in df_bear.columns:
        df_bear = df_bear.sort_values(by="Score", ascending=True).reset_index(drop=True)

    return df_bull, df_bear
