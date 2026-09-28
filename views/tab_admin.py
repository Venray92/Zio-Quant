"""Halaman Admin Panel: kelola akun (approve/tolak), atur akses fitur per akun + tanggal kedaluwarsa.
HANYA muncul/bisa diakses akun dgn is_admin=True (dicek di sini juga, bukan cuma disembunyikan dari
menu -- pertahanan berlapis)."""
from datetime import date, datetime, timedelta, timezone
from html import escape

import pandas as pd
import streamlit as st

from utils import account as ACC
from utils import auth as AUTH
from utils.card_html import compact_html
from utils.compat import STRETCH
from utils.icons import svg_icon
from utils.screeners import SCREENERS

_STATUS_LABEL = {ACC.STATUS_PENDING: "Pending", ACC.STATUS_APPROVED: "Approved", ACC.STATUS_REJECTED: "Ditolak"}
_STATUS_COLOR = {ACC.STATUS_PENDING: "#E3B341", ACC.STATUS_APPROVED: "#00FF66", ACC.STATUS_REJECTED: "#FF007F"}
_WIB = timezone(timedelta(hours=7))


def _load_accounts():
    try:
        return ACC.list_all_accounts(), None
    except AUTH.AuthError as e:
        return [], str(e)


def _fmt_wib(iso_str):
    """ISO UTC (tersimpan di utils/account.py) -> 'DD-MM-YYYY HH:MM WIB', atau '-' kalau kosong/rusak."""
    if not iso_str:
        return "-"
    try:
        dt = datetime.fromisoformat(str(iso_str))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(_WIB).strftime("%d-%m-%Y %H:%M") + " WIB"
    except ValueError:
        return "-"


def _row_dict(acc):
    # Status TERSIMPAN tetap "approved" walau tanggal kedaluwarsa sudah lewat (supaya kalau nanti
    # diperpanjang, tidak perlu approve ulang dari nol) -- tapi yang DITAMPILKAN ke admin di sini
    # dikomputasi "Kadaluwarsa" biar ketahuan akun itu sekarang nonaktif, bukan diam-diam masih
    # kelihatan "Approved" padahal sudah lewat batas.
    status = acc.get("status")
    if status == ACC.STATUS_APPROVED and not ACC.is_access_active(acc):
        status_label = "Kadaluwarsa"
    else:
        status_label = _STATUS_LABEL.get(status, status)
    return {
        "Nama": acc.get("full_name") or "-",
        "Email": acc.get("email", ""),
        "Status": status_label,
        "Email Terverifikasi": "Ya" if acc.get("_email_confirmed") else "Belum",
        "Daftar": acc.get("created_at", ""),
        "Akses s.d.": acc.get("expires_at") or "Tanpa batas",
        "Terakhir Login": _fmt_wib(acc.get("last_login_at")),
        "Total Jam Aktif": ACC.format_duration(acc.get("total_active_seconds")),
        "_auth_id": acc.get("_auth_id"),
    }


def render_page_admin():
    from utils.profile import current_account

    me = current_account()
    if not me or not me.get("is_admin"):
        st.error("Halaman ini khusus admin.")
        return

    st.markdown(
        compact_html(
            f"""<div class="zq-hero">
<h1>{svg_icon("shield-check", 24, "#00F3FF", 2, margin_right=8)}ADMIN PANEL</h1>
<p>Kelola akun, approval, dan akses fitur.</p>
</div>"""
        ),
        unsafe_allow_html=True,
    )

    accounts, err = _load_accounts()
    if err:
        st.error(f"Tidak bisa memuat daftar akun: {err}")
        return
    if not accounts:
        st.info("Belum ada akun yang mendaftar.")
        return

    col_search, col_f1, col_f2, col_f3, col_f4 = st.columns([3, 1, 1, 1, 1])
    with col_search:
        q = st.text_input("Cari", key="admin_search", placeholder="Cari nama atau email...", label_visibility="collapsed")
    status_filter = st.session_state.get("admin_status_filter", "Semua")
    with col_f1:
        if st.button("Semua", key="f_all", type="primary" if status_filter == "Semua" else "secondary", **STRETCH):
            st.session_state["admin_status_filter"] = "Semua"; st.rerun()
    with col_f2:
        n_pending = sum(1 for a in accounts if a["status"] == ACC.STATUS_PENDING)
        if st.button(f"Pending ({n_pending})", key="f_pending", type="primary" if status_filter == "Pending" else "secondary", **STRETCH):
            st.session_state["admin_status_filter"] = "Pending"; st.rerun()
    with col_f3:
        if st.button("Approved", key="f_approved", type="primary" if status_filter == "Approved" else "secondary", **STRETCH):
            st.session_state["admin_status_filter"] = "Approved"; st.rerun()
    with col_f4:
        if st.button("Ditolak", key="f_rejected", type="primary" if status_filter == "Ditolak" else "secondary", **STRETCH):
            st.session_state["admin_status_filter"] = "Ditolak"; st.rerun()

    filtered = accounts
    if status_filter != "Semua":
        filtered = [a for a in filtered if _STATUS_LABEL.get(a["status"]) == status_filter]
    if q:
        ql = q.strip().lower()
        filtered = [a for a in filtered if ql in (a.get("full_name") or "").lower() or ql in (a.get("email") or "").lower()]

    if not filtered:
        st.info("Tidak ada akun yang cocok.")
        return

    df = pd.DataFrame([_row_dict(a) for a in filtered])
    event = st.dataframe(
        df.drop(columns=["_auth_id"]), hide_index=True, **STRETCH,
        on_select="rerun", selection_mode="single-row", key="admin_table",
    )
    sel_rows = event.selection.rows if event and event.selection else []
    if not sel_rows:
        st.caption("Klik salah satu baris di atas untuk melihat & mengubah detail akun.")
        return

    acc = filtered[sel_rows[0]]
    auth_id = acc["_auth_id"]
    st.markdown(
        compact_html(
            f'<div class="zq-card"><div class="zq-muted" style="font-size:12px;">Detail akun</div>'
            f'<div style="color:#00F3FF; font-weight:800; font-size:15px;">{escape(acc.get("full_name") or "(tanpa nama)")} &mdash; {escape(acc.get("email", ""))}</div></div>'
        ),
        unsafe_allow_html=True,
    )

    st.markdown('<div class="zq-muted" style="font-size:12px; margin-top:10px;">Akses fitur:</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    new_features = {}
    for i, s in enumerate(SCREENERS):
        with cols[i % 3]:
            new_features[s["key"]] = st.checkbox(s["name"], value=bool(acc["features"].get(s["key"], False)), key=f"feat_{auth_id}_{s['key']}")

    c1, c2 = st.columns([1, 2])
    with c1:
        has_expiry = st.checkbox("Batasi tanggal kedaluwarsa", value=bool(acc.get("expires_at")), key=f"has_exp_{auth_id}")
    with c2:
        default_date = date.fromisoformat(acc["expires_at"]) if acc.get("expires_at") else date.today() + timedelta(days=365)
        new_expiry = st.date_input("Berlaku sampai", value=default_date, disabled=not has_expiry, key=f"exp_{auth_id}", label_visibility="collapsed")

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("Approve", key=f"btn_approve_{auth_id}", **STRETCH, icon=":material/check_circle:"):
            # Approve ikut bawa fitur & tanggal kedaluwarsa yang lagi dicentang di form ini (dulu
            # cuma status yg keubah, jadi fitur/tanggalnya balik kosong & admin harus pencet
            # "Simpan Akses" lagi terpisah -- sekarang 1 klik langsung semua ke-apply).
            new_acc = dict(acc)
            new_acc["status"] = ACC.STATUS_APPROVED
            new_acc["features"] = new_features
            new_acc["expires_at"] = new_expiry.isoformat() if has_expiry else None
            ACC.save_account(auth_id, new_acc)
            st.toast("Akun disetujui & akses disimpan.")
            st.rerun()
    with b2:
        if st.button("Tolak", key=f"btn_reject_{auth_id}", **STRETCH, icon=":material/cancel:"):
            new_acc = dict(acc); new_acc["status"] = ACC.STATUS_REJECTED
            ACC.save_account(auth_id, new_acc)
            st.toast("Akun ditolak.")
            st.rerun()
    with b3:
        if st.button("Simpan Akses", key=f"btn_save_{auth_id}", **STRETCH, icon=":material/save:"):
            new_acc = dict(acc)
            new_acc["features"] = new_features
            new_acc["expires_at"] = new_expiry.isoformat() if has_expiry else None
            ACC.save_account(auth_id, new_acc)
            st.toast("Akses disimpan.")
            st.rerun()
    with b4:
        if not acc.get("_email_confirmed") and st.button("Verifikasi Email", key=f"btn_verify_{auth_id}", **STRETCH, icon=":material/mark_email_read:"):
            try:
                AUTH.admin_confirm_email(auth_id)
                st.toast("Email ditandai terverifikasi.")
                st.rerun()
            except AUTH.AuthError as e:
                st.error(str(e))
