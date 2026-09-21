"""Halaman Home: hero, ringkasan pribadi, arah pasar (IHSG), Market Pulse, rekap screener harian dan mingguan."""
from html import escape

import pandas as pd
import streamlit as st

from engines import market_view as MVW
from engines import recap as RC
from utils.card_html import GREEN, PINK, compact_html, fmt_id
from utils.icons import svg_icon
from utils import market_source, watchlist_store
from utils.profile import current_profile
from utils.pages import get_pages, keyed_container, link_width_kwargs
from utils.screeners import get_screener
from views.footer import fetch_ihsg, fmt_id_num
from views.home_today import MODE_COLOR, render_today_block

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
    try:
        return len(watchlist_store.load_watchlist())
    except Exception:
        return 0


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

AMBER = "#E3B341"


# ---------------------------------------------------------------- arah pasar (IHSG)
@st.cache_data(ttl=600, show_spinner=False)
def _cached_market_view(stamp):
    ihsg = market_source.load_ihsg()
    if ihsg is None:
        return None
    data_map, meta = market_source.load_shared_file()
    breadth = MVW.compute_breadth(data_map, meta.get("last_candle_date", "")) if data_map and meta else None
    return MVW.build_market_view(ihsg, breadth)


def _factor_rows(view):
    rows = ""
    for f in view["mode"]["factors"]:
        col = "#00FF66" if f["points"] > 0 else ("#FF007F" if f["points"] < 0 else "#8B949E")
        rows += (
            f'<div class="zq-row"><span>{escape(f["label"])}</span><span class="zq-muted">{escape(str(f["value"]))}</span>'
            f'<span style="color:{col};">{escape(f["note"])}</span></div>'
        )
    return rows


def _levels_html(view):
    lv = view["levels"]

    def row(tag, x, color):
        return (
            f'<div class="zq-row"><span style="color:{color}; font-weight:700;">{tag}</span>'
            f'<span>{MVW.id_num(x["price"])}</span><span class="zq-muted">{MVW.id_pct(x["pct"], 1, True)} · kekuatan {x["strength"]}</span></div>'
        )

    body = ""
    for i, x in reversed(list(enumerate(lv["resistances"], 1))):
        body += row(f"R{i}", x, "#FF007F")
    if not lv["resistances"]:
        body += '<div class="zq-row"><span style="color:#FF007F; font-weight:700;">R</span><span class="zq-muted">tidak ada resisten historis terdekat</span></div>'
    body += (
        f'<div class="zq-row" style="border-top:1px solid #30363D; border-bottom:1px solid #30363D;"><span style="color:#FFFFFF; font-weight:800;">IHSG</span>'
        f'<span style="color:#FFFFFF; font-weight:800;">{MVW.id_num(view["close"])}</span><span class="zq-muted">{MVW.id_pct(view["chg"], 2, True)} · per {escape(pd.to_datetime(view["asof"]).strftime("%d %b %Y"))}</span></div>'
    )
    for i, x in enumerate(lv["supports"], 1):
        body += row(f"S{i}", x, "#00FF66")
    if not lv["supports"]:
        body += '<div class="zq-row"><span style="color:#00FF66; font-weight:700;">S</span><span class="zq-muted">tidak ada support terdekat</span></div>'
    return body


def render_market_view(view):
    _html(_label("compass", "Arah Pasar (IHSG)"))
    if not view:
        st.info("Analisis arah pasar tampil setelah data harian versi terbaru berjalan (butuh riwayat IHSG dan histori saham 12 bulan).")
        return
    m = view["mode"]
    col = MODE_COLOR[m["mode"]]
    c1, c2 = st.columns([3, 2])
    with c1:
        _html(
            f'<div class="zq-card" style="height:100%;"><div class="zq-stat-label">Mode pasar</div>'
            f'<div style="font-size:26px; font-weight:800; color:{col};">{escape(m["label"])} '
            f'<span class="zq-muted" style="font-size:13px; font-weight:600;">skor {m["score"]:+d}</span></div>'
            f'<div class="zq-muted" style="font-size:12px; margin-bottom:8px;">{escape(m["desc"])}</div>{_factor_rows(view)}'
            f'<div class="zq-muted" style="font-size:11px; margin-top:6px;">Skor dari {m["n_factors"]} faktor di atas. Agresif jika skor +3 atau lebih, Defensif jika -3 atau kurang, selain itu Netral.</div></div>'
        )
    with c2:
        _html(f'<div class="zq-card" style="height:100%;"><div class="zq-stat-label">Level penting</div>{_levels_html(view)}</div>')
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    lines = "".join(f'<div style="margin:3px 0; font-size:13px; color:#C9D1D9;">{escape(x)}</div>' for x in view["outlook"])
    _html(
        f'<div class="zq-card"><div style="color:#00F3FF; font-weight:800; margin-bottom:6px;">{svg_icon("bulb", 15, "#00F3FF", 2, margin_right=6)}Pandangan otomatis</div>{lines}'
        '<div class="zq-muted" style="font-size:11px; margin-top:6px;">Pandangan teknikal yang dihitung otomatis dari data harga IHSG dan sebaran saham. Bukan prediksi dan bukan rekomendasi.</div></div>'
    )


# ---------------------------------------------------------------- rekap screener
def _names(rows, n=3):
    return ", ".join(f"{escape(r['t'].replace('.JK', ''))} ({r['s']:g})" for r in rows[:n]) or "-"


def _daily_card(key, name, history):
    cat = get_screener(key)["category"]
    dr = RC.daily_recap(history, key)
    days = (history or {}).get("days") or {}
    last = days[sorted(days)[-1]] if days else {}
    head = (
        f'<span class="zq-chip">{escape(cat)}</span>'
        f'<div style="color:#FFFFFF; font-size:16px; font-weight:800;">{escape(name)}</div>'
    )
    if dr is None:
        msg = "Screener ini gagal dijalankan pada update terakhir." if "error" in last.get(key, {}) else "Belum ada hasil harian."
        return f'<div class="zq-card">{head}<div class="zq-muted" style="font-size:12px; margin-top:6px;">{msg}</div></div>'
    new_b = f" ({dr['n_new_bull']} baru)" if dr["n_new_bull"] is not None else ""
    new_r = f" ({dr['n_new_bear']} baru)" if dr["n_new_bear"] is not None else ""
    return (
        f'<div class="zq-card">{head}<div class="zq-muted" style="font-size:11px; margin-bottom:6px;">Data per {escape(pd.to_datetime(dr["date"]).strftime("%d %b %Y"))}</div>'
        f'<div class="zq-row"><span style="color:{GREEN}; font-weight:700;">Bullish</span><span>{dr["n_bull"]}{new_b}</span></div>'
        f'<div class="zq-muted" style="font-size:12px; margin-bottom:4px;">Teratas: {_names(dr["top_bull"])}</div>'
        f'<div class="zq-row"><span style="color:{PINK}; font-weight:700;">Bearish</span><span>{dr["n_bear"]}{new_r}</span></div>'
        f'<div class="zq-muted" style="font-size:12px;">Teratas: {_names(dr["top_bear"])}</div></div>'
    )


def _weekly_card(key, name, history, last_close):
    cat = get_screener(key)["category"]
    w = RC.weekly_recap(history, key, last_close)
    head = f'<span class="zq-chip">{escape(cat)}</span><div style="color:#FFFFFF; font-size:16px; font-weight:800;">{escape(name)}</div>'
    if w is None:
        return f'<div class="zq-card">{head}<div class="zq-muted" style="font-size:12px; margin-top:6px;">Belum ada riwayat mingguan.</div></div>'
    body = f'<div class="zq-muted" style="font-size:11px; margin-bottom:6px;">{len(w["dates"])} hari bursa terakhir · {w["n_unique"]} saham unik</div>'
    for d, tag, col in (("bull", "Bullish", GREEN), ("bear", "Bearish", PINK)):
        x = w[d]
        if x["n_measured"]:
            eg = MVW.id_pct(x["avg_edge"], 1, True)
            res = f'{x["n_right"]} dari {x["n_measured"]} searah sinyal · rata-rata {eg}'
        else:
            res = "belum ada yang bisa diukur"
        body += f'<div class="zq-row"><span style="color:{col}; font-weight:700;">{tag}</span><span>{x["n"]} saham</span></div><div class="zq-muted" style="font-size:12px; margin-bottom:4px;">{res}</div>'
    rep = sorted(w["bull"]["repeat"] + w["bear"]["repeat"], key=lambda r: (-r["days"], r["t"]))[:3]
    if rep:
        body += '<div class="zq-muted" style="font-size:12px;">Muncul berulang: ' + ", ".join(f'{escape(r["t"].replace(".JK", ""))} ({r["days"]} hari)' for r in rep) + "</div>"
    return f'<div class="zq-card">{head}{body}</div>'


def render_recaps():
    history = market_source.load_recap()
    days = (history or {}).get("days") or {}
    _html(_label("calendar-event", "Rekap Screener Harian"))
    if not days:
        st.info("Rekap tampil setelah data harian versi terbaru berjalan. Hasilnya memakai pengaturan bawaan tiap screener.")
        return
    pages, width = get_pages(), link_width_kwargs()
    cols = st.columns(len(RC.SCREENERS))
    for col, (key, name) in zip(cols, RC.SCREENERS):
        with col:
            _html(_daily_card(key, name, history))
            with keyed_container(f"zopen_{key}"):
                st.page_link(pages[key], label=f"Open {name}", icon=":material/arrow_forward:", **width)
    st.caption("Rekap memakai pengaturan bawaan tiap screener, jadi bisa berbeda dari hasil di halaman screener kalau kamu mengubah pilihan di sana.")

    data_map, _ = market_source.load_shared_file()
    want = {h["t"] for d in sorted(days)[-5:] for e in days[d].values() if isinstance(e, dict) for h in e.get("hits", [])}
    last_close = {}
    for t in want:
        df = (data_map or {}).get(t)
        try:
            if df is not None and len(df):
                last_close[t] = float(df["Close"].iloc[-1])
        except Exception:
            pass
    _html(_label("calendar-week", "Rekap Mingguan"))
    cols = st.columns(len(RC.SCREENERS))
    for col, (key, name) in zip(cols, RC.SCREENERS):
        with col:
            _html(_weekly_card(key, name, history, last_close))
    st.caption("Hasil = perubahan harga dari harga sinyal sampai penutupan terakhir, searah sinyal (bearish: turun dihitung sesuai), belum termasuk biaya. Sampel kecil dan hasil masa lalu bukan jaminan.")


def _safe(fn, *args):
    """Satu bagian Home yang error tidak boleh membuat seluruh Home kosong."""
    try:
        return fn(*args)
    except Exception:
        st.caption("Bagian ini belum bisa ditampilkan. Coba muat ulang halaman.")
        return None


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
            st.page_link(pages["how_to"], label="Learn", icon=":material/menu_book:", **width)

    _, meta = market_source.load_shared_file()
    stamp = f"{(meta or {}).get('last_candle_date', '')}|{(meta or {}).get('updated_at_wib', '')}"
    view = _safe(_cached_market_view, stamp) if meta else None

    render_today_block(view)
    _safe(render_market_view, view)
    render_market_pulse()
    _safe(render_recaps)

    n_wl = _watchlist_count()
    _html(_label("bookmarks", "Watchlist"))
    w1, w2 = st.columns([3, 1], vertical_alignment="center")
    with w1:
        _html(
            f'<div class="zq-card"><span style="color:#FFFFFF; font-size:18px; font-weight:800;">{n_wl}</span> '
            f'<span class="zq-muted">saham di watchlist kamu</span>'
            + (
                ""
                if current_profile()
                else '<div class="zq-muted" style="font-size:11px; margin-top:4px;">Guest mode: buat profil di halaman Watchlist supaya tersimpan.</div>'
            )
            + "</div>"
        )
    with w2:
        with keyed_container("zopen_watchlist"):
            st.page_link(pages["watchlist"], label="Open watchlist", icon=":material/bookmarks:", **width)

    _html(
        '<div class="zq-disclaimer">Semua data dan trade plan di sini hasil perhitungan sistem, bukan rekomendasi '
        "investasi. Cek ulang chart dan terapkan money management. Do Your Own Research (DYOR), Do With Your Own Risk (DWYOR).</div>"
    )
