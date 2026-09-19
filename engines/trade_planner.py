import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
import yfinance as yf


class TradePlanner:

    def __init__(self, ticker="INCO.JK", period="6mo"):
        self.ticker = ticker.upper()
        self.period = period
        self.df = None
        self.atr_14 = 0.0
        self.highs_15 = pd.DataFrame()
        self.lows_15 = pd.DataFrame()
        self.highs_5 = pd.DataFrame()
        self.strong_support = pd.DataFrame()
        self.strong_resistance = pd.DataFrame()

    @staticmethod
    def get_tick_size(price: float) -> int:
        """Fraksi Harga Sesuai Regulasi Bursa Efek Indonesia (BEI)"""
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
        for _ in range(n_ticks):
            p += cls.get_tick_size(p)
        return round(p, 2)

    @classmethod
    def sub_ticks(cls, price: float, n_ticks: int) -> float:
        p = float(price)
        for _ in range(n_ticks):
            tick = cls.get_tick_size(p)
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

    def fetch_and_prepare_data(self):
        stock = yf.Ticker(self.ticker)
        df = stock.history(period=self.period, interval="1d").reset_index()

        # Handling yfinance multi-index columns jika ada
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        if df.empty or len(df) < 20:
            raise ValueError(
                f"Data tidak mencukupi (minimal 20 bar) atau tidak ditemukan untuk ticker '{self.ticker}'."
            )

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)

        df["Body_Top"] = df[["Open", "Close"]].max(axis=1)
        df["Body_Bottom"] = df[["Open", "Close"]].min(axis=1)

        # ATR(14) Calculation
        df["Prev_Close"] = df["Close"].shift(1)
        df["TR"] = np.maximum(
            df["High"] - df["Low"],
            np.maximum(
                abs(df["High"] - df["Prev_Close"]),
                abs(df["Low"] - df["Prev_Close"]),
            ),
        )
        atr_series = df["TR"].rolling(window=14).mean()
        self.atr_14 = float(
            atr_series.iloc[-1] if not pd.isna(atr_series.iloc[-1]) else 0.0
        )

        # Swing Points Detection
        order = 3
        high_idx = argrelextrema(
            df["High"].values, np.greater_equal, order=order
        )[0]
        low_idx = argrelextrema(
            df["Low"].values, np.less_equal, order=order
        )[0]

        df["Swing_Type"] = ""
        df.loc[df.index.isin(high_idx), "Swing_Type"] = "Swing High"
        df.loc[df.index.isin(low_idx), "Swing_Type"] = "Swing Low"

        self.df = df

        self.highs_15 = (
            df[df["Swing_Type"] == "Swing High"]
            .sort_values(by="Date", ascending=False)
            .head(15)
        )
        self.lows_15 = (
            df[df["Swing_Type"] == "Swing Low"]
            .sort_values(by="Date", ascending=False)
            .head(15)
        )
        self.highs_5 = self.highs_15.head(5)

        self._calculate_strong_levels()

    @staticmethod
    def _filter_overlapping_levels(df_levels, col1, col2, prefix="Resistance"):
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
            sort_ascending = True if prefix == "Resistance" else False
            sort_by_col = col1 if col1 in res_df.columns else col2
            res_df = (
                res_df.sort_values(by=sort_by_col, ascending=sort_ascending)
                .head(3)
                .reset_index(drop=True)
            )

            ranks = [
                f"1st {prefix} (Terdekat)"
                if i == 0
                else (f"2nd {prefix}" if i == 1 else f"3rd {prefix} (Terjauh)")
                for i in range(len(res_df))
            ]
            res_df["Rank"] = ranks

        return res_df

    def _calculate_strong_levels(self):
        sorted_highs = self.highs_5.sort_values(by="Date", ascending=False)
        res_results = []
        for _, row in sorted_highs.iterrows():
            idx = row.name
            body_tops = [row["Body_Top"]]
            if idx > 0 and (idx - 1) in self.df.index:
                body_tops.append(self.df.loc[idx - 1, "Body_Top"])
            if (idx + 1) in self.df.index:
                body_tops.append(self.df.loc[idx + 1, "Body_Top"])

            res_results.append(
                {
                    "Date": row["Date"].strftime("%Y-%m-%d"),
                    "Body_Top": self.round_to_nearest_tick(max(body_tops)),
                    "High": self.round_to_nearest_tick(row["High"]),
                }
            )

        self.strong_resistance = self._filter_overlapping_levels(
            pd.DataFrame(res_results), "Body_Top", "High", prefix="Resistance"
        )

        recent_lows = self.lows_15.sort_values(
            by="Date", ascending=False
        ).head(5)
        sup_results = []
        for _, row in recent_lows.iterrows():
            idx = row.name
            body_bottoms = [row["Body_Bottom"]]
            if idx > 0 and (idx - 1) in self.df.index:
                body_bottoms.append(self.df.loc[idx - 1, "Body_Bottom"])
            if (idx + 1) in self.df.index:
                body_bottoms.append(self.df.loc[idx + 1, "Body_Bottom"])

            sup_results.append(
                {
                    "Date": row["Date"].strftime("%Y-%m-%d"),
                    "Low": self.round_to_nearest_tick(row["Low"]),
                    "Body_Bottom": self.round_to_nearest_tick(min(body_bottoms)),
                }
            )

        self.strong_support = self._filter_overlapping_levels(
            pd.DataFrame(sup_results), "Body_Bottom", "Low", prefix="Support"
        )

    def get_direction(self):
        if self.highs_5.empty or self.lows_15.empty:
            return pd.DataFrame()

        latest_high_val = self.highs_5.sort_values(
            by="Date", ascending=False
        ).iloc[0]["High"]
        latest_low_val = (
            self.lows_15.head(5)
            .sort_values(by="Date", ascending=False)
            .iloc[0]["Low"]
        )

        last_market_close = self.df.iloc[-1]["Close"]
        midpoint_50 = (latest_high_val + latest_low_val) / 2.0
        direction_result = "BOB" if last_market_close >= midpoint_50 else "BOW"

        return pd.DataFrame(
            [
                {
                    "Swing High Terupdate": self.round_to_nearest_tick(
                        latest_high_val
                    ),
                    "Swing Low Terupdate": self.round_to_nearest_tick(
                        latest_low_val
                    ),
                    "Level 50%": self.round_to_nearest_tick(midpoint_50),
                    "Last Close Market": self.round_to_nearest_tick(
                        last_market_close
                    ),
                    "Direction": direction_result,
                }
            ]
        )

    def classify_candle(self):
        if len(self.df) < 20 or self.atr_14 <= 0:
            return "Standard Candle", "NEUTRAL"

        ma20 = self.df["Close"].rolling(20).mean().iloc[-1]
        last_close = self.df.iloc[-1]["Close"]
        is_downtrend = last_close < ma20
        is_uptrend = last_close >= ma20

        def get_props(row):
            high, low, open_p, close = (
                row["High"],
                row["Low"],
                row["Open"],
                row["Close"],
            )
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

        if (
            p3["is_green"]
            and p2["is_green"]
            and p1["is_green"]
            and (p1["close"] > p2["close"] > p3["close"])
            and is_large_body
        ):
            return "Three White Soldiers", "BULLISH"
        if (
            p3["is_red"]
            and (p3["body_size"] >= 0.8 * self.atr_14)
            and (p2["body_size"] < 0.4 * self.atr_14)
            and p1["is_green"]
            and (p1["close"] >= (p3["open"] + p3["close"]) / 2)
            and is_downtrend
        ):
            return "Morning Star (Reversal)", "BULLISH"
        if (
            p3["is_green"]
            and (p3["body_size"] >= 0.8 * self.atr_14)
            and (p2["body_size"] < 0.4 * self.atr_14)
            and p1["is_red"]
            and (p1["close"] <= (p3["open"] + p3["close"]) / 2)
            and is_uptrend
        ):
            return "Evening Star (Reversal)", "BEARISH"

        if (
            p1["is_green"]
            and p2["is_red"]
            and (p1["body_top"] >= p2["body_top"])
            and (p1["body_bottom"] <= p2["body_bottom"])
            and is_large_body
        ):
            return (
                (
                    "Bullish Engulfing (Reversal)"
                    if is_downtrend
                    else "Bullish Engulfing"
                ),
                "BULLISH",
            )
        if (
            p1["is_red"]
            and p2["is_green"]
            and (p1["body_bottom"] <= p2["body_bottom"])
            and (p1["body_top"] >= p2["body_top"])
            and is_large_body
        ):
            return "Bearish Engulfing", "BEARISH"

        if p1["is_doji"]:
            if (p1["lower_shadow"] >= 2.5 * p1["body_size"]) and (
                p1["upper_shadow"] <= 0.5 * p1["body_size"]
            ):
                return "Dragonfly Doji", "BULLISH"
            elif (p1["upper_shadow"] >= 2.5 * p1["body_size"]) and (
                p1["lower_shadow"] <= 0.5 * p1["body_size"]
            ):
                return "Gravestone Doji", "BEARISH"
            return "Doji (Indecision)", "NEUTRAL"

        is_marubozu_body = p1["body_size"] >= (1.1 * self.atr_14)
        has_minimal_shadows = (
            p1["upper_shadow"] <= 0.1 * p1["total_range"]
        ) and (p1["lower_shadow"] <= 0.1 * p1["total_range"])

        if is_marubozu_body and has_minimal_shadows:
            return (
                (
                    "Bullish Marubozu (Strong)"
                    if p1["is_green"]
                    else "Bearish Marubozu (Strong)"
                ),
                "BULLISH" if p1["is_green"] else "BEARISH",
            )

        is_hammer_shape = (p1["lower_shadow"] >= 2.0 * p1["body_size"]) and (
            p1["upper_shadow"] <= 0.3 * p1["body_size"]
        )
        is_shooting_shape = (p1["upper_shadow"] >= 2.0 * p1["body_size"]) and (
            p1["lower_shadow"] <= 0.3 * p1["body_size"]
        )

        if is_hammer_shape:
            return (
                ("Hammer (Valid Reversal)", "BULLISH")
                if is_downtrend
                else ("Hanging Man", "BEARISH")
            )

        if is_shooting_shape:
            return (
                ("Shooting Star (Valid Reversal)", "BEARISH")
                if is_uptrend
                else ("Inverted Hammer", "NEUTRAL")
            )

        color_str = "Hijau" if p1["is_green"] else "Merah"
        if is_small_body:
            return f"Small {color_str} / Spinning Top", "NEUTRAL"

        return (
            f"Standard {color_str}",
            "BULLISH" if p1["is_green"] else "BEARISH",
        )

    def calculate_score_and_warnings(
        self,
        plan_type,
        buy_min,
        buy_max,
        target_1,
        stop_loss,
        rr_ratio,
        candle_type,
        candle_bias,
    ):
        last_close = self.df.iloc[-1]["Close"]
        p1_high = self.df.iloc[-1]["High"]
        p1_low = self.df.iloc[-1]["Low"]
        p1_body_top = max(self.df.iloc[-1]["Open"], last_close)
        upper_shadow = p1_high - p1_body_top

        # 1. RISK-TO-REWARD SCORE (MAX 35)
        if rr_ratio >= 3.0:
            score_rr = 35
        elif rr_ratio >= 2.0:
            score_rr = 28
        elif rr_ratio >= 1.5:
            score_rr = 20
        elif rr_ratio >= 1.0:
            score_rr = 10
        else:
            score_rr = 0

        # 2. PRICE POSITION / ZONE SCORE (MAX 25)
        if buy_min <= last_close <= buy_max:
            score_zone = 25
            pos_status = "In Buy Zone"
        elif (
            last_close > buy_max
            and ((last_close - buy_max) / buy_max * 100) <= 2.0
        ):
            score_zone = 15
            pos_status = "Near Zone"
        elif last_close < buy_min:
            score_zone = 5
            pos_status = "Below Buy Zone"
        else:
            score_zone = 0
            pos_status = "Running / Away"

        # 3. CANDLESTICK SCORE (MAX 20)
        if candle_bias == "BULLISH":
            if any(
                k in candle_type
                for k in ["Engulfing", "Morning Star", "Soldiers", "Marubozu"]
            ):
                score_candle = 20
            else:
                score_candle = 15
        elif candle_bias == "NEUTRAL":
            score_candle = 10
        else:
            score_candle = 0

        # 4. SAFETY & WARNING PENALTIES (MAX 20)
        penalty = 0
        warnings = []

        if rr_ratio < 1.0:
            warnings.append("🚫 R:R Buruk (< 1:1)")
            penalty += 15
        elif rr_ratio < 1.5:
            warnings.append("⚠️ R:R Kurang Ideal (< 1:1.5)")
            penalty += 5

        if plan_type == "BOW":
            dist_to_support = (
                ((last_close - buy_min) / buy_min) * 100 if buy_min > 0 else 0
            )
            if dist_to_support > 4.0:
                warnings.append(
                    f"⚠️ Jauh dari Support (+{round(dist_to_support, 1)}%)"
                )
                penalty += 10

        dist_to_target = (
            ((target_1 - last_close) / last_close) * 100 if last_close > 0 else 0
        )
        if 0 < dist_to_target <= 1.5:
            warnings.append(
                f"⚠️ Dekat Resistance (Sisa +{round(dist_to_target, 1)}%)"
            )
            penalty += 5

        if upper_shadow >= (0.4 * (p1_high - p1_low)) and upper_shadow > 0:
            warnings.append("⚡ Tekanan Jual Ekor Atas")
            penalty += 5

        if candle_bias == "BEARISH":
            warnings.append("⚠️ Sinyal Candle Masih Bearish")
            penalty += 10

        score_safety = max(0, 20 - penalty)
        total_score = int(
            score_rr + score_zone + score_candle + score_safety
        )

        if total_score >= 85:
            grade = "🟢 Grade A+ (Prime)"
        elif total_score >= 70:
            grade = "🟢 Grade A (Ideal)"
        elif total_score >= 50:
            grade = "🟡 Grade B (Moderate)"
        else:
            grade = "🔴 Grade C (High Risk)"

        warning_str = (
            " | ".join(warnings)
            if warnings
            else "✅ Setup Clean / Minimum Risk"
        )

        return total_score, grade, pos_status, warning_str

    def generate_trade_plan(self):
        min_point_gap = max(
            self.get_tick_size(self.df.iloc[-1]["Close"]) * 2, 5
        )

        def find_target_1(min_val):
            if not self.strong_resistance.empty:
                valid_res = sorted(
                    [
                        p
                        for p in self.strong_resistance["High"].values
                        if (p - min_val) >= min_point_gap
                    ]
                )
                if valid_res:
                    return self.round_to_nearest_tick(valid_res[0])

            sh_sorted = self.highs_15.sort_values(by="Date", ascending=False)
            sh_valid = sh_sorted[(sh_sorted["High"] - min_val) >= min_point_gap]
            if not sh_valid.empty:
                return self.round_to_nearest_tick(sh_valid.iloc[0]["High"])

            return self.round_to_nearest_tick(
                min_val + max(1.5 * self.atr_14, min_point_gap + 2)
            )

        def find_target_2(target_1):
            if not self.strong_resistance.empty:
                valid_res = sorted(
                    [
                        p
                        for p in self.strong_resistance["High"].values
                        if (p - target_1) >= min_point_gap
                    ]
                )
                if valid_res:
                    return self.round_to_nearest_tick(valid_res[0])

            sh_sorted = self.highs_15.sort_values(by="Date", ascending=False)
            sh_valid = sh_sorted[(sh_sorted["High"] - target_1) >= min_point_gap]
            if not sh_valid.empty:
                return self.round_to_nearest_tick(sh_valid.iloc[0]["High"])

            return self.round_to_nearest_tick(
                target_1 + max(1.5 * self.atr_14, min_point_gap + 2)
            )

        candle_name, candle_bias = self.classify_candle()

        # 1. BOW PLAN
        if not self.strong_support.empty:
            sup_row = self.strong_support.iloc[0]
            s_low, s_bb = sup_row["Low"], sup_row["Body_Bottom"]
        else:
            last_low = self.df.iloc[-1]["Low"]
            s_low, s_bb = last_low, last_low

        rb_bow_min, rb_bow_max = min(s_low, s_bb), max(s_low, s_bb)
        stop_loss_bow = self.sub_ticks(rb_bow_min, 3)
        target_1_bow = find_target_1(rb_bow_max)
        target_2_bow = find_target_2(target_1_bow)
        risk_bow = rb_bow_min - stop_loss_bow
        reward_bow = target_1_bow - rb_bow_min
        rr_val_bow = round(reward_bow / risk_bow, 1) if risk_bow > 0 else 0.0

        score_bow, grade_bow, pos_bow, warn_bow = (
            self.calculate_score_and_warnings(
                "BOW",
                rb_bow_min,
                rb_bow_max,
                target_1_bow,
                stop_loss_bow,
                rr_val_bow,
                candle_name,
                candle_bias,
            )
        )

        # 2. BOB PLAN
        if not self.strong_resistance.empty:
            res_sorted = self.strong_resistance.sort_values(
                by="Date", ascending=False
            )
            base_bob_high = res_sorted.iloc[0]["High"]
        else:
            base_bob_high = self.df.iloc[-1]["High"]

        upper_bob_high = self.add_ticks(base_bob_high, 3)
        stop_loss_bob = self.sub_ticks(base_bob_high, 3)
        target_1_bob = find_target_1(upper_bob_high)
        target_2_bob = find_target_2(target_1_bob)
        risk_bob = base_bob_high - stop_loss_bob
        reward_bob = target_1_bob - base_bob_high
        rr_val_bob = round(reward_bob / risk_bob, 1) if risk_bob > 0 else 0.0

        score_bob, grade_bob, pos_bob, warn_bob = (
            self.calculate_score_and_warnings(
                "BOB",
                base_bob_high,
                upper_bob_high,
                target_1_bob,
                stop_loss_bob,
                rr_val_bob,
                candle_name,
                candle_bias,
            )
        )

        def fmt_range(p_min, p_max):
            p_min_str = (
                f"{int(p_min):,}" if p_min.is_integer() else f"{p_min:,}"
            )
            p_max_str = (
                f"{int(p_max):,}" if p_max.is_integer() else f"{p_max:,}"
            )
            return f"{p_min_str} - {p_max_str}"

        plan_data = [
            {
                "No": 1,
                "Type": "BOW",
                "Score": score_bow,
                "Grade": grade_bow,
                "Posisi Harga": pos_bow,
                "Range Buy Min": rb_bow_min,
                "Range Buy Max": rb_bow_max,
                "Area Buy": fmt_range(rb_bow_min, rb_bow_max),
                "Stop Loss": stop_loss_bow,
                "TP 1": target_1_bow,
                "TP 2": target_2_bow,
                "Rasio (R:R)": f"1 : {rr_val_bow}" if rr_val_bow > 0 else "-",
                "RR_Val": rr_val_bow,
                "Pola Candle": candle_name,
                "Warning": warn_bow,
            },
            {
                "No": 2,
                "Type": "BOB",
                "Score": score_bob,
                "Grade": grade_bob,
                "Posisi Harga": pos_bob,
                "Range Buy Min": base_bob_high,
                "Range Buy Max": upper_bob_high,
                "Area Buy": fmt_range(base_bob_high, upper_bob_high),
                "Stop Loss": stop_loss_bob,
                "TP 1": target_1_bob,
                "TP 2": target_2_bob,
                "Rasio (R:R)": f"1 : {rr_val_bob}" if rr_val_bob > 0 else "-",
                "RR_Val": rr_val_bob,
                "Pola Candle": candle_name,
                "Warning": warn_bob,
            },
        ]
        return pd.DataFrame(plan_data)
