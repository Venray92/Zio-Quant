"""Halaman Profil: ubah data akun sendiri (nama, tanggal lahir, alamat, email, password) + lihat
(bukan ubah) akses fitur yang diatur admin."""
import re
from datetime import date

import streamlit as st

from utils import account as ACC
from utils import auth as AUTH
from utils.card_html import compact_html, escape
from utils.compat import STRETCH
from utils.icons import svg_icon
from utils.screeners import SCREENERS

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
_PHONE_RE = re.compile(r"^\d{8,15}$")
_MIN_BIRTHDATE = date(1900, 1, 1)


def _save_basic(auth_id, acc, full_name, birthdate, address, phone):
    if not full_name.strip():
        st.error("Nama lengkap tidak boleh kosong.")
        return
    if phone and not _PHONE_RE.match(phone):
        st.error("No. HP: angka saja, 8-15 digit, tanpa spasi atau simbol.")
        return
    new_acc = dict(acc)
    new_acc["full_name"] = full_name.strip()
    new_acc["birthdate"] = birthdate.isoformat() if birthdate else ""
    new_acc["address"] = address.strip()
    new_acc["phone"] = phone.strip()
    ACC.save_account(auth_id, new_acc)
    try:
        AUTH.admin_update_user(auth_id, full_name=full_name.strip())
    except AUTH.AuthError:
        pass  # data profil kita sendiri tetap tersimpan walau sinkron ke Supabase gagal
    st.toast("Perubahan disimpan.")
    st.rerun()


def _change_email(auth_id, new_email):
    if not _EMAIL_RE.match(new_email):
        st.error("Format email tidak valid.")
        return
    try:
        AUTH.admin_update_user(auth_id, email=new_email)
    except AUTH.AuthError as e:
        st.error(str(e))
        return
    acc = ACC.load_account(auth_id)
    acc["email"] = new_email.strip().lower()
    ACC.save_account(auth_id, acc)
    st.toast("Email diubah. Cek email baru kalau ada link verifikasi ulang.")
    st.rerun()


def _change_password(auth_id, pw, pw2):
    if len(pw) < 8:
        st.error("Password minimal 8 karakter.")
        return
    if pw != pw2:
        st.error("Password dan ulangi password belum sama.")
        return
    try:
        AUTH.admin_update_user(auth_id, password=pw)
    except AUTH.AuthError as e:
        st.error(str(e))
        return
    st.toast("Password diubah.")


def render_page_profile():
    from utils.profile import current_account, current_auth_uid

    auth_id = current_auth_uid()
    acc = current_account()
    if not auth_id or not acc:
        st.error("Kamu belum login.")
        return

    st.markdown(
        compact_html(
            f"""<div class="zq-hero">
<h1>{svg_icon("user", 24, "#00F3FF", 2, margin_right=8)}PROFIL SAYA</h1>
<p>Ubah data akun kamu.</p>
</div>"""
        ),
        unsafe_allow_html=True,
    )
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        with st.form("profile_basic_form", border=False):
            full_name = st.text_input("Nama lengkap", value=acc.get("full_name", ""))
            birthdate_val = date.fromisoformat(acc["birthdate"]) if acc.get("birthdate") else None
            birthdate = st.date_input("Tanggal lahir", value=birthdate_val, min_value=_MIN_BIRTHDATE, max_value=date.today())
            address = st.text_input("Alamat", value=acc.get("address", ""))
            phone = st.text_input("No. HP", value=acc.get("phone", ""), placeholder="08123456789")
            submitted_basic = st.form_submit_button("Simpan Perubahan", **STRETCH, type="primary")
        if submitted_basic:
            _save_basic(auth_id, acc, full_name, birthdate, address, phone)

        st.markdown('<div style="margin-top:8px; border-top:1px solid #30363D; padding-top:10px;"></div>', unsafe_allow_html=True)
        with st.form("profile_email_form", border=False):
            new_email = st.text_input("Email", value=acc.get("email", ""))
            st.caption("Ganti email perlu verifikasi ulang.")
            submitted_email = st.form_submit_button("Ganti Email", **STRETCH)
        if submitted_email:
            if new_email.strip().lower() != acc.get("email", ""):
                _change_email(auth_id, new_email)
            else:
                st.info("Email tidak berubah.")

        st.markdown('<div style="margin-top:8px; border-top:1px solid #30363D; padding-top:10px;"></div>', unsafe_allow_html=True)
        with st.form("profile_password_form", border=False):
            pw = st.text_input("Password baru", type="password", placeholder="Minimal 8 karakter")
            pw2 = st.text_input("Ulangi password baru", type="password", placeholder="********")
            submitted_pw = st.form_submit_button("Ganti Password", **STRETCH)
        if submitted_pw:
            _change_password(auth_id, pw, pw2)

        st.markdown('<div style="margin-top:8px; border-top:1px solid #30363D; padding-top:10px;"></div>', unsafe_allow_html=True)
        enabled = [s["name"] for s in SCREENERS if acc["features"].get(s["key"])]
        feat_txt = ", ".join(enabled) if enabled else "Belum ada fitur yang diaktifkan admin."
        exp_txt = f"Berlaku sampai {acc['expires_at']}" if acc.get("expires_at") else "Tanpa batas waktu"
        st.markdown(
            compact_html(
                f'<div class="zq-muted" style="font-size:12px;">Akses fitur kamu (diatur admin):</div>'
                f'<div style="font-size:13px; color:#C9D1D9; margin-bottom:4px;">{escape(feat_txt)}</div>'
                f'<div style="font-size:12px; color:#E3B341;">{escape(exp_txt)}</div>'
            ),
            unsafe_allow_html=True,
        )
