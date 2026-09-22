"""Halaman Trend Scanner: Breakout Surge, Trend Reset, Quiet Accumulation (satu kali scan, 3 mode)."""
from html import escape

import pandas as pd
import streamlit as st

from data.ihsg_tickers import get_all_ihsg_tickers
from engines.screener_trend import run_trend_screener
from engines.sector_map import get_company_name
from utils.card_html import GREEN, build_card, compact_html, fmt_id, info_row, pill, section_label, source_note_html
from utils.icons import icon_kwargs, svg_icon
from utils.market_source import prepare_batch_source
from utils.ui_helpers import render_inline_trade_planner

CYAN, AMBER = "#00F3FF", "#E3B341"
_MODES = ("Breakout Surge", "Trend Reset", "Quiet Accumulation")
_DESC = {
    "Breakout Surge": "Saham baru tembus resistance disertai lonjakan volume.",
    "Trend Reset": "Saham tren naik yang lagi koreksi sehat ke area support.",
    "Quiet Accumulation": "Harga menyempit sambil volume naik. Layak dipantau, BUKAN sinyal beli.",
}
_KEY = {"Breakout Surge": "df_trend_breakout", "Trend Reset": "df_trend_reset", "Quiet Accumulation": "df_trend_squeeze"}


def _num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _breakout_card(row, is_selected):
    saham = str(row.get("Saham", ""))
    price = _num(row.get("Close_Price")); chg = _num(row.get("Change_Pct"))
    badges = pill(f"Score {int(_num(row.get('Score')))}", "cyan")
    line = f"Tembus {fmt_id(_num(row.get('Breakout Level')))} · Vol {_num(row.get('Vol x MA20')):.1f}x MA20"
    rows = info_row(line, "bolt")
    _name = get_company_name(saham)
    rows = (info_row(escape(_name)) if _name else "") + rows
    pills = pill(f"Age H+{int(_num(row.get('Age')))}") + pill(f"{_num(row.get('Dist to Level (%)')):+.1f}% dari level")
    if row.get("Streak"):
        pills += pill("Naik 2+ hari beruntun", "cyan")
    if row.get("Narrowing Base"):
        pills += pill("Base makin sempit", "cyan")
    if row.get("From Squeeze"):
        pills += pill("Dari Quiet Accumulation", "cyan")
    if row.get("Volatile Tinggi"):
        atr = row.get("ATR % Now")
        label = f"Volatilitas tinggi (ATR {_num(atr):.0f}%)" if atr is not None and pd.notna(atr) else "Volatilitas tinggi"
        pills += pill(label, "amber")
    if not row.get("Candle Final", True):
        pills += pill("Candle belum final", "amber")
    return build_card(is_selected, saham, badges, price, chg, rows, pills)


def _reset_card(row, is_selected):
    saham = str(row.get("Saham", ""))
    price = _num(row.get("Close_Price")); chg = _num(row.get("Change_Pct"))
    badges = pill(f"Score {int(_num(row.get('Score')))}", "cyan")
    line = f"Koreksi {_num(row.get('Depth From High (%)')):.1f}% dari puncak {fmt_id(_num(row.get('Recent High')))}"
    rows = info_row(line, "trending-down")
    _name = get_company_name(saham)
    rows = (info_row(escape(_name)) if _name else "") + rows
    pills = ""
    if row.get("Near EMA20"):
        pills += pill("Pantul di EMA20", "cyan")
    if row.get("Vol Bounce"):
        pills += pill("Volume balik naik", "cyan")
    if row.get("Reversal Candle"):
        pills += pill("Candle balik arah", "cyan")
    if row.get("Volatile Tinggi"):
        atr = row.get("ATR % Now")
        label = f"Volatilitas tinggi (ATR {_num(atr):.0f}%)" if atr is not None and pd.notna(atr) else "Volatilitas tinggi"
        pills += pill(label, "amber")
    if not row.get("Candle Final", True):
        pills += pill("Candle belum final", "amber")
    return build_card(is_selected, saham, badges, price, chg, rows, pills)


def _squeeze_card(row, is_selected):
    saham = str(row.get("Saham", ""))
    price = _num(row.get("Close_Price")); chg = _num(row.get("Change_Pct"))
    badges = pill(f"{int(_num(row.get('Squeeze Days')))} hari", "cyan")
    line = f"Rentang tersempit dalam {int(_num(row.get('Narrowest In (Days)')))} hari"
    rows = info_row(line, "hourglass")
    _name = get_company_name(saham)
    rows = (info_row(escape(_name)) if _name else "") + rows
    pills = pill(f"Volume +{_num(row.get('Vol Increase (%)')):.0f}% dari biasa", "cyan")
    if row.get("Volatile Tinggi"):
        atr = row.get("ATR % Now")
        label = f"Volatilitas tinggi (ATR {_num(atr):.0f}%)" if atr is not None and pd.notna(atr) else "Volatilitas tinggi"
        pills += pill(label, "amber")
    if not row.get("Candle Final", True):
        pills += pill("Candle belum final", "amber")
    return build_card(is_selected, saham, badges, price, chg, rows, pills)


_CARD_FN = {"Breakout Surge": _breakout_card, "Trend Reset": _reset_card, "Quiet Accumulation": _squeeze_card}


def _sel_key(mode):
    return f"selected_trend_ticker__{mode}"


def render_tab_trend():
    st.markdown(
        compact_html(
            f"""<div class="zq-hero">
<h1>{svg_icon("bolt", 24, "#00F3FF", 2, margin_right=8)}TREND SCANNER</h1>
<p>Breakout Surge, Trend Reset, dan Quiet Accumulation -- struktur harga & volume, bukan oscillator.</p>
</div>"""
        ),
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 5])
    with c1:
        run_clicked = st.button("Run Screening", key="btn_run_trend_scanner", type="primary", use_container_width=True, **icon_kwargs("bolt"))
    with c2:
        stop_clicked = st.button("Stop", key="btn_stop_trend_scanner", use_container_width=True, **icon_kwargs("stop_circle"))
    if stop_clicked:
        st.session_state["stop_trend_scan"] = True

    if run_clicked:
        st.session_state["stop_trend_scan"] = False
        with st.spinner("Mengambil daftar saham..."):
            all_tickers = get_all_ihsg_tickers()
        if not all_tickers:
            st.warning("Daftar saham kosong, tidak ada yang bisa di-scan.")
        else:
            data_map, source_text = prepare_batch_source()
            pbar, pstatus = st.progress(0), st.empty()

            def _progress(done, total):
                pbar.progress(min(1.0, done / total) if total else 0)
                pstatus.text(f"Scanning: {done}/{total} saham...")

            def _phase(phase, batch_no, n_batches, first, last, total):
                pstatus.text(f"Downloading batch {batch_no}/{n_batches} (saham {first}-{last} dari {total})...")

            df_b, df_r, df_s, info = run_trend_screener(
                all_tickers, progress_callback=_progress, phase_callback=_phase, data=data_map,
                should_stop=lambda: st.session_state.get("stop_trend_scan", False),
            )
            pstatus.empty(); pbar.empty()
            if data_map and info.get("downloaded"):
                source_text += f" · {info['downloaded']} saham tidak ada di file, diambil langsung"
            st.session_state[_KEY["Breakout Surge"]] = df_b
            st.session_state[_KEY["Trend Reset"]] = df_r
            st.session_state[_KEY["Quiet Accumulation"]] = df_s
            st.session_state["trend_source_text"] = source_text
            st.session_state["trend_info"] = info
            for m in _MODES:
                df_m = st.session_state[_KEY[m]]
                st.session_state[_sel_key(m)] = df_m.iloc[0]["Ticker"] if not df_m.empty else None
            first = next((m for m in _MODES if not st.session_state[_KEY[m]].empty), None)
            st.session_state["trend_mode_select"] = first or "Breakout Surge"

    has_results = "trend_info" in st.session_state
    if not has_results:
        st.info("Klik **Run Screening** untuk memindai pasar.")
        return

    info = st.session_state["trend_info"]
    cards = "".join(
        f'<div class="zq-card"><div class="zq-stat-label">{escape(label)}</div><div class="zq-stat-value" style="{f"color:{color};" if color else ""}">{val}</div></div>'
        for label, val, color in (
            ("Total Scanned", info["total"], None), ("Breakout Surge", info["matched_breakout"], GREEN),
            ("Trend Reset", info["matched_reset"], CYAN), ("Quiet Accumulation", info["matched_squeeze"], AMBER),
        )
    )
    st.markdown(compact_html(f'<div class="zq-grid zq-grid4">{cards}</div>'), unsafe_allow_html=True)

    st.markdown(section_label("adjustments-horizontal", "MODE"), unsafe_allow_html=True)
    col_mode, col_export = st.columns([3.2, 0.8], vertical_alignment="bottom")
    with col_mode:
        mode = st.selectbox("Mode", options=list(_MODES), key="trend_mode_select", label_visibility="collapsed")
    df_target = st.session_state.get(_KEY[mode], pd.DataFrame())
    with col_export:
        if not df_target.empty:
            st.download_button("CSV", df_target.to_csv(index=False).encode("utf-8"), file_name=f"trend_{mode.lower().replace(' ', '_')}.csv",
                                mime="text/csv", use_container_width=True, **icon_kwargs("download", "download_button"))
        else:
            st.button("CSV", disabled=True, use_container_width=True, **icon_kwargs("download"))

    st.caption(_DESC[mode])
    st.markdown(source_note_html(st.session_state.get("trend_source_text", "")), unsafe_allow_html=True)
    if mode == "Quiet Accumulation":
        st.caption("Mode ini tanpa skor dan tanpa arah beli/jual -- murni daftar pantau.")

    if df_target.empty:
        st.info(f"Tidak ada saham yang cocok untuk {mode} pada data saat ini.")
        return

    card_fn = _CARD_FN[mode]
    sel_key = _sel_key(mode)
    with st.container(height=700, border=False):
        for idx, row in df_target.iterrows():
            ticker = str(row.get("Ticker", "")); saham = ticker.replace(".JK", "")
            is_selected = st.session_state.get(sel_key) == ticker
            st.markdown(card_fn(row, is_selected), unsafe_allow_html=True)
            btn_label = f"SELECTED ({saham})" if is_selected else f"SELECT {saham}"
            if st.button(btn_label, key=f"select_trend_btn_{mode}_{ticker}_{idx}", use_container_width=True, type="primary" if is_selected else "secondary", **(icon_kwargs("check") if is_selected else {})):
                st.session_state[sel_key] = ticker
                st.rerun()
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

    if mode != "Quiet Accumulation" and st.session_state.get(sel_key):
        render_inline_trade_planner(st.session_state[sel_key].replace(".JK", ""), key_suffix="trend", screener_name="Trend Scanner")
