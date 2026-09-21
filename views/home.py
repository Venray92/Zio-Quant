"""Halaman Home: hero, Market Pulse (dari file harian), kartu screener, quick start."""
from html import escape

import pandas as pd
import streamlit as st

from utils.card_html import compact_html, fmt_id
from utils.icons import svg_icon
from utils import market_source
from utils.pages import get_pages, keyed_container, link_width_kwargs
from utils.screeners import SCREENERS
from views.footer import fetch_ihsg, fmt_id_num

MIN_VALUE_RP = 1_000_000_000  # likuiditas minimal untuk daftar gainer/loser (rata-rata 20 hari)
MIN_PRICE = 50


def _label(icon, text):
    return f'<div class="zq-label">{svg_icon(icon, 13, "#FF007F", 2)}{escape(text)}</div>'


def _html(s):
    st.markdown(compact_html(s), unsafe_allow_html=True)


def compute_pulse(data_map, last_date):
    """Ringkasan pasar dari file harian. Hanya saham yang punya candle di tanggal terakhir."""
    rows = []
    for ticker, df in (data_map or {}).items():
        try:
            if df is None or len(df) < 2:
                continue
            dates = pd.to_datetime(df["Date"]) if "Date" in df.columns else pd.to_datetime(df.index)
            if pd.Timestamp(dates.iloc[-1]).strftime("%Y-%m-%d") != str(last_date)[:10]:
                continue
            c1, c0 = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
            if c0 <= 0 or c1 <= 0:
                continue
            value = (df["Close"] * df["Volume"]).astype(float)
            rows.append(
                {
                    "Ticker": str(ticker).replace(".JK", ""),
                    "Close": c1,
                    "Chg": (c1 - c0) / c0 * 100,
                    "Value": float(value.iloc[-1]),
                    "Avg20": float(value.tail(20).mean()),
                }
            )
        except Exception:
            continue
    df = pd.DataFrame(rows)
    if df.empty:
        return None
    liquid = df[(df["Avg20"] >= MIN_VALUE_RP) & (df["Close"] >= MIN_PRICE)]
    return {
        "total": len(df),
        "up": int((df["Chg"] > 0).sum()),
        "down": int((df["Chg"] < 0).sum()),
        "flat": int((df["Chg"] == 0).sum()),
        "gainers": liquid.sort_values("Chg", ascending=False, kind="stable").head(5).to_dict("records"),
        "losers": liquid.sort_values("Chg", ascending=True, kind="stable").head(5).to_dict("records"),
        "value": df.sort_values("Value", ascending=False, kind="stable").head(5).to_dict("records"),
    }


@st.cache_data(ttl=600, show_spinner=False)
def _cached_pulse(stamp):
    data_map, meta = market_source.load_shared_file()
    if not data_map or not meta:
        return None
    return compute_pulse(data_map, meta.get("last_candle_date", ""))


def _value_text(v):
    if v >= 1e12:
        return f"Rp {fmt_id_num(v / 1e12, 1)} T"
    if v >= 1e9:
        return f"Rp {fmt_id_num(v / 1e9, 1)} M"
    return f"Rp {fmt_id(v)}"


def _chg_html(chg):
    cls = "zq-up" if chg > 0 else ("zq-down" if chg < 0 else "zq-muted")
    return f'<span class="{cls}">{"+" if chg > 0 else ""}{fmt_id_num(chg)}%</span>'


def _list_card(title, icon, rows, kind):
    if not rows:
        body = '<div class="zq-muted" style="font-size:12px;">Belum ada data.</div>'
    else:
        body = "".join(
            f'<div class="zq-row"><span style="color:#FFFFFF; font-weight:700;">{escape(r["Ticker"])}</span>'
            f'<span class="zq-muted">{fmt_id(r["Close"])}</span>'
            + (f'<span>{_value_text(r["Value"])}</span>' if kind == "value" else _chg_html(r["Chg"]))
            + "</div>"
            for r in rows
        )
    return (
        f'<div class="zq-card"><div class="zq-stat-label" style="margin-bottom:4px;">'
        f'{svg_icon(icon, 13, "#00F3FF", 2, margin_right=4)}{escape(title)}</div>{body}</div>'
    )


def _stat(label, value_html, sub_html=""):
    return (
        f'<div class="zq-card"><div class="zq-stat-label">{escape(label)}</div>'
        f'<div class="zq-stat-value">{value_html}</div><div class="zq-stat-sub">{sub_html}</div></div>'
    )


def _watchlist_count():
    items = st.session_state.get("watchlist_data")
    if items is None:
        try:
            from views.watchlist import load_watchlist_from_file

            items = load_watchlist_from_file()
        except Exception:
            items = []
    return len(items or [])


def render_market_pulse():
    data_map, meta = market_source.load_shared_file()
    stamp = f"{(meta or {}).get('last_candle_date', '')}|{(meta or {}).get('updated_at_wib', '')}"
    pulse = _cached_pulse(stamp) if meta else None
    ihsg = fetch_ihsg()

    date_txt = ""
    if meta and meta.get("last_candle_date"):
        try:
            date_txt = pd.to_datetime(meta["last_candle_date"]).strftime("%d %b %Y")
        except Exception:
            date_txt = str(meta["last_candle_date"])

    _html(
        _label("world", "Market Pulse")
        + (
            f'<div class="zq-muted" style="font-size:11px; margin:-4px 0 8px 0;">'
            f'{svg_icon("database", 12, "#8B949E", 1.8, margin_right=4)}Data penutupan {escape(date_txt)} (file harian, bukan real-time)</div>'
            if date_txt
            else ""
        )
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if ihsg:
            _html(_stat("IHSG", fmt_id_num(ihsg["last"]), _chg_html(ihsg["chg"]) + f' <span class="zq-muted">· {escape(ihsg["date"])}</span>'))
        else:
            _html(_stat("IHSG", '<span class="zq-muted">-</span>', '<span class="zq-muted">Tidak tersedia</span>'))

    if not pulse:
        with c2:
            _html(_stat("Naik / turun", '<span class="zq-muted">-</span>'))
        with c3:
            _html(_stat("Top gainer", '<span class="zq-muted">-</span>'))
        with c4:
            _html(_stat("Top value", '<span class="zq-muted">-</span>'))
        st.info("Market Pulse tampil setelah data harian tersedia. Data diperbarui otomatis tiap hari bursa sekitar 17:30 WIB.")
        return

    up_pct = pulse["up"] / pulse["total"] * 100 if pulse["total"] else 0
    down_pct = pulse["down"] / pulse["total"] * 100 if pulse["total"] else 0
    bar = (
        '<div style="display:flex; height:5px; border-radius:3px; overflow:hidden; background:#30363D; margin-top:6px;">'
        f'<div style="width:{up_pct:.1f}%; background:#00FF66;"></div>'
        f'<div style="width:{100 - up_pct - down_pct:.1f}%; background:#30363D;"></div>'
        f'<div style="width:{down_pct:.1f}%; background:#FF007F;"></div></div>'
    )
    with c2:
        _html(
            _stat(
                "Naik / turun",
                f'<span class="zq-up">{pulse["up"]}</span> <span class="zq-muted">/</span> <span class="zq-down">{pulse["down"]}</span>',
                f'<span class="zq-muted">{pulse["flat"]} tetap</span>{bar}',
            )
        )
    with c3:
        g = pulse["gainers"][0] if pulse["gainers"] else None
        _html(_stat("Top gainer", escape(g["Ticker"]) if g else "-", _chg_html(g["Chg"]) if g else ""))
    with c4:
        v = pulse["value"][0] if pulse["value"] else None
        _html(_stat("Top value", escape(v["Ticker"]) if v else "-", f'<span class="zq-muted">{_value_text(v["Value"])}</span>' if v else ""))

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    l1, l2, l3 = st.columns(3)
    with l1:
        _html(_list_card("Top gainers", "trending-up", pulse["gainers"], "chg"))
    with l2:
        _html(_list_card("Top losers", "trending-down", pulse["losers"], "chg"))
    with l3:
        _html(_list_card("Top value", "chart-bar", pulse["value"], "value"))
    st.caption("Gainer/loser hanya saham dengan rata-rata transaksi 20 hari minimal Rp 1 M dan harga minimal Rp 50.")


def render_page_home():
    pages = get_pages()
    width = link_width_kwargs()

    _html(
        """<div class="zq-hero">
<h1>Z-QUANT TERMINAL</h1>
<p>Screener saham IDX: cari sinyal, susun trade plan, lalu atur risiko sebelum entry.</p>
</div>"""
    )
    b1, b2, _ = st.columns([1, 1, 3])
    with b1:
        with keyed_container("zcta_primary"):
            st.page_link(pages["trade_plan"], label="Start screening", icon=":material/play_arrow:", **width)
    with b2:
        with keyed_container("zcta_secondary"):
            st.page_link(pages["how_to"], label="How to use", icon=":material/menu_book:", **width)

    render_market_pulse()

    _html(_label("radar-2", "Screeners"))
    cols = st.columns(len(SCREENERS))
    for col, s in zip(cols, SCREENERS):
        with col:
            _html(
                f"""<div class="zq-card">
<span class="zq-chip">{escape(s["category"])}</span>
<div style="display:flex; align-items:center; gap:8px; color:#FFFFFF; font-size:16px; font-weight:800;">{svg_icon(s["icon"], 18, "#00F3FF", 2)}{escape(s["name"])}</div>
<div class="zq-muted" style="font-size:12px; margin-top:4px;">{escape(s["desc"])}</div>
</div>"""
            )
            with keyed_container(f"zopen_{s['key']}"):
                st.page_link(pages[s["key"]], label=f"Open {s['name']}", icon=":material/arrow_forward:", **width)

    _html(_label("list-numbers", "Quick Start"))
    q1, q2, q3, q4 = st.columns(4)
    steps = [
        ("Pilih screener", "Buka menu Screeners, lalu klik Run Screening."),
        ("Cek trade plan", "Klik saham untuk melihat area buy, SL, TP, dan grade."),
        ("Simpan ke watchlist", "Pantau saham pilihan di halaman Watchlist."),
        ("Atur risiko", "Hitung jumlah lot di Money Management sebelum entry."),
    ]
    for col, (i, (title, desc)) in zip((q1, q2, q3, q4), enumerate(steps, 1)):
        with col:
            _html(
                f'<div class="zq-card"><div style="color:#FFFFFF; font-weight:800; font-size:14px;">'
                f'<span class="zq-step-no">{i}</span>{escape(title)}</div>'
                f'<div class="zq-muted" style="font-size:12px; margin-top:6px;">{escape(desc)}</div></div>'
            )

    n_wl = _watchlist_count()
    _html(_label("bookmarks", "Watchlist"))
    w1, w2 = st.columns([3, 1], vertical_alignment="center")
    with w1:
        _html(
            f'<div class="zq-card"><span style="color:#FFFFFF; font-size:18px; font-weight:800;">{n_wl}</span> '
            f'<span class="zq-muted">saham di watchlist kamu</span></div>'
        )
    with w2:
        with keyed_container("zopen_watchlist"):
            st.page_link(pages["watchlist"], label="Open watchlist", icon=":material/bookmarks:", **width)

    _html(
        '<div class="zq-disclaimer">Semua data dan trade plan di sini hasil perhitungan sistem, bukan rekomendasi '
        "investasi. Cek ulang chart dan terapkan money management. Do Your Own Research (DYOR), Do With Your Own Risk (DWYOR).</div>"
    )
