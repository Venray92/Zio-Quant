"""Halaman Login / Daftar. Ini GERBANG -- ditampilkan sendirian (tanpa menu/navbar) kalau belum ada
sesi login valid, lihat app.py. Validasi kolom di sisi kita (huruf/angka/format) SEBELUM dikirim ke
Supabase, supaya pesan errornya cepat & jelas -- Supabase sendiri tetap jadi penjaga akhir (kita
tidak simpan password sendiri sama sekali)."""
import re

import streamlit as st

from utils import account as ACC
from utils import auth as AUTH
from utils import session as SESS
from utils.card_html import compact_html, escape
from utils.compat import STRETCH
from utils.icons import svg_icon

_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,59}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
_PHONE_RE = re.compile(r"^\d{8,15}$")


def _hero():
    st.markdown(
        compact_html(
            f"""<div style="text-align:center; margin-bottom:4px;">
{svg_icon("bolt", 28, "#00F3FF", 2)}<div style="display:inline-block; font-size:22px; font-weight:800; color:#00F3FF; letter-spacing:3px; vertical-align:middle; margin-left:6px;">Z-QUANT</div>
<div style="color:#8B949E; font-size:11px; letter-spacing:1px; margin-top:2px;">IDX SCREENER TERMINAL</div>
</div>"""
        ),
        unsafe_allow_html=True,
    )


def _login_form():
    with st.form("login_form", border=False):
        email = st.text_input("Email", key="login_email", placeholder="nama@email.com")
        password = st.text_input("Password", key="login_password", type="password", placeholder="********")
        submitted = st.form_submit_button("Masuk", **STRETCH, type="primary")
    if not submitted:
        return
    email = (email or "").strip()
    if not email or not password:
        st.error("Isi email dan password dulu.")
        return
    try:
        sess = AUTH.sign_in(email, password)
    except AUTH.AuthError as e:
        st.error(str(e))
        return
    auth_uid = sess["user"]["id"]
    acc = ACC.load_account(auth_uid)
    if acc is None:
        acc = ACC.create_account(auth_uid, email, (sess["user"].get("user_metadata") or {}).get("full_name", ""))
    if acc["status"] == ACC.STATUS_REJECTED:
        st.error("Akun ini tidak disetujui. Hubungi admin kalau menurutmu ini keliru.")
        return
    token = SESS.create_session(auth_uid)
    from utils import profile

    profile.set_session_token(token)
    if acc["status"] != ACC.STATUS_APPROVED:
        st.session_state["_just_logged_in_pending"] = True
    st.rerun()


def _signup_form():
    with st.form("signup_form", border=False):
        full_name = st.text_input("Nama lengkap", key="signup_name", placeholder="Steven Wu")
        email = st.text_input("Email", key="signup_email", placeholder="nama@email.com")
        phone = st.text_input("No. HP (opsional)", key="signup_phone", placeholder="08123456789")
        password = st.text_input("Password", key="signup_password", type="password", placeholder="Minimal 8 karakter")
        password2 = st.text_input("Ulangi password", key="signup_password2", type="password", placeholder="********")
        submitted = st.form_submit_button("Daftar", **STRETCH, type="primary")
    if not submitted:
        return
    full_name, email, phone = (full_name or "").strip(), (email or "").strip(), (phone or "").strip()
    if not _NAME_RE.match(full_name):
        st.error("Nama lengkap: huruf dan spasi saja, 2-60 karakter.")
        return
    if not _EMAIL_RE.match(email):
        st.error("Format email tidak valid (contoh: nama@email.com).")
        return
    if phone and not _PHONE_RE.match(phone):
        st.error("No. HP: angka saja, 8-15 digit, tanpa spasi atau simbol.")
        return
    if len(password) < 8:
        st.error("Password minimal 8 karakter.")
        return
    if password != password2:
        st.error("Password dan ulangi password belum sama.")
        return
    try:
        user = AUTH.sign_up(email, password, full_name=full_name)
    except AUTH.AuthError as e:
        st.error(str(e))
        return
    acc = ACC.create_account(user["id"], email, full_name)
    if phone:
        acc["phone"] = phone
        ACC.save_account(user["id"], acc)
    st.success("Pendaftaran berhasil! Cek email kamu untuk link konfirmasi, lalu tunggu akun disetujui admin sebelum bisa masuk.")


def render_page_login():
    _hero()
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        tab_login, tab_signup = st.tabs(["Masuk", "Daftar"])
        with tab_login:
            _login_form()
        with tab_signup:
            _signup_form()
        st.markdown(
            '<div style="margin-top:14px; padding-top:12px; border-top:1px solid #30363D; font-size:11px; color:#E3B341; text-align:center;">'
            "Akun baru perlu verifikasi email dan persetujuan admin sebelum bisa masuk.</div>",
            unsafe_allow_html=True,
        )


def render_pending_notice(account):
    """Ditampilkan (bukan app biasa) kalau sudah login tapi belum di-approve/ditolak admin."""
    _hero()
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        status = (account or {}).get("status")
        if status == ACC.STATUS_REJECTED:
            title, msg, color = "Akun tidak disetujui", "Pendaftaranmu tidak disetujui admin. Hubungi admin kalau menurutmu ini keliru.", "#FF007F"
        else:
            title, msg, color = "Menunggu persetujuan", "Akun kamu sudah terdaftar dan sedang menunggu persetujuan admin. Coba buka lagi nanti.", "#E3B341"
        st.markdown(
            compact_html(
                f'<div class="zq-card" style="text-align:center; padding:28px;">'
                f'<div style="color:{color}; font-weight:800; font-size:16px; margin-bottom:8px;">{escape(title)}</div>'
                f'<div class="zq-muted" style="font-size:13px;">{escape(msg)}</div></div>'
            ),
            unsafe_allow_html=True,
        )
        if st.button("Keluar", **STRETCH, icon=":material/logout:"):
            from utils import profile

            profile.clear_session()
            st.rerun()
