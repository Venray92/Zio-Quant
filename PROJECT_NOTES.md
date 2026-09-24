# PROJECT NOTES: Z-QUANT — Dashboard Screener Saham IDX (Streamlit)

Dokumen serah-terima. Chat baru di Claude Project tidak melihat chat lama, jadi semua keputusan penting
harus ada di sini. Update file ini di akhir sesi kalau ada perubahan berarti (user yang minta, atau tanya
di akhir sesi).

Terakhir diperbarui: 25 Sep 2026 (ronde LOGIN SELESAI + catatan ronde sebelumnya yang ketinggalan:
screener BSJP/BPJS, halaman Rekap Screener terpisah. Login: Supabase Auth email+password, approval
manual admin, gerbang WAJIB LOGIN di app.py, chip profil jadi dropdown, Admin Panel, halaman Profil.
Lihat bagian 3b & 4b — PENTING dibaca kalau mulai sesi baru, ada 13 file yang statusnya "dikirim ke
user tapi belum tentu ke-upload ke GitHub", cek dulu sebelum asumsi apa-apa).

Ronde sebelum ini (24 Sep, masih berlaku): perbaikan Trend Scanner, 2 screener baru MACD Momentum &
MFI Reversal, Leaderboard Screener, lonceng notifikasi icon-only, ringkasan pagi + streak, alert harga
per saham, heatmap Sector Radar, tip harian, threshold Sector Radar disesuaikan, Learn diperbarui total.

Repo GitHub: `Venray92/Zio-Quant` (public, cabang `main` + cabang `data` khusus data harian).
Deploy: Streamlit Cloud, path server `/mount/src/zio-quant/`.

## 1. Apa isi app ini sekarang

**WAJIB LOGIN sekarang** (lihat bagian 3b) — siapapun buka app tanpa sesi login valid cuma lihat
halaman Login/Daftar, apapun URL-nya. Menu atas (urutan dropdown Screeners disengaja: struktur dulu,
lalu oscillator berselang gaya, Overnight, Radar, Planner paling akhir): **Home**, **Screeners** ▸
Trend Scanner, RSI Reversal, Stoch Momentum, MACD Momentum, MFI Reversal, BSJP/BPJS, Sector Radar,
Trade Planner, lalu **Watchlist**, **Money**, **Leaderboard** ▸ Leaderboard Screener/Rekap Screener,
**Learn**. Lonceng notifikasi (ikon bulat) + chip profil (klik → Profil/Admin Page/Keluar) pojok kanan atas.

- **RSI Reversal** — divergence RSI(10) + pola candle.
- **Stoch Momentum** — Stochastic 10,5,5 + PSAR, Golden/Dead Cross.
- **MACD Momentum** — **(baru)** Golden/Dead Cross garis MACD vs garis Sinyal, filter tren EMA,
  dikonfirmasi **ADX/+DI/-DI** (bedanya dari Stoch: yang menyaring "tren beneran lahir vs cuma noise"
  itu ADX, bukan PSAR), volume, dan candle (closing strength).
- **MFI Reversal** — **(baru)** MESIN SAMA PERSIS dengan RSI Reversal (lihat bagian 3), oscillator-nya
  diganti **MFI (Money Flow Index)** — "RSI yang ikut menghitung volume". Sengaja TANPA filter candle
  (beda dari MACD Momentum) supaya nggak "telat" — MFI+OBV itu gaya deteksi dini, bukan gaya konfirmasi.
- **Trend Scanner** — 3 mode berbasis struktur harga & volume: Breakout Surge, Trend Reset, Quiet
  Accumulation. **5 bug diperbaiki 24 Sep** (lihat bagian 3).
- **BSJP / BPJS** — `engines/screener_overnight.py`, `views/tab_overnight.py`: BSJP = Beli Sore Jual
  Pagi, BPJS = Beli Pagi Jual Sore. Threshold relatif ATR (bukan persen tetap), gap dibandingkan ke
  IHSG (biar bisa bedain gerak spesifik saham vs market bareng-bareng), bonus konfluensi kalau saham
  yg sama juga nyala di Breakout Surge/Sector Radar.
- **Sector Radar** — 11 sektor IDX-IC, threshold disesuaikan 24 Sep (lihat bagian 3), + **heatmap 90
  hari terakhir** (baru).
- **Trade Planner** — area beli (BOW/BOB), SL, TP1/TP2, RR, grade.
- **Leaderboard Screener** — **(baru)** ranking win rate & rata-rata edge tiap screener dari `engines/recap.py`,
  murni transparansi sistem (bukan lomba antar user), halaman sendiri sebelah kiri Learn.
- **Watchlist** — simpan saham per profil, catatan bebas per saham (Notes & target — sudah ada dari
  awal), **alert harga** per saham (baru, lihat bagian 3).
- **Money Management** — Portfolio, Position Sizer, Journal (termasuk grafik equity curve — sudah ada
  dari awal), Settings.
- **Home** — hero, **tip harian**, blok pribadi "Untuk kamu hari ini" (+ **streak hari beruntun**),
  Arah Pasar (dgn tanggal data terakhir), Market Pulse, ringkasan Sector Radar, Watchlist count. Rekap
  harian & mingguan SUDAH PINDAH ke halaman **Rekap Screener** sendiri (bukan lagi di Home).
- **Lonceng notifikasi** — **(baru)** ikon bulat kecil di sebelah chip profil (bukan di baris menu),
  badge angka kalau ada yang belum dibaca, isinya gabungan: watchlist masuk zona beli, sinyal baru,
  sektor baru menyala, alert harga kena, SL/TP kena. **Bukan push notification** — dicek ulang tiap
  kali halaman dibuka, bukan dikirim ke HP saat app tertutup (app ini nggak punya jalur push).
- **Learn** — diperbarui total 24 Sep, semua screener/fitur baru terdokumentasi. Alamat lama `/how-to`
  redirect ke `/learn`.

## 2. Aturan kerja (wajib, tidak berubah)
- Jangan ubah nama fungsi, nama variabel, atau format kolom hasil yang tidak berhubungan.
- Jangan ubah desain halaman tanpa persetujuan.
- Bahasa: jawaban santai (Jaksel), singkat. Teks UI: Bahasa Indonesia; grade tetap English singkat.
- Diskusi dulu sampai user acc, JANGAN mulai ngoding sebelum acc. Kalau user udah bilang gas
  ("acc semua", "lanjut langsung semua"), boleh kerjain beberapa item besar berturut-turut tanpa
  nunggu konfirmasi ulang tiap langkah, tapi tiap ada TEMUAN BARU (bug tambahan, celah desain) yang
  DI LUAR yang sudah di-acc, tetap laporkan dulu sebelum dikerjain (jangan diam-diam diperluas sendiri).
- Sebelum ubah file, sebutkan file apa. Sesudah, laporkan hasil tes & batasan dengan jujur.
- Tes: dites lawan referensi independen. Indikator BENAR-BENAR BARU (belum pernah ada di project ini,
  misal MACD/ADX/MFI) WAJIB dites lawan library eksternal yang sudah mapan (`ta`, sudah ada di
  requirements.txt) — bukan cuma loop manual — karena rawan beda konvensi "pemanasan"
  (seeding/warm-up) EMA/Wilder yang butuh puluhan-ratusan candle buat konvergen; kalau tes gagal di
  awal deret data, JANGAN buru-buru anggap bug — cek dulu apa itu cuma transient pemanasan yang
  konvergen di titik lebih jauh, sebelum menyimpulkan salah.
- **Reuse mesin yang sudah teruji itu SAH dan disukai** ketimbang nulis ulang dari nol (contoh: MFI
  Reversal reuse mesin RSI Reversal via parameter `oscillator=`, bukan file 800 baris baru) — asal
  perubahan MINIMAL, backward-compatible (default behavior lama harus 100% terjaga, dites ulang lawan
  seluruh regression yang sudah ada buat mode lama), dan didokumentasikan jelas kenapa.
- Verifikasi visual browser (desktop + mobile 390px) WAJIB untuk halaman baru/berubah tampilan. Sudah
  berulang kali nemuin bug nyata yang nggak kelihatan dari AppTest doang (CSS, kolom nggak stack di HP,
  patch server salah target sehingga fallback ke live-fetch, dll — kalau screenshot nunjukin sumber
  data "live (Yahoo)" padahal harusnya pakai data patch, itu tanda patch salah attach ke modul, cek
  ulang `import X as Y` mana yang dipatch).
- **Kalau nemuin bug/celah desain BARU pas lagi ngerjain sesuatu yang lain** (di luar scope yang
  sedang di-acc): laporkan dulu, tunggu keputusan user, JANGAN diam-diam diperluas sendiri — kecuali
  user sudah bilang "lanjut semua" secara eksplisit untuk paket kerjaan itu.
- Hasil dikirim sebagai file lengkap, CRLF (ikuti line ending yang sudah ada — `data/daftar_saham.txt`
  dan `data/sector_map.csv` sama-sama CRLF).
- Semua bobot skor & ambang adalah titik awal, belum divalidasi backtest riil.
- Jangan sentuh file rahasia (.env, kunci API).
- Akhir sesi: tanya apakah PROJECT_NOTES.md perlu diupdate.

## 3. Keputusan & perbaikan penting ronde ini (24 Sep) — detail teknis

**Trend Scanner — 5 bug diperbaiki** (`engines/screener_trend.py`):
1. Breakout Surge: dulu nggak ngecek breakout MASIH VALID sekarang (bisa udah gagal balik ke bawah
   level, tetap nongol krn masih umur H+2) — sekarang digugurkan kalau harga sudah balik di bawah level.
2. Breakout Surge: jendela base-check disamakan dgn jendela level tembus (`BRK_BASE_LOOKBACK =
   BRK_HIGH_LOOKBACK`, dulu 15 vs 20, nggak sinkron).
3. Trend Reset: "puncak terakhir"/"swing low struktur" dulu salah ambil (harga TERTINGGI sepanjang
   histori, bukan yang PALING BARU) — fungsi baru `_recent_swings()` ambil yang PALING BARU, dipakai
   ulang jendela yang sama (120 hari) utk keduanya (dulu inkonsisten).
4. Volume rata-rata di KETIGA mode dulu ikut menghitung hari yang lagi dicek sendiri (nggak exclude
   hari ini, beda dari cara level harga dihitung yg pakai `.shift(1)`) — di Trend Reset ini bikin
   kontradiksi nyata (syarat wajib "volume mengering" vs bonus "volume balik naik" saling jegal).
   Sekarang semua exclude hari ini via `.shift(1)`.
5. Quiet Accumulation: TIDAK ADA cek posisi terhadap support sama sekali (laporan nyata user: saham yg
   udah jebol support masih nongol). Awalnya dicoba pakai swing low terakhir, TAPI swing ikut "pindah"
   ke level baru begitu saham cukup lama ngumpul di sana (nggak robust) — diganti pakai cek perubahan
   harga langsung: `SQZ_DECLINE_LOOKBACK = 40` hari (sengaja LEBIH PANJANG dari `SQZ_BB_PERIOD = 20`,
   supaya begitu Bollinger "lupa" sama hari jebolnya, cek ini masih inget), turun >`SQZ_MAX_DECLINE_PCT
   = 15.0`% dalam jendela itu → digugurkan.

**MACD Momentum** (`engines/screener_macd.py`, `views/tab_macd.py`, BARU): MACD(12,26,9) + ADX/+DI/-DI
Wilder — dites lawan `ta.trend.MACD` & `ta.trend.ADXIndicator` (independen). Golden Cross: filter tren
`Close>EMA50>EMA200`, dikonfirmasi ADX "tren baru lahir" (ADX pernah <20 dlm 10 hari lalu naik, +DI>-DI),
volume ≥1.2x MA20 (exclude hari ini), bonus candle (closing strength). Dead Cross: mirror.

**MFI Reversal** (`engines/screener_mfi_reversal.py`, `views/tab_mfi.py`, BARU): wrapper tipis di atas
`engines/screener_rsi_divergence.py` yang sekarang punya parameter `oscillator='rsi'|'mfi'` (default
`'rsi'`, jadi RSI Reversal 100% tidak berubah — dites ulang lawan SELURUH regression RSI yg sudah ada).
Kolom internal `df['RSI_10']` TETAP dipakai apa adanya utk dua-duanya (nama generik internal, tidak
pernah keluar ke pengguna — label output `'{osc_label} Kiri/Kanan'` yg berubah). `calculate_mfi()` dites
lawan `ta.volume.MFIIndicator`. **Sengaja TANPA filter candle** (beda dari MACD Momentum — MFI+OBV itu
gaya "deteksi dini", nggak boleh nunggu konfirmasi candle atau kehilangan sifat "duluan tau"-nya; kalau
mau nambah candle nanti, JANGAN minta candle bagus, cukup veto candle jelek/long-upper-wick).

**Leaderboard Screener** (`views/tab_leaderboard.py`, `engines/recap.py::leaderboard()`, BARU): ranking
4 screener oscillator (RSI/Stoch/MACD/MFI — BUKAN Trend Scanner/Sector Radar) berdasar win rate lalu
avg edge tertimbang, window 20 hari bursa. Halaman sendiri, posisi navbar sebelah kiri Learn.

**Sector Radar — threshold disesuaikan** (`engines/sector_radar.py`): persentil ≥80→**70**, saham naik
≥55%→**50%**, konsentrasi ≤70%→**75%** (sengaja TIDAK banyak dilonggarkan — syarat ini yg justru kerja
BENAR nangkep kasus 1 saham RVOL ekstrem mendominasi sektor, contoh nyata: CARE RVOL 1123x bikin
Healthcare gagal "menyala" walau persentil 95, itu bukan bug).

**Fitur "lebih hidup" (baru)**: `utils/activity_store.py` (streak + status baca notif per profil),
`utils/alert_store.py` (alert harga per saham), `engines/notifications.py` (susun item lonceng),
`engines/tips.py` (30 tip harian, rotasi per tanggal), heatmap sektor (`engines/sector_radar.py::
hot_summary/add_day/clean_history/heatmap_data` + `sector_history.json` baru di job harian, LIHAT
bagian 4). Lonceng & alert harga **BUKAN push** — dicek ulang tiap halaman dibuka.

**Lonceng dipindah 2x**: awalnya di baris menu (kolom ke-6), lalu dipindah ke header sebelah chip
profil (masih berbentuk tombol lebar bertuliskan "Notifikasi ▾"), lalu — setelah user lihat
screenshot & bilang "jelek" — diubah final jadi **ikon bulat kecil tanpa label** (icon-only,
`st.popover("", icon=...)`), badge angka overlay via CSS (`.zq-bell-badge`), header pakai 3 kolom
(`col_logo, col_bell, col_chip`) dgn `col_bell` di-flex `justify-content:flex-end` dan chip
`text-align:left` supaya bell nempel persis di kiri chip.

## 3b. LOGIN SYSTEM (25 Sep) — arsitektur lengkap

**⚠️ STATUS UPLOAD KE GITHUB BELUM PASTI.** Semua file Login (13 total, lihat 4b) sudah dikirim ke
user lewat file delivery Claude, TAPI histori nunjukin file yang "dikirim" tidak otomatis ke-upload ke
repo GitHub — user upload manual. **Sebelum mulai kerjaan apapun soal Login di sesi baru, cek dulu
apakah file-file di 4b beneran ada di repo** (jangan asumsi dari PROJECT_NOTES ini doang — pernah
kejadian kerjaan 1 sesi penuh dianggap "hilang" padahal cuma belum keupload, cek langsung ke repo).

**Alur autentikasi**: Supabase Auth (GoTrue REST API, `utils/auth.py`) buat sign up/sign in/verifikasi
email — BUKAN OAuth/Google, email+password polos. Sesi di sisi app pakai token acak di URL (`?s=`,
`utils/session.py`, 30 hari, disimpan di tabel `user_data` yang SAMA (kind="session") — bukan cookie
asli krn Streamlit nggak punya cookie native tanpa komponen tambahan).

**Approval dobel**: (1) Supabase kirim email verifikasi otomatis saat sign up, (2) admin HARUS approve
manual lewat Admin Panel sebelum akun bisa masuk (`utils/account.py::STATUS_PENDING/APPROVED/REJECTED`).
Login ditolak (`views/tab_auth.py::_login_form`) kalau status masih pending/rejected → tampil
`render_pending_notice()` (bukan app biasa).

**Akses per fitur**: tiap akun punya `features: {screener_key: bool}` + `expires_at` (tanggal
kedaluwarsa akses, opsional, admin yg atur). `utils/account.py::has_feature()` = admin selalu True
(bypass semua), selain itu harus approved+belum kedaluwarsa+fitur itu dicentang. Gerbangnya SATU TITIK
saja: `utils/screeners.py::render_screener()` — jadi screener baru otomatis ikut ke-gate, nggak perlu
sentuh 7 file `tab_*.py` satu-satu.

**Gerbang WAJIB LOGIN di app.py**: user putuskan 25 Sep — SEMUA orang termasuk pemilik sendiri via
link lama `?u=nama` (mode tamu tanpa password) **TIDAK LAGI cukup**, harus login pakai akun. Logikanya
di `app.py` persis sesudah `adopt_query_profile()`: no `auth_uid` → `render_page_login()` + `st.stop()`
(tanpa header/navbar sama sekali); ada `auth_uid` tapi `not can_enter_app(account)` →
`render_pending_notice()` + `st.stop()`; baru kalau lolos dua-duanya, app render seperti biasa. Mode
tamu lama (`utils.profile` docstring nyebut "profil tamu") jadi CADANGAN yang secara efektif nggak
kepake lagi selama gerbang ini aktif (kodenya masih ada, sengaja nggak dihapus — kalau nanti mau
dilonggarkan lagi tinggal ubah kondisi ini, nggak perlu nyambung ulang dari nol).

**Admin pertama (bootstrap, WAJIB manual, cuma sekali)**: nggak ada UI buat bikin admin pertama
(circular — Admin Panel sendiri butuh sudah jadi admin). Caranya: (1) sign up biasa lewat halaman
Daftar, (2) buka Supabase dashboard → Table Editor → tabel `user_data` → cari baris
`user_id = 'auth:<uid akun itu>'` dan `kind = 'account'`, (3) edit kolom `data` (jsonb), set
`"is_admin": true` dan `"status": "approved"` langsung di situ. Sesudah itu approval akun2 berikutnya
bisa lewat Admin Panel biasa.

**Config Supabase yang dibutuhin (beda dari keepalive di bagian 8!)**: app butuh `[supabase] url` +
`key` di Streamlit Cloud Secrets, dan key-nya **HARUS service_role key** (bukan publishable/anon) —
soalnya endpoint admin (`admin_list_users`, `admin_confirm_email`, `admin_update_user` yg dipakai
halaman Profil buat ubah email/password/nama SENDIRI) butuh hak admin krn sesi kita cuma nyimpen uid,
bukan access_token Supabase asli user tsb. Tanpa service_role key, Admin Panel error "Supabase belum
diatur" — sudah dites & errornya graceful (nggak crash), tapi ya nggak fungsi.

**Sudah dites**: gerbang app.py (belum login → Login page, pending → notice, approved → app biasa,
admin bypass walau belum approved), chip dropdown (Profil/Admin Page cuma utk admin/Keluar), halaman
Profil & Admin Panel render tanpa error, mode tamu lama (`?u=` doang) sekarang ketolak juga. **1 bug
asli ketemu & dibenerin**: chip dropdown (`views/header.py::_render_account_chip`) awalnya manggil
`utils.account.load_account()` LANGSUNG (bukan lewat `current_account()`), jadi kalau dites/di-mock,
status admin nggak kebaca — link "Admin Page" nggak pernah muncul walau akunnya admin beneran.
Dibenerin: sekarang selalu lewat `utils.profile.current_account()` (satu jalur resolusi yg sama dgn
gerbang app.py & gate screeners.py). Verifikasi visual browser (Playwright, desktop 1400px + mobile
390px) udah dilakuin buat: halaman Login, chip dropdown terbuka, halaman Profil, halaman Admin Panel.

**Belum/nggak sempat dites di sesi ini**: regression suite lama (ratusan tes dari sesi2 sebelumnya,
file `test_*.py`) TIDAK ADA di container/repo manapun yang bisa diakses sesi ini — histori nunjukin
file tes nggak pernah ikut dikirim ke user (cuma file produksi). Jadi tes yang jalan di ronde ini
semuanya ditulis ulang dari nol (AppTest, ~19 skenario gerbang+halaman) — BUKAN regression penuh atas
seluruh app. Kalau mau regression lengkap kaya dulu, perlu ditulis ulang lagi (mahal, belum diminta).

## 4. Peta file tambahan ronde ini (di luar yang sudah ada di peta lama)

| File | Peran |
|---|---|
| `engines/screener_macd.py`, `views/tab_macd.py` | MACD Momentum (baru, lihat bagian 3). |
| `engines/screener_mfi_reversal.py`, `views/tab_mfi.py` | MFI Reversal (baru, wrapper RSI Reversal). |
| `views/tab_leaderboard.py` | Leaderboard Screener (baru). |
| `utils/activity_store.py` | Streak kunjungan + `last_notif_check` per profil (storage generik). |
| `utils/alert_store.py` | Alert harga per saham per profil (`add_alert/remove_alert/check_alerts`). |
| `engines/notifications.py` | `build_notifications()` — gabung watchlist/portofolio/sinyal/sektor/alert jadi item lonceng, pakai keluaran `views/home_today.py::build_today()`. |
| `engines/tips.py` | 30 tip harian, `tip_of_day(tanggal)` deterministik per hari. |
| `engines/recap.py::leaderboard()` | Ranking win rate/avg edge, dipakai Leaderboard Screener. |
| `engines/sector_radar.py::hot_summary/add_day/clean_history/heatmap_data` | Histori harian sektor "menyala" (90 hari), utk heatmap. |
| `engines/market_data.py::SECTOR_HISTORY_FILE/load_sector_history` | Baca `sector_history.json` dari cabang data. |
| `utils/market_source.py::load_sector_hist()` | Wrapper cache utk histori sektor. |
| `scripts/update_market_data.py::run_sector_radar()` | Job harian sekarang juga hitung & simpan histori sektor (gagal tidak menggagalkan job utama). |
| `engines/screener_overnight.py`, `views/tab_overnight.py` | BSJP/BPJS overnight screener (24 Sep, ketinggalan kecatat sebelumnya). |
| `views/tab_recap.py` | Halaman Rekap Screener (rekap harian+mingguan yg tadinya di Home). |

## 4b. Peta file — LOGIN SYSTEM (25 Sep, lihat 3b)

| File | Peran | Status upload GitHub |
|---|---|---|
| `utils/auth.py` | Wrapper REST Supabase Auth (GoTrue): sign_up/sign_in/admin_*. | Cek langsung ke repo |
| `utils/session.py` | Token sesi acak di URL (`?s=`), create/resolve/destroy_session. | Cek langsung ke repo |
| `utils/account.py` | Profil akun, status approval, akses fitur per screener, `can_enter_app()`/`has_feature()`. | Cek langsung ke repo |
| `utils/profile.py` | DIUBAH: dual-identity (login diutamakan, profil tamu jadi cadangan) — `current_auth_uid/current_account/current_profile/user_id` dll. | Cek langsung ke repo |
| `utils/screeners.py` | DIUBAH: gate akses fitur di `render_screener()`, satu titik. | Cek langsung ke repo |
| `utils/pages.py` | DIUBAH: daftar halaman "profile"+"admin" (sengaja TIDAK di navbar utama). | Cek langsung ke repo |
| `views/header.py` | DIUBAH: chip profil jadi `st.popover` (Profil/Admin Page/Keluar) kalau sudah login. | Cek langsung ke repo |
| `views/footer.py` | DIUBAH: baris kecil "Dibuat oleh Zio". | Cek langsung ke repo |
| `views/tab_auth.py` | Halaman Login/Daftar (`render_page_login`) + notice pending/rejected (`render_pending_notice`). | Cek langsung ke repo |
| `views/tab_admin.py` | Admin Panel: tabel akun sortable/searchable/filterable + approve/tolak/set akses/expiry/verifikasi email. | Cek langsung ke repo |
| `views/tab_profile.py` | Halaman Profil: ubah nama/tgl lahir/alamat/HP/email/password sendiri; lihat (bukan ubah) akses fitur. | Cek langsung ke repo |
| `app.py` | DIUBAH: gerbang wajib login (lihat 3b). | Cek langsung ke repo |
| `supabase_setup.sql` | Setup tabel `user_data` (SAMA dgn yg dipakai watchlist/money — bukan tabel baru khusus login). | Cek langsung ke repo |

## 5. Yang DITUNDA sampai user minta lagi
- **Alarm bulanan otomatis `sector_map.csv`** — masih manual.
- **Legal OJK** & **lisensi yfinance komersial** — Login sudah kelar, ini bisa mulai dibahas kalau user minta.
- **Ranking Leaderboard (halaman baru, MENGGANTIKAN Leaderboard Screener + Rekap Screener)** — sudah
  didiskusikan & disepakati konsepnya (belum diimplementasi, urutan setelah Login): Rank 1 = Top 30
  saham berdasar % kenaikan (jendela waktu & ambang minimum diatur user, ada filter tanggal buat lihat
  histori), dedup per saham (gain terbaik menang), tampilkan Saham/Screener asal/Tanggal
  Sinyal/Harga Sinyal→Sekarang/Kenaikan%. Rank 2 = screener mana yg paling banyak nyumbang saham ke Top
  30 itu (bantu user liat screener mana yg "lagi jalan" vs "lagi nggak nyala" di kondisi market
  sekarang). **Prasyarat**: `scripts/update_market_data.py` harus mulai rekam MACD/MFI/BSJP-BPJS ke
  histori harian (sekarang cuma RSI/Stoch/Breakout Surge/Trend Reset yg kerekam). **WAJIB kasih mockup
  dulu ke user sebelum implementasi** (user eksplisit minta ini).
- **Badge/Milestone Journal** — sempat dijelasin konsepnya (badge permanen dari jumlah trade/streak
  journal, ditaro di tab Journal Money Management), user bilang skip dulu.
- **Disclaimer NFA yang lebih tegas** — user acc konsepnya ("murni analisis pribadi/edukasi, bukan
  ajakan beli/jual"), tapi minta ditunda, ditaro di Learn atau Home biar "lebih ada artinya". BELUM
  dikerjain — disclaimer yang ADA sekarang tersebar di beberapa tempat (Home footer, Arah Pasar,
  Sector Radar, Learn FAQ) tapi belum ada satu pernyataan tegas yang eksplisit pakai framing
  "edukasi semata"/NFA.
- **Domain custom (bukan `*.streamlit.app`)** — statusnya nggak jelas di Streamlit Community Cloud
  (fitur baru yg masih digulirkan bertahap per akun), cek langsung ke dashboard pas waktunya tiba.

## 6. Backlog aktif (belum dikerjain, TIDAK ditunda)
- **Mode bandingkan saham** (2-3 saham sisi-sisian) — user bilang "nanti".
- **Backtest sederhana per screener** — user bilang "ngak dlu".
- Kombo oscillator lanjutan yang sempat dibahas tapi belum diimplementasi: **OBV** (dipasangkan dgn MFI
  utk "deteksi dini akumulasi" — MFI+OBV, beda gaya dari MACD+ADX yg sudah jadi). Belum diminta dikerjain.
- Audit 41 kode delisted di tempat lain di luar `data/daftar_saham.txt` (belum diaudit penuh).

## 7. Cara tes yang disepakati
A. Referensi independen — loop manual ATAU library eksternal mapan (`ta`) utk indikator benar-benar
baru. B. Verifikasi visual browser (desktop + mobile 390px) utk apapun yg ubah tampilan. C. User
forward-test manual di market asli — belum ada proses otomatis.

## 8. Info lain
- Supabase keepalive (GitHub Actions, BEDA dari config app di bawah): `SUPABASE_URL`+`SUPABASE_KEY`
  (publishable key dari dashboard Supabase, BUKAN dari file repo) diisi di GitHub Settings → Secrets
  and variables → Actions (Repository secrets, BUKAN Environment secrets).
- Supabase config APP (Streamlit Cloud Secrets, `[supabase] url` + `key`) — dipakai storage.py (data
  watchlist dst) DAN sekarang juga Login. **Untuk Login, key-nya WAJIB service_role** (bukan
  publishable/anon) karena endpoint admin Auth (`admin_list_users`, `admin_confirm_email`,
  `admin_update_user`) butuh hak admin. Kalau cuma publishable key: storage tetap jalan, tapi Admin
  Panel & ganti email/password di halaman Profil akan gagal. Isi di Streamlit Cloud → app settings →
  Secrets (BUKAN GitHub Secrets di atas — beda tempat, beda tujuan).
- Cek GitHub Actions tidak auto-disable (60 hari tanpa aktivitas, repo public).
- BEI menghapus batas harga minimum Rp50 efektif 28 Sep 2026 — filter `MIN_PRICE = 50` di beberapa
  screener perlu ditinjau ulang setelah tanggal itu.
- Streamlit 1.64.0 terpasang. `library ta==0.11.0` (sudah ada di requirements.txt) dipakai sbg referensi
  tes independen utk MACD/ADX/MFI — bukan dependency runtime app, cuma dipakai pas nulis tes.
- `use_container_width` deprecated, pakai `utils.compat.STRETCH` utk kode baru.
