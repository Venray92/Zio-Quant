"""Profil pengguna: dua jalur identitas.

1. LOGIN (baru): email+password lewat Supabase Auth (lihat utils.auth/session/account), sesi lewat
   token di URL (?s=<token>, lihat utils.session). Ini yang dipakai kalau sudah ada.
2. Profil tamu (lama, sebelum ada login): nama profil -> user_id 'profile:<nama>', TANPA password --
   siapa pun yang tahu nama profil bisa membuka datanya. Dipakai sebagai CADANGAN kalau belum/tidak
   login (mis. Supabase Auth belum diatur), supaya app tetap bisa dipakai.

current_profile()/user_id() otomatis pilih LOGIN dulu kalau ada sesi valid, baru profil tamu -- semua
halaman yang sudah pakai dua fungsi ini (Watchlist, Money Management, dst) TIDAK PERLU diubah sama
sekali, ikut otomatis begitu user login.
"""
import re

import streamlit as st

from utils.compat import STRETCH
from utils import storage
from utils.card_html import escape
from utils.icons import expander_kwargs, icon_kwargs, svg_icon

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,31}$")
_RESERVED = {"guest", "admin", "root", "null", "none", "undefined"}


def current_auth_uid():
    """uid Supabase Auth mentah (tanpa prefiks 'auth:') kalau ada sesi login valid, else None. Dicek
    sekali per rerun lalu di-cache di session_state (resolve_session bisa 1x panggilan storage)."""
    if "auth_uid" in st.session_state:
        return st.session_state["auth_uid"]
    uid, token = None, None
    try:
        from utils.session import resolve_session

        token = st.query_params.get("s")
        if token:
            uid = resolve_session(token)
    except Exception:
        uid = None
    st.session_state["auth_uid"] = uid
    st.session_state["auth_token"] = token if uid else None  # token cuma disimpan kalau memang valid
    return uid


def current_session_token():
    current_auth_uid()  # pastikan sudah di-resolve & di-cache
    return st.session_state.get("auth_token")


def set_session_token(token):
    """Dipanggil halaman Login setelah sign_in sukses & create_session()."""
    st.session_state.pop("auth_uid", None)  # paksa current_auth_uid() resolve ulang dari token baru
    st.session_state.pop("auth_token", None)
    try:
        st.query_params["s"] = token
    except Exception:
        pass
    storage.reset_cache()


def clear_session():
    """Logout dari akun Login (beda dari clear_profile(), yang itu utk profil tamu lama)."""
    token = current_session_token()
    if token:
        try:
            from utils.session import destroy_session

            destroy_session(token)
        except Exception:
            pass
    st.session_state.pop("auth_uid", None)
    st.session_state.pop("auth_token", None)
    try:
        if "s" in st.query_params:
            del st.query_params["s"]
    except Exception:
        pass
    storage.reset_cache()


def current_account():
    """Dict akun (profil+status+akses fitur) kalau sedang login, else None. Lihat utils.account."""
    uid = current_auth_uid()
    if not uid:
        return None
    from utils import account

    return account.load_account(uid)


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
    """Nama tampilan: dari akun login (nama lengkap atau email) kalau ada, else profil tamu lama."""
    acc = current_account()
    if acc:
        return acc.get("full_name") or acc.get("email") or "Akun"
    return st.session_state.get("profile")


def user_id():
    uid = current_auth_uid()
    if uid:
        return f"auth:{uid}"
    p = st.session_state.get("profile")
    return f"profile:{p}" if p else None


def adopt_query_profile():
    """Pulihkan identitas dari URL: sesi login (?s=) diutamakan, baru profil tamu lama (?u=)."""
    current_auth_uid()  # cache sesi login (kalau ada ?s=) ke session_state lebih dulu
    if st.session_state.get("profile"):
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
    """query_params untuk st.page_link supaya identitas ikut terbawa saat pindah halaman:
    sesi login (?s=) diutamakan, baru profil tamu lama (?u=)."""
    token = current_session_token()
    if token:
        return {"s": token}
    p = st.session_state.get("profile")
    return {"u": p} if p else {}


def render_profile_card():
    """Kartu profil di atas halaman yang menyimpan data. Return True kalau profil sudah dipilih.
    Kalau sudah login (akun Supabase), identitas diatur lewat chip profil di header -- kartu ini
    dilewati sama sekali (bukan lagi mode 'profil tamu tanpa password')."""
    if current_auth_uid():
        return True
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
                submitted = st.form_submit_button("Save profile", **STRETCH, **icon_kwargs("person_add"))
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
        if st.button("Switch", key="btn_switch_profile", **STRETCH, **icon_kwargs("logout")):
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
