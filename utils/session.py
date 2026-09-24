"""Sesi login lewat token acak di URL (bukan cookie beneran -- Streamlit tidak punya cookie asli
tanpa komponen tambahan). Reuse utils.storage apa adanya (token jadi "user_id" penyimpanan, bukan
tabel baru) -- pola sama seperti alert_store/activity_store dkk."""
import secrets
from datetime import datetime, timedelta, timezone

from utils import storage

SESSION_DAYS = 30
_PREFIX = "session:"
_EXPIRED = "1970-01-01T00:00:00+00:00"


def create_session(user_id, days=SESSION_DAYS):
    """Bikin token sesi baru, valid `days` hari. Return token (taruh ini di URL, mis. ?s=<token>)."""
    token = secrets.token_hex(16)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    storage.save(_PREFIX + token, "session", {"uid": str(user_id), "expires_at": expires_at})
    return token


def resolve_session(token):
    """Token -> user_id, atau None kalau tidak ada/rusak/kedaluwarsa. Tidak pernah melempar error --
    sesi yang tidak valid itu wajar (link lama, logout, dll), bukan kegagalan sistem."""
    if not token or not isinstance(token, str):
        return None
    try:
        data = storage.load(_PREFIX + token, "session")
    except Exception:
        return None
    if not isinstance(data, dict) or not data.get("uid") or "expires_at" not in data:
        return None
    try:
        expires = datetime.fromisoformat(str(data["expires_at"]))
    except ValueError:
        return None
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        return None
    return data["uid"]


def destroy_session(token):
    """Logout: sesi langsung tidak valid lagi (bukan nunggu kedaluwarsa alami)."""
    if not token:
        return
    try:
        storage.save(_PREFIX + token, "session", {"uid": None, "expires_at": _EXPIRED})
    except Exception:
        pass
