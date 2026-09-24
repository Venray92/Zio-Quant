"""Supabase Auth (GoTrue) via REST -- email+password, terpisah dari utils/storage.py (yang urus data
watchlist/dst). Pakai project & kunci yang SAMA (st.secrets['supabase']), endpoint beda (/auth/v1/...
bukan /rest/v1/...). Password TIDAK PERNAH kita simpan sendiri -- sepenuhnya di Supabase.

Aksi admin (admin_list_users, admin_delete_user, admin_confirm_email) BUTUH service_role key (bukan
anon key) -- kunci yang sekarang sudah dipakai utils/storage.py kemungkinan besar sudah service_role
(lihat komentar _KEY_NAMES di sana), tapi kalau ternyata cuma anon key, fungsi admin_* akan gagal
dengan AuthError yang jelas, bukan diam-diam salah.
"""
import json

import requests

from utils.storage import _raw_config, _http, TIMEOUT


class AuthError(Exception):
    """Pesan sengaja ramah-pengguna, siap ditampilkan apa adanya (bukan traceback mentah)."""


def _config():
    url, key = _raw_config()
    if not url or not key:
        raise AuthError("Supabase belum diatur (cek Secrets di Streamlit Cloud).")
    return url.rstrip("/"), key.strip()


def _headers(key, token=None):
    h = {"apikey": key, "Content-Type": "application/json"}
    h["Authorization"] = f"Bearer {token or key}"
    return h


def _post(path, body, token=None):
    url, key = _config()
    try:
        resp = _http().post(f"{url}{path}", headers=_headers(key, token), data=json.dumps(body), timeout=TIMEOUT)
    except requests.RequestException:
        raise AuthError("Tidak bisa menghubungi server. Coba lagi.") from None
    try:
        payload = resp.json() if resp.content else {}
    except ValueError:
        raise AuthError("Jawaban server tidak terbaca.") from None
    return resp.status_code, payload


def _get(path, token=None, params=None):
    url, key = _config()
    try:
        resp = _http().get(f"{url}{path}", headers=_headers(key, token), params=params or {}, timeout=TIMEOUT)
    except requests.RequestException:
        raise AuthError("Tidak bisa menghubungi server. Coba lagi.") from None
    try:
        payload = resp.json() if resp.content else {}
    except ValueError:
        raise AuthError("Jawaban server tidak terbaca.") from None
    return resp.status_code, payload


def _delete(path, token=None):
    url, key = _config()
    try:
        resp = _http().delete(f"{url}{path}", headers=_headers(key, token), timeout=TIMEOUT)
    except requests.RequestException:
        raise AuthError("Tidak bisa menghubungi server. Coba lagi.") from None
    return resp.status_code


_FRIENDLY = {
    "user_already_exists": "Email ini sudah terdaftar. Coba masuk, atau reset password.",
    "email_exists": "Email ini sudah terdaftar. Coba masuk, atau reset password.",
    "weak_password": "Password terlalu lemah, minimal 8 karakter.",
    "invalid_credentials": "Email atau password salah.",
    "email_not_confirmed": "Email belum diverifikasi. Cek kotak masuk (dan folder spam) untuk link konfirmasi.",
}


def _friendly(payload, fallback):
    code = str(payload.get("error_code") or payload.get("code") or "").lower()
    if code in _FRIENDLY:
        return _FRIENDLY[code]
    msg = payload.get("msg") or payload.get("error_description") or payload.get("error") or payload.get("message")
    if isinstance(msg, str) and "already registered" in msg.lower():
        return _FRIENDLY["user_already_exists"]
    if isinstance(msg, str) and "confirm" in msg.lower() and "email" in msg.lower():
        return _FRIENDLY["email_not_confirmed"]
    if isinstance(msg, str) and "password" in msg.lower() and ("weak" in msg.lower() or "short" in msg.lower() or "at least" in msg.lower()):
        return _FRIENDLY["weak_password"]
    if isinstance(msg, str) and "invalid" in msg.lower() and "credential" in msg.lower():
        return _FRIENDLY["invalid_credentials"]
    return fallback


def sign_up(email, password, full_name=None):
    """Daftar akun baru. Return dict user Supabase ({'id', 'email', 'confirmation_sent_at', ...}).
    Supabase otomatis kirim email konfirmasi (kalau diaktifkan di dashboard Supabase -- Authentication
    > Providers > Email > 'Confirm email'). Melempar AuthError kalau gagal (email sudah dipakai, dst)."""
    email = str(email).strip().lower()
    body = {"email": email, "password": password}
    if full_name:
        body["data"] = {"full_name": str(full_name).strip()}
    status, payload = _post("/auth/v1/signup", body)
    if status >= 400:
        raise AuthError(_friendly(payload, "Pendaftaran gagal. Coba lagi."))
    return payload


def sign_in(email, password):
    """Masuk. Return dict {'access_token', 'refresh_token', 'expires_in', 'user': {...}}.
    Melempar AuthError kalau email/password salah atau email belum diverifikasi."""
    email = str(email).strip().lower()
    status, payload = _post("/auth/v1/token?grant_type=password", {"email": email, "password": password})
    if status >= 400:
        raise AuthError(_friendly(payload, "Gagal masuk. Coba lagi."))
    return payload


def get_user(access_token):
    """Ambil data user dari access token (utk verifikasi sesi masih valid). None kalau token
    invalid/kedaluwarsa (BUKAN exception -- ini dipakai utk cek sesi rutin, gagal itu wajar)."""
    try:
        status, payload = _get("/auth/v1/user", token=access_token)
    except AuthError:
        return None
    return payload if status < 400 else None


def refresh_session(refresh_token):
    """Perpanjang sesi pakai refresh token. Return dict sesi baru (sama bentuknya kayak sign_in),
    atau None kalau refresh token juga sudah tidak valid."""
    status, payload = _post("/auth/v1/token?grant_type=refresh_token", {"refresh_token": refresh_token})
    return payload if status < 400 else None


def sign_out(access_token):
    """Cabut sesi di sisi Supabase. Tidak melempar error kalau gagal -- logout lokal (hapus token
    dari session_state/URL) tetap harus jalan apa pun hasilnya."""
    try:
        _post("/auth/v1/logout", {}, token=access_token)
    except AuthError:
        pass


# ---------------------------------------------------------------- Admin (butuh service_role key)
def admin_list_users(page=1, per_page=200):
    """Daftar SEMUA akun Supabase Auth (email, tanggal daftar, status verifikasi email, dst).
    BUTUH service_role key. Melempar AuthError yang jelas kalau kuncinya cuma anon key (403)."""
    status, payload = _get("/auth/v1/admin/users", params={"page": page, "per_page": per_page})
    if status >= 400:
        raise AuthError(_friendly(payload, "Tidak bisa mengambil daftar akun (kunci mungkin bukan service_role)."))
    return payload.get("users", payload if isinstance(payload, list) else [])


def admin_confirm_email(user_id):
    """Paksa tandai email seorang user sebagai terverifikasi (dipakai kalau admin mau approve
    akun walau user belum sempat klik link konfirmasinya sendiri)."""
    url, key = _config()
    try:
        resp = _http().put(f"{url}/auth/v1/admin/users/{user_id}", headers=_headers(key), data=json.dumps({"email_confirm": True}), timeout=TIMEOUT)
    except requests.RequestException:
        raise AuthError("Tidak bisa menghubungi server. Coba lagi.") from None
    if resp.status_code >= 400:
        raise AuthError("Gagal memverifikasi email akun ini.")


def admin_update_user(user_id, email=None, password=None, full_name=None):
    """Ubah email/password/nama seorang user. Dipakai halaman Profil utk ubah data akun SENDIRI --
    lewat jalur admin (service_role key) krn sesi kita (utils.session) cuma nyimpen uid, bukan
    access_token Supabase asli, jadi tidak bisa pakai endpoint /auth/v1/user (butuh Bearer token
    milik user itu sendiri). Ganti email: perilaku verifikasi ulang mengikuti pengaturan Supabase
    (Authentication > Emails di dashboard), bukan sesuatu yang kita atur dari sini."""
    body = {}
    if email:
        body["email"] = str(email).strip().lower()
    if password:
        body["password"] = password
    if full_name is not None:
        body["user_metadata"] = {"full_name": str(full_name).strip()}
    if not body:
        return
    url, key = _config()
    try:
        resp = _http().put(f"{url}/auth/v1/admin/users/{user_id}", headers=_headers(key), data=json.dumps(body), timeout=TIMEOUT)
    except requests.RequestException:
        raise AuthError("Tidak bisa menghubungi server. Coba lagi.") from None
    if resp.status_code >= 400:
        try:
            payload = resp.json()
        except ValueError:
            payload = {}
        raise AuthError(_friendly(payload, "Gagal menyimpan perubahan akun."))


def admin_delete_user(user_id):
    status = _delete(f"/auth/v1/admin/users/{user_id}")
    if status >= 400:
        raise AuthError("Gagal menghapus akun ini.")
