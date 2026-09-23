"""Blok "Untuk kamu hari ini" di atas Home. Hanya tampil untuk pengguna yang sudah punya profil.

Merangkum data pribadi yang sudah ada di app: watchlist yang masuk zona beli, kondisi portofolio, dan sinyal
screener hari ini untuk saham milik pengguna. Tidak ada perhitungan baru di sini, hanya penyusunan ringkasan.
"""
from html import escape

import streamlit as st

from engines import money as M
from engines import recap as RC
from engines.market_data import now_wib
from utils import activity_store, market_source, money_store, watchlist_store
from utils.card_html import GREEN, PINK, compact_html, fmt_id
from utils.icons import svg_icon
from utils.pages import get_pages, keyed_container, link_width_kwargs
from utils.profile import current_profile

AMBER, CYAN = "#E3B341", "#00F3FF"
MODE_COLOR = {"risk_on": GREEN, "neutral": AMBER, "defensive": PINK}


def build_today(tickers, snaps, summary, checks, recap_day):
    """Susun isi blok dari data yang sudah dimuat (murni, bisa diuji)."""
    out = {"n_watch": len(tickers), "n_pos": summary["n_positions"] if summary else 0}
    zone_in, zone_near = [], []
    for t in tickers:
        s = (snaps or {}).get(t)
        p = s.get("plan") if s else None
        if not p:
            continue
        row = {"t": t.replace(".JK", ""), "last": s["last"], "buy_min": p["buy_min"], "buy_max": p["buy_max"], "type": p["type"], "grade": p["grade"]}
        if p["zone"] == "In Buy Zone":
            zone_in.append(row)
        elif p["zone"] == "Near Zone":
            zone_near.append(row)
    out["zone_in"], out["zone_near"] = zone_in, zone_near
    keep = ("sl_hit", "near_sl", "tp_hit", "no_sl")
    out["alerts"] = [c for c in (checks or []) if c["key"] in keep or (c["key"] in ("total_risk", "cash", "slots", "concentration") and c["level"] in ("warn", "fail"))]
    out["risk"] = next((c for c in (checks or []) if c["key"] == "total_risk"), None)
    mine = set(tickers) | {p["ticker"] for p in (summary["positions"] if summary else [])}
    sig = []
    for key, name in RC.SCREENERS:
        e = (recap_day or {}).get(key)
        hits = e.get("hits") if isinstance(e, dict) else None
        for h in hits if isinstance(hits, list) else []:
            if isinstance(h, dict) and h.get("t") in mine:
                sig.append({"t": h["t"].replace(".JK", ""), "screener": name, "d": h["d"], "s": h["s"]})
    out["signals"] = sorted(sig, key=lambda x: (x["screener"], x["d"] != "Bullish", x["t"]))
    return out


def _html(s):
    st.markdown(compact_html(s), unsafe_allow_html=True)


def _card(icon, title, body):
    return (
        f'<div class="zq-card" style="height:100%;"><div style="color:#00F3FF; font-weight:800; margin-bottom:6px;">'
        f'{svg_icon(icon, 15, "#00F3FF", 2, margin_right=6)}{escape(title)}</div>{body}</div>'
    )


def _line(color, text):
    return f'<div style="display:flex; gap:6px; align-items:flex-start; margin:3px 0; font-size:13px; color:#C9D1D9;"><span style="color:{color}; font-weight:800;">&bull;</span><span>{text}</span></div>'


def _muted(text):
    return f'<div class="zq-muted" style="font-size:12px;">{escape(text)}</div>'


def _watch_body(t):
    if not t["n_watch"]:
        return _muted("Watchlist masih kosong.")
    if not t["zone_in"] and not t["zone_near"]:
        return _muted(f"Belum ada dari {t['n_watch']} saham yang masuk atau mendekati zona beli.")
    body = ""
    for row in t["zone_in"][:4]:
        body += _line(GREEN, f"<b>{escape(row['t'])}</b> di zona beli ({fmt_id(row['buy_min'])} - {fmt_id(row['buy_max'])}), harga {fmt_id(row['last'])}")
    for row in t["zone_near"][:4]:
        body += _line(CYAN, f"<b>{escape(row['t'])}</b> mendekati zona beli ({fmt_id(row['buy_min'])} - {fmt_id(row['buy_max'])})")
    extra = len(t["zone_in"]) + len(t["zone_near"]) - min(len(t["zone_in"]), 4) - min(len(t["zone_near"]), 4)
    return body + (_muted(f"+{extra} lainnya di Watchlist") if extra > 0 else "")


def _portfolio_body(t, text_fn):
    if not t["n_pos"]:
        return _muted("Belum ada posisi tercatat.")
    if not t["alerts"]:
        risk = t["risk"]
        return _line(GREEN, f"{t['n_pos']} posisi, tidak ada peringatan." + (f" Total risiko {text_fn(risk).replace('Total risiko ', '')}." if risk else ""))
    col = {"fail": PINK, "warn": AMBER, "info": CYAN}
    return "".join(_line(col.get(c["level"], CYAN), escape(text_fn(c))) for c in t["alerts"][:6])


def _signals_body(t):
    if not t["signals"]:
        return _muted("Tidak ada sinyal baru untuk saham di watchlist atau portofolio kamu.")
    col = {"Bullish": GREEN, "Bearish": PINK}
    return "".join(_line(col[s["d"]], f"<b>{escape(s['t'])}</b> di {escape(s['screener'])} ({s['d']})") for s in t["signals"][:6])


def render_today_block(view=None):
    """view: hasil engines.market_view.build_market_view (opsional, untuk menampilkan mode pasar)."""
    if not current_profile():
        return
    try:
        from views.money_management import _bucket, _check_text, _prices
        from views.watchlist import _snapshots

        tickers = watchlist_store.tickers()
        snaps = _snapshots(tuple(tickers), _bucket())["items"] if tickers else {}
        doc, settings = money_store.load_portfolio(), money_store.load_settings()
        summary, checks = None, []
        if doc["positions"]:
            prices = _prices(tuple(p["ticker"] for p in doc["positions"]), _bucket())["prices"]
            summary = M.portfolio_summary(doc["positions"], {t: v["last"] for t, v in prices.items()}, settings, doc["cashflows"], doc["journal"])
            checks = M.risk_checks(summary, settings)
        recap = market_source.load_recap()
        days = (recap or {}).get("days") or {}
        recap_day = days[sorted(days)[-1]] if days else None
        t = build_today(tickers, snaps, summary, checks, recap_day)
    except Exception:
        st.caption("Ringkasan pribadi belum bisa dimuat. Coba muat ulang halaman.")
        return

    mode = ""
    if view:
        m = view["mode"]
        mode = f' <span style="font-size:11px; padding:1px 8px; border:1px solid {MODE_COLOR[m["mode"]]}; color:{MODE_COLOR[m["mode"]]}; border-radius:4px; margin-left:6px;">Pasar: {escape(m["label"])}</span>'
    try:
        streak, _ = activity_store.record_visit(now_wib().strftime("%Y-%m-%d"))
    except Exception:
        streak = 0
    streak_html = f' <span style="font-size:11px; color:#8B949E;">&bull; {streak} hari beruntun kamu buka app</span>' if streak > 1 else ""
    _html(f'<div class="zq-label">{svg_icon("sun", 13, "#FF007F", 2)}Untuk kamu hari ini{mode}{streak_html}</div>')
    if not t["n_watch"] and not t["n_pos"]:
        _html(
            '<div class="zq-card"><div class="zq-muted" style="font-size:13px;">Ringkasan ini terisi setelah kamu menambah saham ke Watchlist '
            "atau mencatat posisi di Money. Datanya tersimpan di profilmu.</div></div>"
        )
        pages, width = get_pages(), link_width_kwargs()
        a, b, _ = st.columns([1, 1, 2])
        with a:
            with keyed_container("ztoday_wl"):
                st.page_link(pages["watchlist"], label="Open Watchlist", icon=":material/bookmarks:", **width)
        with b:
            with keyed_container("ztoday_money"):
                st.page_link(pages["money_management"], label="Open Money", icon=":material/account_balance_wallet:", **width)
        return
    c1, c2, c3 = st.columns(3)
    with c1:
        _html(_card("bookmarks", "Watchlist", _watch_body(t)))
    with c2:
        _html(_card("wallet", "Portofolio", _portfolio_body(t, _check_text)))
    with c3:
        _html(_card("radar-2", "Sinyal baru", _signals_body(t)))
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
