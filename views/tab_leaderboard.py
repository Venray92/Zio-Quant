"""Leaderboard Screener: ranking win rate & rata-rata edge tiap screener, murni transparansi sistem
(bukan lomba antar-pengguna). Datanya dari engines.recap.leaderboard(), sama seperti rekap Home."""
from html import escape

import streamlit as st

from engines import market_view as MVW
from engines import recap as RC
from utils.card_html import compact_html
from utils.icons import svg_icon
from utils.pages import get_pages, keyed_container, link_width_kwargs
from utils.screeners import get_screener

GREEN, PINK, AMBER = "#00FF66", "#FF007F", "#E3B341"
_CATEGORY = {"rsi": None, "stoch_psar": None, "breakout_surge": "Breakout", "trend_reset": "Pullback"}
_PAGE_KEY = {"rsi": "rsi", "stoch_psar": "stoch_psar", "breakout_surge": "trend_scanner", "trend_reset": "trend_scanner"}
_WINDOW = 20


def _html(s):
    st.markdown(compact_html(s), unsafe_allow_html=True)


def _category(key):
    return _CATEGORY[key] or get_screener(key)["category"]


def _row_html(rank, row):
    wr = row["win_rate"]
    wr_col = GREEN if (wr or 0) >= 55 else (PINK if wr is not None and wr <= 45 else AMBER)
    edge = row["avg_edge"]
    edge_txt = MVW.id_pct(edge, 1, True) if edge is not None else "-"
    medal = f"#{rank}"
    dir_note = "hanya Bullish" if row["single_direction"] else "Bullish & Bearish"
    return (
        f'<div class="zq-card zq-lb-row" style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">'
        f'<div style="font-size:20px; font-weight:800; color:#8B949E; min-width:36px;">{medal}</div>'
        f'<div style="flex:2; min-width:160px;">'
        f'<span class="zq-chip">{escape(_category(row["key"]))}</span>'
        f'<div style="color:#FFFFFF; font-weight:800; font-size:15px;">{escape(row["name"])}</div>'
        f'<div class="zq-muted" style="font-size:11px;">{row["n_measured"]} sinyal terukur ({dir_note}) &bull; {row["n_days"]} hari bursa terakhir</div>'
        f'</div>'
        f'<div class="zq-lb-num" style="text-align:right; min-width:90px;">'
        f'<div style="font-size:20px; font-weight:800; color:{wr_col};">{f"{wr:.0f}%" if wr is not None else "-"}</div>'
        f'<div class="zq-muted" style="font-size:11px;">win rate</div></div>'
        f'<div class="zq-lb-num" style="text-align:right; min-width:80px;">'
        f'<div style="font-size:16px; font-weight:700; color:{GREEN if (edge or 0) >= 0 else PINK};">{edge_txt}</div>'
        f'<div class="zq-muted" style="font-size:11px;">rata-rata edge</div></div>'
        f'</div>'
    )


def render_page_leaderboard():
    _html(
        f"""<div class="zq-hero">
<h1>{svg_icon("trophy", 24, "#00F3FF", 2, margin_right=8)}LEADERBOARD SCREENER</h1>
<p>Screener mana yang paling akurat belakangan ini -- transparansi sistem, bukan lomba antar pengguna.</p>
</div>"""
    )

    from utils import market_source

    history = market_source.load_recap()
    if not (history or {}).get("days"):
        st.info("Leaderboard tampil setelah rekap harian versi terbaru berjalan beberapa hari.")
        return

    days = history["days"]
    want = {h["t"] for d in sorted(days)[-_WINDOW:] for e in days[d].values() if isinstance(e, dict) for h in e.get("hits", [])}
    data_map, _ = market_source.load_shared_file()
    last_close = {}
    for t in want:
        df = (data_map or {}).get(t)
        try:
            if df is not None and len(df):
                last_close[t] = float(df["Close"].iloc[-1])
        except Exception:
            pass

    rows = RC.leaderboard(history, last_close, window=_WINDOW)
    measured = [r for r in rows if r["win_rate"] is not None]
    if not measured:
        st.info("Belum ada sinyal yang bisa diukur hasilnya (butuh waktu berjalan dulu sejak sinyal muncul).")
        return

    st.caption(f"Berdasarkan sinyal {_WINDOW} hari bursa terakhir, diukur sampai harga penutupan terbaru. Hasil masa lalu bukan jaminan hasil ke depan -- sampel bisa masih kecil di awal.")
    pages, width = get_pages(), link_width_kwargs()
    rank = 1
    for row in rows:
        if row["win_rate"] is None:
            continue
        _html(_row_html(rank, row))
        page_key = _PAGE_KEY[row["key"]]
        with keyed_container(f"zlb_open_{row['key']}"):
            st.page_link(pages[page_key], label=f"Open {row['name']}", icon=":material/arrow_forward:", **width)
        st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
        rank += 1

    skipped = [r for r in rows if r["win_rate"] is None]
    if skipped:
        st.caption("Belum cukup data terukur: " + ", ".join(r["name"] for r in skipped))
