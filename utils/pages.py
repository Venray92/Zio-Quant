"""Halaman aplikasi untuk st.navigation (URL per halaman, tombol Back browser jalan)."""
import streamlit as st

from utils.screeners import SCREENERS, render_screener

# (key, judul halaman, label di menu, ikon Material)
BASE_PAGES = [
    ("home", "Home", "Home", "home"),
    ("watchlist", "Watchlist", "Watchlist", "bookmarks"),
    ("money_management", "Money Management", "Money", "account_balance_wallet"),
    ("how_to", "How To", "How To", "menu_book"),
]
SCREENER_KEYS = [s["key"] for s in SCREENERS]

_PAGES = None


def _mark(page_key, screener_key=None):
    # kompatibel dengan kode lama yang membaca selected_page / selected_screener
    st.session_state["selected_page"] = "home" if screener_key else page_key
    st.session_state["selected_screener"] = screener_key


def _home():
    from views.home import render_page_home

    _mark("home")
    render_page_home()


def _watchlist():
    from views.watchlist import render_page_watchlist

    _mark("watchlist")
    render_page_watchlist()


def _money_management():
    from views.money_management import render_page_money_management

    _mark("money_management")
    render_page_money_management()


def _how_to():
    from views.how_to import render_page_how_to

    _mark("how_to")
    render_page_how_to()


_BASE_FUNCS = {
    "home": _home,
    "watchlist": _watchlist,
    "money_management": _money_management,
    "how_to": _how_to,
}


def _screener_page(s):
    def page():
        _mark("home", s["key"])
        st.session_state["active_screener_name"] = s["name"]
        render_screener(s["key"])

    page.__name__ = f"screener_{s['key']}"
    return page


def get_pages():
    """dict key -> st.Page (dibuat sekali, dipakai ulang di menu dan link)."""
    global _PAGES
    if _PAGES is None:
        pages = {}
        for key, title, _, icon in BASE_PAGES:
            pages[key] = st.Page(
                _BASE_FUNCS[key],
                title=title,
                icon=f":material/{icon}:",
                url_path=key.replace("_", "-"),
                default=(key == "home"),
            )
        for s in SCREENERS:
            pages[s["key"]] = st.Page(
                _screener_page(s),
                title=s["name"],
                icon=f":material/{s['material']}:",
                url_path=s["url"],
            )
        _PAGES = pages
    return _PAGES


def page_key(page):
    """Key halaman yang sedang aktif (dari objek hasil st.navigation)."""
    for key, p in get_pages().items():
        if p.title == getattr(page, "title", None):
            return key
    return "home"


def keyed_container(key):
    """st.container(key=...) kalau didukung (untuk styling per elemen), kalau tidak container biasa."""
    try:
        return st.container(key=key)
    except TypeError:
        return st.container()


def link_width_kwargs():
    import inspect

    try:
        params = inspect.signature(st.page_link).parameters
    except Exception:
        return {}
    if "width" in params:
        return {"width": "stretch"}
    if "use_container_width" in params:
        return {"use_container_width": True}
    return {}
