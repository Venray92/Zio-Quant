import re

import pandas as pd
import streamlit as st

from data.ihsg_tickers import get_all_ihsg_tickers
from engines.screener_rsi_divergence import run_rsi_screener
from utils.card_html import (
    build_card,
    fmt_id,
    info_row,
    pill,
    score_badge,
    section_label,
    source_note_html,
)
from utils.icons import icon_kwargs, svg_icon
from utils.market_source import prepare_batch_source
from utils.ui_helpers import render_inline_trade_planner

_MODE_LABELS = {"Bullish": "Bullish Divergence", "Bearish": "Bearish Divergence"}


def shorten_pattern(pattern_name):
    """Menyingkat nama pattern agar rapi di UI."""
    if not pattern_name or pattern_name == "-":
        return "-"

    res = str(pattern_name)
    res = res.replace("Regular Bullish Divergence", "Reg Bull Div")
    res = res.replace("Hidden Bullish Divergence", "Hid Bull Div")
    res = res.replace("Regular Bearish Divergence", "Reg Bear Div")
    res = res.replace("Hidden Bearish Divergence", "Hid Bear Div")
    res = res.replace("Bullish Divergence", "Bull Div")
    res = res.replace("Bearish Divergence", "Bear Div")
    res = res.replace(" Valid (GC Confirmed)", " [GC]")
    res = res.replace(" Valid (DC Confirmed)", " [DC]")
    res = res.replace(" Valid", "")
    return res


def _short_date(value):
    try:
        return pd.to_datetime(value).strftime("%d %b")
    except Exception:
        return str(value)


def _rp(value):
    """'Rp 1,250' -> '1.250'"""
    try:
        return fmt_id(float(re.sub(r"[^0-9.]", "", str(value)) or 0))
    except Exception:
        return "-"


def _num(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _rsi_card_html(row, is_selected):
    ticker = str(row.get("Ticker", row.get("Saham", "")))
    saham = row.get("Saham", ticker.replace(".JK", ""))
    pattern_raw = str(row.get("Pattern", "-"))
    is_bull = str(row.get("Direction", "")) == "Bullish" or (
        "Bullish" in pattern_raw and str(row.get("Direction", "")) != "Bearish"
    )
    kind = "GC" if is_bull else "DC"

    rows = info_row(shorten_pattern(pattern_raw), "chart-candle")
    rows += info_row(
        f"{_short_date(row.get('Tgl Kiri', '-'))} → {_short_date(row.get('Tgl Kanan', '-'))}",
        "calendar",
    )
    rows += info_row(
        f"T1 {_rp(row.get('Harga Kiri'))} (RSI {_num(row.get('RSI Kiri')):.0f}) → "
        f"T2 {_rp(row.get('Harga Kanan'))} (RSI {_num(row.get('RSI Kanan')):.0f})"
    )

    pills = ""
    if "T2 Age" in row.index and pd.notna(row.get("T2 Age")):
        pills += pill(f"T2: H+{int(row['T2 Age'])}", "cyan")
    if "Dist to T2 (%)" in row.index and pd.notna(row.get("Dist to T2 (%)")):
        side = "di atas low T2" if is_bull else "di bawah high T2"
        pills += pill(f"{_num(row['Dist to T2 (%)']):.1f}% {side}")
    if bool(row.get("Has Base", False)):
        pills += pill("Base T1-T2")
    if bool(row.get(f"Vol {kind}", False)):
        pills += pill(f"Vol {kind} di atas rata-rata")
    if "T2 Confirmed" in row.index and not bool(row.get("T2 Confirmed", True)):
        pills += pill("T2 belum terkonfirmasi", "amber")
    if "Candle Final" in row.index and not bool(row.get("Candle Final", True)):
        pills += pill("Candle belum final", "amber")

    return build_card(
        is_selected,
        saham,
        score_badge(row.get("Score", 0)),
        _num(row.get("Close_Price", 0)),
        _num(row.get("Change_Pct", 0.0)),
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


def render_tab_rsi():
    # Style CSS Full Cyberpunk & Neon Futuristic (Dengan Perbaikan Border Tombol)
    st.markdown(
        """
        <style>
        /* =========================================================
            1. CYBERPUNK HEADER BANNER & GLOWING STATUS DOT
            ========================================================= */
        .cyber-header-container {
            position: relative;
            background: linear-gradient(135deg, rgba(255, 0, 127, 0.2) 0%, rgba(0, 243, 255, 0.2) 100%);
            border: 1.5px solid #00F3FF;
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 14px;
            text-align: center;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.35), inset 0 0 12px rgba(255, 0, 127, 0.25);
        }
        .cyber-header-title {
            font-size: 18px;
            font-weight: 900;
            letter-spacing: 2.5px;
            text-transform: uppercase;
            background: linear-gradient(90deg, #FF007F, #00F3FF, #00FF66);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 12px rgba(0, 243, 255, 0.6);
            margin: 0;
        }
        .cyber-status-dot {
            width: 10px;
            height: 10px;
            background-color: #00F3FF;
            border-radius: 50%;
            box-shadow: 0 0 10px #00F3FF, 0 0 20px #00F3FF;
            display: inline-block;
            margin-bottom: 6px;
            animation: pulse-glow 2s infinite ease-in-out;
        }

        @keyframes pulse-glow {
            0% { opacity: 0.5; box-shadow: 0 0 5px #00F3FF; }
            50% { opacity: 1; box-shadow: 0 0 15px #00F3FF, 0 0 25px #00F3FF; }
            100% { opacity: 0.5; box-shadow: 0 0 5px #00F3FF; }
        }

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
            2. PERBAIKAN UTAMA: STYLING BORDER & WARNA TOMBOL STREAMLIT
            ========================================================= */
        /* Tombol Run Screening */
        div[data-testid="stColumn"]:has(div[key="btn_run_rsi_screener"]) button {
            background: linear-gradient(135deg, #00F3FF 0%, #00FF66 100%) !important;
            color: #050811 !important;
            font-weight: 900 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            border: 1.5px solid #00F3FF !important;
            border-radius: 6px !important;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.5) !important;
            transition: all 0.25s ease-in-out !important;
        }
        div[data-testid="stColumn"]:has(div[key="btn_run_rsi_screener"]) button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            border-color: #00FF66 !important;
            box-shadow: 0 0 25px rgba(0, 255, 102, 0.8) !important;
        }

        /* Tombol Stop */
        div[data-testid="stColumn"]:has(div[key="btn_stop_rsi_screener"]) button {
            background: linear-gradient(135deg, #FF007F 0%, #7928CA 100%) !important;
            color: #FFFFFF !important;
            font-weight: 900 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            border: 1.5px solid #FF007F !important;
            border-radius: 6px !important;
            box-shadow: 0 0 15px rgba(255, 0, 127, 0.5) !important;
            transition: all 0.25s ease-in-out !important;
        }
        div[data-testid="stColumn"]:has(div[key="btn_stop_rsi_screener"]) button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            border-color: #00F3FF !important;
            box-shadow: 0 0 25px rgba(255, 0, 127, 0.8) !important;
        }

        /* General Streamlit Buttons (Primary & Secondary / SELECT Buttons) */
        .stButton button {
            border-radius: 6px !important;
            font-weight: 800 !important;
            transition: all 0.25s ease-in-out !important;
        }

        /* Primary Button (Selected State) - Border Tegas Cyan/Neon */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #FF007F 0%, #00F3FF 100%) !important;
            color: #FFFFFF !important;
            border: 1.5px solid #00F3FF !important;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.6) !important;
            text-shadow: 0 0 6px rgba(0,0,0,0.8) !important;
        }
        .stButton button[kind="primary"]:hover {
            border-color: #FF007F !important;
            box-shadow: 0 0 25px rgba(255, 0, 127, 0.8) !important;
            transform: translateY(-1px) !important;
        }

        /* Secondary Button (Unselected State) - Border Gelap / Neon Halus */
        .stButton button[kind="secondary"] {
            background-color: #161B22 !important;
            color: #00F3FF !important;
            border: 1.5px solid #30363D !important;
        }
        .stButton button[kind="secondary"]:hover {
            border-color: #FF007F !important;
            color: #FFFFFF !important;
            box-shadow: 0 0 12px rgba(0, 243, 255, 0.4) !important;
        }

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

    # Inisialisasi State
    if "stop_rsi_scan" not in st.session_state:
        st.session_state["stop_rsi_scan"] = False

    if "active_rsi_type" not in st.session_state:
        st.session_state["active_rsi_type"] = "Bullish"

    if "selected_rsi_ticker" not in st.session_state:
        st.session_state["selected_rsi_ticker"] = None

    # ---------------------------------------------------------
    # LAYOUT UTAMA: SPLIT SCREEN (KIRI 38% : KANAN 62%)
    # ---------------------------------------------------------
    col_left, col_right = st.columns([1.3, 2.7], gap="medium")

    # =========================================================
    # PANEL KIRI: SCREENER CONTROL & DAFTAR SAHAM
    # =========================================================
    with col_left:
        st.markdown(
            f"""
            <div class="cyber-header-container">
                <div style="display: flex; justify-content: center; align-items: center;">
                    <span class="cyber-status-dot"></span>
                </div>
                <div style="display: flex; justify-content: center; align-items: center; gap: 8px;">
                    {svg_icon("bolt", 18, "#00F3FF", 2)}
                    <span class="cyber-header-title">RSI REVERSAL</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_btn_run, col_btn_stop = st.columns([1, 1])

        with col_btn_run:
            run_clicked = st.button(
                "Run Screening",
                key="btn_run_rsi_screener",
                use_container_width=True,
                **icon_kwargs("play_arrow"),
            )

        with col_btn_stop:
            stop_clicked = st.button(
                "Stop",
                key="btn_stop_rsi_screener",
                use_container_width=True,
                **icon_kwargs("stop_circle"),
            )

        if stop_clicked:
            st.session_state["stop_rsi_scan"] = True

        if run_clicked:
            st.session_state["stop_rsi_scan"] = False
            with st.spinner("Fetching IHSG tickers list..."):
                all_tickers = get_all_ihsg_tickers()

            total_tickers = len(all_tickers)
            if total_tickers == 0:
                st.warning("Daftar saham kosong, tidak ada yang bisa di-scan.")
            else:
                data_map, source_text = prepare_batch_source()
                pbar_rsi = st.progress(0)
                pstatus_rsi = st.empty()

                def _progress(done, total):
                    pbar_rsi.progress(min(1.0, done / total) if total else 0)
                    pstatus_rsi.text(f"Scanning RSI: {done}/{total} tickers...")

                def _phase(phase, batch_no, n_batches, first, last, total):
                    pstatus_rsi.text(
                        f"Downloading batch {batch_no}/{n_batches} (tickers {first}-{last} of {total})..."
                    )

                df_rsi_all, info = run_rsi_screener(
                    all_tickers,
                    progress_callback=_progress,
                    phase_callback=_phase,
                    data=data_map,
                    should_stop=lambda: st.session_state.get("stop_rsi_scan", False),
                )
                if st.session_state.get("stop_rsi_scan", False):
                    pstatus_rsi.warning("Screening process cancelled.")
                else:
                    pstatus_rsi.empty()
                pbar_rsi.empty()

                if data_map and info.get("downloaded"):
                    source_text += f" · {info['downloaded']} saham tidak ada di file, diambil langsung"

                df_rsi_bullish = pd.DataFrame()
                df_rsi_bearish = pd.DataFrame()
                if not df_rsi_all.empty and "Pattern" in df_rsi_all.columns:
                    df_rsi_bullish = df_rsi_all[
                        df_rsi_all["Pattern"].str.contains("Bullish", case=False, na=False)
                    ]
                    df_rsi_bearish = df_rsi_all[
                        df_rsi_all["Pattern"].str.contains("Bearish", case=False, na=False)
                    ]

                st.session_state["rsi_stats"] = {
                    "total": total_tickers,
                    "success": info["success"],
                    "failed": info["failed"],
                    "bullish_count": len(df_rsi_bullish),
                    "bearish_count": len(df_rsi_bearish),
                    "matched": len(df_rsi_all),
                }
                st.session_state["rsi_source_text"] = source_text
                st.session_state["df_rsi_bullish"] = df_rsi_bullish
                st.session_state["df_rsi_bearish"] = df_rsi_bearish

                # Pilihan awal: saham teratas; kalau hasil kosong, pilihan lama dikosongkan
                if not df_rsi_bullish.empty:
                    first = df_rsi_bullish.iloc[0]
                    st.session_state["selected_rsi_ticker"] = first.get("Ticker", first.get("Saham"))
                    st.session_state["active_rsi_type"] = "Bullish"
                elif not df_rsi_bearish.empty:
                    first = df_rsi_bearish.iloc[0]
                    st.session_state["selected_rsi_ticker"] = first.get("Ticker", first.get("Saham"))
                    st.session_state["active_rsi_type"] = "Bearish"
                else:
                    st.session_state["selected_rsi_ticker"] = None
                st.session_state["rsi_screener_mode_select"] = st.session_state["active_rsi_type"]

        st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)

        has_results = "rsi_stats" in st.session_state

        if has_results:
            st.markdown(
                section_label("adjustments-horizontal", "SCREENER MODE"),
                unsafe_allow_html=True,
            )

            col_filter, col_export = st.columns([3.2, 0.8])

            with col_filter:
                screener_mode = st.selectbox(
                    "Screener Mode",
                    options=["Bullish", "Bearish"],
                    **({} if "rsi_screener_mode_select" in st.session_state else {"index": 0}),
                    format_func=lambda v: _MODE_LABELS.get(v, v),
                    key="rsi_screener_mode_select",
                    label_visibility="collapsed",
                )

            with col_export:
                df_export = (
                    st.session_state.get("df_rsi_bullish", pd.DataFrame())
                    if screener_mode == "Bullish"
                    else st.session_state.get("df_rsi_bearish", pd.DataFrame())
                )

                if not df_export.empty:
                    csv_data = df_export.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="CSV",
                        data=csv_data,
                        file_name=f"screening_{screener_mode.lower()}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key=f"download_{screener_mode.lower()}",
                        help=f"Export {screener_mode} to CSV",
                        **icon_kwargs("download", "download_button"),
                    )
                else:
                    st.button(
                        "CSV",
                        disabled=True,
                        use_container_width=True,
                        key=f"download_empty_{screener_mode.lower()}",
                        help="Data kosong",
                        **icon_kwargs("download"),
                    )

            st.session_state["active_rsi_type"] = screener_mode

            st.markdown(
                source_note_html(st.session_state.get("rsi_source_text", "")),
                unsafe_allow_html=True,
            )
            st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

            is_bull_tab = screener_mode == "Bullish"
            df_target = (
                st.session_state.get("df_rsi_bullish", pd.DataFrame())
                if is_bull_tab
                else st.session_state.get("df_rsi_bearish", pd.DataFrame())
            )

            if not df_target.empty:
                with st.container(height=800, border=False):
                    for idx, row in df_target.iterrows():
                        ticker = str(row.get("Ticker", row.get("Saham", "")))
                        saham = row.get("Saham", ticker.replace(".JK", ""))
                        is_selected = st.session_state.get("selected_rsi_ticker") == ticker

                        with st.container():
                            st.markdown(_rsi_card_html(row, is_selected), unsafe_allow_html=True)

                            btn_label = f"SELECTED ({saham})" if is_selected else f"SELECT {saham}"
                            btn_type = "primary" if is_selected else "secondary"

                            if st.button(
                                btn_label,
                                key=f"select_rsi_btn_{ticker}_{idx}",
                                use_container_width=True,
                                type=btn_type,
                                **(icon_kwargs("check") if is_selected else {}),
                            ):
                                st.session_state["selected_rsi_ticker"] = ticker
                                st.rerun()

                            st.markdown(
                                "<div style='margin-bottom: 10px;'></div>",
                                unsafe_allow_html=True,
                            )
            else:
                st.info(f"No {screener_mode} patterns detected.")
        else:
            st.info("Click **Run Screening** above to start scanning the market.")

    # =========================================================
    # PANEL KANAN: WORKSPACE & LIVE TRADE PLANNER
    # =========================================================
    with col_right:
        if "rsi_stats" in st.session_state:
            stats = st.session_state["rsi_stats"]
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
                        <div class="metric-label" style="color: #00FF66;">Bullish</div>
                        <div class="metric-value" style="color: #00FF66;">{stats['bullish_count']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m3:
                st.markdown(
                    f"""<div class="metric-card" style="border-color: #FF007F;">
                        <div class="metric-label" style="color: #FF007F;">Bearish</div>
                        <div class="metric-value" style="color: #FF007F;">{stats['bearish_count']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with m4:
                st.markdown(
                    f"""<div class="metric-card">
                        <div class="metric-label">Signals Found</div>
                        <div class="metric-value">{stats['matched']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

        selected_rsi_symbol = st.session_state.get("selected_rsi_ticker")

        if selected_rsi_symbol:
            if not selected_rsi_symbol.endswith(".JK") and "." not in selected_rsi_symbol:
                selected_rsi_symbol += ".JK"

            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, rgba(0, 243, 255, 0.12) 0%, rgba(255, 0, 127, 0.1) 100%); border: 1.5px solid #00F3FF; padding: 8px 14px; border-radius: 8px; color: #FFFFFF; font-weight: 600; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 0 12px rgba(0, 243, 255, 0.25);">
                    <span>{svg_icon("target", 18, "#00F3FF", 2, margin_right=6)}SELECTED SYMBOL: <strong style="color: #00F3FF; font-size: 15px; margin-left: 6px;">{selected_rsi_symbol}</strong></span>
                    <span style="color: #8B949E; font-size: 11px; font-weight: 500;">Interactive Analysis Workspace</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            try:
                render_inline_trade_planner(selected_rsi_symbol, key_suffix="rsi_tab")
            except KeyError as ke:
                if "Status Candle" in str(ke):
                    st.warning(f"Trade Plan rendered with partial data for {selected_rsi_symbol}.")
                else:
                    st.error(f"Failed to load Trade Plan for {selected_rsi_symbol}: {ke}")
            except Exception as e:
                st.error(f"Failed to load Trade Plan for {selected_rsi_symbol}: {e}")
        else:
            st.markdown(
                _help_html(
                    """
                <div class="empty-card" style="text-align: left; padding: 20px; background-color: #161B22; border-radius: 8px; border: 1px solid #30363D;">
                    <h3 style="color: #FFFFFF; font-size: 16px; margin-top: 0; margin-bottom: 12px;">
                        __I_STAR__ How To Read These Results
                    </h3>
                    <p style="font-size: 13px; color: #C9D1D9; margin-bottom: 12px; line-height: 1.5;">
                        Screener menemukan divergence RSI yang sudah dikonfirmasi RSI GC/DC (maks. H+3 dari titik ke-2). 
                        <strong>Ini kandidat, bukan sinyal final.</strong> Sebelum masuk, cek di chart:
                    </p>
                    <ul style="font-size: 12px; color: #8B949E; margin-left: 0; padding-left: 20px; line-height: 1.6; margin-bottom: 16px;">
                        <li style="margin-bottom: 6px;">
                            <strong style="color: #C9D1D9;">Garis divergence:</strong> Tarik garis titik 1 ke titik 2 di harga dan di RSI, pastikan polanya bersih dan tidak ada candle yang menembusnya.
                        </li>
                        <li style="margin-bottom: 6px;">
                            <strong style="color: #C9D1D9;">Konfirmasi candle:</strong> Lebih kuat kalau harga close di atas high kemarin atau muncul candle pembalikan, bukan cuma RSI yang naik.
                        </li>
                        <li style="margin-bottom: 6px;">
                            <strong style="color: #C9D1D9;">Volume:</strong> Lebih meyakinkan kalau volume naik saat harga memantul. Skor sudah menghitung volume, tapi tetap lihat sendiri di chart.
                        </li>
                        <li style="margin-bottom: 6px;">
                            <strong style="color: #C9D1D9;">Tipe pola:</strong> Regular = potensi pembalikan arah (lebih berisiko kalau tren besar masih berlawanan). Hidden = lanjutan tren (lebih cocok kalau tren utama masih searah).
                        </li>
                        <li style="margin-bottom: 6px;">
                            <strong style="color: #C9D1D9;">Support/resistance dan jarak harga:</strong> Cek ruang ke resistance terdekat. Makin jauh harga dari titik ke-2, makin kecil risk-reward-nya.
                        </li>
                        <li style="margin-bottom: 6px;">
                            <strong style="color: #C9D1D9;">Bearish:</strong> Tanda momentum melemah (waspada), bukan otomatis sinyal jual atau short.
                        </li>
                    </ul>
                    <p style="font-size: 12px; color: #E3B341; margin-bottom: 0; font-weight: 500;">
                        __I_ALERT__ Saham hilang dari daftar setelah H+3. Itu bukan sinyal jual.
                    </p>
                </div>
                """
                ),
                unsafe_allow_html=True,
            )
