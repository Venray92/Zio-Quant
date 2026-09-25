"""Halaman aplikasi untuk st.navigation (URL per halaman, tombol Back browser jalan)."""
import streamlit as st

from utils.screeners import SCREENERS, render_screener

# (key, judul halaman, label di menu, ikon Material)
BASE_PAGES = [
    ("home", "Home", "Home", "home"),
    ("watchlist", "Watchlist", "Watchlist", "bookmarks"),
    ("money_management", "Money Management", "Money", "account_balance_wallet"),
    ("ranking_leaderboard", "Ranking Leaderboard", "Ranking", "trophy"),
    ("how_to", "Learn", "Learn", "menu_book"),
    ("profile", "Profil Saya", "Profil", "person"),
    ("admin", "Admin Panel", "Admin", "shield_person"),
]
SCREENER_KEYS = [s["key"] for s in SCREENERS]
# Alamat halaman yang tidak mengikuti nama key (key "how_to" tetap dipakai internal, alamatnya jadi /learn).
URL_PATHS = {"how_to": "learn"}

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
    from utils import watchlist_store
    from views.money_management import render_page_money_management

    _mark("money_management")
    try:
        watchlist_store.load_watchlist()  # mengisi daftar watchlist yang dipakai halaman ini
    except Exception:
        pass
    render_page_money_management()


def _how_to():
    from views.how_to import render_page_how_to

    _mark("how_to")
    render_page_how_to()


def _ranking_leaderboard():
    from views.tab_ranking import render_page_ranking

    _mark("ranking_leaderboard")
    render_page_ranking()


def _how_to_old_url():
    """Alamat lama /how-to diarahkan ke halaman Learn supaya bookmark lama tidak mati."""
    st.switch_page(get_pages()["how_to"])


def _profile():
    from views.tab_profile import render_page_profile

    _mark("profile")
    render_page_profile()


def _admin():
    from views.tab_admin import render_page_admin

    _mark("admin")
    render_page_admin()


_BASE_FUNCS = {
    "home": _home,
    "watchlist": _watchlist,
    "money_management": _money_management,
    "ranking_leaderboard": _ranking_leaderboard,
    "how_to": _how_to,
    "profile": _profile,
    "admin": _admin,
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
                url_path=URL_PATHS.get(key, key.replace("_", "-")),
                default=(key == "home"),
            )
        pages["how_to_old_url"] = st.Page(_how_to_old_url, title="How To (alamat lama)", url_path="how-to")
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
    """Argumen bersama untuk st.page_link: lebar penuh + profil (?u=) ikut terbawa antar halaman."""
    import inspect

    from utils.profile import nav_query_params

    try:
        params = inspect.signature(st.page_link).parameters
    except Exception:
        return {}
    kw = {}
    if "width" in params:
        kw["width"] = "stretch"
    elif "use_container_width" in params:
        kw["use_container_width"] = True
    qp = nav_query_params()
    if qp and "query_params" in params:
        kw["query_params"] = qp
    return kw
