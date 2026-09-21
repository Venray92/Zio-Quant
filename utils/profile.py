"""Profil pengguna (sementara, sebelum ada login): nama profil -> user_id 'profile:<nama>'.

Bukan password: siapa pun yang tahu nama profil bisa membuka datanya. Saat login dibuat,
user_id cukup diganti (mis. 'auth:<uuid>') dan semua halaman otomatis ikut.
"""
import re

import streamlit as st

from utils import storage
from utils.card_html import escape
from utils.icons import expander_kwargs, icon_kwargs, svg_icon

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,31}$")
_RESERVED = {"guest", "admin", "root", "null", "none", "undefined"}


def clean_profile_name(raw):
    """(nama, None) kalau valid, (None, pesan_error) kalau tidak."""
    name = re.sub(r"\s+", "-", str(raw or "").strip().lower())
    if not name:
        return None, "Isi nama profil dulu."
    if not _NAME_RE.match(name):
        return None, "Nama profil 3 sampai 32 karakter: huruf, angka, tanda - atau _ (tanpa spasi)."
    if name in _RESERVED:
        return None, "Nama itu tidak bisa dipakai. Coba nama lain."
    return name, None


def current_profile():
    return st.session_state.get("profile")


def user_id():
    p = current_profile()
    return f"profile:{p}" if p else None


def adopt_query_profile():
    """Pulihkan profil dari ?u=nama di URL (supaya refresh atau bookmark tidak kehilangan profil)."""
    if current_profile():
        return
    try:
        raw = st.query_params.get("u")
    except Exception:
        return
    name, err = clean_profile_name(raw)
    if not err:
        st.session_state["profile"] = name


def set_profile(raw):
    name, err = clean_profile_name(raw)
    if err:
        return False, err
    guest = dict(st.session_state.get("_guest_data", {}))
    st.session_state["profile"] = name
    try:
        st.query_params["u"] = name
    except Exception:
        pass
    storage.reset_cache()
    if guest.get("watchlist"):
        from utils import watchlist_store

        watchlist_store.merge_guest(guest["watchlist"])
    st.session_state["_guest_data"] = {}
    return True, name


def clear_profile():
    st.session_state.pop("profile", None)
    st.session_state.pop("watchlist_data", None)
    storage.reset_cache()
    try:
        if "u" in st.query_params:
            del st.query_params["u"]
    except Exception:
        pass


def nav_query_params():
    """query_params untuk st.page_link supaya profil ikut terbawa saat pindah halaman."""
    p = current_profile()
    return {"u": p} if p else {}


def render_profile_card():
    """Kartu profil di atas halaman yang menyimpan data. Return True kalau profil sudah dipilih."""
    if not current_profile():
        st.markdown(
            f"""<div class="zq-card" style="margin-bottom:8px;">
<div style="color:#FFFFFF; font-weight:800; font-size:14px;">{svg_icon("user", 16, "#E3B341", 2, margin_right=6)}Guest mode: data belum tersimpan</div>
<div class="zq-muted" style="font-size:12px; margin-top:4px;">Buat nama profil supaya watchlist tetap ada saat kamu buka lagi. Belum ada password: siapa pun yang tahu nama profilmu bisa membuka datanya, jadi pakai nama yang sulit ditebak dan jangan bagikan link-nya.</div>
</div>""".replace("\n", ""),
            unsafe_allow_html=True,
        )
        with st.form("profile_form", clear_on_submit=False, border=False):
            c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
            with c1:
                raw = st.text_input("Profile name", placeholder="mis. stev-idx", max_chars=32, key="profile_name_input")
            with c2:
                submitted = st.form_submit_button("Save profile", use_container_width=True, **icon_kwargs("person_add"))
        if submitted:
            ok, msg = set_profile(raw)
            if ok:
                st.rerun()
            else:
                st.error(msg)
        return False

    info = storage.status(user_id())
    if info["error"]:
        tag, color = "Cloud tidak terhubung, memakai penyimpanan sementara", "#E3B341"
    elif info["mode"] == "cloud":
        tag, color = "Tersimpan di cloud", "#00FF66"
    else:
        tag, color = "Tersimpan di server (sementara, bisa hilang saat app restart)", "#E3B341"
    c1, c2 = st.columns([4, 1], vertical_alignment="center")
    with c1:
        st.markdown(
            f"""<div class="zq-card" style="padding:8px 12px;"><span style="color:#FFFFFF; font-weight:800;">{svg_icon("user", 15, "#00F3FF", 2, margin_right=6)}{escape(current_profile())}</span>
<span style="color:{color}; font-size:11px; margin-left:10px;">{escape(tag)}</span></div>""".replace("\n", ""),
            unsafe_allow_html=True,
        )
    with c2:
        if st.button("Switch", key="btn_switch_profile", use_container_width=True, **icon_kwargs("logout")):
            clear_profile()
            st.rerun()
    if info["error"]:
        if st.button("Retry cloud", key="btn_retry_cloud", **icon_kwargs("refresh")):
            storage.reset_cache()
            st.rerun()
    if info["mode"] != "cloud" or info["error"]:
        with st.expander("Storage status", expanded=False, **expander_kwargs("cloud_off")):
            st.markdown(f"- {storage.config_diagnosis()[1]}")
            if info["error"]:
                st.markdown(f"- Kesalahan terakhir: {info['error']}")
            st.caption("Selama cloud belum aktif, data disimpan sementara di server dan bisa hilang saat app restart.")
            if st.button("Test connection", key="btn_test_cloud", **icon_kwargs("network_check")):
                ok, msg = storage.test_connection()
                (st.success if ok else st.error)(msg)
    return True
