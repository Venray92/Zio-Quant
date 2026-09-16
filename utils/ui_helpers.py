return []


def _safe_get_method_or_attr(obj, possible_names):
    """Helper internal untuk mengambil data dari objek TradePlanner secara fleksibel."""
    for name in possible_names:
        if hasattr(obj, name):
            attr = getattr(obj, name)
            if callable(attr):
                try:
                    return attr()
                except Exception:
                    continue
            return attr
    return None


def render_inline_trade_planner(ticker_symbol, key_suffix):
"""Helper function untuk merender detail Trade Planner di bawah tabel."""
st.markdown("---")
@@ -123,53 +137,66 @@ def render_inline_trade_planner(ticker_symbol, key_suffix):
planner = TradePlanner(
ticker=ticker_symbol.upper(), period=period_selected
)
            planner.fetch_and_prepare_data()
            
            # Fetch & prepare data
            if hasattr(planner, "fetch_and_prepare_data"):
                planner.fetch_and_prepare_data()

# 1. Direction Market
st.markdown("#### 📌 Direction Market")
            df_dir = planner.get_direction()
            st.dataframe(df_dir, use_container_width=True)

            if not df_dir.empty and "Direction" in df_dir.columns:
                direction_val = df_dir["Direction"].iloc[0]
                if direction_val == "BOB":
                    st.success("Analisis Arah: **BOB (Breakout Buy)**")
                else:
                    st.info("Analisis Arah: **BOW (Buy on Weakness)**")
            df_dir = _safe_get_method_or_attr(planner, ["get_direction", "direction"])
            if df_dir is not None:
                st.dataframe(df_dir, use_container_width=True)
                if hasattr(df_dir, "columns") and "Direction" in df_dir.columns and len(df_dir) > 0:
                    direction_val = df_dir["Direction"].iloc[0]
                    if direction_val == "BOB":
                        st.success("Analisis Arah: **BOB (Breakout Buy)**")
                    else:
                        st.info("Analisis Arah: **BOW (Buy on Weakness)**")

# 2. Strategy Trade Plan
st.markdown("#### 🎯 Trade Plan Recommendation")
            df_plan = planner.generate_trade_plan()
            st.dataframe(df_plan, use_container_width=True)

            # SAFE CHECKING: Mencegah KeyError jika kolom 'Status Candle' / 'Warning' tidak ada
            if not df_plan.empty:
                warning_msg = df_plan["Warning"].iloc[0] if "Warning" in df_plan.columns else "-"
                candle_type = df_plan["Status Candle"].iloc[0] if "Status Candle" in df_plan.columns else "-"
                
                if candle_type != "-" or warning_msg != "-":
                    st.warning(
                        f"**Pola Candle Terdeteksi:** {candle_type} — {warning_msg}"
                    )

            # 3. Support & Resistance Levels
            df_plan = _safe_get_method_or_attr(planner, ["generate_trade_plan", "get_trade_plan"])
            if df_plan is not None:
                st.dataframe(df_plan, use_container_width=True)

                if hasattr(df_plan, "columns") and len(df_plan) > 0:
                    warning_msg = df_plan["Warning"].iloc[0] if "Warning" in df_plan.columns else "-"
                    candle_type = df_plan["Status Candle"].iloc[0] if "Status Candle" in df_plan.columns else "-"
                    
                    if candle_type != "-" or warning_msg != "-":
                        st.warning(
                            f"**Pola Candle Terdeteksi:** {candle_type} — {warning_msg}"
                        )

            # 3. Support & Resistance Levels (Dilengkapi Safe Fallback)
            df_sup = _safe_get_method_or_attr(
                planner, ["get_strong_support", "get_support_levels", "get_support", "support_levels"]
            )
            df_res = _safe_get_method_or_attr(
                planner, ["get_strong_resistance", "get_resistance_levels", "get_resistance", "resistance_levels"]
            )

col_sup, col_res = st.columns(2)
with col_sup:
st.markdown("#### 🛡️ Support Levels")
                st.dataframe(
                    planner.get_strong_support(), use_container_width=True
                )
                if df_sup is not None:
                    st.dataframe(df_sup, use_container_width=True)
                else:
                    st.caption("Data support tidak tersedia.")

with col_res:
st.markdown("#### 🧱 Resistance Levels")
                st.dataframe(
                    planner.get_strong_resistance(), use_container_width=True
                )
                if df_res is not None:
                    st.dataframe(df_res, use_container_width=True)
                else:
                    st.caption("Data resistance tidak tersedia.")

# 4. Swing Points
            st.markdown("#### 📍 Swing Points & Metpoints")
            st.dataframe(
                planner.get_swing_points(), use_container_width=True
            )
            df_swing = _safe_get_method_or_attr(planner, ["get_swing_points", "swing_points"])
            if df_swing is not None:
                st.markdown("#### 📍 Swing Points & Metpoints")
                st.dataframe(df_swing, use_container_width=True)

except Exception as e:
st.error(f"Gagal memuat Trade Plan untuk {ticker_symbol}: {e}")
