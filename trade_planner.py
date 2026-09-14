import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
import yfinance as yf


class TradePlanner:

  def __init__(self, ticker: str = "INCO.JK", period: str = "6mo"):
    self.ticker = ticker
    self.period = period
    self.df = None
    self.atr_14 = None
    self.highs_15 = None
    self.lows_15 = None
    self.highs_5 = None

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
    p = price
    for _ in range(n_ticks):
      p += cls.get_tick_size(p)
    return round(p, 2)

  @classmethod
  def sub_ticks(cls, price, n_ticks):
    p = price
    for _ in range(n_ticks):
      tick = cls.get_tick_size(p)
      p -= tick
      if p < 1:
        p = 1
    return round(p, 2)

  @classmethod
  def round_to_nearest_tick(cls, price):
    tick = cls.get_tick_size(price)
    return round(round(price / tick) * tick, 2)

  def fetch_and_prepare_data(self):
    stock = yf.Ticker(self.ticker)
    df = stock.history(period=self.period, interval="1d").reset_index()

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
    self.atr_14 = df["TR"].rolling(window=14).mean().iloc[-1]

    order = 3
    high_idx = argrelextrema(df["High"].values, np.greater_equal, order=order)[
        0
    ]
    low_idx = argrelextrema(df["Low"].values, np.less_equal, order=order)[0]

    df["Swing_Type"] = ""
    df.iloc[high_idx, df.columns.get_loc("Swing_Type")] = "Swing High"
    df.iloc[low_idx, df.columns.get_loc("Swing_Type")] = "Swing Low"

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

  @staticmethod
  def filter_overlapping_levels(df_levels, col1, col2):
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
        accepted_rows.append(row)
        accepted_ranges.append((r_min, r_max))
    return pd.DataFrame(accepted_rows)

  def get_strong_resistance(self):
    sorted_swings = self.highs_5.sort_values(by="High", ascending=False).iloc[
        :3
    ]
    results = []
    ranks = [
        "1st Highest (Utama)",
        "2nd Highest (Kedua)",
        "3rd Highest (Ketiga)",
    ]

    for rank_label, (_, row) in zip(ranks, sorted_swings.iterrows()):
      idx = row.name
      body_tops = [row["Body_Top"]]
      if idx > 0:
        body_tops.append(self.df.loc[idx - 1, "Body_Top"])
      if idx < len(self.df) - 1:
        body_tops.append(self.df.loc[idx + 1, "Body_Top"])

      results.append({
          "Date": row["Date"].strftime("%Y-%m-%d"),
          "Rank": rank_label,
          "Body_Top": round(max(body_tops), 2),
          "High": round(row["High"], 2),
      })
    raw = pd.DataFrame(results)
    return self.filter_overlapping_levels(raw, "Body_Top", "High")

  def get_strong_support(self):
    recent_lows = self.lows_15.sort_values(by="Date", ascending=False).head(3)
    results = []
    ranks = [
        "1st Support (Terdekat)",
        "2nd Support",
        "3rd Support (Terjauh)",
    ]

    for rank_label, (_, row) in zip(ranks, recent_lows.iterrows()):
      idx = row.name
      body_bottoms = [row["Body_Bottom"]]
      if idx > 0:
        body_bottoms.append(self.df.loc[idx - 1, "Body_Bottom"])
      if idx < len(self.df) - 1:
        body_bottoms.append(self.df.loc[idx + 1, "Body_Bottom"])

      results.append({
          "Date": row["Date"].strftime("%Y-%m-%d"),
          "Rank": rank_label,
          "Low": round(row["Low"], 2),
          "Body_Bottom": round(min(body_bottoms), 2),
      })
    raw = pd.DataFrame(results)
    return self.filter_overlapping_levels(raw, "Body_Bottom", "Low")

  @staticmethod
  def _get_props(row):
    high, low, open_p, close = (
        row["High"],
        row["Low"],
        row["Open"],
        row["Close"],
    )
    body_top, body_bottom = max(open_p, close), min(open_p, close)
    total_range = high - low if (high - low) != 0 else 0.0001
    return {
        "high": high,
        "low": low,
        "open": open_p,
        "close": close,
        "body_top": body_top,
        "body_bottom": body_bottom,
        "body_size": body_top - body_bottom,
        "total_range": total_range,
        "upper_shadow": high - body_top,
        "lower_shadow": body_bottom - low,
        "is_green": close > open_p,
        "is_red": close < open_p,
    }

  def classify_candle(self):
    if len(self.df) < 3:
      return (
          "Standard Doji",
          (
              "ℹ️ Info: Kekuatan pembeli dan penjual seimbang. Pasar sedang"
              " ragu, wait and see."
          ),
      )

    p3 = self._get_props(self.df.iloc[-3])
    p2 = self._get_props(self.df.iloc[-2])
    p1 = self._get_props(self.df.iloc[-1])

    if (
        p3["is_green"]
        and p2["is_green"]
        and p1["is_green"]
        and p1["close"] > p2["close"]
        and p2["close"] > p3["close"]
    ):
      return (
          "Three White Soldiers",
          "💡 Sinyal: Pembeli dominan berturut-turut. Momentum naik sangat kuat.",
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
          (
              "💡 Sinyal: Fase penurunan berakhir. Pola pembalikan arah naik"
              " berakurasi tinggi."
          ),
      )
    if (
        p3["is_green"]
        and p3["body_size"] >= 0.4 * p3["total_range"]
        and p2["body_size"] <= 0.3 * p2["total_range"]
        and p1["is_red"]
        and p1["close"] <= (p3["open"] + p3["close"]) / 2
    ):
      return (
          "Evening Star",
          (
              "⚠️ Warning: Tren naik resmi patah. Persiapkan strategi exit atau"
              " Stop Loss."
          ),
      )
    if (
        p1["is_green"]
        and p2["is_red"]
        and p1["body_top"] >= p2["body_top"]
        and p1["body_bottom"] <= p2["body_bottom"]
    ):
      return (
          "Bullish Engulfing",
          (
              "💡 Sinyal: Pembeli mengambil alih. Sinyal pembalikan arah naik"
              " cukup valid."
          ),
      )
    if (
        p1["is_red"]
        and p2["is_green"]
        and p1["body_bottom"] <= p2["body_bottom"]
        and p1["body_top"] >= p2["body_top"]
    ):
      return (
          "Bearish Engulfing",
          (
              "⚠️ Warning: Penjual menguasai pasar secara agresif. Waspada"
              " koreksi tajam."
          ),
      )
    if (
        p1["is_green"]
        and p2["is_red"]
        and p1["close"] >= (p2["open"] + p2["close"]) / 2
        and p1["open"] <= p2["close"]
    ):
      return (
          "Piercing Line",
          (
              "💡 Sinyal: Perlawanan pembeli menembus pertengahan candle merah."
              " Sinyal pembalikan arah."
          ),
      )
    if (
        p1["is_red"]
        and p2["is_green"]
        and p1["close"] <= (p2["open"] + p2["close"]) / 2
        and p1["open"] >= p2["close"]
    ):
      return (
          "Dark Cloud Cover",
          (
              "⚠️ Warning: Penjual menekan balik hingga melewati separuh candle"
              " hijau. Amankan profit!"
          ),
      )
    if (
        p1["body_size"] <= 0.15 * p1["total_range"]
        and p1["lower_shadow"] >= 0.6 * p1["total_range"]
        and p1["upper_shadow"] <= 0.1 * p1["total_range"]
    ):
      return (
          "Dragonfly Doji",
          (
              "💡 Sinyal: Penolakan bawah sangat kuat. Area support valid,"
              " siap-siap berburu entry."
          ),
      )
    if (
        p1["body_size"] <= 0.15 * p1["total_range"]
        and p1["upper_shadow"] >= 0.6 * p1["total_range"]
        and p1["lower_shadow"] <= 0.1 * p1["total_range"]
    ):
      return (
          "Gravestone Doji",
          (
              "⚠️ Warning: Penolakan atas sangat masif. Pasokan melimpah, rawan"
              " dump."
          ),
      )
    if (
        p1["body_size"] <= 0.2 * p1["total_range"]
        and p1["upper_shadow"] >= 0.35 * p1["total_range"]
        and p1["lower_shadow"] >= 0.35 * p1["total_range"]
    ):
      return (
          "Long-Legged Doji",
          (
              "ℹ️ Info: Volatilitas ekstrem tetapi berakhir imbang. Tunggu"
              " penentuan arah break."
          ),
      )
    if p1["body_size"] <= 0.2 * p1["total_range"]:
      if p1["upper_shadow"] <= 0.1 and p1["lower_shadow"] <= 0.1:
        return (
            "Standard Doji",
            (
                "ℹ️ Info: Kekuatan pembeli dan penjual seimbang. Pasar sedang"
                " ragu, wait and see."
            ),
        )
      else:
        return (
            "Spinning Top",
            (
                "ℹ️ Info: Konsolidasi tipis. Momentum melambat, bersiap untuk"
                " pergerakan berikutnya."
            ),
        )
    if (
        p1["is_green"]
        and p1["upper_shadow"] <= 0.05 * p1["total_range"]
        and p1["lower_shadow"] <= 0.05 * p1["total_range"]
    ):
      return (
          "Marubozu Hijau",
          (
              "💡 Sinyal: Pembeli dominan penuh. Momentum naik sangat kuat, siap"
              " lanjut rally."
          ),
      )
    if (
        p1["is_red"]
        and p1["upper_shadow"] <= 0.05 * p1["total_range"]
        and p1["lower_shadow"] <= 0.05 * p1["total_range"]
    ):
      return (
          "Marubozu Merah",
          (
              "⚠️ Warning: Tekanan jual sangat deras (falling knife). Hindari"
              " beli, tunggu konfirmasi pantulan!"
          ),
      )
    if (
        p1["upper_shadow"] >= 0.66 * p1["total_range"]
        or p1["lower_shadow"] >= 0.66 * p1["total_range"]
    ):
      return (
          "Pinbar",
          (
              "💡 / ⚠️ Sinyal: Terjadi liquidity sweep / penolakan ekor panjang."
              " Ikuti arah ekor penolakannya."
          ),
      )

    if p1["is_green"]:
      if p1["lower_shadow"] >= 2 * p1["body_size"]:
        return (
            "Hammer",
            (
                "💡 Sinyal: Tekanan jual ditolak kuat di bawah. Potensi bounce"
                " (pantulan naik)."
            ),
        )
      elif p1["upper_shadow"] >= 2 * p1["body_size"]:
        return (
            "Inverted Hammer",
            (
                "💡 Sinyal: Pembeli mulai merangsek naik. Tunggu konfirmasi"
                " candle hijau berikutnya."
            ),
        )
      else:
        return (
            "Marubozu Hijau",
            (
                "💡 Sinyal: Pembeli dominan penuh. Momentum naik sangat kuat,"
                " siap lanjut rally."
            ),
        )
    else:
      if p1["upper_shadow"] >= 2 * p1["body_size"]:
        return (
            "Shooting Star",
            (
                "⚠️ Warning: Kenaikan harga ditolak keras di atas. Potensi"
                " longsor dari puncak."
            ),
        )
      elif p1["lower_shadow"] >= 2 * p1["body_size"]:
        return (
            "Hanging Man",
            (
                "⚠️ Warning: Sinyal bahaya di area atas. Pembeli mulai kehilangan"
                " tenaga."
            ),
        )
      else:
        return (
            "Marubozu Merah",
            (
                "⚠️ Warning: Tekanan jual sangat deras (falling knife). Hindari"
                " beli, tunggu konfirmasi pantulan!"
            ),
        )

  def generate_trade_plan(self):
    strong_sup_df = self.get_strong_support()
    strong_res_df = self.get_strong_resistance()

    def find_target_1(min_val):
      valid_res = sorted([
          p for p in strong_res_df["High"].values if p > min_val
      ])
      if valid_res:
        return self.round_to_nearest_tick(valid_res[0])
      sh_sorted = self.highs_15.sort_values(by="Date", ascending=False)
      sh_valid = sh_sorted[sh_sorted["High"] > min_val]
      if not sh_valid.empty:
        return self.round_to_nearest_tick(sh_valid.iloc[0]["High"])
      return self.round_to_nearest_tick(min_val)

    def find_target_2(target_1):
      valid_res = sorted([
          p for p in strong_res_df["High"].values if p > target_1
      ])
      if valid_res:
        return self.round_to_nearest_tick(valid_res[0])
      sh_sorted = self.highs_15.sort_values(by="Date", ascending=False)
      sh_valid = sh_sorted[sh_sorted["High"] > target_1]
      if not sh_valid.empty:
        return self.round_to_nearest_tick(sh_valid.iloc[0]["High"])
      target_2_atr = target_1 + (1.5 * self.atr_14)
      return self.round_to_nearest_tick(target_2_atr)

    candle_name, current_warning = self.classify_candle()

    # 1. BOW PLAN
    sup_row = strong_sup_df.iloc[0]
    s_low, s_bb = sup_row["Low"], sup_row["Body_Bottom"]
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
    res_sorted_by_date = strong_res_df.sort_values(by="Date", ascending=False)
    latest_res_row = res_sorted_by_date.iloc[0]
    base_bob_high = latest_res_row["High"]
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

    return pd.DataFrame([
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
    ])

  def get_swing_points(self):
    swing_points = pd.concat([self.highs_15, self.lows_15]).copy()
    swing_points = swing_points.sort_values(
        by=["Swing_Type", "Date"], ascending=[True, False]
    )
    swing_points["No"] = range(1, len(swing_points) + 1)

    tolerance_pct = 0.015

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
            if abs(p1 - p2) / p1 <= tolerance_pct:
              matched_prices.add(round(p1, 2))

      return (
          ", ".join(map(str, sorted(matched_prices))) if matched_prices else "-"
      )

    swing_points["metpoint"] = swing_points.apply(
        lambda r: find_metpoints(r, swing_points), axis=1
    )
    swing_points = swing_points.set_index("Date")
    swing_points = swing_points[
        ["No", "Open", "High", "Low", "Close", "Swing_Type", "metpoint"]
    ]
    swing_points[["Open", "High", "Low", "Close"]] = swing_points[
        ["Open", "High", "Low", "Close"]
    ].round(2)
    return swing_points