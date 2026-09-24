import streamlit as st

from utils.pages import get_pages, page_key
from utils.profile import adopt_query_profile, current_account, current_auth_uid
from utils.theme import hide_sidebar_nav, inject_theme
from utils.ui_helpers import inject_custom_css
from views.footer import render_footer
from views.header import render_header, render_header_divider
from views.top_nav import render_top_nav

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Z-QUANT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Tema: CSS dasar (assets/style.css) + tema global (tombol, menu, Home, footer)
inject_custom_css()
inject_theme()

# 3. Inisialisasi Session State (profil dipulihkan dari ?u= di URL kalau ada)
adopt_query_profile()

# 3b. Gerbang Login (WAJIB) -- tanpa sesi login valid, cuma halaman Login/Daftar yang
# ditampilkan (tanpa menu/navbar), apapun URL yang diketik/di-bookmark. Profil tamu lama (?u=)
# TIDAK LAGI cukup untuk masuk -- lihat utils/profile.py & utils/account.py untuk detail sesi.
_auth_uid = current_auth_uid()
if not _auth_uid:
    from views.tab_auth import render_page_login

    render_page_login()
    render_footer()
    st.stop()

from utils import account as ACC  # noqa: E402

_account = current_account()
if not ACC.can_enter_app(_account):
    from views.tab_auth import render_pending_notice

    render_pending_notice(_account)
    render_footer()
    st.stop()

if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "home"

if "selected_screener" not in st.session_state:
    st.session_state["selected_screener"] = None

if "active_screener_name" not in st.session_state:
    st.session_state["active_screener_name"] = "Screener"

# 4. Navigasi: tiap halaman punya URL sendiri (mis. /watchlist, /rsi-reversal)
pages = list(get_pages().values())
try:
    current_page = st.navigation(pages, position="hidden")
except TypeError:  # Streamlit lama tanpa position="hidden"
    current_page = st.navigation(pages)
    hide_sidebar_nav()

current = page_key(current_page)
st.session_state["current_page"] = current

# 5. Layout atas (Header -> Menu -> Divider), isi halaman, lalu footer
render_header(current)
render_top_nav(current)
render_header_divider()

current_page.run()

render_footer()
