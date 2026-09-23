"""Status kunjungan per profil: kapan terakhir buka app (streak harian) dan kapan terakhir cek
notifikasi (dipakai lonceng utk tau mana yang 'baru'). Pola sama seperti watchlist_store.py."""
from datetime import date, timedelta

from utils import storage
from utils.profile import user_id

KIND = "activity"
_DEFAULT = {"last_visit": "", "streak": 0, "last_notif_check": ""}


def _clean(raw):
    if not isinstance(raw, dict):
        return dict(_DEFAULT)
    out = dict(_DEFAULT)
    for k in ("last_visit", "last_notif_check"):
        v = raw.get(k)
        out[k] = str(v)[:10] if v else ""
    try:
        out["streak"] = max(0, int(raw.get("streak") or 0))
    except (TypeError, ValueError):
        out["streak"] = 0
    return out


def load_activity():
    return _clean(storage.load(user_id(), KIND, dict(_DEFAULT)))


def save_activity(data):
    return storage.save(user_id(), KIND, _clean(data))


def record_visit(today_iso):
    """Panggil sekali per hari (Home). Update streak (naik kalau kunjungan hari sebelumnya persis
    kemarin, reset ke 1 kalau ada bolong, tetap kalau hari ini sudah tercatat). Return (streak, is_new_day)."""
    a = load_activity()
    if a["last_visit"] == today_iso:
        return a["streak"], False
    try:
        prev = date.fromisoformat(a["last_visit"]) if a["last_visit"] else None
        today = date.fromisoformat(today_iso)
    except ValueError:
        prev, today = None, None
    if prev and today and today - prev == timedelta(days=1):
        streak = a["streak"] + 1
    else:
        streak = 1
    a["last_visit"], a["streak"] = today_iso, streak
    save_activity(a)
    return streak, True


def last_notif_check():
    return load_activity()["last_notif_check"]


def mark_notif_checked(now_iso):
    a = load_activity()
    a["last_notif_check"] = now_iso
    save_activity(a)
