import base64
import os

import streamlit as st

from utils.card_html import escape
from utils.compat import STRETCH
from utils.icons import icon_kwargs, svg_icon
from utils.pages import keyed_container


def get_logo_base64(file_path="logo.jpg"):
    """Konversi file logo ke format base64."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None


def _render_account_chip(auth_uid, display_name):
    """Chip profil yang bisa diklik (sesudah login): Profil, Admin Page (kalau admin), Keluar.
    Pakai current_account() (bukan account.load_account() langsung) supaya jalur resolusinya SAMA
    dengan yang dipakai gerbang app.py/gate screeners.py -- juga supaya gampang di-mock di tes."""
    from utils.profile import current_account

    acc = current_account()
    is_admin = bool(acc and acc.get("is_admin"))
    with keyed_container("zheader_chip"):
        with st.popover(display_name or "Akun", **icon_kwargs("person", "popover")):
            from utils.pages import get_pages

            pages = get_pages()
            if "profile" in pages:
                st.page_link(pages["profile"], label="Profil", icon=":material/person:", **STRETCH)
            if is_admin and "admin" in pages:
                st.page_link(pages["admin"], label="Admin Page", icon=":material/shield_person:", **STRETCH)
            if st.button("Keluar", key="btn_header_logout", **STRETCH, icon=":material/logout:"):
                from utils.profile import clear_session

                clear_session()
                st.rerun()


def render_header(current=None):
    """Header: logo Z-QUANT (kiri) + tagline. Menu ada di render_top_nav()."""
    from utils.profile import current_auth_uid, current_profile

    # Link lama (?reset=true) tetap didukung: arahkan ke Home
    if st.query_params.get("reset") == "true":
        st.session_state["selected_screener"] = None
        st.session_state["selected_page"] = "home"
        st.query_params.clear()
        if current not in (None, "home"):
            from utils.pages import get_pages

            st.switch_page(get_pages()["home"])

    logo_b64 = get_logo_base64("logo.jpg")

    if logo_b64:
        logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" class="brand-logo-img" />'
    else:
        logo_html = (
            '<span style="display:inline-flex; width:50px; height:50px; align-items:center; '
            'justify-content:center; border:1.5px solid #00F3FF; border-radius:8px;">'
            f'{svg_icon("bolt", 28, "#00F3FF", 2)}</span>'
        )

    auth_uid = current_auth_uid()
    profile = current_profile()
    chip = (
        f'<span style="display:inline-flex; align-items:center; gap:6px; border:1px solid {"#00F3FF" if profile else "#30363D"}; border-radius:16px; '
        f'padding:3px 12px; font-size:12px; color:{"#FFFFFF" if profile else "#8B949E"}; font-family:\'Share Tech Mono\', monospace;">'
        f'{svg_icon("user", 14, "#00F3FF" if profile else "#8B949E", 2)}{escape(profile) if profile else "Guest"}</span>'
    )
    col_logo, col_bell, col_chip = st.columns([7.6, 0.5, 1.5], vertical_alignment="center")
    with col_logo:
        st.markdown(
            f"""<div class="brand-container" style="display:flex; align-items:center;">
<div style="display:inline-flex; align-items:center; gap:12px;">
{logo_html}
<div>
<div class="brand-title-text">Z-QUANT</div>
<div style="color:#8B949E; font-size:11px; letter-spacing:1px; font-family:'Share Tech Mono', monospace;">IDX SCREENER TERMINAL</div>
</div>
</div>
</div>""",
            unsafe_allow_html=True,
        )
    with col_bell:
        with keyed_container("zheader_bell"):
            from views.top_nav import render_bell

            render_bell()
    with col_chip:
        if auth_uid:
            _render_account_chip(auth_uid, profile)
        else:
            st.markdown(f'<div style="text-align:left; padding-top:6px;">{chip}</div>', unsafe_allow_html=True)


def render_header_divider():
    """Menampilkan garis pembatas neon biru di bawah top navigation."""
    st.markdown(
        "<hr style='margin-top: 8px; margin-bottom: 24px; border: 0; height: 1px; background: linear-gradient(90deg, #00F3FF, transparent);'>",
        unsafe_allow_html=True,
    )


def render_welcome():
    """Kompatibilitas: halaman sambutan lama sekarang = halaman Home baru."""
    from views.home import render_page_home

    render_page_home()
