import math
import os
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# Safe import TradePlanner dari modul backend
try:
    from engines.trade_planner import TradePlanner
except ImportError:
    TradePlanner = None


# ==============================================================================
# 1. EXTERNAL CSS INJECTOR
# ==============================================================================
def inject_cyberpunk_theme():
    """Membaca file CSS eksternal dari folder assets dan memasangnya ke Streamlit."""
    css_file_path = os.path.join("assets", "style-money-management.css")

    if os.path.exists(css_file_path):
        with open(css_file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(
            f"⚠️ File style `{css_file_path}` tidak ditemukan. Menggunakan tampilan default Streamlit."
        )


# ==============================================================================
# 2. STRATEGY RULES CONSTANTS
# ==============================================================================
PROFILE_RULES = {
    "Scalping / Fast Trade": {
        "max_alloc": 10.0,
        "max_pos": 10,
        "cash_buff": 30.0,
        "desc": "High frequency, holding < 1 hari. Strict risk management.",
    },
    "Swing Trading": {
        "max_alloc": 20.0,
        "max_pos": 5,
        "cash_buff": 15.0,
        "desc": "Sweet spot IDX. Holding period 3 hari - 3 minggu.",
    },
    "Trend Following": {
        "max_alloc": 25.0,
        "max_pos": 4,
        "cash_buff": 10.0,
        "desc": "Riding trend berbulan-bulan hingga tren terkonfirmasi patah.",
    },
    "Investing (Value/Growth)": {
        "max_alloc": 33.0,
        "max_pos": 3,
        "cash_buff": 0.0,
        "desc": "Fokus fundamental & akumulasi posisi secara bertahap.",
    },
}


# ==============================================================================
# 3. HELPER FUNCTIONS
# ==============================================================================
def fetch_trade_plan(full_ticker: str, plan_type: str, clean_ticker: str) -> bool:
    """Mengambil data Trade Plan dari TradePlanner engine backend."""
    if not TradePlanner:
        st.error("[SYS_ERR] Modul `TradePlanner` tidak ditemukan.")
        return False

    try:
        with st.spinner(f"[SYNC] Syncing Trade Plan {full_ticker}..."):
            planner = TradePlanner(ticker=full_ticker)
            planner.fetch_and_prepare_data()
            df_plan = planner.generate_trade_plan()

            matched = df_plan[df_plan["Type"] == plan_type]
            if matched.empty:
                matched = df_plan

            row = matched.iloc[0]

            st.session_state["input_entry_price"] = float(row["Range Buy Min"])
            st.session_state["input_sl_price"] = float(row["Stop Loss"])
            st.session_state["input_tp1_price"] = float(row["TP 1"])
            st.session_state["input_tp2_price"] = float(row["TP 2"])
            st.session_state["last_synced_ticker"] = clean_ticker
            st.session_state["last_synced_type"] = plan_type
            return True
    except Exception as e:
        st.error(f"[SYS_ERR] Gagal sinkronisasi {clean_ticker}: {e}")
        return False


def clear_ticker_callback():
    """Callback untuk mengosongkan input ticker dan session state terkait."""
    st.session_state["mm_raw_ticker_input"] = ""
    st.session_state["selected_watchlist_ticker"] = ""


# ==============================================================================
# 4. MAIN RENDER FUNCTION
# ==============================================================================
def render_page_money_management():
    """Render utama Halaman Money Management."""
    inject_cyberpunk_theme()

    # Header Utama
    st.markdown(
        '<h1 style="color: #FFFFFF !important; font-size: 32px !important; text-shadow: 0 0 10px #00F3FF, 0 0 20px #00F3FF, 0 0 40px #00F3FF !important; margin-bottom: 0px;">⚡ CYBERPUNK MONEY MANAGEMENT ENGINE</h1>', 
        unsafe_allow_html=True
    )
    st.caption("System Execution & Position Sizing Analytics for IDX Trading")
    st.markdown("<br>", unsafe_allow_html=True)

    # Grid Utama
    col_input, col_output = st.columns([1.1, 1.9], gap="large")

    # --------------------------------------------------------------------------
    # KOLOM 1: PARAMETER INPUT CONTROL
    # --------------------------------------------------------------------------
    with col_input:
        st.markdown(
            '<h2 style="color: #FFFFFF !important; font-size: 20px !important; text-shadow: 0 0 8px #00F3FF, 0 0 15px #00F3FF !important; margin-top: 0px;">⚙️ SYSTEM CONTROLS</h2>', 
            unsafe_allow_html=True
        )

        with st.expander("👤 CAPITAL & TRADER PROFILE", expanded=True):
            capital = st.number_input(
                "Total Capital (IDR)",
                min_value=1_000_000,
                value=100_000_000,
                step=5_000_000,
                format="%d",
                key="mm_capital_input",
            )
            trading_style = st.selectbox(
                "Trading Strategy Profile",
                list(PROFILE_RULES.keys()),
                index=1,
                key="mm_style_select",
            )
            risk_pct = st.slider(
                "Max Risk Tolerance per Trade (%)",
                min_value=0.25,
                max_value=10.0,
                value=1.0,
                step=0.25,
                key="mm_risk_slider",
            )

            rule = PROFILE_RULES[trading_style]
            st.caption(f"💡 *{rule['desc']}*")

        with st.expander("📊 TRADE EXECUTION SETUP", expanded=True):
            st.session_state.setdefault("input_entry_price", 125.0)
            st.session_state.setdefault("input_sl_price", 120.0)
            st.session_state.setdefault("input_tp1_price", 151.0)
            st.session_state.setdefault("input_tp2_price", 216.0)

            # Fitur Pilih dari Watchlist (jika ada datanya di session state)
            watchlist_items = st.session_state.get("watchlist_data", [])
            if watchlist_items:
                wl_tickers = ["-- Pilih dari Watchlist --"] + [
                    x.get("Ticker", "").replace(".JK", "") for x in watchlist_items if isinstance(x, dict)
                ]
                selected_from_wl = st.selectbox(
                    "📌 Ambil dari Watchlist",
                    wl_tickers,
                    key="mm_select_from_watchlist"
                )
                if selected_from_wl != "-- Pilih dari Watchlist --":
                    st.session_state["mm_raw_ticker_input"] = selected_from_wl

            # Kolom Ticker Input berdampingan dengan Tombol Clear
            col_tinput, col_tclear = st.columns([3, 1], vertical_alignment="bottom")

            with col_tinput:
                default_ticker_val = st.session_state.get("mm_raw_ticker_input", "")
                ticker_input = st.text_input(
                    "Ticker Code",
                    value=default_ticker_val,
                    key="mm_raw_ticker_input",
                    placeholder="COCO / BBCA",
                ).strip()

            with col_tclear:
                st.button("🧹 Clear", key="btn_clear_ticker", on_click=clear_ticker_callback, use_container_width=True)

            clean_ticker = (
                ticker_input.upper().replace(".JK", "").strip() or "COCO"
            )
            full_ticker = f"{clean_ticker}.JK"

            st.markdown("<p style='font-size: 12px; color: #8d9bb0; margin-bottom: 4px;'>Trade Strategy Type (Checklist)</p>", unsafe_allow_html=True)
            c_chk1, c_chk2 = st.columns(2)
            with c_chk1:
                chk_bow = st.checkbox("BOW (Buy on Weakness)", value=True, key="chk_strat_bow")
            with c_chk2:
                chk_bob = st.checkbox("BOB (Buy on Breakout)", value=False, key="chk_strat_bob")

            # Tentukan tipe plan aktif berdasarkan checkbox
            active_plan_type = "BOW" if chk_bow else ("BOB" if chk_bob else "BOW")

            if st.button("🔄 Sync with Trade Planner", use_container_width=True):
                if fetch_trade_plan(full_ticker, active_plan_type, clean_ticker):
                    st.rerun()

            c_entry, c_sl = st.columns(2)
            with c_entry:
                entry_price = st.number_input(
                    "Entry Price",
                    min_value=1.0,
                    step=1.0,
                    key="input_entry_price",
                )
            with c_sl:
                sl_price = st.number_input(
                    "Stop Loss (SL)",
                    min_value=1.0,
                    step=1.0,
                    key="input_sl_price",
                )

            c_tp1, c_tp2 = st.columns(2)
            with c_tp1:
                tp1_price = st.number_input(
                    "Target Price 1",
                    min_value=1.0,
                    step=1.0,
                    key="input_tp1_price",
                )
            with c_tp2:
                tp2_price = st.number_input(
                    "Target Price 2",
                    min_value=1.0,
                    step=1.0,
                    key="input_tp2_price",
                )

        with st.expander("🛠️ BROKERAGE FEES", expanded=False):
            fee_buy = (
                st.number_input(
                    "Buy Fee (%)",
                    min_value=0.0,
                    value=0.15,
                    step=0.01,
                    key="mm_fee_buy",
                )
                / 100
            )
            fee_sell = (
                st.number_input(
                    "Sell Fee (%)",
                    min_value=0.0,
                    value=0.25,
                    step=0.01,
                    key="mm_fee_sell",
                )
                / 100
            )

    # --------------------------------------------------------------------------
    # KOLOM 2: ANALYTICS OUTPUT
    # --------------------------------------------------------------------------
    with col_output:
        c_title, c_btn = st.columns([2.5, 1], vertical_alignment="center")
        with c_title:
            st.markdown(
                '<h2 style="color: #FFFFFF !important; font-size: 20px !important; text-shadow: 0 0 8px #00F3FF, 0 0 15px #00F3FF !important; margin: 0;">🎯 POSITION SIZING ANALYTICS</h2>', 
                unsafe_allow_html=True
            )

        # Validasi Input Logic
        if sl_price >= entry_price:
            st.error(
                "❌ [LOGIC ERROR] Stop Loss (SL) harus LEBIH KECIL dari Harga Entry!"
            )
            return

        # Core Calculation Engine
        max_risk_allowed_idr = capital * (risk_pct / 100)
        risk_per_share_raw = entry_price - sl_price
        total_risk_per_share_with_fee = (entry_price * (1 + fee_buy)) - (
            sl_price * (1 - fee_sell)
        )

        raw_shares_by_risk = (
            max_risk_allowed_idr / total_risk_per_share_with_fee
        )
        lot_by_risk = math.floor(raw_shares_by_risk / 100)

        max_alloc_pct = rule["max_alloc"]
        max_capital_allowed = capital * (max_alloc_pct / 100)
        lot_by_cap = math.floor(
            max_capital_allowed / (entry_price * 100 * (1 + fee_buy))
        )

        final_lot = min(lot_by_risk, lot_by_cap)
        final_shares = final_lot * 100
        total_buy_value = final_shares * entry_price
        total_cost_with_fee = total_buy_value * (1 + fee_buy)

        actual_risk_idr = (
            (final_shares * entry_price * (1 + fee_buy))
            - (final_shares * sl_price * (1 - fee_sell))
            if final_lot > 0
            else 0.0
        )
        actual_risk_pct = (
            (actual_risk_idr / capital) * 100 if capital > 0 else 0.0
        )

        reward_tp1 = tp1_price - entry_price
        rrr_tp1 = (
            reward_tp1 / risk_per_share_raw if risk_per_share_raw > 0 else 0
        )
        is_capped = (lot_by_cap < lot_by_risk) and (lot_by_risk > 0)

        # Teks untuk fitur Copy MM Plan
        strategies_active = []
        if chk_bow: strategies_active.append("BOW")
        if chk_bob: strategies_active.append("BOB")
        strat_str = " & ".join(strategies_active) if strategies_active else active_plan_type

        mm_copyable_text = f"""=== MONEY MANAGEMENT PLAN: {clean_ticker} ===
Strategy: {strat_str} | Profile: {trading_style}
Capital: Rp {capital:,.0f}
Entry Price: Rp {entry_price:,.0f}
Stop Loss: Rp {sl_price:,.0f}
Target 1: Rp {tp1_price:,.0f}
Target 2: Rp {tp2_price:,.0f}
----------------------------------------
Recommended Size: {final_lot:,} Lot ({final_shares:,} Lembar)
Total Buy Value: Rp {total_buy_value:,.0f} ({(total_buy_value/capital)*100:.1f}%)
Risk/Reward Ratio: 1 : {rrr_tp1:.2f}
========================================"""

        with c_btn:
            btn_id_mm = "copy_btn_money_management"
            copy_mm_html = f"""
            <div style="display: flex; justify-content: flex-end; align-items: center;">
                <button id="{btn_id_mm}" style="background: linear-gradient(135deg, #A855F7 0%, #00F0FF 100%); color: #050811; border: none; padding: 6px 12px; border-radius: 4px; font-weight: 800; font-size: 11px; cursor: pointer; box-shadow: 0 0 8px rgba(0, 240, 255, 0.4); transition: all 0.2s;">
                    📋 COPY PLAN
                </button>
            </div>
            <script>
            const textToCopy_{btn_id_mm} = `{mm_copyable_text}`;
            const btn_{btn_id_mm} = document.getElementById("{btn_id_mm}");
            btn_{btn_id_mm}.onclick = function() {{
                navigator.clipboard.writeText(textToCopy_{btn_id_mm}).then(function() {{
                    btn_{btn_id_mm}.innerText = "✅ COPIED!";
                    btn_{btn_id_mm}.style.background = "#00FF66";
                    setTimeout(function() {{
                        btn_{btn_id_mm}.innerText = "📋 COPY PLAN";
                        btn_{btn_id_mm}.style.background = "linear-gradient(135deg, #A855F7 0%, #00F0FF 100%)";
                    }}, 2000);
                }}).catch(function(err) {{
                    console.error('Gagal menyalin text: ', err);
                }});
            }};
            </script>
            """
            components.html(copy_mm_html, height=35)

        # 3 Card Neon Display
        m1, m2, m3 = st.columns(3)

        with m1:
            st.markdown(
                f"""
                <div class="cyber-card">
                    <div class="cyber-label">RECOMMENDED SIZE</div>
                    <div class="cyber-value">{final_lot:,} LOT</div>
                    <div style="font-size: 11px; color: #8d9bb0;">({final_shares:,} Lembar)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m2:
            st.markdown(
                f"""
                <div class="cyber-card">
                    <div class="cyber-label">TOTAL BUY VALUE</div>
                    <div class="cyber-value" style="color:#ffffff;">Rp {total_buy_value:,.0f}</div>
                    <div style="font-size: 11px; color: #8d9bb0;">Alloc: {(total_buy_value/capital)*100:.1f}% Modal</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m3:
            if rrr_tp1 >= 2.0:
                rrr_badge = (
                    '<span class="cyber-badge badge-cyan">EXCELLENT</span>'
                )
            elif rrr_tp1 >= 1.5:
                rrr_badge = (
                    '<span class="cyber-badge badge-yellow">ACCEPTABLE</span>'
                )
            else:
                rrr_badge = (
                    '<span class="cyber-badge badge-pink">POOR RISK</span>'
                )

            st.markdown(
                f"""
                <div class="cyber-card">
                    <div class="cyber-label">RISK / REWARD</div>
                    <div class="cyber-value" style="color:#ffe600;">1 : {rrr_tp1:.2f}</div>
                    <div>{rrr_badge}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if is_capped:
            st.warning(
                f"⚠️ **CAP ALERT:** Toleransi risk mengizinkan **{lot_by_risk:,} Lot**, "
                f"namun dibatasi max **{final_lot:,} Lot** sesuai profil {trading_style} ({max_alloc_pct}%)."
            )

        # Partial Profit Taking Execution Plan
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<h2 style="color: #FFFFFF !important; font-size: 20px !important; text-shadow: 0 0 8px #00F3FF, 0 0 15px #00F3FF !important;">✂️ PARTIAL PROFIT TAKING PLAN</h2>', 
            unsafe_allow_html=True
        )

        lot_tp1 = math.floor(final_lot * 0.5)
        lot_tp2 = final_lot - lot_tp1

        p_tp1 = (lot_tp1 * 100 * tp1_price) * (1 - fee_sell) - (
            lot_tp1 * 100 * entry_price * (1 + fee_buy)
        )
        p_tp2 = (lot_tp2 * 100 * tp2_price) * (1 - fee_sell) - (
            lot_tp2 * 100 * entry_price * (1 + fee_buy)
        )
        total_potential_profit = p_tp1 + p_tp2

        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(
                f"""
                <div class="cyber-card">
                    <h4 style="margin:0; color:#00f3ff; font-size:14px;">TAHAP 1: SELL 50% @ TP1</h4>
                    <p style="margin:6px 0; font-size:13px; color:#ffffff;">Jual <b>{lot_tp1:,} Lot</b> @ <b>Rp {tp1_price:,.0f}</b></p>
                    <p style="margin:0; font-size:12px; color:#8d9bb0;">Est. Profit: <b style="color:#00ff66;">+Rp {p_tp1:,.0f}</b></p>
                    <hr style="margin:10px 0; border-color:#1e2638;">
                    <span style="font-size:11px; color:#ffe600;">📌 Action: Set Break-Even SL @ Rp {entry_price:,.0f}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with sc2:
            st.markdown(
                f"""
                <div class="cyber-card">
                    <h4 style="margin:0; color:#00f3ff; font-size:14px;">TAHAP 2: SELL 50% @ TP2</h4>
                    <p style="margin:6px 0; font-size:13px; color:#ffffff;">Jual <b>{lot_tp2:,} Lot</b> @ <b>Rp {tp2_price:,.0f}</b></p>
                    <p style="margin:0; font-size:12px; color:#8d9bb0;">Est. Profit: <b style="color:#00ff66;">+Rp {p_tp2:,.0f}</b></p>
                    <hr style="margin:10px 0; border-color:#1e2638;">
                    <span style="font-size:11px; color:#00f3ff;">💰 Total Potential: <b style="color:#00ff66;">+Rp {total_potential_profit:,.0f}</b></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Plotly Visualizers
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<h2 style="color: #FFFFFF !important; font-size: 20px !important; text-shadow: 0 0 8px #00F3FF, 0 0 15px #00F3FF !important;">📈 RISK VISUALIZER & EXPOSURE</h2>', 
            unsafe_allow_html=True
        )

        v1, v2 = st.columns(2)

        with v1:
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=actual_risk_pct,
                    number={"suffix": "%", "font": {"color": "#00f3ff"}},
                    domain={"x": [0, 1], "y": [0, 1]},
                    gauge={
                        "axis": {"range": [0, max(10.0, risk_pct * 1.5)]},
                        "bar": {
                            "color": (
                                "#00f3ff"
                                if actual_risk_pct <= risk_pct
                                else "#ff0055"
                            )
                        },
                        "steps": [
                            {"range": [0, risk_pct], "color": "#0d111a"},
                            {"range": [risk_pct, 10.0], "color": "#1c0812"},
                        ],
                    },
                )
            )
            fig_gauge.update_layout(
                height=180,
                margin=dict(l=20, r=20, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#ffffff"},
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        with v2:
            cash_left = max(0.0, capital - total_cost_with_fee)
            fig_donut = go.Figure(
                data=[
                    go.Pie(
                        labels=[f"Posisi {clean_ticker}", "Cash"],
                        values=[total_cost_with_fee, cash_left],
                        hole=0.6,
                        marker_colors=["#00f3ff", "#1e2638"],
                    )
                ]
            )
            fig_donut.update_layout(
                height=180,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#ffffff"},
                showlegend=False,
            )
            st.plotly_chart(fig_donut, use_container_width=True)
