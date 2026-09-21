import pandas as pd
import streamlit as st

from data.ihsg_tickers import get_all_ihsg_tickers
from engines.market_data import normalize_ticker
from engines.screener_stoch_psar import run_stoch_psar_screener
from utils.card_html import (
    build_card,
    direction_badge,
    info_row,
    pill,
    score_badge,
    section_label,
    source_note_html,
)
from utils.icons import icon_kwargs, svg_icon
from utils.market_source import prepare_batch_source
from utils.ui_helpers import render_inline_trade_planner

_MODE_LABELS = {
    "Golden Cross (Buy)": "Golden Cross (Bullish)",
    "Dead Cross (Sell)": "Dead Cross (Bearish)",
}
_SIGNAL_DAY = {"H0": "H-0", "H1": "H-1", "H2": "H-2", "EARLY": "Early"}


def _num(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _tag_kind(tag):
    low = str(tag).lower()
    if any(x in low for x in ("lonjakan", "diabaikan", "reversal di downtrend", "sudah turun")):
        return "amber"
    if "flip" in low:
        return "cyan"
    return "neutral"


def _stoch_card_html(row, is_selected, is_gc):
    ticker = str(row.get("Ticker", ""))
    saham = ticker.replace(".JK", "")
    kind = "GC" if is_gc else "DC"
    score = abs(int(_num(row.get("Score", 0))))  # kekuatan sinyal (DC disimpan negatif, tampil positif)

    badges = score_badge(score) + ("" if is_gc else direction_badge("DC", "red"))

    day = _SIGNAL_DAY.get(str(row.get("Signal", "")), "")
    line = f"{kind} {day}".strip() if day else kind
    line += f" · %K {_num(row.get('Stoch %K')):.0f} / %D {_num(row.get('Stoch %D')):.0f}"
    vol = _num(row.get("Vol x MA20"), 0.0)
    if vol > 0:
        line += f" · Vol {vol:.1f}x MA20"
    rows = info_row(line, "chart-candle")

    if "Signal Tags" in row.index and isinstance(row.get("Signal Tags"), str):
        tags = [t.strip() for t in row["Signal Tags"].split("|") if t.strip()]
    else:  # data lama tanpa kolom label
        tags = [t.strip() for t in str(row.get("Detail Signal", "")).split("|")[1:] if t.strip()]
    pills = "".join(pill(t, _tag_kind(t)) for t in tags)
    if "Candle Final" in row.index and not bool(row.get("Candle Final", True)):
        pills += pill("Candle belum final", "amber")

    return build_card(
        is_selected,
        saham,
        badges,
        _num(row.get("Harga", 0)),
        _num(row.get("Change (%)", 0.0)),
        rows,
        pills,
    )


def _help_html(html):
    return (
        html.replace("__I_STAR__", svg_icon("star", 16, "#E3B341", 2, margin_right=6))
        .replace("__I_ALERT__", svg_icon("alert-triangle", 14, "#E3B341", 2, margin_right=4))
        .replace("__I_BULB__", svg_icon("bulb", 14, "#E3B341", 2, margin_right=4))
        .replace("__I_STAR_S__", svg_icon("star", 11, "#FFD700", 2, margin_right=4))
    )


def render_tab_stoch_psar():
    # Style CSS Full Cyberpunk & Neon Futuristic
    st.markdown(
        """
        <style>
        /* =========================================================
           1. CYBERPUNK HEADER BANNER
           ========================================================= */
        .cyber-header-container {
            position: relative;
            background: linear-gradient(135deg, rgba(255, 0, 127, 0.2) 0%, rgba(0, 243, 255, 0.2) 100%);
            border: 1.5px solid #00F3FF;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 14px;
            text-align: center;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.35), inset 0 0 12px rgba(255, 0, 127, 0.25);
        }
        .cyber-header-title {
            font-size: 16px;
            font-weight: 900;
            letter-spacing: 2.5px;
            text-transform: uppercase;
            background: linear-gradient(90deg, #FF007F, #00F3FF, #00FF66);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 12px rgba(0, 243, 255, 0.6);
            margin: 0;
        }

        /* Status Dot Cyberpunk */
        .cyber-status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #FF007F;
            border-radius: 50%;
            box-shadow: 0 0 10px #FF007F, 0 0 18px #FF007F;
            margin-right: 6px;
            animation: cyberpunk-pulse 1.5s infinite alternate;
        }

        @keyframes cyberpunk-pulse {
            0% { transform: scale(0.9); box-shadow: 0 0 6px #FF007F; }
            100% { transform: scale(1.3); box-shadow: 0 0 15px #00F3FF; background-color: #00F3FF; }
        }

        /* =========================================================
           2. SECTION LABEL "CHOOSE SIGNAL MODE"
           ========================================================= */
        .cyber-section-label {
            font-size: 11px;
            font-weight: 800;
            color: #FF007F;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            text-shadow: 0 0 8px rgba(255, 0, 127, 0.6);
            margin-top: 14px;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* =========================================================
           3. STYLING STREAMLIT BUTTONS (RUN & STOP)
           ========================================================= */
        /* Tombol Run Screening */
        button[key="btn_run_stoch_screener"],
        div[data-testid="stColumn"] button[kind="secondary"]:has(p:contains("Run")) {
            background: linear-gradient(135deg, #00F3FF 0%, #00FF66 100%) !important;
            color: #050811 !important;
            font-weight: 900 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            border: none !important;
            border-radius: 6px !important;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.5) !important;
            transition: all 0.25s ease-in-out !important;
        }
        button[key="btn_run_stoch_screener"]:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 0 25px rgba(0, 255, 102, 0.8) !important;
            color: #050811 !important;
        }

        /* Tombol Stop */
        button[key="btn_stop_stoch_screener"],
        div[data-testid="stColumn"] button[kind="secondary"]:has(p:contains("Stop")) {
            background: linear-gradient(135deg, #FF007F 0%, #7928CA 100%) !important;
            color: #FFFFFF !important;
            font-weight: 900 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            border: none !important;
            border-radius: 6px !important;
            box-shadow: 0 0 15px rgba(255, 0, 127, 0.5) !important;
            transition: all 0.25s ease-in-out !important;
        }
        button[key="btn_stop_stoch_screener"]:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 0 25px rgba(255, 0, 127, 0.8) !important;
            color: #FFFFFF !important;
        }

        /* =========================================================
           4. STYLING SELECT SAHAM BUTTON (PRIMARY & SECONDARY)
           ========================================================= */
        /* Tombol Selected (Primary) */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #FF007F 0%, #00F3FF 100%) !important;
            color: #FFFFFF !important;
            border: 1.5px solid #00F3FF !important;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.6) !important;
            border-radius: 6px !important;
            font-weight: 800 !important;
            text-shadow: 0 0 6px rgba(0,0,0,0.8) !important;
        }
        .stButton button[kind="primary"]:hover {
            box-shadow: 0 0 25px rgba(255, 0, 127, 0.8) !important;
            transform: translateY(-1px) !important;
        }

        /* Tombol Select Saham Biasa (Secondary) di dalam list */
        .stButton button[kind="secondary"] {
            background-color: #161B22 !important;
            color: #00F3FF !important;
            border: 1px solid #00F3FF !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
            box-shadow: 0 0 8px rgba(0, 243, 255, 0.2) !important;
            transition: all 0.25s ease-in-out !important;
        }
        .stButton button[kind="secondary"]:hover {
            border-color: #FF007F !important;
            color: #FFFFFF !important;
            background: rgba(0, 243, 255, 0.15) !important;
            box-shadow: 0 0 15px rgba(255, 0, 127, 0.5) !important;
        }

        /* =========================================================
           5. STYLING SELECTBOX / DROPDOWN
           ========================================================= */
        div[data-testid="stSelectbox"] > div > div {
            background-color: #0D1117 !important;
            border: 1.5px solid #00F3FF !important;
            border-radius: 6px !important;
            color: #00F3FF !important;
            font-weight: 700 !important;
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.2) !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[data-testid="stSelectbox"] > div > div:hover {
            border-color: #FF007F !important;
            box-shadow: 0 0 15px rgba(255, 0, 127, 0.4) !important;
        }
        div[data-testid="stSelectbox"] div[role="button"] {
            color: #00F3FF !important;
            font-weight: 700 !important;
        }

        /* =========================================================
           6. METRIC CARDS & CONTAINER STYLES
           ========================================================= */
        .metric-card {
            background: #161B22;
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 10px 12px;
            text-align: center;
            box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.5);
        }
        .metric-value {
            font-size: 18px;
            font-weight: 800;
            color: #FFFFFF;
        }
        .metric-label {
            font-size: 10px;
            color: #8B949E;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .empty-card {
            background-color: #161B22;
            border: 1px dashed #30363D;
            border-radius: 10px;
            padding: 50px 20px;
            text-align: center;
            color: #8B949E;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "stop_stoch_scan" not in st.session_state:
        st.session_state["stop_stoch_scan"] = False

    if "active_stoch_type" not in st.session_state:
        st.session_state["active_stoch_type"] = "Golden Cross (Buy)"

    if "selected_stoch_ticker" not in st.session_state:
        st.session_state["selected_stoch_ticker"] = None

    col_left, col_right = st.columns([1.3, 2.7], gap="medium")

    # =========================================================
    # LEFT PANEL: SCREENER CONTROL & STOCK LIST
    # =========================================================
    with col_left:
        st.markdown(
            f"""
            <div class="cyber-header-container">
                <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 4px;">
                    <span class="cyber-status-dot"></span>
                </div>
                <div style="display: flex; justify-content: center; align-items: center; gap: 8px;">
                    {svg_icon("bolt", 18, "#00F3FF", 2)}
                    <span class="cyber-header-title">STOCH-TREND RADAR</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_btn_run, col_btn_stop = st.columns([1, 1])

        with col_btn_run:
            run_clicked = st.button(
                "Run Screening",
                key="btn_run_stoch_screener",
                use_container_width=True,
                **icon_kwargs("play_arrow"),
            )

        with col_btn_stop:
            stop_clicked = st.button(
                "Stop",
                key="btn_stop_stoch_screener",
                use_container_width=True,
                **icon_kwargs("stop_circle"),
            )

        if stop_clicked:
            st.session_state["stop_stoch_scan"] = True

        if run_clicked:
            st.session_state["stop_stoch_scan"] = False
            with st.spinner("Fetching IHSG Tickers List..."):
                all_stoch_tickers = get_all_ihsg_tickers()

            total_stoch_tickers = len(all_stoch_tickers)
            data_map, source_text = prepare_batch_source()
            pbar_stoch = st.progress(0)
            pstatus_stoch = st.empty()

            def update_stoch_progress(current, total):
                if st.session_state.get("stop_stoch_scan", False):
                    pstatus_stoch.warning("Screening process cancelled by user.")
                    return
                pct = current / total if total > 0 else 0
                pbar_stoch.progress(pct)
                pstatus_stoch.text(f"Scanning Stoch & PSAR: {current}/{total} tickers...")

            def update_stoch_phase(phase, batch_no, n_batches, first, last, total):
                pstatus_stoch.text(
                    f"Downloading batch {batch_no}/{n_batches} (tickers {first}-{last} of {total})..."
                )

            try:
                df_gc, df_dc = run_stoch_psar_screener(
                    tickers=all_stoch_tickers,
                    progress_callback=update_stoch_progress,
                    phase_callback=update_stoch_phase,
                    data=data_map,
                )
                pbar_stoch.empty()
                pstatus_stoch.empty()

                # Urutan sudah diatur screener: GC skor tertinggi dulu, DC paling negatif (terkuat) dulu.
                st.session_state["df_gc_data"] = df_gc if df_gc is not None else pd.DataFrame()
                st.session_state["df_dc_data"] = df_dc if df_dc is not None else pd.DataFrame()

                gc_len = len(df_gc) if df_gc is not None else 0
                dc_len = len(df_dc) if df_dc is not None else 0

                if data_map:
                    keys = {normalize_ticker(k) for k in data_map}
                    n_live = sum(1 for t in all_stoch_tickers if normalize_ticker(t) not in keys)
                    if n_live:
                        source_text += f" · {n_live} saham tidak ada di file, diambil langsung"
                st.session_state["stoch_source_text"] = source_text

                st.session_state["stoch_stats"] = {
                    "total": total_stoch_tickers,
                    "matched_gc": gc_len,
                    "matched_dc": dc_len,
                    "total_signal": gc_len + dc_len,
                }

                # Pilihan awal: saham teratas; kalau hasil kosong, pilihan lama dikosongkan
                if df_gc is not None and not df_gc.empty:
                    st.session_state["selected_stoch_ticker"] = df_gc.iloc[0].get("Ticker", "")
                    st.session_state["active_stoch_type"] = "Golden Cross (Buy)"
                elif df_dc is not None and not df_dc.empty:
                    st.session_state["selected_stoch_ticker"] = df_dc.iloc[0].get("Ticker", "")
                    st.session_state["active_stoch_type"] = "Dead Cross (Sell)"
                else:
                    st.session_state["selected_stoch_ticker"] = None
                st.session_state["stoch_screener_mode_select"] = st.session_state["active_stoch_type"]

            except Exception as e:
                pbar_stoch.empty()
                pstatus_stoch.empty()
                st.error(f"An error occurred: {e}")

        st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)

        has_results = "stoch_stats" in st.session_state

        if has_results:
            st.markdown(
                section_label("adjustments-horizontal", "SIGNAL MODE"),
                unsafe_allow_html=True,
            )

            # --- DROPDOWN LEBAR DI KIRI & TOMBOL EXPORT DI KANAN ---
            col_filter, col_export = st.columns([3.2, 0.8], vertical_alignment="bottom")

            with col_filter:
                screener_mode = st.selectbox(
                    "Signal Mode",
                    options=["Golden Cross (Buy)", "Dead Cross (Sell)"],
                    **({} if "stoch_screener_mode_select" in st.session_state else {"index": 0}),
                    format_func=lambda v: _MODE_LABELS.get(v, v),
                    key="stoch_screener_mode_select",
                    label_visibility="collapsed",
                )

            with col_export:
                is_gc_tab_export = "Buy" in screener_mode
                df_export = (
                    st.session_state.get("df_gc_data", pd.DataFrame())
                    if is_gc_tab_export
                    else st.session_state.get("df_dc_data", pd.DataFrame())
                )

                if not df_export.empty:
                    csv_data = df_export.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="CSV",
                        data=csv_data,
                        file_name=f"stoch_screening_{'buy' if is_gc_tab_export else 'sell'}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help=f"Export {_MODE_LABELS.get(screener_mode, screener_mode)} to CSV",
                        **icon_kwargs("download", "download_button"),
                    )
                else:
                    st.button(
                        "CSV",
                        disabled=True,
                        use_container_width=True,
                        help="Data kosong",
                        **icon_kwargs("download"),
                    )

            st.session_state["active_stoch_type"] = screener_mode

            st.markdown(
                source_note_html(st.session_state.get("stoch_source_text", "")),
                unsafe_allow_html=True,
            )
            st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

            is_gc_tab = "Buy" in screener_mode
            df_target = (
                st.session_state.get("df_gc_data", pd.DataFrame())
                if is_gc_tab
                else st.session_state.get("df_dc_data", pd.DataFrame())
            )

            if not df_target.empty:
                with st.container(height=800, border=False):
                    for idx, row in df_target.iterrows():
                        ticker = str(row.get("Ticker", ""))
                        saham = ticker.replace(".JK", "")
                        is_selected = st.session_state.get("selected_stoch_ticker") == ticker

                        st.markdown(_stoch_card_html(row, is_selected, is_gc_tab), unsafe_allow_html=True)

                        btn_label = f"SELECTED ({saham})" if is_selected else f"SELECT {saham}"
                        btn_type = "primary" if is_selected else "secondary"

                        if st.button(
                            btn_label,
                            key=f"select_stoch_btn_{ticker}_{idx}",
                            use_container_width=True,
                            type=btn_type,
                            **(icon_kwargs("check") if is_selected else {}),
                        ):
                            st.session_state["selected_stoch_ticker"] = ticker
                            st.rerun()

                        st.markdown(
                            "<div style='margin-bottom: 10px;'></div>",
                            unsafe_allow_html=True,
                        )
            else:
                st.info(f"No {_MODE_LABELS.get(screener_mode, screener_mode)} signals detected.")
        else:
            st.info("Click **Run Screening** above to scan the market.")

    # =========================================================
    # RIGHT PANEL: WORKSPACE & LIVE TRADE PLANNER
    # =========================================================
    with col_right:
        if "stoch_stats" in st.session_state:
            stats = st.session_state["stoch_stats"]
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(
                    f"""<div class="metric-card">
                        <div class="metric-label">Total Scanned</div>
                        <div class="metric-value">{stats['total']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m2:
                st.markdown(
                    f"""<div class="metric-card" style="border-color: #00FF66;">
                        <div class="metric-label" style="color: #00FF66;">Golden Cross</div>
                        <div class="metric-value" style="color: #00FF66;">{stats['matched_gc']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m3:
                st.markdown(
                    f"""<div class="metric-card" style="border-color: #FF007F;">
                        <div class="metric-label" style="color: #FF007F;">Dead Cross</div>
                        <div class="metric-value" style="color: #FF007F;">{stats['matched_dc']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m4:
                st.markdown(
                    f"""<div class="metric-card">
                        <div class="metric-label">Total Signals</div>
                        <div class="metric-value">{stats['total_signal']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

        selected_stoch_symbol = st.session_state.get("selected_stoch_ticker")

        if selected_stoch_symbol:
            if not selected_stoch_symbol.endswith(".JK") and "." not in selected_stoch_symbol:
                selected_stoch_symbol += ".JK"

            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, rgba(0, 243, 255, 0.12) 0%, rgba(255, 0, 127, 0.1) 100%); border: 1.5px solid #00F3FF; padding: 8px 14px; border-radius: 8px; color: #FFFFFF; font-weight: 600; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 0 12px rgba(0, 243, 255, 0.25);">
                    <span>{svg_icon("target", 18, "#00F3FF", 2, margin_right=6)}SELECTED SYMBOL: <strong style="color: #00F3FF; font-size: 15px; margin-left: 6px;">{selected_stoch_symbol}</strong></span>
                    <span style="color: #8B949E; font-size: 11px; font-weight: 500;">Interactive Analysis Workspace</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            try:
                render_inline_trade_planner(selected_stoch_symbol, key_suffix="stoch_tab")
            except KeyError as ke:
                if "Status Candle" in str(ke):
                    st.warning(f"Trade Plan rendered with partial data for {selected_stoch_symbol}.")
                else:
                    st.error(f"Failed to load Trade Plan for {selected_stoch_symbol}: {ke}")
            except Exception as e:
                st.error(f"Failed to load Trade Plan for {selected_stoch_symbol}: {e}")
        else:
            st.markdown(
                _help_html(
                    """
                <div class="empty-card" style="text-align: left; padding: 20px; background-color: #161B22; border-radius: 8px; border: 1px solid #30363D;">
                    <h3 style="color: #FFFFFF; font-size: 16px; margin-top: 0; margin-bottom: 12px;">
                        __I_STAR__ How To Read These Results
                    </h3>
                    <p style="font-size: 13px; color: #C9D1D9; margin-bottom: 12px; line-height: 1.5;">
                        Stochastic dan PSAR mengikuti pergerakan harga, jadi sinyalnya bisa terlambat atau palsu, terutama saat sideways. 
                        <strong>Anggap hasilnya kandidat, lalu cek di chart:</strong>
                    </p>
                    <ul style="font-size: 12px; color: #8B949E; margin-left: 0; padding-left: 20px; line-height: 1.6; margin-bottom: 16px; list-style-type: none;">
                        <li style="margin-bottom: 6px;">
                            <span style="color: #FFD700; font-size: 10px; margin-right: 4px;">__I_STAR_S__</span>
                            <strong style="color: #C9D1D9;">Tren:</strong> Lihat label di Detail Signal. "Pullback di Uptrend" umumnya lebih kuat daripada "Reversal di Downtrend" (yang berisiko menangkap pisau jatuh).
                        </li>
                        <li style="margin-bottom: 6px;">
                            <span style="color: #FFD700; font-size: 10px; margin-right: 4px;">__I_STAR_S__</span>
                            <strong style="color: #C9D1D9;">Volume:</strong> Lebih baik kalau volume di hari cross di atas rata-rata (lihat "Vol x MA20").
                        </li>
                        <li style="margin-bottom: 6px;">
                            <span style="color: #FFD700; font-size: 10px; margin-right: 4px;">__I_STAR_S__</span>
                            <strong style="color: #C9D1D9;">Kesegaran sinyal:</strong> H-0 paling segar. H-1 dan H-2 sudah lebih telat, cek apakah harga masih dekat area cross.
                        </li>
                        <li style="margin-bottom: 6px;">
                            <span style="color: #FFD700; font-size: 10px; margin-right: 4px;">__I_STAR_S__</span>
                            <strong style="color: #C9D1D9;">Jangan mengejar:</strong> Kalau harga sudah naik banyak dalam beberapa hari, risk-reward biasanya sudah jelek.
                        </li>
                        <li style="margin-bottom: 6px;">
                            <span style="color: #FFD700; font-size: 10px; margin-right: 4px;">__I_STAR_S__</span>
                            <strong style="color: #C9D1D9;">PSAR:</strong> Kalau ada catatan "PSAR diabaikan (ADX rendah)", artinya kondisi sideways dan sinyal PSAR kurang bisa dipercaya. Titik PSAR juga bisa dipakai sebagai acuan trailing stop.
                        </li>
                        <li style="margin-bottom: 6px;">
                            <span style="color: #FFD700; font-size: 10px; margin-right: 4px;">__I_STAR_S__</span>
                            <strong style="color: #C9D1D9;">Support/resistance:</strong> Cek resistance terdekat di chart sebelum masuk.
                        </li>
                        <li style="margin-bottom: 6px;">
                            <span style="color: #FFD700; font-size: 10px; margin-right: 4px;">__I_STAR_S__</span>
                            <strong style="color: #C9D1D9;">DC (bearish):</strong> Peringatan pelemahan, bukan otomatis sinyal jual atau short.
                        </li>
                    </ul>
                    <p style="font-size: 12px; color: #E3B341; margin-bottom: 0; font-weight: 500;">
                        __I_BULB__ Jalankan scan setelah pasar tutup agar candle sudah final.
                    </p>
                </div>
                """
                ),
                unsafe_allow_html=True,
            )
