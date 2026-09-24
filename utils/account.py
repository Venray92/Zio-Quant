"""Profil akun (nama, tanggal lahir, alamat, dll), status approval, dan akses fitur per screener +
tanggal kedaluwarsa. Disimpan di tabel yang SAMA dengan Watchlist/Money Management (utils.storage),
user_id = f"auth:{uid_supabase}", kind="account" -- tidak perlu tabel baru."""
from datetime import date

from utils import storage
from utils.screeners import SCREENERS

STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
_STATUSES = {STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED}
FEATURE_KEYS = tuple(s["key"] for s in SCREENERS)


def _key(auth_uid):
    return f"auth:{auth_uid}"


def default_account(email, full_name=""):
    return {
        "email": str(email or "").strip().lower(), "full_name": str(full_name or "").strip(),
        "birthdate": "", "address": "", "phone": "",
        "status": STATUS_PENDING, "is_admin": False,
        "created_at": date.today().isoformat(), "expires_at": None,
        "features": {k: False for k in FEATURE_KEYS},
    }


def _clean(acc, email_fallback=""):
    """Bersihkan data dari luar (Supabase) -- jangan percaya mentah-mentah, sama seperti pola di
    seluruh project ini (watchlist_store, alert_store, dst)."""
    d = default_account(email_fallback)
    if not isinstance(acc, dict):
        return d
    for k in ("email", "full_name", "birthdate", "address", "phone"):
        v = acc.get(k)
        d[k] = str(v)[:200] if v else d[k]
    if acc.get("status") in _STATUSES:
        d["status"] = acc["status"]
    d["is_admin"] = bool(acc.get("is_admin", False))
    d["created_at"] = str(acc.get("created_at") or d["created_at"])[:10]
    exp = acc.get("expires_at")
    d["expires_at"] = str(exp)[:10] if exp else None
    feats = acc.get("features")
    if isinstance(feats, dict):
        d["features"] = {k: bool(feats.get(k, False)) for k in FEATURE_KEYS}
    return d


def create_account(auth_uid, email, full_name=""):
    acc = default_account(email, full_name)
    storage.save(_key(auth_uid), "account", acc)
    return acc


def load_account(auth_uid):
    if not auth_uid:
        return None
    raw = storage.load(_key(auth_uid), "account")
    return _clean(raw) if raw is not None else None


def save_account(auth_uid, account):
    storage.save(_key(auth_uid), "account", _clean(account, account.get("email", "") if isinstance(account, dict) else ""))


def is_access_active(account):
    """Approved DAN (tanpa tanggal kedaluwarsa ATAU belum lewat). Admin selalu True (lihat has_feature
    -- fungsi ini sendiri tidak mengecualikan admin, dipakai has_feature yang urus itu)."""
    if not account or account.get("status") != STATUS_APPROVED:
        return False
    exp = account.get("expires_at")
    if not exp:
        return True
    try:
        return date.fromisoformat(exp) >= date.today()
    except ValueError:
        return True  # tanggal rusak -> jangan diam-diam kunci akses, anggap tidak ada batas


def has_feature(account, feature_key):
    """Admin selalu True (bypass semua pembatasan). Selain itu: harus approved+belum kedaluwarsa DAN
    fitur itu dicentang."""
    if not account:
        return False
    if account.get("is_admin"):
        return True
    if not is_access_active(account):
        return False
    return bool((account.get("features") or {}).get(feature_key, False))


def can_enter_app(account):
    """Boleh masuk app sama sekali (bukan soal fitur MANA, itu urusan has_feature). Admin selalu
    boleh; user biasa harus approved & belum kedaluwarsa."""
    if not account:
        return False
    if account.get("is_admin"):
        return True
    return is_access_active(account)


def list_all_accounts():
    """Semua akun (gabungan Supabase Auth + profil kita sendiri). BUTUH service_role key (lewat
    auth.admin_list_users()). Akun yang belum pernah bikin profil (baru signup, belum ke-provision)
    tetap muncul dgn default_account() supaya tidak hilang dari daftar admin."""
    from utils import auth

    users = auth.admin_list_users()
    out = []
    for u in users:
        email = u.get("email", "")
        acc = load_account(u["id"]) or default_account(email)
        acc["_auth_id"] = u["id"]
        acc["_email_confirmed"] = bool(u.get("confirmed_at") or u.get("email_confirmed_at"))
        out.append(acc)
    return out
