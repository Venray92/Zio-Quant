"""Halaman MACD Momentum: crossover MACD, filter tren EMA, ADX (tren baru lahir vs noise), volume,
candle. Layout 2 kolom sama seperti RSI/Stoch/Trend Scanner (kiri list+kontrol, kanan Trade Plan)."""
from html import escape

import pandas as pd
import streamlit as st

from data.ihsg_tickers import get_all_ihsg_tickers
from engines.screener_macd import run_macd_screener
from utils.card_html import build_card, compact_html, info_row, pill, score_badge, section_label, source_note_html
from utils.compat import STRETCH
from utils.icons import icon_kwargs, svg_icon
from utils.market_source import prepare_batch_source
from utils.pages import keyed_container
from utils.ui_helpers import render_inline_trade_planner

GREEN, CYAN, AMBER = "#00FF66", "#00F3FF", "#E3B341"
_MODES = ("Golden Cross", "Dead Cross")
_DESC = {
    "Golden Cross": "Garis MACD baru motong ke atas garis Sinyal, di tren naik, dikonfirmasi ADX & volume.",
    "Dead Cross": "Garis MACD baru motong ke bawah garis Sinyal, di tren turun -- peringatan, bukan otomatis sinyal jual.",
}


def _num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _macd_card_html(row, is_selected, is_gc):
    saham = str(row.get("Saham", ""))
    price, chg = _num(row.get("Close_Price")), _num(row.get("Change_Pct"))
    badges = score_badge(int(_num(row.get("Score"))))
    kind = "Golden Cross" if is_gc else "Dead Cross"
    line = f"{kind} · MACD {_num(row.get('MACD')):.1f} / Sinyal {_num(row.get('Signal')):.1f} · ADX {_num(row.get('ADX')):.0f}"
    rows = info_row(line, "chart-candle")
    pills = pill(f"Age H+{int(_num(row.get('Age')))}")
    if row.get("Fresh Trend"):
        pills += pill("Tren baru lahir (ADX)", "cyan")
    if row.get("Above Zero"):
        pills += pill("Di atas garis 0" if is_gc else "Di bawah garis 0", "cyan")
    if row.get("Strong Candle"):
        pills += pill("Candle kuat", "cyan")
    if bool(row.get("Volatile Tinggi", False)):
        atr = row.get("ATR % Now")
        label = f"Volatilitas tinggi (ATR {_num(atr):.0f}%)" if atr is not None and pd.notna(atr) else "Volatilitas tinggi"
        pills += pill(label, "amber")
    if not row.get("Candle Final", True):
        pills += pill("Candle belum final", "amber")
    return build_card(is_selected, saham, badges, price, chg, rows, pills)


def _sel_key(mode):
    return f"selected_macd_ticker__{mode}"


def _key(mode):
    return "df_macd_gc" if mode == "Golden Cross" else "df_macd_dc"


def _run_scan():
    st.session_state["stop_macd_scan"] = False
    with st.spinner("Mengambil daftar saham..."):
        all_tickers = get_all_ihsg_tickers()
    if not all_tickers:
        st.warning("Daftar saham kosong, tidak ada yang bisa di-scan.")
        return
    data_map, source_text = prepare_batch_source()
    pbar, pstatus = st.progress(0), st.empty()

    def _progress(done, total):
        pbar.progress(min(1.0, done / total) if total else 0)
        pstatus.text(f"Scanning: {done}/{total} saham...")

    def _phase(phase, batch_no, n_batches, first, last, total):
        pstatus.text(f"Downloading batch {batch_no}/{n_batches} (saham {first}-{last} dari {total})...")

    df_gc, df_dc, info = run_macd_screener(
        all_tickers, progress_callback=_progress, phase_callback=_phase, data=data_map,
        should_stop=lambda: st.session_state.get("stop_macd_scan", False),
    )
    pstatus.empty(); pbar.empty()
    if data_map and info.get("downloaded"):
        source_text += f" · {info['downloaded']} saham tidak ada di file, diambil langsung"
    st.session_state["df_macd_gc"] = df_gc
    st.session_state["df_macd_dc"] = df_dc
    st.session_state["macd_source_text"] = source_text
    st.session_state["macd_info"] = info
    for m in _MODES:
        df_m = st.session_state[_key(m)]
        st.session_state[_sel_key(m)] = df_m.iloc[0]["Ticker"] if not df_m.empty else None
    first = "Golden Cross" if not df_gc.empty else ("Dead Cross" if not df_dc.empty else "Golden Cross")
    st.session_state["macd_mode_select"] = first


def render_tab_macd():
    st.markdown(
        compact_html(
            f"""<div class="zq-hero">
<h1>{svg_icon("bolt", 24, "#00F3FF", 2, margin_right=8)}MACD MOMENTUM</h1>
<p>Crossover MACD dikonfirmasi ADX (tren baru lahir vs cuma noise), filter tren EMA, volume, dan candle.</p>
</div>"""
        ),
        unsafe_allow_html=True,
    )

    with keyed_container("zworkspace_macd"):
        col_left, col_right = st.columns([1.3, 2.7], gap="medium")

    with col_left:
        c1, c2 = st.columns(2)
        with c1:
            run_clicked = st.button("Run Screening", key="btn_run_macd_scan", type="primary", **STRETCH, **icon_kwargs("play_arrow"))
        with c2:
            stop_clicked = st.button("Stop", key="btn_stop_macd_scan", **STRETCH, **icon_kwargs("stop_circle"))
        if stop_clicked:
            st.session_state["stop_macd_scan"] = True
        if run_clicked:
            _run_scan()

        if "macd_info" not in st.session_state:
            st.info("Klik **Run Screening** untuk memindai pasar.")
            mode = None
        else:
            st.markdown(section_label("adjustments-horizontal", "MODE"), unsafe_allow_html=True)
            col_mode, col_export = st.columns([3.2, 0.8], vertical_alignment="bottom")
            with col_mode:
                with keyed_container("zmacd_mode"):
                    mode = st.selectbox("Mode", options=list(_MODES), key="macd_mode_select", label_visibility="collapsed")
            df_target = st.session_state.get(_key(mode), pd.DataFrame())
            with col_export:
                if not df_target.empty:
                    st.download_button("CSV", df_target.to_csv(index=False).encode("utf-8"), file_name=f"macd_{mode.lower().replace(' ', '_')}.csv",
                                        mime="text/csv", **STRETCH, **icon_kwargs("download", "download_button"))
                else:
                    st.button("CSV", disabled=True, **STRETCH, **icon_kwargs("download"))

            st.caption(_DESC[mode])
            st.markdown(source_note_html(st.session_state.get("macd_source_text", "")), unsafe_allow_html=True)

            if df_target.empty:
                st.info(f"Tidak ada saham yang cocok untuk {mode} pada data saat ini.")
            else:
                sel_key = _sel_key(mode)
                with st.container(height=800, border=False):
                    for idx, row in df_target.iterrows():
                        ticker = str(row.get("Ticker", "")); saham = ticker.replace(".JK", "")
                        is_selected = st.session_state.get(sel_key) == ticker
                        st.markdown(_macd_card_html(row, is_selected, mode == "Golden Cross"), unsafe_allow_html=True)
                        btn_label = f"SELECTED ({saham})" if is_selected else f"SELECT {saham}"
                        if st.button(btn_label, key=f"select_macd_btn_{mode}_{ticker}_{idx}", **STRETCH,
                                     type="primary" if is_selected else "secondary", **(icon_kwargs("check") if is_selected else {})):
                            st.session_state[sel_key] = ticker
                            st.rerun()
                        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

    with col_right:
        if "macd_info" in st.session_state:
            info = st.session_state["macd_info"]
            cards = "".join(
                f'<div class="zq-card"><div class="zq-stat-label">{escape(label)}</div><div class="zq-stat-value" style="{f"color:{color};" if color else ""}">{val}</div></div>'
                for label, val, color in (
                    ("Total Scanned", info["total"], None), ("Golden Cross", info["matched_gc"], GREEN), ("Dead Cross", info["matched_dc"], "#FF007F"),
                )
            )
            st.markdown(compact_html(f'<div class="zq-grid zq-grid4">{cards}</div>'), unsafe_allow_html=True)

        selected = st.session_state.get(_sel_key(mode)) if mode else None
        if selected:
            try:
                render_inline_trade_planner(selected, key_suffix="macd", screener_name="MACD Momentum")
            except Exception as e:
                st.error(f"Trade Plan untuk {selected} belum bisa dimuat: {e}")
        elif mode:
            st.info("Pilih saham di daftar kiri untuk melihat Trade Plan.")
        else:
            st.markdown(
                compact_html(
                    f"""<div class="zq-card"><div style="color:#FFFFFF; font-weight:800; margin-bottom:6px;">{svg_icon("help-circle", 15, "#00F3FF", 2, margin_right=6)}Cara pakai</div>
<div class="zq-muted" style="font-size:13px;"><b>Golden Cross</b>: {escape(_DESC["Golden Cross"])}<br><b>Dead Cross</b>: {escape(_DESC["Dead Cross"])}<br><br>Klik Run Screening, pilih mode, lalu pilih saham. Trade Plan muncul di panel ini.</div></div>"""
                ),
                unsafe_allow_html=True,
            )
