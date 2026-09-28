"""Profil akun (nama, tanggal lahir, alamat, dll), status approval, dan akses fitur per screener +
tanggal kedaluwarsa. Disimpan di tabel yang SAMA dengan Watchlist/Money Management (utils.storage),
user_id = f"auth:{uid_supabase}", kind="account" -- tidak perlu tabel baru."""
from datetime import date, datetime, timezone

from utils import storage
from utils.screeners import SCREENERS

STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
_STATUSES = {STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED}
FEATURE_KEYS = tuple(s["key"] for s in SCREENERS)

# Dipakai buat pantau "terakhir login" & "total jam aktif" (Admin Panel). Gap antar-aktivitas lebih
# dari ini (detik) dianggap user idle/pergi -- jedanya TIDAK ikut ditambahin ke total_active_seconds
# (jadi tab dibiarin kebuka semaleman gak bikin angkanya meledak, cuma waktu yg "nyambung" yg kehitung).
ACTIVITY_GAP_SECONDS = 600


def _key(auth_uid):
    return f"auth:{auth_uid}"


def default_account(email, full_name=""):
    return {
        "email": str(email or "").strip().lower(), "full_name": str(full_name or "").strip(),
        "birthdate": "", "address": "", "phone": "",
        "status": STATUS_PENDING, "is_admin": False,
        "created_at": date.today().isoformat(), "expires_at": None,
        "features": {k: False for k in FEATURE_KEYS},
        "last_login_at": None, "last_activity_at": None, "total_active_seconds": 0,
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
    for k in ("last_login_at", "last_activity_at"):
        v = acc.get(k)
        d[k] = str(v) if v else None
    try:
        d["total_active_seconds"] = max(0.0, float(acc.get("total_active_seconds") or 0))
    except (TypeError, ValueError):
        d["total_active_seconds"] = 0.0
    return d


def create_account(auth_uid, email, full_name=""):
    acc = default_account(email, full_name)
    storage.save(_key(auth_uid), "account", acc)
    return acc


def load_account(auth_uid):
    """fresh=True (bukan cache biasa) -- status approval/fitur/kedaluwarsa itu gerbang akses, jadi
    HARUS kebaca real-time tiap rerun, biar begitu admin ubah akses (fitur ditambah, atau tanggal
    kedaluwarsa lewat), sesi user yg lagi login langsung ke-apply tanpa perlu logout-login ulang."""
    if not auth_uid:
        return None
    raw = storage.load(_key(auth_uid), "account", fresh=True)
    return _clean(raw) if raw is not None else None


def save_account(auth_uid, account):
    storage.save(_key(auth_uid), "account", _clean(account, account.get("email", "") if isinstance(account, dict) else ""))


def record_login(auth_uid):
    """Dipanggil pas user BERHASIL sign-in (views/tab_auth.py). Catat waktu login ini sebagai
    'terakhir login' -- juga jadi titik awal buat perhitungan total_active_seconds (track_activity)."""
    acc = load_account(auth_uid)
    if acc is None:
        return
    now = datetime.now(timezone.utc).isoformat()
    acc["last_login_at"] = now
    acc["last_activity_at"] = now
    save_account(auth_uid, acc)


def track_activity(account):
    """Dipanggil tiap rerun app (app.py) buat user yg lagi login & aktif. Nambahin jeda dari
    aktivitas terakhir ke total_active_seconds HANYA kalau jedanya < ACTIVITY_GAP_SECONDS (dianggap
    masih 'nyambung' make app -- jeda yg lebih lama dianggap idle/tab dibiarin kebuka, gak dihitung).
    Return dict account yg SUDAH diupdate (belum disimpan -- caller yg save_account, biar 1x request
    nyatu sama gate check lain di app.py)."""
    if not account:
        return account
    now = datetime.now(timezone.utc)
    last = account.get("last_activity_at")
    if last:
        try:
            last_dt = datetime.fromisoformat(str(last))
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            gap = (now - last_dt).total_seconds()
            if 0 < gap < ACTIVITY_GAP_SECONDS:
                account["total_active_seconds"] = float(account.get("total_active_seconds") or 0) + gap
        except ValueError:
            pass
    account["last_activity_at"] = now.isoformat()
    return account


def format_duration(seconds):
    """3661 -> '1 jam 1 menit'. 0/None -> '< 1 menit'."""
    try:
        total = max(0, int(float(seconds or 0)))
    except (TypeError, ValueError):
        total = 0
    h, rem = divmod(total, 3600)
    m = rem // 60
    if h == 0 and m == 0:
        return "< 1 menit"
    if h == 0:
        return f"{m} menit"
    return f"{h} jam {m} menit"


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
