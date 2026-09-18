import concurrent.futures
import json
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from engines.trade_planner import TradePlanner


def load_daftar_saham(filename=os.path.join("data", "daftar_saham.txt")):
    """Reads ticker list from file inside data folder or fallback to root."""
    target_path = filename
    
    if not os.path.exists(target_path):
        alt_path = os.path.basename(filename)
        if os.path.exists(alt_path):
            target_path = alt_path
        else:
            return []

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        tickers = [
            line.strip().upper()
            for line in lines
            if line.strip() and not line.startswith("#")
        ]
        return tickers
    except Exception:
        return []


def process_single_ticker(ticker_code: str):
    """Single ticker execution processor: mengembalikan seluruh DataFrame plan (BOW & BOB) beserta rekomendasi direction."""
    symbol = ticker_code.strip().upper()
    if not symbol.endswith(".JK"):
        symbol += ".JK"

    try:
        planner = TradePlanner(symbol, period="6mo")
        planner.fetch_and_prepare_data()

        df_dir = planner.get_direction()
        df_plan = planner.generate_trade_plan()

        if df_dir is None or df_plan is None or df_dir.empty or df_plan.empty:
            return None

        curr_close = int(df_dir.iloc[0]["Last Close Market"])
        suggested_dir = df_dir.iloc[0]["Direction"] # 'BOW' atau 'BOB'

        processed_plans = []
        for idx, p in df_plan.iterrows():
            plan_type = str(p["Type"])
            
            buy_min = float(p["Range Buy Min"])
            stop_loss = float(p["Stop Loss"])
            tp1 = float(p["TP 1"])
            tp2 = float(p["TP 2"])

            risk = buy_min - stop_loss
            reward_tp1 = tp1 - buy_min
            rr_val = round(reward_tp1 / risk, 1) if risk > 0 else 0.0

            entry_mid = (p["Range Buy Min"] + p["Range Buy Max"]) / 2.0
            pot_gain_tp1 = round(((tp1 - entry_mid) / entry_mid) * 100, 1) if entry_mid > 0 else 0
            pot_gain_tp2 = round(((tp2 - entry_mid) / entry_mid) * 100, 1) if entry_mid > 0 else 0
            
            pot_risk = round(((entry_mid - stop_loss) / entry_mid) * 100, 1) if entry_mid > 0 else 0

            processed_plans.append({
                "Symbol": symbol.replace(".JK", ""),
                "Score": int(p["Score"]) if pd.notnull(p["Score"]) else 0,
                "Grade": str(p["Grade"]),
                "Strategy": plan_type,
                "Suggested Strategy": suggested_dir,
                "Last Price": curr_close,
                "Zone Position": str(p["Posisi Harga"]),
                "Buy Range": str(p["Area Buy"]),
                "Stop Loss (SL)": int(stop_loss) if pd.notnull(stop_loss) else 0,
                "TP 1": int(tp1) if pd.notnull(tp1) else 0,
                "TP 2": int(tp2) if pd.notnull(tp2) else 0,
                "Potential Gain": f"+{pot_gain_tp1}%",
                "Potential Gain TP2": f"+{pot_gain_tp2}%",
                "SL Risk": f"-{pot_risk}%",
                "Risk-Reward Ratio": f"1 : {rr_val}",
                "RR_Val": float(rr_val),
                "Candlestick Pattern": str(p["Pola Candle"]),
                "Analysis & Risk Warning": str(p["Warning"]),
            })

        return processed_plans
    except Exception:
        return None


def run_batch_execution(ticker_list, cache_key):
    """Multi-threaded execution runner with safe main-thread UI updates."""
    total_saham = len(ticker_list)
    if total_saham == 0:
        st.warning("⚠️ Ticker list is empty!")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    all_results = []
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ticker = {
            executor.submit(process_single_ticker, t): t for t in ticker_list
        }

        for future in concurrent.futures.as_completed(future_to_ticker):
            res_list = future.result()
            if res_list:
                all_results.extend(res_list)

            completed += 1
            percent = completed / total_saham
            progress_bar.progress(percent)
            status_text.markdown(
                f"⏳ **Analyzing stocks:** `{completed}/{total_saham}` processed ({int(percent * 100)}%)"
            )

    progress_bar.empty()
    status_text.empty()
    st.toast(
        f"Analysis Complete: Analyzed {len(set(r['Symbol'] for r in all_results))} stocks!",
        icon="✅",
    )

    if all_results:
        df_res = pd.DataFrame(all_results)
        st.session_state[cache_key] = df_res


def reset_filters():
    """Callback function to reset filter choices to defaults."""
    st.session_state["f_strategi"] = "ALL STRATEGIES"
    st.session_state["f_grade"] = "ALL GRADES"
    st.session_state["f_zone"] = "ALL POSITIONS"
    st.session_state["f_rr"] = "ALL RATIOS"
    st.session_state["f_candle"] = "ALL CANDLES"


def clear_cache(cache_key):
    """Clear specific cache mode."""
    st.session_state.pop(cache_key, None)
    st.toast("Data Cache Cleared", icon="🧹")


def add_tickers_to_watchlist(symbols_list):
    storage_file = "watchlist_storage.json"
    try:
        watchlist_data = []
        if os.path.exists(storage_file):
            try:
                with open(storage_file, "r", encoding="utf-8") as f:
                    watchlist_data = json.load(f)
            except Exception:
                watchlist_data = []
        
        existing_tickers = set()
        for item in watchlist_data:
            if isinstance(item, str):
                existing_tickers.add(item.upper())
            elif isinstance(item, dict):
                t = item.get("Ticker", "")
                if t:
                    existing_tickers.add(t.upper())
        
        added_count = 0
        active_screener_name = st.session_state.get("active_screener_name", "Trade Planner Screener")

        for sym in symbols_list:
            clean_sym = sym.strip().upper()
            formatted = clean_sym if clean_sym.endswith(".JK") else f"{clean_sym}.JK"
            
            if formatted not in existing_tickers and clean_sym not in existing_tickers:
                new_item = {
                    "Ticker": formatted,
                    "Notes": active_screener_name,
                    "Target Price": 0
                }
                watchlist_data.append(new_item)
                
                if "watchlist" in st.session_state and isinstance(st.session_state["watchlist"], list):
                    st.session_state["watchlist"].append(new_item)
                if "watchlist_data" in st.session_state and isinstance(st.session_state["watchlist_data"], list):
                    st.session_state["watchlist_data"].append(new_item)

                existing_tickers.add(formatted)
                existing_tickers.add(clean_sym)
                added_count += 1
        
        if added_count > 0:
            with open(storage_file, "w", encoding="utf-8") as f:
                json.dump(watchlist_data, f, indent=4)
            st.toast(f"Berhasil menambahkan {added_count} saham ke Watchlist!", icon="⭐")
        else:
            st.toast("Saham terpilih sudah ada di dalam Watchlist.", icon="ℹ️")
            
    except Exception as e:
        st.error(f"Gagal menyimpan ke watchlist: {e}")


def draw_card(title, value, subtext, badge_text="", variant="blue", value_color="blue"):
    """Reusable Dashboard Card Component."""
    badge_html = (
        f'<span class="card-badge badge-{variant}">{badge_text}</span>'
        if badge_text
        else ""
    )

    card_html = f"""
    <div class="card card-{variant}">
        <div class="card-header">
            <span class="card-title title-{variant}">{title}</span>
            {badge_html}
        </div>
        <div class="card-value val-{value_color}">{value}</div>
        <p class="card-subtext">{subtext}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_trade_plan_cards(df_data, is_title_needed=True, is_single_mode=False):
    """Renders Trade Plan Cards for given stocks Dataframe dengan pilihan dropdown strategi rapi di kiri."""
    if is_title_needed:
        st.markdown(
            f"""
            <h3 class="glow-title">
                <span class="cyan-dot"></span>Trade Plans 
                <span style='font-size:0.9rem; color:#94a3b8;'>({len(df_data['Symbol'].unique())} items)</span>
            </h3>
            """,
            unsafe_allow_html=True,
        )

    symbols = df_data["Symbol"].unique()

    for sym in symbols:
        df_sym = df_data[df_data["Symbol"] == sym]
        
        strategies = df_sym["Strategy"].tolist() if "Strategy" in df_sym.columns else ["BOW"]
        suggested_strat = df_sym["Suggested Strategy"].iloc[0] if "Suggested Strategy" in df_sym.columns else strategies[0]
        
        selected_strat = suggested_strat
        if len(strategies) > 1:
            st.write("")
            
            label_map = {
                "BOW": "Buy On Weakness",
                "BOB": "Buy On Breakout"
            }
            reverse_map = {v: k for k, v in label_map.items()}
            
            display_options = [label_map.get(s, s) for s in strategies]
            default_display = label_map.get(suggested_strat, display_options[0])
            default_idx = display_options.index(default_display) if default_display in display_options else 0
            
            if is_single_mode:
                col_drop, col_space, col_c, col_w, col_cl = st.columns([1.5, 1.2, 0.8, 0.8, 0.8], vertical_alignment="bottom")
            else:
                col_drop, col_space, col_c, col_w = st.columns([1.5, 1.4, 1.0, 1.0], vertical_alignment="bottom")

            with col_drop:
                st.markdown(
                    """
                    <div style="font-weight: 700; color: #00F3FF; font-size: 0.85rem; margin-bottom: 2px;">
                        Pilih Strategi:
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                chosen_display = st.selectbox(
                    "Strategy",
                    options=display_options,
                    index=default_idx,
                    key=f"strat_select_{sym}",
                    label_visibility="collapsed"
                )
            selected_strat = reverse_map.get(chosen_display, chosen_display)

            row = df_sym[df_sym["Strategy"] == selected_strat].iloc[0] if not df_sym[df_sym["Strategy"] == selected_strat].empty else df_sym.iloc[0]
        else:
            row = df_sym.iloc[0]
            if is_single_mode:
                col_drop_dummy, col_space, col_c, col_w, col_cl = st.columns([1.5, 1.2, 0.8, 0.8, 0.8], vertical_alignment="bottom")
            else:
                col_drop_dummy, col_space, col_c, col_w = st.columns([1.5, 1.4, 1.0, 1.0], vertical_alignment="bottom")

            with col_drop_dummy:
                label_map = {"BOW": "Buy On Weakness", "BOB": "Buy On Breakout"}
                strat_code = str(row.get("Strategy", "BOW"))
                st.markdown(
                    f"""
                    <div style="font-weight: 700; color: #00F3FF; font-size: 0.85rem; margin-bottom: 2px;">
                        Pilih Strategi:
                    </div>
                    <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 6px 10px; color: #cbd5e1; font-size: 0.9rem;">
                        {label_map.get(strat_code, strat_code)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        p_gain_tp2 = row.get("Potential Gain TP2", "+0%")
        sl_risk_val = row.get("SL Risk", "-0%")
        tp1_val = row.get("TP 1", 0)
        tp2_val = row.get("TP 2", 0)
        sl_val = row.get("Stop Loss (SL)", 0)
        score_val = row.get("Score", 0)
        grade_val = row.get("Grade", "N/A")
        last_price_val = row.get("Last Price", 0)
        buy_range_val = row.get("Buy Range", "-")
        zone_pos_val = row.get("Zone Position", "-")
        rr_ratio_val = row.get("Risk-Reward Ratio", "1 : 0")
        candle_val = row.get("Candlestick Pattern", "-")
        warning_val = row.get("Analysis & Risk Warning", "-")
        strat_code_val = row.get("Strategy", "BOW")

        copyable_text = f"""=== TRADE PLAN: {sym} ===
Strategy: {strat_code_val}
Grade: {grade_val}
Score: {score_val}/100
Last Price: Rp {last_price_val:,}
Buy Range: {buy_range_val}
Stop Loss: Rp {sl_val:,}
Target 1 (TP1): Rp {tp1_val:,}
Target 2 (TP2): Rp {tp2_val:,}
Zone Position: {zone_pos_val}
Risk-Reward: {rr_ratio_val}
==============================="""

        unique_btn_id = f"copy_btn_tp_{sym}_{strat_code_val}"

        with col_c:
            copy_html = f"""
            <button id="{unique_btn_id}" style="width: 100%; background: linear-gradient(135deg, #A855F7 0%, #00F0FF 100%); color: #050811; border: none; padding: 7px 8px; border-radius: 6px; font-weight: 800; font-size: 11px; cursor: pointer; box-shadow: 0 0 8px rgba(0, 240, 255, 0.4); transition: all 0.2s;">
                📋 Copy
            </button>
            <script>
            const textToCopy_{unique_btn_id} = `{copyable_text}`;
            const btn_{unique_btn_id} = document.getElementById("{unique_btn_id}");
            btn_{unique_btn_id}.onclick = function() {{
                navigator.clipboard.writeText(textToCopy_{unique_btn_id}).then(function() {{
                    btn_{unique_btn_id}.innerText = "✅ Copied";
                    btn_{unique_btn_id}.style.background = "#00FF66";
                    setTimeout(function() {{
                        btn_{unique_btn_id}.innerText = "📋 Copy";
                        btn_{unique_btn_id}.style.background = "linear-gradient(135deg, #A855F7 0%, #00F0FF 100%)";
                    }}, 2000);
                }}).catch(function(err) {{
                    console.error('Gagal menyalin text: ', err);
                }});
            }};
            </script>
            """
            components.html(copy_html, height=36)

        with col_w:
            if st.button("⭐ Watchlist", key=f"btn_wl_{sym}_{strat_code_val}", use_container_width=True):
                add_tickers_to_watchlist([sym])

        if is_single_mode:
            with col_cl:
                if st.button("🗑️ Clear", key=f"btn_clr_{sym}", use_container_width=True):
                    st.session_state.pop("df_screener_single", None)
                    st.rerun()

        strat_display_name = "Buy On Weakness" if strat_code_val == "BOW" else ("Buy On Breakout" if strat_code_val == "BOB" else strat_code_val)
        is_suggestion = " (Suggestion)" if strat_code_val == row.get("Suggested Strategy") else ""

        st.markdown(
            f"""
            <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 14px 20px; margin-top: 10px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                    <span style="font-size: 1.4rem; font-weight: 800; color: #00F3FF;">{sym}</span>
                    <span style="background: #1e293b; color: #cbd5e1; border: 1px solid #334155; padding: 3px 10px; font-size: 0.8rem; font-weight: 600; border-radius: 4px;">Strategy: {strat_display_name}{is_suggestion}</span>
                    <span style="background: #451a03; color: #fcd34d; border: 1px solid #78350f; padding: 3px 10px; font-size: 0.8rem; font-weight: 600; border-radius: 4px;">Grade: {grade_val}</span>
                    <span style="background: #0c4a6e; color: #38bdf8; border: 1px solid #0284c7; padding: 3px 10px; font-size: 0.8rem; font-weight: 600; border-radius: 4px;">Score: {score_val}/100</span>
                </div>
                <div style="color: #94a3b8; font-size: 0.9rem;">
                    Last Price: <strong style="color: #00F3FF; font-size: 1.1rem;">Rp {last_price_val:,}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            draw_card(
                title="BUY RANGE / ENTRY ZONE",
                value=str(buy_range_val),
                subtext=f"Status: {zone_pos_val}",
                badge_text=str(zone_pos_val),
                variant="blue",
                value_color="blue",
            )
            draw_card(
                title="TARGET 1 (TP 1)",
                value=f"Rp {tp1_val:,}",
                subtext="Initial profit target / partial exit.",
                badge_text=str(row.get("Potential Gain", "+0%")),
                variant="green",
                value_color="green",
            )

        with col2:
            draw_card(
                title="STOP LOSS (SL)",
                value=f"Rp {sl_val:,}",
                subtext="Risk management limit.",
                badge_text=str(sl_risk_val),
                variant="red",
                value_color="red",
            )
            draw_card(
                title="TARGET 2 (TP 2)",
                value=f"Rp {tp2_val:,}",
                subtext="Main swing target zone.",
                badge_text=str(p_gain_tp2),
                variant="blue",
                value_color="blue",
            )

        st.markdown(
            f"""
            <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 14px 18px; margin-bottom: 28px; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
                <div>
                    <span style="font-size: 0.75rem; color: #64748b; display: block; font-weight: 600;">RISK : REWARD</span>
                    <span style="font-size: 0.95rem; color: #f8fafc; font-weight: 700;">{rr_ratio_val}</span>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #64748b; display: block; font-weight: 600;">CANDLESTICK PATTERN</span>
                    <span style="font-size: 0.95rem; color: #f8fafc; font-weight: 700;">{candle_val}</span>
                </div>
                <div style="grid-column: span 2;">
                    <span style="font-size: 0.75rem; color: #64748b; display: block; font-weight: 600;">ANALYSIS & WARNING</span>
                    <span style="font-size: 0.88rem; color: #ef4444; font-weight: 600;">{warning_val}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_tab_trade_planner():
    # 🎨 CUSTOM CSS STYLING
    st.markdown(
        """
        <style>
        @keyframes pulseGlow {
            0% { opacity: 0.3; box-shadow: 0 0 4px #00F3FF, 0 0 8px #00F3FF; transform: scale(0.9); }
            50% { opacity: 1; box-shadow: 0 0 12px #00F3FF, 0 0 22px #00F3FF, 0 0 32px #10b981; transform: scale(1.15); }
            100% { opacity: 0.3; box-shadow: 0 0 4px #00F3FF, 0 0 8px #00F3FF; transform: scale(0.9); }
        }

        .header-banner {
            border: 1px solid #00F3FF;
            box-shadow: 0 0 14px rgba(0, 243, 255, 0.4), inset 0 0 14px rgba(0, 243, 255, 0.15);
            border-radius: 8px;
            padding: 12px 24px;
            margin-bottom: 24px;
            background: #0d1117;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 6px;
            text-align: center;
            width: 100%;
        }

        .top-glowing-dot {
            width: 10px;
            height: 10px;
            background-color: #00F3FF;
            border-radius: 50%;
            animation: pulseGlow 2.5s infinite ease-in-out;
        }

        .header-banner h1 {
            margin: 0;
            font-size: 1.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00F3FF 0%, #10b981 50%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 8px rgba(0, 243, 255, 0.5));
            line-height: 1.2;
        }

        .glow-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 800;
            font-size: 1.3rem;
            background: linear-gradient(90deg, #00F3FF 0%, #10b981 60%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 5px rgba(0, 243, 255, 0.4));
            margin-top: 10px;
            margin-bottom: 10px;
        }

        .cyan-dot {
            width: 10px;
            height: 10px;
            background-color: #00F3FF;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px #00F3FF, 0 0 12px #00F3FF;
            flex-shrink: 0;
        }

        div.stButton > button {
            border: 1px solid #00F3FF !important;
            box-shadow: 0 0 8px rgba(0, 243, 255, 0.3) !important;
            border-radius: 6px !important;
            transition: all 0.25s ease-in-out !important;
        }

        div.stButton > button[data-testid="stBaseButton-primary"] {
            background: linear-gradient(135deg, #00b4d8 0%, #00f3ff 100%) !important;
            color: #020617 !important;
            font-weight: 700 !important;
            border: 1px solid #00F3FF !important;
            box-shadow: 0 0 12px rgba(0, 243, 255, 0.6) !important;
        }

        div.stButton > button[data-testid="stBaseButton-primary"]:hover {
            background: linear-gradient(135deg, #00f3ff 0%, #10b981 100%) !important;
            color: #000000 !important;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.9), 0 0 10px rgba(16, 185, 129, 0.8) !important;
        }

        div.stButton > button:hover {
            border-color: #00F3FF !important;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.8) !important;
        }

        .card {
            background-color: #0f172a;
            border-radius: 6px;
            padding: 16px 18px;
            margin-bottom: 14px;
        }
        .card-blue { border: 1px solid #0284c7; }
        .card-red { border: 1px solid #dc2626; }
        .card-green { border: 1px solid #059669; }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .card-title {
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .title-blue { color: #38bdf8; }
        .title-red { color: #f87171; }
        .title-green { color: #34d399; }

        .card-badge {
            font-size: 0.7rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
        }
        .badge-blue { background: #0c4a6e; color: #7dd3fc; }
        .badge-red { background: #450a0a; color: #fca5a5; }
        .badge-green { background: #064e3b; color: #6ee7b7; }

        .card-value {
            font-size: 1.4rem;
            font-weight: 800;
            margin-bottom: 4px;
            line-height: 1.2;
        }
        .val-blue { color: #38bdf8; }
        .val-red { color: #f87171; }
        .val-green { color: #34d399; }

        .card-subtext {
            font-size: 0.78rem;
            color: #94a3b8;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- BANNER HEADER ---
    st.markdown(
        """
        <div class="header-banner">
            <div class="top-glowing-dot"></div>
            <h1>Stock Trade Planner</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "screener_mode" not in st.session_state:
        st.session_state["screener_mode"] = "single"
    if "f_strategi" not in st.session_state:
        st.session_state["f_strategi"] = "ALL STRATEGIES"
    if "f_grade" not in st.session_state:
        st.session_state["f_grade"] = "ALL GRADES"
    if "f_zone" not in st.session_state:
        st.session_state["f_zone"] = "ALL POSITIONS"
    if "f_rr" not in st.session_state:
        st.session_state["f_rr"] = "ALL RATIOS"
    if "f_candle" not in st.session_state:
        st.session_state["f_candle"] = "ALL CANDLES"

    st.markdown(
        """
        <div class="glow-title">
            <span class="cyan-dot"></span>Select Execution Mode
        </div>
        """,
        unsafe_allow_html=True,
    )

    mode_col1, mode_col2 = st.columns(2)
    current_mode = st.session_state["screener_mode"]

    with mode_col1:
        is_single = current_mode == "single"
        btn_type_single = "primary" if is_single else "secondary"
        if st.button(
            "Single Ticker Analysis",
            use_container_width=True,
            type=btn_type_single,
            key="btn_card_single",
        ):
            if st.session_state["screener_mode"] != "single":
                st.session_state["screener_mode"] = "single"
            st.rerun()

    with mode_col2:
        is_batch = current_mode == "batch"
        btn_type_batch = "primary" if is_batch else "secondary"
        if st.button(
            "Batch Screener Analysis",
            use_container_width=True,
            type=btn_type_batch,
            key="btn_card_batch",
        ):
            if st.session_state["screener_mode"] != "batch":
                st.session_state["screener_mode"] = "batch"
            st.rerun()

    st.write("")

    if st.session_state["screener_mode"] == "single":
        col_input, col_btn = st.columns([3.5, 1], vertical_alignment="bottom")
        with col_input:
            st.markdown(
                """
                <div class="glow-title" style="font-size: 1rem;">
                    <span class="cyan-dot"></span>Enter Tickers
                </div>
                """,
                unsafe_allow_html=True,
            )
            input_ticker = st.text_input(
                "Stock Tickers",
                value="",
                placeholder="BBCA, BMRI, TLKM, INCO...",
                label_visibility="collapsed",
            )
        with col_btn:
            btn_single = st.button(
                "Run Analyze", type="primary", use_container_width=True
            )

        if btn_single:
            if not input_ticker.strip():
                st.warning("⚠️ Input ticker list is empty.")
            else:
                list_to_scan = [
                    t.strip().upper()
                    for t in input_ticker.split(",")
                    if t.strip()
                ]
                run_batch_execution(list_to_scan, cache_key="df_screener_single")

        active_cache_key = "df_screener_single"

        if active_cache_key in st.session_state:
            df_single_res = st.session_state[active_cache_key]

            st.write("")
            h_left, _ = st.columns([3, 1], vertical_alignment="center")
            with h_left:
                st.markdown(
                    f"""
                    <h3 class="glow-title" style="margin-bottom: 0px;">
                        <span class="cyan-dot"></span>Analysis Results 
                        <span style='font-size:0.9rem; color:#94a3b8;'>({len(df_single_res['Symbol'].unique())} items)</span>
                    </h3>
                    """,
                    unsafe_allow_html=True,
                )

            if df_single_res.empty:
                st.warning("⚠️ No valid data returned for the selected tickers.")
            else:
                render_trade_plan_cards(df_single_res, is_title_needed=False, is_single_mode=True)

    else:
        all_tickers = load_daftar_saham()
        if not all_tickers:
            st.error("❌ File `daftar_saham.txt` tidak ditemukan di folder `data/` maupun di direktori utama!")
            return

        col_info, col_batch_btn = st.columns([3, 1], vertical_alignment="center")
        with col_info:
            st.info("💡 **Click Run To Screen All Ticker**")
        with col_batch_btn:
            if st.button("Run Screener", type="primary", use_container_width=True):
                run_batch_execution(all_tickers, cache_key="df_screener_batch")

        active_cache_key = "df_screener_batch"

        if active_cache_key in st.session_state:
            df_raw = st.session_state[active_cache_key]

            st.write("")
            with st.expander("🛠️ **Filters & Criteria**", expanded=True):
                r1c1, r1c2, r1c3 = st.columns(3)
                with r1c1:
                    f_strategi = st.selectbox(
                        "🎯 Strategy:",
                        ["ALL STRATEGIES", "Buy On Weakness (BOW)", "Breakout (BOB)"],
                        key="f_strategi",
                    )
                with r1c2:
                    f_grade = st.selectbox(
                        "🏆 Setup Grade:",
                        [
                            "ALL GRADES",
                            "Grade A / A+ Only (High Quality)",
                            "Grade B or Lower (Moderate/Risk)",
                        ],
                        key="f_grade",
                    )
                with r1c3:
                    f_zone = st.selectbox(
                        "📍 Price Zone:",
                        [
                            "ALL POSITIONS",
                            "In Buy Zone (Ready to Execute)",
                            "Near Zone (Approaching Entry)",
                        ],
                        key="f_zone",
                    )

                r2c1, r2c2, r2c3 = st.columns([1.5, 1.5, 1], vertical_alignment="bottom")
                with r2c1:
                    f_rr = st.selectbox(
                        "⚖️ Min Risk-Reward:",
                        [
                            "ALL RATIOS",
                            "Min 1 : 1.5",
                            "Min 1 : 2.0 (Standard)",
                            "Min 1 : 3.0 (High Reward)",
                        ],
                        key="f_rr",
                    )
                with r2c2:
                    f_candle = st.selectbox(
                        "🕯️ Candlestick Pattern:",
                        ["ALL CANDLES", "Bullish Signal Only", "Neutral / Doji Only"],
                        key="f_candle",
                    )
                with r2c3:
                    st.button("🔄 Reset Filters", on_click=reset_filters, use_container_width=True)

            df = df_raw.copy()

            if f_strategi == "Buy On Weakness (BOW)":
                df = df[df["Strategy"] == "BOW"]
            elif f_strategi == "Breakout (BOB)":
                df = df[df["Strategy"] == "BOB"]

            if f_grade == "Grade A / A+ Only (High Quality)":
                df = df[df["Score"] >= 70]
            elif f_grade == "Grade B or Lower (Moderate/Risk)":
                df = df[df["Score"] < 70]

            if f_zone == "In Buy Zone (Ready to Execute)":
                df = df[df["Zone Position"] == "In Buy Zone"]
            elif f_zone == "Near Zone (Approaching Entry)":
                df = df[df["Zone Position"] == "Near Zone"]

            if f_rr == "Min 1 : 1.5":
                df = df[df["RR_Val"] >= 1.5]
            elif f_rr == "Min 1 : 2.0 (Standard)":
                df = df[df["RR_Val"] >= 2.0]
            elif f_rr == "Min 1 : 3.0 (High Reward)":
                df = df[df["RR_Val"] >= 3.0]

            if f_candle == "Bullish Signal Only":
                df = df[
                    df["Candlestick Pattern"].str.contains(
                        "Engulfing|Morning|Soldiers|Marubozu|Hammer|Dragonfly",
                        case=False,
                        na=False,
                    )
                ]
            elif f_candle == "Neutral / Doji Only":
                df = df[
                    df["Candlestick Pattern"].str.contains(
                        "Doji|Spinning|Standard", case=False, na=False
                    )
                ]

            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            st.write("")

            h_left, _ = st.columns([3, 1], vertical_alignment="center")
            with h_left:
                st.markdown(
                    f"""
                    <h3 class="glow-title" style="margin-bottom: 0px;">
                        <span class="cyan-dot"></span>Screener Results 
                        <span style='font-size:0.9rem; color:#94a3b8;'>({len(df)} items)</span>
                    </h3>
                    """,
                    unsafe_allow_html=True,
                )

            if "batch_uncheck_trigger" not in st.session_state:
                st.session_state["batch_uncheck_trigger"] = 0

            editor_key = f"batch_editor_v{st.session_state['batch_uncheck_trigger']}"

            df_table = df.copy()
            df_table.insert(0, "Select", False)

            edited_df = st.data_editor(
                df_table[["Select"] + [col for col in df.columns if col != "Select"]],
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Check to view detailed Trade Plan cards",
                        default=False,
                    ),
                    "Symbol": st.column_config.TextColumn("Symbol"),
                    "Score": st.column_config.NumberColumn("Score", format="%d"),
                    "Last Price": st.column_config.NumberColumn("Last Price", format="Rp %d"),
                    "Stop Loss (SL)": st.column_config.NumberColumn("Stop Loss", format="Rp %d"),
                    "TP 1": st.column_config.NumberColumn("TP 1", format="Rp %d"),
                    "TP 2": st.column_config.NumberColumn("TP 2", format="Rp %d"),
                },
                disabled=[col for col in df.columns if col != "Select"],
                use_container_width=True,
                key=editor_key
            )

            selected_rows = edited_df[edited_df["Select"] == True]

            # Siapkan teks gabungan untuk semua saham yang dicentang (untuk Copy Terpilih)
            batch_copy_text = ""
            if not selected_rows.empty:
                checked_symbols_preview = selected_rows["Symbol"].unique().tolist()
                df_to_preview = df_raw[df_raw["Symbol"].isin(checked_symbols_preview)]
                
                plan_blocks = []
                for _, r in df_to_preview.iterrows():
                    p_text = f"""=== TRADE PLAN: {r.get('Symbol', '')} ===
Strategy: {r.get('Strategy', 'BOW')}
Grade: {r.get('Grade', 'N/A')}
Score: {r.get('Score', 0)}/100
Last Price: Rp {r.get('Last Price', 0):,}
Buy Range: {r.get('Buy Range', '-')}
Stop Loss: Rp {r.get('Stop Loss (SL)', 0):,}
Target 1 (TP1): Rp {r.get('TP 1', 0):,}
Target 2 (TP2): Rp {r.get('TP 2', 0):,}
Zone Position: {r.get('Zone Position', '-')}
Risk-Reward: {r.get('Risk-Reward Ratio', '1 : 0')}
==============================="""
                    plan_blocks.append(p_text)
                batch_copy_text = "\n\n".join(plan_blocks)

            # Tombol aksi Batch: Clear Centang di kiri, Copy Terpilih di tengah, Watchlist Terpilih di kanan
            c_act_clear, c_act_copy, c_act_wl = st.columns([1, 1, 1], vertical_alignment="bottom")
            
            with c_act_clear:
                if st.button("🗑️ Clear Centang", use_container_width=True, key="btn_clear_checks"):
                    st.session_state["batch_uncheck_trigger"] += 1
                    st.rerun()

            with c_act_copy:
                unique_batch_btn_id = "copy_btn_batch_all"
                batch_copy_html = f"""
                <button id="{unique_batch_btn_id}" style="width: 100%; background: linear-gradient(135deg, #A855F7 0%, #00F0FF 100%); color: #050811; border: none; padding: 9px 10px; border-radius: 6px; font-weight: 800; font-size: 13px; cursor: pointer; box-shadow: 0 0 8px rgba(0, 240, 255, 0.4); transition: all 0.2s;">
                    📋 Copy Terpilih
                </button>
                <script>
                const textToCopy_{unique_batch_btn_id} = `{batch_copy_text}`;
                const btn_{unique_batch_btn_id} = document.getElementById("{unique_batch_btn_id}");
                btn_{unique_batch_btn_id}.onclick = function() {{
                    if (!textToCopy_{unique_batch_btn_id}.trim()) {{
                        alert("Pilih minimal satu saham dicentang pada tabel di atas.");
                        return;
                    }}
                    navigator.clipboard.writeText(textToCopy_{unique_batch_btn_id}).then(function() {{
                        btn_{unique_batch_btn_id}.innerText = "✅ Copied!";
                        btn_{unique_batch_btn_id}.style.background = "#00FF66";
                        setTimeout(function() {{
                            btn_{unique_batch_btn_id}.innerText = "📋 Copy Terpilih";
                            btn_{unique_batch_btn_id}.style.background = "linear-gradient(135deg, #A855F7 0%, #00F0FF 100%)";
                        }}, 2000);
                    }}).catch(function(err) {{
                        console.error('Gagal menyalin text: ', err);
                    }});
                }};
                </script>
                """
                components.html(batch_copy_html, height=45)

            with c_act_wl:
                if st.button("⭐ Watchlist Terpilih", use_container_width=True, key="btn_wl_batch_selected"):
                    if not selected_rows.empty:
                        symbols_to_add = selected_rows["Symbol"].unique().tolist()
                        add_tickers_to_watchlist(symbols_to_add)
                    else:
                        st.toast("Pilih minimal satu saham dicentang pada tabel di atas.", icon="⚠️")

            if not selected_rows.empty:
                st.markdown("<br>", unsafe_allow_html=True)
                checked_symbols = selected_rows["Symbol"].unique().tolist()
                df_to_render = df_raw[df_raw["Symbol"].isin(checked_symbols)]
                render_trade_plan_cards(df_to_render, is_title_needed=True, is_single_mode=False)
