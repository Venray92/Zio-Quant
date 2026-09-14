import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
import yfinance as yf


class TradePlanner:

  def __init__(self, ticker="INCO.JK", period="6mo"):
    self.ticker = ticker.upper()
    self.period = period
    self.df = None
    self.atr_14 = 0
    self.highs_15 = pd.DataFrame()
    self.lows_15 = pd.DataFrame()
    self.highs_5 = pd.DataFrame()
    self.strong_support = pd.DataFrame()
    self.strong_resistance = pd.DataFrame()

  # --- HELPER FUNGSIONAL ---
  @staticmethod
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

  @classmethod
  def add_ticks(cls, price, n_ticks):
    p = float(price)
    for _ in range(n_ticks):
      p += cls.get_tick_size(p)
    return round(p, 2)

  @classmethod
  def sub_ticks(cls, price, n_ticks):
    p = float(price)
    for _ in range(n_ticks):
      tick = cls.get_tick_size(p)
      p -= tick
      if p < 1:
        p = 1
    return round(p, 2)

  @classmethod
  def round_to_nearest_tick(cls, price):
    price = float(price)
    tick = cls.get_tick_size(price)
    return round(round(price / tick) * tick, 2)

  # --- MEMUAT & MENYIAPKAN DATA ---
  def fetch_and_prepare_data(self):
    stock = yf.Ticker(self.ticker)
    df = stock.history(period=self.period, interval="1d").reset_index()

    if df.empty:
      raise ValueError(f"Tidak ada data ditemukan untuk ticker {self.ticker}")

    # Body Top & Body Bottom
    df["Body_Top"] = df[["Open", "Close"]].max(axis=1)
    df["Body_Bottom"] = df[["Open", "Close"]].min(axis=1)

    # ATR(14)
    df["Prev_Close"] = df["Close"].shift(1)
    df["TR"] = np.maximum(
        df["High"] - df["Low"],
        np.maximum(
            abs(df["High"] - df["Prev_Close"]),
            abs(df["Low"] - df["Prev_Close"]),
        ),
    )
    self.atr_14 = df["TR"].rolling(window=14).mean().iloc[-1]
    if pd.isna(self.atr_14):
      self.atr_14 = 0.0

    # Swing High & Low Detection
    order = 3
    high_idx = argrelextrema(df["High"].values, np.greater_equal, order=order)[
        0
    ]
    low_idx = argrelextrema(df["Low"].values, np.less_equal, order=order)[0]

    df["Swing_Type"] = ""
    df.iloc[high_idx, df.columns.get_loc("Swing_Type")] = "Swing High"
    df.iloc[low_idx, df.columns.get_loc("Swing_Type")] = "Swing Low"

    self.df = df

    # Top 15 Swing Highs & Lows
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

    # Re-calculate Support & Resistance
    self._calculate_strong_levels()

  # --- FILTER OVERLAPPING ---
  @staticmethod
  def _filter_overlapping_levels(df_levels, col1, col2, prefix="Resistance"):
    if df_levels.empty:
      return pd.DataFrame()

    if "Date" in df_levels.columns:
      df_levels = df_levels.sort_values(by="Date", ascending=False)

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
        accepted_rows.append(row.to_dict())
        accepted_ranges.append((r_min, r_max))

    res_df = pd.DataFrame(accepted_rows)
    if not res_df.empty:
      res_df = res_df.head(3).reset_index(drop=True)
      ranks = []
      for i in range(len(res_df)):
        if i == 0:
          ranks.append(f"1st {prefix} (Terdekat)")
        elif i == 1:
          ranks.append(f"2nd {prefix}")
        else:
          ranks.append(f"3rd {prefix} (Terjauh)")
      res_df["Rank"] = ranks

    return res_df

  def _calculate_strong_levels(self):
    # Resistance calculation
    sorted_highs = self.highs_5.sort_values(by="Date", ascending=False)
    res_results = []
    for _, row in sorted_highs.iterrows():
      idx = row.name
      body_tops = [row["Body_Top"]]
      if idx > 0 and idx - 1 in self.df.index:
        body_tops.append(self.df.loc[idx - 1, "Body_Top"])
      if idx < len(self.df) - 1 and idx + 1 in self.df.index:
        body_tops.append(self.df.loc[idx + 1, "Body_Top"])

      res_results.append({
          "Date": row["Date"].strftime("%Y-%m-%d"),
          "Body_Top": round(max(body_tops), 2),
          "High": round(row["High"], 2),
      })

    raw_res = pd.DataFrame(res_results)
    self.strong_resistance = self._filter_overlapping_levels(
        raw_res, "Body_Top", "High", prefix="Resistance"
    )

    # Support calculation
    recent_lows = self.lows_15.sort_values(by="Date", ascending=False).head(5)
    sup_results = []
    for _, row in recent_lows.iterrows():
      idx = row.name
      body_bottoms = [row["Body_Bottom"]]
      if idx > 0 and idx - 1 in self.df.index:
        body_bottoms.append(self.df.loc[idx - 1, "Body_Bottom"])
      if idx < len(self.df) - 1 and idx + 1 in self.df.index:
        body_bottoms.append(self.df.loc[idx + 1, "Body_Bottom"])

      sup_results.append({
          "Date": row["Date"].strftime("%Y-%m-%d"),
          "Low": round(row["Low"], 2),
          "Body_Bottom": round(min(body_bottoms), 2),
      })

    raw_sup = pd.DataFrame(sup_results)
    self.strong_support = self._filter_overlapping_levels(
        raw_sup, "Body_Bottom", "Low", prefix="Support"
    )

  # --- METHOD PUBLIK UNTUK STREAMLIT ---
  def get_direction(self):
    latest_high_row = self.highs_5.sort_values(
        by="Date", ascending=False
    ).iloc[0]
    latest_low_row = (
        self.lows_15.head(5).sort_values(by="Date", ascending=False).iloc[0]
    )

    latest_high_val = latest_high_row["High"]
    latest_low_val = latest_low_row["Low"]
    last_market_close = self.df.iloc[-1]["Close"]
    midpoint_50 = (latest_high_val + latest_low_val) / 2
    direction_result = "BOB" if last_market_close >= midpoint_50 else "BOW"

    return pd.DataFrame([{
        "Swing High Terupdate": round(latest_high_val, 2),
        "Swing Low Terupdate": round(latest_low_val, 2),
        "Level 50%": round(midpoint_50, 2),
        "Last Close Market": round(last_market_close, 2),
        "Direction": direction_result,
    }])

  def get_strong_support(self):
    return self.strong_support

  def get_strong_resistance(self):
    return self.strong_resistance

  def classify_candle(self):
    if len(self.df) < 3:
      return (
          "Standard Doji",
          "ℹ️ Info: Kekuatan seimbang. Wait and see.",
      )

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
      }

    p3, p2, p1 = (
        get_props(self.df.iloc[-3]),
        get_props(self.df.iloc[-2]),
        get_props(self.df.iloc[-1]),
    )

    if (
        p3["is_green"]
        and p2["is_green"]
        and p1["is_green"]
        and p1["close"] > p2["close"] > p3["close"]
    ):
      return (
          "Three White Soldiers",
          "💡 Sinyal: Momentum naik sangat kuat.",
      )
    if (
        p3["is_red"]
        and p3["body_size"] >= 0.4 * p3["total_range"]
        and p2["body_size"] <= 0.3 * p2["total_range"]
        and p1["is_green"]
        and p1["close"] >= (p3["open"] + p3["close"]) / 2
    ):
      return (
          "Morning Star",
          "💡 Sinyal: Pola pembalikan arah naik berakurasi tinggi.",
      )
    if (
        p3["is_green"]
        and p3["body_size"] >= 0.4 * p3["total_range"]
        and p2["body_size"] <= 0.3 * p2["total_range"]
        and p1["is_red"]
        and p1["close"] <= (p3["open"] + p3["close"]) / 2
    ):
      return "Evening Star", "⚠️ Warning: Tren naik resmi patah."
    if (
        p1["is_green"]
        and p2["is_red"]
        and p1["body_top"] >= p2["body_top"]
        and p1["body_bottom"] <= p2["body_bottom"]
    ):
      return (
          "Bullish Engulfing",
          "💡 Sinyal: Pembeli mengambil alih. Sinyal pembalikan arah naik.",
      )
    if (
        p1["is_red"]
        and p2["is_green"]
        and p1["body_bottom"] <= p2["body_bottom"]
        and p1["body_top"] >= p2["body_top"]
    ):
      return (
          "Bearish Engulfing",
          "⚠️ Warning: Penjual menguasai pasar secara agresif.",
      )

    if p1["is_green"]:
      return (
          (
              "Hammer"
              if p1["lower_shadow"] >= 2 * p1["body_size"]
              else "Marubozu Hijau"
          ),
          "💡 Sinyal: Potensi pantulan naik.",
      )
    else:
      return (
          (
              "Shooting Star"
              if p1["upper_shadow"] >= 2 * p1["body_size"]
              else "Marubozu Merah"
          ),
          "⚠️ Warning: Tekanan jual tinggi.",
      )

  def generate_trade_plan(self):
    min_point_gap = 9

    def find_target_1(min_val):
      if not self.strong_resistance.empty:
        valid_res = sorted([
            p
            for p in self.strong_resistance["High"].values
            if (p - min_val) >= min_point_gap
        ])
        if valid_res:
          return self.round_to_nearest_tick(valid_res[0])

      sh_sorted = self.highs_15.sort_values(by="Date", ascending=False)
      sh_valid = sh_sorted[(sh_sorted["High"] - min_val) >= min_point_gap]
      if not sh_valid.empty:
        return self.round_to_nearest_tick(sh_valid.iloc[0]["High"])

      target_1_atr = min_val + max(1.5 * self.atr_14, min_point_gap + 1)
      return self.round_to_nearest_tick(target_1_atr)

    def find_target_2(target_1):
      if not self.strong_resistance.empty:
        valid_res = sorted([
            p
            for p in self.strong_resistance["High"].values
            if (p - target_1) >= min_point_gap
        ])
        if valid_res:
          return self.round_to_nearest_tick(valid_res[0])

      sh_sorted = self.highs_15.sort_values(by="Date", ascending=False)
      sh_valid = sh_sorted[(sh_sorted["High"] - target_1) >= min_point_gap]
      if not sh_valid.empty:
        return self.round_to_nearest_tick(sh_valid.iloc[0]["High"])

      target_2_atr = target_1 + max(1.5 * self.atr_14, min_point_gap + 1)
      return self.round_to_nearest_tick(target_2_atr)

    candle_name, current_warning = self.classify_candle()

    # 1. BOW PLAN
    if not self.strong_support.empty:
      sup_row = self.strong_support.iloc[0]
      s_low, s_bb = sup_row["Low"], sup_row["Body_Bottom"]
    else:
      last_low = self.df.iloc[-1]["Low"]
      s_low, s_bb = last_low, last_low

    rb_bow_min, rb_bow_max = min(s_low, s_bb), max(s_low, s_bb)
    range_buy_bow = f"{rb_bow_min} - {rb_bow_max}"
    stop_loss_bow = self.sub_ticks(rb_bow_min, 3)
    target_1_bow = find_target_1(rb_bow_max)
    target_2_bow = find_target_2(target_1_bow)
    risk_bow = rb_bow_min - stop_loss_bow
    reward_bow = target_1_bow - rb_bow_min
    ratio_bow = (
        f"1 : {round(reward_bow / risk_bow, 1)}" if risk_bow > 0 else "-"
    )

    # 2. BOB PLAN
    if not self.strong_resistance.empty:
      res_sorted = self.strong_resistance.sort_values(
          by="Date", ascending=False
      )
      latest_res_row = res_sorted.iloc[0]
      base_bob_high = latest_res_row["High"]
    else:
      base_bob_high = self.df.iloc[-1]["High"]

    upper_bob_high = self.add_ticks(base_bob_high, 3)
    range_buy_bob = f"{base_bob_high} - {upper_bob_high}"
    stop_loss_bob = self.sub_ticks(base_bob_high, 3)
    target_1_bob = find_target_1(upper_bob_high)
    target_2_bob = find_target_2(target_1_bob)
    risk_bob = base_bob_high - stop_loss_bob
    reward_bob = target_1_bob - base_bob_high
    ratio_bob_val = (
        f"1 : {round(reward_bob / risk_bob, 1)}" if risk_bob > 0 else "-"
    )

    plan_data = [
        {
            "No": 1,
            "Type": "BOW",
            "Range Buy": range_buy_bow,
            "Stop Loss": stop_loss_bow,
            "Target 1": target_1_bow,
            "Target 2": target_2_bow,
            "Rasio (R:R)": ratio_bow,
            "Status Candle": candle_name,
            "Warning": current_warning,
        },
        {
            "No": 2,
            "Type": "BOB",
            "Range Buy": range_buy_bob,
            "Stop Loss": stop_loss_bob,
            "Target 1": target_1_bob,
            "Target 2": target_2_bob,
            "Rasio (R:R)": ratio_bob_val,
            "Status Candle": candle_name,
            "Warning": current_warning,
        },
    ]
    return pd.DataFrame(plan_data)

  def get_swing_points(self):
    swing_points = pd.concat([self.highs_15, self.lows_15]).copy()
    swing_points = swing_points.sort_values(
        by=["Swing_Type", "Date"], ascending=[True, False]
    )
    swing_points["No"] = range(1, len(swing_points) + 1)

    TOLERANCE_PCT = 0.015

    def find_metpoints(row, df_all):
      no_curr = row["No"]
      stype_curr = row["Swing_Type"]
      prices_curr = (
          [row["Low"], row["Close"]]
          if stype_curr == "Swing Low"
          else [row["High"], row["Open"]]
      )
      matched_prices = set()

      for _, other_row in df_all.iterrows():
        if no_curr == other_row["No"]:
          continue
        stype_other = other_row["Swing_Type"]
        prices_other = (
            [other_row["Low"], other_row["Close"]]
            if stype_other == "Swing Low"
            else [other_row["High"], other_row["Open"]]
        )
        for p1 in prices_curr:
          for p2 in prices_other:
            if abs(p1 - p2) / p1 <= TOLERANCE_PCT:
              matched_prices.add(round(p1, 2))

      return (
          ", ".join(map(str, sorted(matched_prices))) if matched_prices else "-"
      )

    swing_points["metpoint"] = swing_points.apply(
        lambda r: find_metpoints(r, swing_points), axis=1
    )
    swing_points["Date"] = swing_points["Date"].dt.strftime("%Y-%m-%d")
    swing_points = swing_points.set_index("Date")
    swing_points = swing_points[
        ["No", "Open", "High", "Low", "Close", "Swing_Type", "metpoint"]
    ]
    swing_points[["Open", "High", "Low", "Close"]] = swing_points[
        ["Open", "High", "Low", "Close"]
    ].round(2)

    return swing_points


# --- RUN TEST (UNTUK PENGETESAN LOKAL SCRIPT) ---
if __name__ == "__main__":
  planner = TradePlanner("INCO.JK", "6mo")
  planner.fetch_and_prepare_data()

  print("=== TABEL DIRECTION ===")
  print(planner.get_direction().to_string(index=False))

  print("\n=== STRONG RESISTANCE ===")
  print(planner.get_strong_resistance().to_string(index=False))

  print("\n=== STRONG SUPPORT ===")
  print(planner.get_strong_support().to_string(index=False))

  print("\n=== TABEL TRADE PLAN ===")
  print(planner.generate_trade_plan().to_string(index=False))

  print("\n=== TABEL SWING POINTS ===")
  print(planner.get_swing_points().to_string())
