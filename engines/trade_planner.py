import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone

from engines.market_data import candle_is_final, expected_last_candle_date, now_wib

# Swing: butuh 3 candle di kiri dan 2 candle di kanan agar berstatus "Confirmed".
# Swing yang masih kurang candle di kanannya tetap dibaca sebagai "Developing".
SWING_LEFT = 3
SWING_RIGHT = 2

# TP2 dibatasi maksimal TP1 + (angka ini x ATR). Tebakan awal, perlu divalidasi.
TP2_MAX_ATR_MULT = 2.0
# Catatan volatilitas tinggi jika ATR lebih dari persen ini dari harga.
HIGH_VOL_ATR_PCT = 8.0
# Catatan likuiditas rendah jika rata-rata nilai transaksi harian 20 hari di bawah ini (Rupiah).
LOW_LIQUIDITY_VALUE = 1_000_000_000
# Hammer dibaca Hanging Man hanya jika harga lebih dari angka ini x ATR di atas MA20.
HAMMER_FAR_ABOVE_MA20_ATR = 1.0


class TradePlanner:

    def __init__(self, ticker="INCO.JK", period="6mo"):
        self.ticker = ticker.upper()
        self.period = period
        self.df = None
        self.atr_14 = 0.0
        self.ma20 = None
        self.ma50 = None
        self.vol_ratio = 0.0
        self.last_candle_date = None
        self.candle_final = True
        self.expected_last_date = None
        self.data_stale = False
        self.avg_value_20 = 0.0
        self.highs_15 = pd.DataFrame()
        self.lows_15 = pd.DataFrame()
        self.highs_5 = pd.DataFrame()
        self.strong_support = pd.DataFrame()
        self.strong_resistance = pd.DataFrame()

    # ------------------------------------------------------------------
    # FRAKSI HARGA IDX
    # ------------------------------------------------------------------
    @staticmethod
    def get_tick_size(price: float) -> int:
        p = float(price)
        if p < 200:
            return 1
        elif p < 500:
            return 2
        elif p < 2000:
            return 5
        elif p < 5000:
            return 10
        else:
            return 25

    @classmethod
    def add_ticks(cls, price: float, n_ticks: int) -> float:
        p = float(price)
        if p > 0:
            p = cls.round_to_nearest_tick(p)
        for _ in range(n_ticks):
            p += cls.get_tick_size(p)
        return round(p, 2)

    @classmethod
    def sub_ticks(cls, price: float, n_ticks: int) -> float:
        p = float(price)
        for _ in range(n_ticks):
            # pakai fraksi band tepat di bawah harga (mis. 500 -> 498, bukan 495)
            tick = cls.get_tick_size(p - 1e-6)
            p -= tick
            if p < 1:
                p = 1.0
                break
        return round(p, 2)

    @classmethod
    def round_to_nearest_tick(cls, price: float) -> float:
        price = float(price)
        if price <= 0:
            return 0.0
        tick = cls.get_tick_size(price)
        return round(round(price / tick) * tick, 2)

    @classmethod
    def floor_to_tick(cls, price: float) -> float:
        price = float(price)
        if price <= 0:
            return 0.0
        tick = cls.get_tick_size(price)
        return round(float(np.floor(price / tick + 1e-9)) * tick, 2)

    # ------------------------------------------------------------------
    # DATA & SWING
    # ------------------------------------------------------------------
    @staticmethod
    def _wilder_atr(tr_values, length=14):
        """ATR gaya TradingView (RMA/Wilder): awal = rata-rata TR 14 candle pertama."""
        tr = np.asarray(tr_values, dtype=float)
        if len(tr) < length or np.isnan(tr[:length]).any():
            return 0.0
        atr = float(tr[:length].mean())
        for i in range(length, len(tr)):
            atr = (atr * (length - 1) + tr[i]) / length
        return float(atr)

    def fetch_and_prepare_data(self, data=None):
        if data is not None:
            # Data siap pakai (mis. dari file harian bersama), tidak download lagi
            df = data.copy()
            if "Date" not in df.columns:
                df = df.reset_index()
        else:
            stock = yf.Ticker(self.ticker)
            # auto_adjust=False: harga sama dengan chart asli (bukan harga yang disesuaikan)
            df = stock.history(
                period=self.period, interval="1d", auto_adjust=False
            ).reset_index()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        if df.empty or len(df) < 20:
            raise ValueError(
                f"Data tidak mencukupi untuk ticker '{self.ticker}'."
            )

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)

        df = df.dropna(subset=["Open", "High", "Low", "Close"]).reset_index(drop=True)
        if len(df) < 20:
            raise ValueError(
                f"Data tidak mencukupi untuk ticker '{self.ticker}'."
            )
        df["Volume"] = df["Volume"].fillna(0)

        df["Body_Top"] = df[["Open", "Close"]].max(axis=1)
        df["Body_Bottom"] = df[["Open", "Close"]].min(axis=1)

        df["Prev_Close"] = df["Close"].shift(1)
        df["TR"] = np.maximum(
            df["High"] - df["Low"],
            np.maximum(
                abs(df["High"] - df["Prev_Close"]),
                abs(df["Low"] - df["Prev_Close"]),
            ),
        )
        # candle pertama tidak punya close sebelumnya: TR = High - Low (sama dengan TradingView)
        df["TR"] = df["TR"].fillna(df["High"] - df["Low"])
        self.atr_14 = self._wilder_atr(df["TR"].values, 14)

        # Tren (MA20 / MA50) dan volume relatif (dibanding 20 hari sebelumnya)
        ma20 = df["Close"].rolling(20).mean().iloc[-1]
        ma50 = df["Close"].rolling(50).mean().iloc[-1]
        self.ma20 = float(ma20) if pd.notna(ma20) else None
        self.ma50 = float(ma50) if pd.notna(ma50) else None

        vol_ma = df["Volume"].rolling(20).mean().shift(1).iloc[-1]
        last_vol = float(df["Volume"].iloc[-1])
        avg_val = (df["Close"] * df["Volume"]).rolling(20).mean().iloc[-1]
        self.avg_value_20 = float(avg_val) if pd.notna(avg_val) else 0.0
        self.vol_ratio = float(last_vol / vol_ma) if pd.notna(vol_ma) and vol_ma > 0 else 0.0

        # Tanggal data dan status candle terakhir (final / belum)
        self.last_candle_date = pd.Timestamp(df["Date"].iloc[-1])
        now = now_wib()
        self.candle_final = candle_is_final(self.last_candle_date.date(), now)
        self.expected_last_date = expected_last_candle_date(now)
        self.data_stale = self.last_candle_date.date() < self.expected_last_date

        self.df = df
        self._detect_swings()
        self._calculate_strong_levels()

    def _detect_swings(self):
        df = self.df
        n = len(df)
        highs = df["High"].values
        lows = df["Low"].values
        sh = [""] * n
        sl = [""] * n

        # Confirmed: 3 candle di kiri, 2 candle di kanan
        for i in range(SWING_LEFT, n - SWING_RIGHT):
            if (
                highs[i] >= highs[i - SWING_LEFT:i].max()
                and highs[i] > highs[i + 1:i + 1 + SWING_RIGHT].max()
            ):
                sh[i] = "Confirmed"
            if (
                lows[i] <= lows[i - SWING_LEFT:i].min()
                and lows[i] < lows[i + 1:i + 1 + SWING_RIGHT].min()
            ):
                sl[i] = "Confirmed"

        # Developing: swing terbaru yang belum punya cukup candle di kanan
        for i in range(max(SWING_LEFT, n - SWING_RIGHT), n):
            right_h = highs[i + 1:]
            right_l = lows[i + 1:]
            if highs[i] >= highs[i - SWING_LEFT:i].max() and (
                len(right_h) == 0 or highs[i] > right_h.max()
            ):
                sh[i] = "Developing"
            if lows[i] <= lows[i - SWING_LEFT:i].min() and (
                len(right_l) == 0 or lows[i] < right_l.min()
            ):
                sl[i] = "Developing"

        df["SH_Status"] = sh
        df["SL_Status"] = sl
        df["Swing_Type"] = ""
        df.loc[df["SH_Status"] != "", "Swing_Type"] = "Swing High"
        df.loc[df["SL_Status"] != "", "Swing_Type"] = "Swing Low"
        df["Swing_Status"] = np.where(
            df["Swing_Type"] == "Swing Low",
            df["SL_Status"],
            np.where(df["Swing_Type"] == "Swing High", df["SH_Status"], ""),
        )

        highs_df = df[df["SH_Status"] != ""].copy()
        highs_df["Swing_Status"] = highs_df["SH_Status"]
        lows_df = df[df["SL_Status"] != ""].copy()
        lows_df["Swing_Status"] = lows_df["SL_Status"]

        self.highs_15 = highs_df.sort_values(by="Date", ascending=False).head(15)
        self.lows_15 = lows_df.sort_values(by="Date", ascending=False).head(15)
        self.highs_5 = self.highs_15.head(5)

    @staticmethod
    def _filter_overlapping_levels(
        df_levels, col1, col2, prefix="Resistance", max_levels=3
    ):
        if df_levels.empty:
            return pd.DataFrame()

        if "Date" in df_levels.columns:
            df_levels = df_levels.sort_values(by="Date", ascending=False)

        accepted_rows, accepted_ranges = [], []
        for _, row in df_levels.iterrows():
            r_min = min(row[col1], row[col2])
            r_max = max(row[col1], row[col2])
            overlap = False
            for a_min, a_max in accepted_ranges:
                if max(r_min, a_min) <= min(r_max, a_max):
                    overlap = True
                    break
            if not overlap:
                accepted_rows.append(row.to_dict())
                accepted_ranges.append((r_min, r_max))

        res_df = pd.DataFrame(accepted_rows)
        if not res_df.empty:
            res_df = res_df.head(max_levels).reset_index(drop=True)
            res_df["Rank"] = [
                f"1st {prefix} (Terdekat)" if i == 0 else (f"2nd {prefix}" if i == 1 else f"3rd {prefix} (Terjauh)")
                for i in range(len(res_df))
            ]
        return res_df

    @staticmethod
    def _rank_by_proximity(levels, prefix, last_close):
        """Urutkan level dari yang paling dekat harga sekarang (bukan yang paling baru)."""
        if levels is None or levels.empty:
            return pd.DataFrame()
        lv = levels.copy()
        if prefix == "Resistance":
            ahead = lv[lv["High"] >= last_close].sort_values(by="Body_Top", ascending=True)
            behind = lv[lv["High"] < last_close].sort_values(by="High", ascending=False)
            ordered = pd.concat([ahead, behind])
        else:
            below = lv[lv["Low"] <= last_close].sort_values(by="Body_Bottom", ascending=False)
            above = lv[lv["Low"] > last_close].sort_values(by="Low", ascending=True)
            ordered = pd.concat([below, above])
        ordered = ordered.head(3).reset_index(drop=True)
        ordered["Rank"] = [
            f"1st {prefix} (Terdekat)" if i == 0 else (f"2nd {prefix}" if i == 1 else f"3rd {prefix} (Terjauh)")
            for i in range(len(ordered))
        ]
        return ordered

    def _calculate_strong_levels(self):
        last_close = float(self.df.iloc[-1]["Close"])

        res_results = []
        for _, row in self.highs_15.sort_values(by="Date", ascending=False).head(8).iterrows():
            idx = row.name
            body_tops = [row["Body_Top"]]
            if idx > 0 and (idx - 1) in self.df.index:
                body_tops.append(self.df.loc[idx - 1, "Body_Top"])
            if (idx + 1) in self.df.index:
                body_tops.append(self.df.loc[idx + 1, "Body_Top"])

            res_results.append({
                "Date": row["Date"].strftime("%Y-%m-%d"),
                "Body_Top": round(max(body_tops), 2),
                "High": round(row["High"], 2),
                "Status": row["Swing_Status"],
            })

        res_df = self._filter_overlapping_levels(
            pd.DataFrame(res_results), "Body_Top", "High",
            prefix="Resistance", max_levels=8,
        )
        self.strong_resistance = self._rank_by_proximity(res_df, "Resistance", last_close)

        sup_results = []
        for _, row in self.lows_15.sort_values(by="Date", ascending=False).head(8).iterrows():
            idx = row.name
            body_bottoms = [row["Body_Bottom"]]
            if idx > 0 and (idx - 1) in self.df.index:
                body_bottoms.append(self.df.loc[idx - 1, "Body_Bottom"])
            if (idx + 1) in self.df.index:
                body_bottoms.append(self.df.loc[idx + 1, "Body_Bottom"])

            sup_results.append({
                "Date": row["Date"].strftime("%Y-%m-%d"),
                "Low": round(row["Low"], 2),
                "Body_Bottom": round(min(body_bottoms), 2),
                "Status": row["Swing_Status"],
            })

        sup_df = self._filter_overlapping_levels(
            pd.DataFrame(sup_results), "Body_Bottom", "Low",
            prefix="Support", max_levels=8,
        )
        self.strong_support = self._rank_by_proximity(sup_df, "Support", last_close)

    # ------------------------------------------------------------------
    # ARAH (BOB / BOW)
    # ------------------------------------------------------------------
    def get_direction(self):
        if self.highs_15.empty or self.lows_15.empty:
            return pd.DataFrame()

        hi = self.highs_15.sort_values(by="Date", ascending=False)
        lo = self.lows_15.sort_values(by="Date", ascending=False)
        latest_high_val = float(hi.iloc[0]["High"])
        latest_low_val = float(lo.iloc[0]["Low"])
        last_market_close = float(self.df.iloc[-1]["Close"])
        midpoint_50 = (latest_high_val + latest_low_val) / 2.0
        rng = latest_high_val - latest_low_val
        pos_pct = ((last_market_close - latest_low_val) / rng * 100.0) if rng > 0 else 50.0

        conf_hi = hi[hi["Swing_Status"] == "Confirmed"]
        conf_lo = lo[lo["Swing_Status"] == "Confirmed"]
        conf_high_val = float(conf_hi.iloc[0]["High"]) if not conf_hi.empty else latest_high_val
        conf_low_val = float(conf_lo.iloc[0]["Low"]) if not conf_lo.empty else latest_low_val

        if rng < 2.0 * self.atr_14:
            structure = "Range sempit (kurang dari 2x ATR), level 50% kurang bermakna"
        elif last_market_close > conf_high_val:
            structure = "Breakout: harga di atas swing high terakhir"
        elif last_market_close < conf_low_val:
            structure = "Struktur turun: harga di bawah swing low terakhir"
        elif 40.0 <= pos_pct <= 60.0:
            structure = "Zona netral (40-60% dari range)"
        elif pos_pct > 60.0:
            structure = "Harga di paruh atas range"
        else:
            structure = "Harga di paruh bawah range"

        return pd.DataFrame([{
            "Swing High Terupdate": self.round_to_nearest_tick(latest_high_val),
            "Swing Low Terupdate": self.round_to_nearest_tick(latest_low_val),
            "Level 50%": self.round_to_nearest_tick(midpoint_50),
            "Last Close Market": self.round_to_nearest_tick(last_market_close),
            "Direction": "BOB" if last_market_close >= midpoint_50 else "BOW",
            "Posisi Range (%)": round(pos_pct, 1),
            "Status Struktur": structure,
            "Swing High Status": str(hi.iloc[0]["Swing_Status"]),
            "Swing Low Status": str(lo.iloc[0]["Swing_Status"]),
        }])

    # ------------------------------------------------------------------
    # CANDLE
    # ------------------------------------------------------------------
    def classify_candle(self):
        if len(self.df) < 20 or self.atr_14 <= 0:
            return "Standard (tanpa pola)", "NEUTRAL"

        ma20 = self.df["Close"].rolling(20).mean().iloc[-1]
        last_close = self.df.iloc[-1]["Close"]
        is_downtrend = last_close < ma20
        is_uptrend = last_close >= ma20

        def get_props(row):
            high, low, open_p, close = row["High"], row["Low"], row["Open"], row["Close"]
            body_top, body_bottom = max(open_p, close), min(open_p, close)
            body_size = body_top - body_bottom
            total_range = max(high - low, 0.0001)
            return {
                "high": high,
                "low": low,
                "open": open_p,
                "close": close,
                "body_top": body_top,
                "body_bottom": body_bottom,
                "body_size": body_size,
                "total_range": total_range,
                "upper_shadow": high - body_top,
                "lower_shadow": body_bottom - low,
                "is_green": close > open_p,
                "is_red": close < open_p,
                "is_doji": body_size <= (total_range * 0.1),
            }

        p3 = get_props(self.df.iloc[-3])
        p2 = get_props(self.df.iloc[-2])
        p1 = get_props(self.df.iloc[-1])

        is_large_body = p1["body_size"] >= (1.0 * self.atr_14)
        is_small_body = p1["body_size"] < (0.4 * self.atr_14)

        if p3["is_green"] and p2["is_green"] and p1["is_green"] and (p1["close"] > p2["close"] > p3["close"]) and is_large_body:
            return "Three White Soldiers, tekanan beli berlanjut", "BULLISH"
        if p3["is_red"] and (p3["body_size"] >= 0.8 * self.atr_14) and (p2["body_size"] < 0.4 * self.atr_14) and p1["is_green"] and (p1["close"] >= (p3["open"] + p3["close"]) / 2) and is_downtrend:
            return "Morning Star, potensi pembalikan naik", "BULLISH"
        if p3["is_green"] and (p3["body_size"] >= 0.8 * self.atr_14) and (p2["body_size"] < 0.4 * self.atr_14) and p1["is_red"] and (p1["close"] <= (p3["open"] + p3["close"]) / 2) and is_uptrend:
            return "Evening Star, potensi pembalikan turun", "BEARISH"

        if p1["is_green"] and p2["is_red"] and (p1["body_top"] >= p2["body_top"]) and (p1["body_bottom"] <= p2["body_bottom"]) and is_large_body:
            return (
                "Bullish Engulfing, potensi pembalikan naik" if is_downtrend
                else "Bullish Engulfing, tekanan beli kuat"
            ), "BULLISH"
        if p1["is_red"] and p2["is_green"] and (p1["body_bottom"] <= p2["body_bottom"]) and (p1["body_top"] >= p2["body_top"]) and is_large_body:
            return "Bearish Engulfing, tekanan jual kuat", "BEARISH"

        if p1["is_doji"]:
            if (p1["lower_shadow"] >= 2.5 * p1["body_size"]) and (p1["upper_shadow"] <= 0.5 * p1["body_size"]):
                return "Dragonfly Doji, potensi rebound", "BULLISH"
            elif (p1["upper_shadow"] >= 2.5 * p1["body_size"]) and (p1["lower_shadow"] <= 0.5 * p1["body_size"]):
                return "Gravestone Doji, waspada pelemahan", "BEARISH"
            return "Doji, pasar ragu-ragu", "NEUTRAL"

        is_marubozu_body = p1["body_size"] >= (1.1 * self.atr_14)
        has_minimal_shadows = (p1["upper_shadow"] <= 0.1 * p1["total_range"]) and (p1["lower_shadow"] <= 0.1 * p1["total_range"])

        if is_marubozu_body and has_minimal_shadows:
            if p1["is_green"]:
                return "Bullish Marubozu, tekanan beli kuat", "BULLISH"
            return "Bearish Marubozu, tekanan jual kuat", "BEARISH"

        is_hammer_shape = (p1["lower_shadow"] >= 2.0 * p1["body_size"]) and (p1["upper_shadow"] <= 0.3 * p1["body_size"])
        is_shooting_shape = (p1["upper_shadow"] >= 2.0 * p1["body_size"]) and (p1["lower_shadow"] <= 0.3 * p1["body_size"])

        if is_hammer_shape:
            # Hanging Man hanya jika harga sudah jauh di atas MA20; selain itu dibaca Hammer
            far_above_ma20 = last_close > ma20 + HAMMER_FAR_ABOVE_MA20_ATR * self.atr_14
            if not far_above_ma20:
                return "Hammer, potensi rebound", "BULLISH"
            return "Hanging Man, waspada pelemahan", "BEARISH"

        if is_shooting_shape:
            if is_uptrend:
                return "Shooting Star, potensi pelemahan", "BEARISH"
            return "Inverted Hammer, belum ada konfirmasi", "NEUTRAL"

        color_str = "Hijau" if p1["is_green"] else "Merah"
        if is_small_body:
            return "Spinning Top, pasar ragu-ragu", "NEUTRAL"

        # Candle biasa tanpa pola dianggap netral (bukan bullish/bearish)
        return f"Standard {color_str} (tanpa pola)", "NEUTRAL"

    # ------------------------------------------------------------------
    # PENILAIAN PLAN (skor, grade, warning)
    # ------------------------------------------------------------------
    @staticmethod
    def _grade_label(total_score):
        if total_score >= 85:
            return "🟢 Strong Setup"
        elif total_score >= 70:
            return "🟢 Good Setup"
        elif total_score >= 50:
            return "🟡 Fair Setup"
        return "🔴 Weak Setup"

    @staticmethod
    def _entry_price(plan_type, last_close, buy_min, buy_max):
        """Harga entry yang realistis untuk menghitung risk-reward."""
        if plan_type == "BOW":
            return min(max(last_close, buy_min), buy_max)
        return max(last_close, buy_min)  # BOB: buy stop di buy_min, atau harga sekarang

    @staticmethod
    def _position_status(plan_type, last_close, buy_min, buy_max):
        if buy_min <= last_close <= buy_max:
            return "In Buy Zone"
        if plan_type == "BOW":
            if last_close > buy_max:
                dist = (last_close - buy_max) / buy_max * 100 if buy_max > 0 else 0
                return "Near Zone" if dist <= 2.0 else "Running / Away"
            return "Below Buy Zone"
        # BOB: harga di bawah zona = menunggu breakout, di atas zona = sudah lewat
        if last_close < buy_min:
            dist = (buy_min - last_close) / buy_min * 100 if buy_min > 0 else 0
            return "Near Zone" if dist <= 2.0 else "Below Buy Zone"
        return "Running / Away"

    def _trend_state(self):
        close = float(self.df.iloc[-1]["Close"])
        if self.ma20 is None:
            return "UNKNOWN"
        if self.ma50 is None:
            return "UP" if close > self.ma20 else "DOWN"
        if close > self.ma50 and self.ma20 > self.ma50:
            return "UP"
        if close > self.ma50:
            return "ABOVE50"
        if close < self.ma50 and self.ma20 < self.ma50:
            return "DOWN"
        return "BELOW50"

    def _evaluate_plan(
        self, plan_type, buy_min, buy_max, stop_loss, target_1, target_2,
        level_confirmed, candle_type, candle_bias, structure_note=None,
    ):
        last = self.df.iloc[-1]
        c = float(last["Close"])
        o = float(last["Open"])
        h = float(last["High"])
        lo = float(last["Low"])
        upper_shadow = h - max(o, c)

        # Candle belum final: pola candle dinilai netral
        if not self.candle_final:
            candle_bias = "NEUTRAL"

        warnings = []  # (level, teks)
        penalty = 0

        # --- risk-reward dari entry realistis ---
        entry = self._entry_price(plan_type, c, buy_min, buy_max)
        risk = entry - stop_loss
        reward_1 = (target_1 - entry) if target_1 else 0.0
        rr1 = round(reward_1 / risk, 1) if (risk > 0 and reward_1 > 0) else 0.0
        reward_2 = (target_2 - entry) if target_2 else 0.0
        rr2 = round(reward_2 / risk, 1) if (risk > 0 and reward_2 > 0) else 0.0
        risk_pct = (risk / entry * 100.0) if entry > 0 else 0.0

        pos_status = self._position_status(plan_type, c, buy_min, buy_max)

        # 1) RR (25)
        if rr1 >= 3.0:
            score_rr = 25
        elif rr1 >= 2.0:
            score_rr = 20
        elif rr1 >= 1.5:
            score_rr = 14
        elif rr1 >= 1.0:
            score_rr = 7
        else:
            score_rr = 0

        target_passed = bool(target_1) and entry >= target_1
        if target_passed:
            warnings.append(("critical", "🚫 Harga entry sudah melewati Target 1, ruang naik ke target sudah habis"))
            penalty += 6
        elif rr1 <= 0:
            warnings.append(("critical", "🚫 Risk-reward tidak bisa dihitung, target tidak berada di atas entry"))
            penalty += 6
        elif rr1 < 1.0:
            warnings.append(("critical", "🚫 Risk-reward di bawah 1:1, potensi rugi lebih besar dari potensi untung"))
            penalty += 6
        elif rr1 < 1.5:
            warnings.append(("caution", "⚠️ Risk-reward rendah (di bawah 1:1,5)"))
            penalty += 3
        elif rr1 > 6.0:
            warnings.append(("caution", f"⚠️ Stop loss sangat dekat ({risk_pct:.1f}% dari entry), rawan kena volatilitas biasa"))
            penalty += 2

        # 2) Posisi harga terhadap zona (20). Level yang belum terkonfirmasi tidak diberi poin zona.
        if not level_confirmed:
            score_zone = 0
        elif pos_status == "In Buy Zone":
            score_zone = 20
        elif pos_status == "Near Zone":
            score_zone = 14
        elif pos_status == "Below Buy Zone":
            score_zone = 5
        else:
            score_zone = 0

        if plan_type == "BOW" and buy_max > 0 and c > buy_max:
            dist_above = (c - buy_max) / buy_max * 100.0
            if dist_above > 4.0:
                warnings.append(("caution", f"⚠️ Harga sudah {dist_above:.1f}% di atas area beli, pertimbangkan menunggu pullback"))
                penalty += 4
        if plan_type == "BOB" and pos_status == "Running / Away" and buy_max > 0:
            dist_above = (c - buy_max) / buy_max * 100.0
            warnings.append(("caution", f"⚠️ Harga sudah {dist_above:.1f}% di atas titik breakout, area beli sudah terlewat"))
            penalty += 4

        # 3) Tren MA20/MA50 (20)
        trend = self._trend_state()
        score_trend = {"UP": 20, "ABOVE50": 12, "BELOW50": 5, "DOWN": 0, "UNKNOWN": 8}[trend]
        if trend == "DOWN":
            if plan_type == "BOW":
                warnings.append(("caution", "⚠️ Tren turun (harga di bawah MA20 dan MA50), risiko menangkap pisau jatuh"))
            else:
                warnings.append(("caution", "⚠️ Breakout di tengah tren turun (di bawah MA20 dan MA50), rawan gagal"))

        # 4) Candle di area zona (15)
        at_zone = (lo <= buy_max * 1.01) and (h >= buy_min * 0.99)
        if candle_bias == "BULLISH":
            score_candle = 15 if at_zone else 6
        elif candle_bias == "NEUTRAL":
            score_candle = 6
        else:
            score_candle = 0
            warnings.append(("caution", "⚠️ Candle terakhir bearish, belum ada konfirmasi pantulan"))
            penalty += 3

        if self.candle_final and upper_shadow >= (0.4 * (h - lo)) and upper_shadow > 0:
            warnings.append(("caution", "⚠️ Ekor atas panjang, ada tekanan jual di akhir sesi"))
            penalty += 2

        # 5) Volume (10)
        vr = self.vol_ratio
        is_green = c > o
        is_red = c < o
        if not self.candle_final:
            score_vol = 5  # volume hari ini belum lengkap: dinilai netral
        elif plan_type == "BOW":
            if is_red and vr >= 1.5:
                score_vol = 0
                warnings.append(("caution", f"⚠️ Volume jual besar di candle terakhir ({vr:.1f}x rata-rata 20 hari)"))
                penalty += 2
            elif is_green and vr >= 1.2:
                score_vol = 10
            elif 0 < vr <= 0.7:
                score_vol = 7
            else:
                score_vol = 4
        else:
            if vr >= 1.5:
                score_vol = 10
            elif vr >= 1.0:
                score_vol = 6
            else:
                score_vol = 2
            if 0 < vr < 1.0 and pos_status in ("In Buy Zone", "Near Zone", "Running / Away"):
                warnings.append(("caution", f"⚠️ Volume breakout belum kuat ({vr:.1f}x rata-rata 20 hari)"))
                penalty += 2

        # Jarak target 1
        if target_1 and entry > 0 and not target_passed:
            dist_to_target = (target_1 - entry) / entry * 100.0
            if 0 < dist_to_target <= 1.5:
                warnings.append(("caution", f"⚠️ Target 1 hanya {dist_to_target:.1f}% dari harga entry, ruang naik terbatas"))
                penalty += 2

        # Volatilitas dan likuiditas (catatan saja, tidak memotong skor)
        atr_pct = (self.atr_14 / c * 100.0) if c > 0 else 0.0
        if atr_pct > HIGH_VOL_ATR_PCT:
            warnings.append(("caution", f"⚠️ Volatilitas tinggi (ATR {atr_pct:.1f}% dari harga), stop loss dan target bisa tersentuh cepat"))
        if self.avg_value_20 < LOW_LIQUIDITY_VALUE:
            warnings.append(("caution", f"⚠️ Likuiditas rendah (rata-rata transaksi harian sekitar Rp{self.avg_value_20 / 1e6:,.0f} juta), bisa sulit masuk atau keluar posisi"))

        # Struktur dan status level (info)
        if structure_note:
            warnings.append(("caution", structure_note))
        if not level_confirmed:
            if plan_type == "BOW":
                warnings.append(("info", "ℹ️ Support belum terkonfirmasi (masih berkembang), level bisa bergeser bila ada low baru"))
            else:
                warnings.append(("info", "ℹ️ Resistance belum terkonfirmasi (masih berkembang), level bisa bergeser bila ada high baru"))
            penalty += 2
        if not self.candle_final:
            warnings.append(("info", "ℹ️ Candle hari ini belum final: volume dan pola candle dinilai netral, level dan status bisa berubah setelah pasar tutup"))
        if self.data_stale and self.expected_last_date is not None:
            warnings.append(("info", f"ℹ️ Data tertinggal: candle terakhir {self.last_candle_date.strftime('%d %b %Y')}, hari bursa terakhir {self.expected_last_date.strftime('%d %b %Y')} (data belum diperbarui atau saham disuspensi)"))

        score_clean = max(0, 10 - penalty)
        total_score = int(score_rr + score_zone + score_trend + score_candle + score_vol + score_clean)
        total_score = max(0, min(100, total_score))

        levels = [w[0] for w in warnings]
        if "critical" in levels:
            warning_level = "critical"
        elif "caution" in levels:
            warning_level = "caution"
        else:
            warning_level = "ok"

        order = {"critical": 0, "caution": 1, "info": 2}
        texts = [t for _, t in sorted(warnings, key=lambda x: order[x[0]])]
        if warning_level == "ok":
            texts = ["✅ Tidak ada peringatan dari aturan screener. Tetap cek chart dan volume."] + texts
        warning_str = " | ".join(texts)

        return {
            "score": total_score,
            "grade": self._grade_label(total_score),
            "pos_status": pos_status,
            "warning": warning_str,
            "warning_level": warning_level,
            "rr1": rr1,
            "rr2": rr2,
            "entry": entry,
            "score_detail": (
                f"RR {score_rr}/25 | Posisi {score_zone}/20 | Tren {score_trend}/20 | "
                f"Candle {score_candle}/15 | Volume {score_vol}/10 | Kebersihan {score_clean}/10"
            ),
        }

    def calculate_score_and_warnings(self, plan_type, buy_min, buy_max, target_1, stop_loss, rr_ratio, candle_type, candle_bias):
        """Kompatibel dengan versi lama (return 4 nilai). rr_ratio dihitung ulang
        dari entry realistis, jadi parameter ini diabaikan."""
        ev = self._evaluate_plan(
            plan_type, buy_min, buy_max, stop_loss, target_1, None, True,
            candle_type, candle_bias,
        )
        return ev["score"], ev["grade"], ev["pos_status"], ev["warning"]

    # ------------------------------------------------------------------
    # PEMILIHAN LEVEL (yang paling dekat harga, termasuk swing yang masih berkembang)
    # ------------------------------------------------------------------
    def _neighbor_extreme(self, idx, col, use_min):
        vals = [self.df.loc[idx, col]]
        if idx > 0:
            vals.append(self.df.loc[idx - 1, col])
        if (idx + 1) in self.df.index:
            vals.append(self.df.loc[idx + 1, col])
        return min(vals) if use_min else max(vals)

    def _pick_support(self, last_close):
        if not self.strong_support.empty:
            row = self.strong_support.iloc[0]
            if float(row["Low"]) <= last_close:
                return {
                    "low": float(row["Low"]),
                    "body": float(row["Body_Bottom"]),
                    "confirmed": str(row["Status"]) == "Confirmed",
                    "date": str(row["Date"]),
                }
        # tidak ada support di bawah harga: pakai low terendah 5 candle terakhir
        seg = self.df.iloc[max(0, len(self.df) - 5):]
        idx = seg["Low"].idxmin()
        return {
            "low": float(self.df.loc[idx, "Low"]),
            "body": float(self._neighbor_extreme(idx, "Body_Bottom", True)),
            "confirmed": False,
            "date": pd.Timestamp(self.df.loc[idx, "Date"]).strftime("%Y-%m-%d"),
        }

    def _pick_resistance(self, last_close):
        if not self.strong_resistance.empty:
            row = self.strong_resistance.iloc[0]
            if float(row["High"]) >= last_close:
                return {
                    "high": float(row["High"]),
                    "confirmed": str(row["Status"]) == "Confirmed",
                    "date": str(row["Date"]),
                }
        # harga sudah di atas semua swing high: pakai high tertinggi 5 candle terakhir
        seg = self.df.iloc[max(0, len(self.df) - 5):]
        idx = seg["High"].idxmax()
        return {
            "high": float(self.df.loc[idx, "High"]),
            "confirmed": False,
            "date": pd.Timestamp(self.df.loc[idx, "Date"]).strftime("%Y-%m-%d"),
        }

    def _broken_support_note(self, last_close):
        """Cari swing low terkonfirmasi yang sudah ditembus ke bawah (support lama jebol)."""
        conf = self.lows_15[self.lows_15["Swing_Status"] == "Confirmed"].head(8)
        above = conf[conf["Low"] > last_close]
        if above.empty:
            return None
        lvl = self.round_to_nearest_tick(float(above["Low"].min()))
        return (
            f"⚠️ Harga sudah di bawah support sebelumnya ({int(lvl):,}), "
            f"area beli mengikuti low terbaru"
        )

    @staticmethod
    def _fmt_date(date_str):
        try:
            return pd.to_datetime(date_str).strftime("%d %b")
        except Exception:
            return str(date_str)

    # ------------------------------------------------------------------
    # TRADE PLAN
    # ------------------------------------------------------------------
    def generate_trade_plan(self):
        last_close = float(self.df.iloc[-1]["Close"])
        min_point_gap = max(self.get_tick_size(last_close) * 2, 5)

        def resistance_targets():
            """TP di tepi bawah zona resistance (Body_Top) dikurangi 1 tick."""
            out = []
            if not self.strong_resistance.empty:
                for bt in self.strong_resistance["Body_Top"].values:
                    out.append(self.sub_ticks(self.round_to_nearest_tick(bt), 1))
            return sorted(out)

        def swing_high_targets():
            out = []
            if not self.highs_15.empty:
                for bt in self.highs_15["Body_Top"].values:
                    out.append(self.sub_ticks(self.round_to_nearest_tick(bt), 1))
            return sorted(out)

        def find_target_1(min_val):
            """Return (harga, sumber)."""
            valid = [p for p in resistance_targets() if (p - min_val) >= min_point_gap]
            if valid:
                return float(valid[0]), "resistance"
            valid = [p for p in swing_high_targets() if (p - min_val) >= min_point_gap]
            if valid:
                return float(valid[0]), "swing high"
            return (
                self.round_to_nearest_tick(min_val + max(1.5 * self.atr_14, min_point_gap + 2)),
                "proyeksi ATR",
            )

        def find_target_2(target_1):
            """Return (harga, sumber). Dibatasi maksimal TP1 + TP2_MAX_ATR_MULT x ATR."""
            if not target_1 or pd.isna(target_1):
                return None, ""
            min_tp2 = max(
                self.add_ticks(target_1, 10),
                self.round_to_nearest_tick(target_1 + 0.75 * self.atr_14),
            )
            cap = max(min_tp2, self.floor_to_tick(target_1 + TP2_MAX_ATR_MULT * self.atr_14))
            for source, cands in (
                ("resistance", resistance_targets()),
                ("swing high", swing_high_targets()),
            ):
                valid = [p for p in cands if p >= min_tp2]
                if valid:
                    p = float(valid[0])
                    if p <= cap:
                        return p, source
                    return float(cap), "proyeksi ATR (resistance berikutnya terlalu jauh)"
            fallback = max(min_tp2, self.round_to_nearest_tick(target_1 + 1.5 * self.atr_14))
            return float(min(fallback, cap)), "proyeksi ATR"

        candle_name, candle_bias = self.classify_candle()
        if not self.candle_final:
            candle_bias = "NEUTRAL"
            candle_name = f"{candle_name} (belum final, dinilai netral)"

        # 1. BOW PLAN (zona dari support terdekat di bawah harga, termasuk low yang masih berkembang)
        sup = self._pick_support(last_close)
        rb_bow_min = self.round_to_nearest_tick(min(sup["low"], sup["body"]))
        rb_bow_max = self.round_to_nearest_tick(max(sup["low"], sup["body"]))
        stop_loss_bow = self._sl_below(rb_bow_min)
        target_1_bow, tp1_src_bow = find_target_1(rb_bow_max)
        target_2_bow, tp2_src_bow = find_target_2(target_1_bow)
        ev_bow = self._evaluate_plan(
            "BOW", rb_bow_min, rb_bow_max, stop_loss_bow, target_1_bow, target_2_bow,
            sup["confirmed"], candle_name, candle_bias,
            structure_note=self._broken_support_note(last_close),
        )

        # 2. BOB PLAN (zona di atas resistance terdekat yang belum ditembus)
        res = self._pick_resistance(last_close)
        base_bob_high = self.round_to_nearest_tick(res["high"])
        upper_bob_high = self.add_ticks(base_bob_high, 3)
        stop_loss_bob = self._sl_below(base_bob_high)
        target_1_bob, tp1_src_bob = find_target_1(upper_bob_high)
        target_2_bob, tp2_src_bob = find_target_2(target_1_bob)
        ev_bob = self._evaluate_plan(
            "BOB", base_bob_high, upper_bob_high, stop_loss_bob, target_1_bob, target_2_bob,
            res["confirmed"], candle_name, candle_bias,
        )

        def fmt_range(p_min, p_max):
            def f(x):
                x = float(x)
                return f"{int(x):,}" if x.is_integer() else f"{x:,}"
            if float(p_min) == float(p_max):
                return f(p_min)
            return f"{f(p_min)} - {f(p_max)}"

        as_of = self.last_candle_date.strftime("%Y-%m-%d")

        bow_status = (
            f"Confirmed swing low · {self._fmt_date(sup['date'])}" if sup["confirmed"]
            else f"Developing low (unconfirmed) · {self._fmt_date(sup['date'])}"
        )
        bob_status = (
            f"Confirmed swing high · {self._fmt_date(res['date'])}" if res["confirmed"]
            else f"Developing high (unconfirmed) · {self._fmt_date(res['date'])}"
        )

        def plan_status(plan_type, ev, has_broken):
            if plan_type == "BOW":
                return "Support sebelumnya jebol, mengikuti low terbaru" if has_broken else "Normal"
            return "Sudah breakout" if ev["pos_status"] == "Running / Away" else "Normal"

        plan_data = [
            {
                "No": 1,
                "Type": "BOW",
                "Score": ev_bow["score"],
                "Grade": ev_bow["grade"],
                "Posisi Harga": ev_bow["pos_status"],
                "Range Buy Min": float(rb_bow_min),
                "Range Buy Max": float(rb_bow_max),
                "Area Buy": fmt_range(rb_bow_min, rb_bow_max),
                "Stop Loss": float(stop_loss_bow),
                "TP 1": float(target_1_bow),
                "TP 2": float(target_2_bow) if target_2_bow is not None else None,
                "Rasio (R:R)": f"1 : {ev_bow['rr1']}" if ev_bow["rr1"] > 0 else "-",
                "RR_Val": ev_bow["rr1"],
                "Pola Candle": candle_name,
                "Warning": ev_bow["warning"],
                # kolom tambahan
                "Status Level": bow_status,
                "Level Confirmed": bool(sup["confirmed"]),
                "Plan Status": plan_status("BOW", ev_bow, self._broken_support_note(last_close) is not None),
                "Warning Level": ev_bow["warning_level"],
                "Candle Bias": candle_bias,
                "Entry Basis": float(ev_bow["entry"]),
                "RR TP2": ev_bow["rr2"],
                "Score Detail": ev_bow["score_detail"],
                "Data As Of": as_of,
                "Candle Final": bool(self.candle_final),
                "TP1 Source": tp1_src_bow,
                "TP2 Source": tp2_src_bow,
            },
            {
                "No": 2,
                "Type": "BOB",
                "Score": ev_bob["score"],
                "Grade": ev_bob["grade"],
                "Posisi Harga": ev_bob["pos_status"],
                "Range Buy Min": float(base_bob_high),
                "Range Buy Max": float(upper_bob_high),
                "Area Buy": fmt_range(base_bob_high, upper_bob_high),
                "Stop Loss": float(stop_loss_bob),
                "TP 1": float(target_1_bob),
                "TP 2": float(target_2_bob) if target_2_bob is not None else None,
                "Rasio (R:R)": f"1 : {ev_bob['rr1']}" if ev_bob["rr1"] > 0 else "-",
                "RR_Val": ev_bob["rr1"],
                "Pola Candle": candle_name,
                "Warning": ev_bob["warning"],
                "Status Level": bob_status,
                "Level Confirmed": bool(res["confirmed"]),
                "Plan Status": plan_status("BOB", ev_bob, False),
                "Warning Level": ev_bob["warning_level"],
                "Candle Bias": candle_bias,
                "Entry Basis": float(ev_bob["entry"]),
                "RR TP2": ev_bob["rr2"],
                "Score Detail": ev_bob["score_detail"],
                "Data As Of": as_of,
                "Candle Final": bool(self.candle_final),
                "TP1 Source": tp1_src_bob,
                "TP2 Source": tp2_src_bob,
            },
        ]
        return pd.DataFrame(plan_data)

    def _sl_below(self, level):
        """Stop loss di bawah level dengan buffer = max(3 tick, 0.5 x ATR), sesuai fraksi harga."""
        level = float(level)
        tick = self.get_tick_size(level)
        buffer = max(3 * tick, 0.5 * self.atr_14)
        sl = self.floor_to_tick(level - buffer)
        if sl >= level:
            sl = self.sub_ticks(level, 3)
        return max(sl, 1.0)
