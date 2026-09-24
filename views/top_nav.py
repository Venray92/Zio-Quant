from html import escape

import streamlit as st

from utils.icons import icon_kwargs, svg_icon
from utils.pages import BASE_PAGES, SCREENER_KEYS, get_pages, keyed_container, link_width_kwargs
from utils.profile import current_profile
from utils.screeners import SCREENERS, get_screener


_POP_KEY = "znav_screeners_pop"
_LAST_PAGE_KEY = "_znav_last_page"


def _active(flag):
    return "__active" if flag else ""


def render_top_nav(current=None):
    """Menu atas: Home, Screeners (dropdown), Watchlist, Money, Learn. Halaman aktif menyala."""
    current = current or st.session_state.get("current_page", "home")
    pages = get_pages()
    width = link_width_kwargs()
    labels = {key: (label, icon) for key, _, label, icon in BASE_PAGES}

    cols = st.columns([1, 1.35, 1, 1, 1.3, 1], vertical_alignment="center")

    def nav_link(col, key):
        label, icon = labels[key]
        with col:
            with keyed_container(f"znav_{key}{_active(current == key)}"):
                st.page_link(pages[key], label=label, icon=f":material/{icon}:", **width)

    nav_link(cols[0], "home")

    # ---- Screeners dropdown ----
    active_scr = current if current in SCREENER_KEYS else None
    pop_label = get_screener(active_scr)["name"] if active_scr else "Screeners"
    pop_kwargs = {"use_container_width": True}
    try:
        import inspect

        params = inspect.signature(st.popover).parameters
        if "width" in params:
            pop_kwargs = {"width": "stretch"}
        if "key" in params and "on_change" in params:
            # Popover yang menyimpan status buka/tutup: setiap kali halaman berganti, dropdown ditutup
            # (bawaan Streamlit: setelah klik salah satu screener, dropdown tetap terbuka di halaman baru).
            if st.session_state.get(_LAST_PAGE_KEY) != current:
                st.session_state[_POP_KEY] = False
            st.session_state[_LAST_PAGE_KEY] = current
            pop_kwargs.update(key=_POP_KEY, on_change="rerun")
    except Exception:
        pass
    with cols[1]:
        with keyed_container(f"znav_screeners{_active(active_scr is not None)}"):
            with st.popover(pop_label, **pop_kwargs, **icon_kwargs("radar", "popover")):
                st.markdown(
                    f"""<div style="display:flex; justify-content:space-between; font-family:'Share Tech Mono', monospace; font-size:11px; font-weight:800; letter-spacing:1px; color:#00F3FF; margin-bottom:6px;">
<span>SCREENERS</span><span>{len(SCREENERS)} AVAILABLE</span></div>""",
                    unsafe_allow_html=True,
                )
                for s in SCREENERS:
                    is_on = s["key"] == active_scr
                    with keyed_container(f"zscr_{s['key']}{_active(is_on)}"):
                        st.page_link(
                            pages[s["key"]],
                            label=s["name"] + ("  ·  Active" if is_on else ""),
                            icon=f":material/{s['material']}:",
                            **width,
                        )
                        st.caption(f"{s['category']} · {s['desc']}")

    nav_link(cols[2], "watchlist")
    nav_link(cols[3], "money_management")
    nav_link(cols[4], "leaderboard")
    nav_link(cols[5], "how_to")



def _gather_notifications():
    """Kumpulkan bahan lonceng dari data yang sudah ada (sama seperti blok 'Untuk kamu hari ini'),
    dibungkus try/except supaya sekali gagal (koneksi, dsb.) tidak bikin header error."""
    from engines import money as M
    from engines import notifications as N
    from engines.market_data import now_wib
    from utils import activity_store, alert_store, market_source, money_store, watchlist_store
    from views.home_today import build_today
    from views.money_management import _bucket, _check_text, _prices
    from views.watchlist import _snapshots

    today_iso = now_wib().strftime("%Y-%m-%d")
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
    today = build_today(tickers, snaps, summary, checks, recap_day)

    sector_hist = market_source.load_sector_hist()
    s_days = sorted((sector_hist or {}).get("days") or {})
    sector_today = sector_hist["days"][s_days[-1]] if s_days else {}
    sector_prev = sector_hist["days"][s_days[-2]] if len(s_days) > 1 else {}

    alerts = alert_store.load_alerts()
    fired = []
    if alerts:
        data_map, _ = market_source.load_shared_file()
        last_close = {}
        for t in {a["Ticker"] for a in alerts}:
            df = (data_map or {}).get(t)
            if df is not None and len(df):
                last_close[t] = float(df["Close"].iloc[-1])
        fired = alert_store.check_alerts(last_close, today_iso)

    items = N.build_notifications(today, text_fn=_check_text, sector_today=sector_today, sector_prev=sector_prev, fired_alerts=fired)
    seen_today = activity_store.last_notif_check() == today_iso
    return items, seen_today, today_iso


def render_bell():
    """Lonceng notifikasi, dipanggil dari header.py di sebelah chip profil (bukan dari nav bar).
    Kosong (tidak render apa-apa) kalau belum ada profil -- notifikasi ini data pribadi per profil."""
    if not current_profile():
        return
    try:
        items, seen_today, today_iso = _gather_notifications()
    except Exception:
        items, seen_today, today_iso = [], True, ""
    from utils import activity_store

    badge = 0 if seen_today else len(items)
    badge_html = f'<div class="zq-bell-badge">{badge if badge < 100 else "99+"}</div>' if badge else ""
    with keyed_container(f"zbell{_active(bool(badge))}"):
        if badge_html:
            st.markdown(badge_html, unsafe_allow_html=True)
        with st.popover("", **icon_kwargs("notifications", "popover")):
            top = st.columns([5, 1])
            with top[1]:
                if st.button("", key="btn_refresh_bell", help="Muat ulang notifikasi", **icon_kwargs("refresh")):
                    st.rerun()
            if today_iso and not seen_today:
                activity_store.mark_notif_checked(today_iso)
            if not items:
                st.caption("Belum ada yang perlu diperhatikan hari ini.")
            else:
                pages = get_pages()
                col = {"good": "#00FF66", "warn": "#E3B341", "fail": "#FF007F", "info": "#00F3FF"}
                for it in items[:12]:
                    st.markdown(
                        f'<div style="display:flex; gap:6px; align-items:flex-start; margin:5px 0; font-size:13px; color:#C9D1D9;">'
                        f'{svg_icon(it["icon"], 14, col.get(it["level"], "#8B949E"), 2, margin_right=2)}<span>{escape(it["text"])}</span></div>',
                        unsafe_allow_html=True,
                    )
                    if it["page_key"] and it["page_key"] in pages:
                        st.page_link(pages[it["page_key"]], label="Buka", icon=":material/arrow_forward:")
                if len(items) > 12:
                    st.caption(f"+{len(items) - 12} lainnya")
            st.caption("Alert harga & rekap dicek tiap kali halaman ini dibuka -- bukan pesan yang dikirim ke HP.")
