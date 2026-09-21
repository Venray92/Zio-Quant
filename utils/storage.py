"""Penyimpanan data per pengguna (watchlist, portofolio, setelan).

Semua halaman membaca dan menulis lewat modul ini, dan SELALU membawa user_id.
Nanti saat login dibuat, cukup ganti asal user_id (profile:nama -> auth:<uuid>),
halaman-halamannya tidak perlu diubah.

Backend:
  - Supabase (REST/PostgREST): aktif kalau kunci ada di Streamlit secrets [supabase] url + key.
  - File lokal user_data/<user>.json: cadangan (di Streamlit Cloud sifatnya sementara,
    hilang saat app restart).
  - Tanpa profil (user_id None) = mode tamu, data hanya di sesi browser.
"""
import copy
import json
import os
import re
import threading
from datetime import datetime, timezone

import requests
import streamlit as st

TABLE = "user_data"
TIMEOUT = 8
LOCAL_DIR = "user_data"
_LOCK = threading.Lock()
_SESSION = None


class StorageError(Exception):
    """Gagal baca/tulis. Pesan sengaja singkat dan tanpa detail sensitif (kunci, header, isi respons)."""


def _http():
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
    return _SESSION


def _safe_name(user_id):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", str(user_id))


class LocalBackend:
    name = "local"

    def __init__(self, root=None):
        self.root = root or LOCAL_DIR

    def _path(self, user_id):
        return os.path.join(self.root, _safe_name(user_id) + ".json")

    def _read(self, user_id):
        path = self._path(user_id)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            raise StorageError("File penyimpanan lokal tidak bisa dibaca") from None

    def load(self, user_id, kind):
        return self._read(user_id).get(kind)

    def save(self, user_id, kind, data):
        with _LOCK:
            try:
                os.makedirs(self.root, exist_ok=True)
                try:
                    current = self._read(user_id)
                except StorageError:
                    current = {}
                current[kind] = data
                path = self._path(user_id)
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(current, f, ensure_ascii=False)
                os.replace(tmp, path)
            except OSError:
                raise StorageError("File penyimpanan lokal tidak bisa ditulis") from None


class SupabaseBackend:
    name = "cloud"

    def __init__(self, url, key):
        self.url = str(url).rstrip("/")
        self.key = str(key).strip()

    def _headers(self, extra=None):
        # Kunci baru (sb_secret_...) dikirim lewat header apikey saja. Kunci lama (JWT, awalan eyJ)
        # juga butuh Authorization Bearer.
        h = {"apikey": self.key, "Content-Type": "application/json"}
        if self.key.startswith("eyJ"):
            h["Authorization"] = f"Bearer {self.key}"
        if extra:
            h.update(extra)
        return h

    @staticmethod
    def _check(resp):
        if resp.status_code >= 400:
            raise StorageError(f"Supabase menolak permintaan (kode {resp.status_code})")

    def load(self, user_id, kind):
        try:
            resp = _http().get(
                f"{self.url}/rest/v1/{TABLE}",
                params={"select": "data", "user_id": f"eq.{user_id}", "kind": f"eq.{kind}", "limit": "1"},
                headers=self._headers(),
                timeout=TIMEOUT,
            )
        except requests.RequestException:
            raise StorageError("Supabase tidak bisa dihubungi") from None
        self._check(resp)
        try:
            rows = resp.json()
        except ValueError:
            raise StorageError("Jawaban Supabase tidak terbaca") from None
        return rows[0]["data"] if rows else None

    def save(self, user_id, kind, data):
        payload = [
            {
                "user_id": user_id,
                "kind": kind,
                "data": data,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
        try:
            resp = _http().post(
                f"{self.url}/rest/v1/{TABLE}",
                params={"on_conflict": "user_id,kind"},
                headers=self._headers({"Prefer": "resolution=merge-duplicates,return=minimal"}),
                data=json.dumps(payload),
                timeout=TIMEOUT,
            )
        except requests.RequestException:
            raise StorageError("Supabase tidak bisa dihubungi") from None
        self._check(resp)


_URL_NAMES = ("url", "SUPABASE_URL", "supabase_url", "project_url")
_KEY_NAMES = (
    "key",
    "secret_key",
    "service_role_key",
    "SUPABASE_SECRET_KEY",
    "SUPABASE_KEY",
    "supabase_key",
    "service_key",
)


def _lookup(src, names):
    for n in names:
        try:
            v = src.get(n)
        except Exception:
            v = None
        if isinstance(v, str) and v.strip():
            return v
    return None


def _raw_config():
    """Cari url dan key di Streamlit secrets ([supabase] atau langsung di atas) lalu environment."""
    sources = []
    try:
        sec = st.secrets.get("supabase")
        if sec is not None and not isinstance(sec, str) and hasattr(sec, "get"):
            sources.append(sec)
        sources.append(st.secrets)
    except Exception:
        pass
    sources.append(os.environ)
    url = key = None
    for src in sources:
        url = url or _lookup(src, _URL_NAMES)
        key = key or _lookup(src, _KEY_NAMES)
    return url, key


def _clean_url(u):
    u = str(u).strip().strip("\"'").strip()
    if not u:
        return None
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    u = u.rstrip("/")
    return re.sub(r"/rest(/v1)?$", "", u, flags=re.I)


def _valid_url(u):
    return bool(u) and re.match(r"^https?://[A-Za-z0-9.-]+(:\d+)?$", u) is not None


def _clean_key(k):
    return str(k).strip().strip("\"'").strip()


def _config():
    url, key = _raw_config()
    if not url or not key:
        return None
    url, key = _clean_url(url), _clean_key(key)
    if not _valid_url(url) or not key or key.startswith("sb_publishable_"):
        return None
    return url, key


def config_diagnosis():
    """(status, pesan) tentang konfigurasi Supabase, tanpa membuka isi kunci.
    status: 'ok' | 'missing' | 'problem'"""
    url, key = _raw_config()
    if not url and not key:
        return "missing", "Secrets Supabase belum terbaca. Pastikan ada bagian [supabase] berisi url dan key, lalu Reboot app."
    if not url:
        return "problem", "key terbaca, tapi url belum ada (Project URL, mis. https://xxxx.supabase.co)."
    if not key:
        return "problem", "url terbaca, tapi key belum ada (secret key berawalan sb_secret_)."
    if not _valid_url(_clean_url(url)):
        return "problem", "url tidak valid. Pakai Project URL saja, mis. https://xxxx.supabase.co (bukan alamat dashboard)."
    k = _clean_key(key)
    if k.startswith("sb_publishable_"):
        return "problem", "Itu kunci publishable. Pakai secret key (sb_secret_...) dari Settings > API Keys."
    if not (k.startswith("sb_secret_") or k.startswith("eyJ")):
        return "problem", "key tidak dikenali (seharusnya berawalan sb_secret_)."
    return "ok", "Konfigurasi terbaca."


def _explain_status(code):
    if code in (200, 206):
        return None
    if code in (401, 403):
        return f"Ditolak (kode {code}): key salah atau sudah dihapus. Pakai secret key dari Settings > API Keys."
    if code == 404:
        return "Tabel user_data tidak ditemukan (kode 404). Jalankan supabase_setup.sql di SQL Editor, atau cek Project URL."
    return f"Supabase menjawab kode {code}."


def test_connection():
    """Uji baca dan tulis ke Supabase. Return (berhasil, pesan)."""
    cfg = _config()
    if not cfg:
        return False, config_diagnosis()[1]
    be = SupabaseBackend(*cfg)
    try:
        resp = _http().get(
            f"{be.url}/rest/v1/{TABLE}",
            params={"select": "user_id", "limit": "1"},
            headers=be._headers(),
            timeout=TIMEOUT,
        )
    except requests.RequestException:
        return False, "Tidak bisa menghubungi Supabase. Cek Project URL dan koneksi."
    msg = _explain_status(resp.status_code)
    if msg:
        return False, msg
    try:
        be.save("system:healthcheck", "ping", {"at": datetime.now(timezone.utc).isoformat()})
        be.load("system:healthcheck", "ping")
    except StorageError as e:
        return False, f"Membaca berhasil, tapi menulis gagal ({e}). Pastikan memakai secret key, bukan publishable."
    return True, "Terhubung: baca dan tulis berhasil."


_OVERRIDE = None  # (primary, fallback) untuk tes


def get_backends():
    """(utama, cadangan). Utama = Supabase kalau dikonfigurasi, kalau tidak file lokal."""
    if _OVERRIDE:
        return _OVERRIDE
    local = LocalBackend()
    cfg = _config()
    return (SupabaseBackend(*cfg), local) if cfg else (local, local)


def cloud_configured():
    return get_backends()[0].name == "cloud"


# ---------------- API untuk halaman ----------------
def _cache():
    return st.session_state.setdefault("_store_cache", {})


def _guest():
    return st.session_state.setdefault("_guest_data", {})


def _set_error(msg):
    st.session_state["_store_error"] = msg


def load(user_id, kind, default=None):
    """Baca data. user_id None = tamu (hanya di sesi ini)."""
    if user_id is None:
        val = _guest().get(kind)
        return copy.deepcopy(val) if val is not None else default
    cache = _cache()
    key = (user_id, kind)
    if key not in cache:
        primary, fallback = get_backends()
        data = None
        try:
            data = primary.load(user_id, kind)
            st.session_state["_store_error"] = None
        except StorageError as e:
            _set_error(str(e))
            if fallback is not primary:
                try:
                    data = fallback.load(user_id, kind)
                except StorageError:
                    data = None
        cache[key] = data
    val = cache[key]
    return copy.deepcopy(val) if val is not None else default


def save(user_id, kind, data):
    """Tulis data. True kalau tersimpan di penyimpanan utama."""
    data = copy.deepcopy(data)
    if user_id is None:
        _guest()[kind] = data
        return True
    primary, fallback = get_backends()
    ok = True
    try:
        primary.save(user_id, kind, data)
        st.session_state["_store_error"] = None
    except StorageError as e:
        ok = False
        _set_error(str(e))
        if fallback is not primary:
            try:
                fallback.save(user_id, kind, data)
            except StorageError:
                pass
    _cache()[(user_id, kind)] = data
    return ok


def reset_cache():
    st.session_state.pop("_store_cache", None)
    st.session_state["_store_error"] = None


def status(user_id):
    """{'mode': 'guest'|'cloud'|'local', 'error': str|None}"""
    if user_id is None:
        return {"mode": "guest", "error": None}
    return {"mode": get_backends()[0].name, "error": st.session_state.get("_store_error")}
