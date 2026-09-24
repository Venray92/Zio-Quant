# PROJECT NOTES: Z-QUANT — Dashboard Screener Saham IDX (Streamlit)

Dokumen serah-terima. Chat baru di Claude Project tidak melihat chat lama, jadi semua keputusan penting
harus ada di sini. Update file ini di akhir sesi kalau ada perubahan berarti (user yang minta, atau tanya
di akhir sesi).

Terakhir diperbarui: 24 Sep 2026 (akhir ronde sangat besar: perbaikan Trend Scanner, 2 screener baru
MACD Momentum & MFI Reversal, Leaderboard Screener, lonceng notifikasi icon-only, ringkasan pagi + streak,
alert harga per saham, heatmap Sector Radar, tip harian, threshold Sector Radar disesuaikan, Learn
diperbarui total).

Repo GitHub: `Venray92/Zio-Quant` (public, cabang `main` + cabang `data` khusus data harian).
Deploy: Streamlit Cloud, path server `/mount/src/zio-quant/`.

## 1. Apa isi app ini sekarang

Menu atas (urutan dropdown Screeners disengaja: struktur dulu, lalu 4 oscillator berselang gaya,
Radar, Planner paling akhir): **Home**, **Screeners** ▸ Trend Scanner, RSI Reversal, Stoch Momentum,
MACD Momentum, MFI Reversal, Sector Radar, Trade Planner, lalu **Watchlist**, **Money**,
**Leaderboard**, **Learn**. Lonceng notifikasi (ikon bulat kecil) + chip profil di pojok kanan atas.

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
- **Sector Radar** — 11 sektor IDX-IC, threshold disesuaikan 24 Sep (lihat bagian 3), + **heatmap 90
  hari terakhir** (baru).
- **Trade Planner** — area beli (BOW/BOB), SL, TP1/TP2, RR, grade.
- **Leaderboard Screener** — **(baru)** ranking win rate & rata-rata edge tiap screener dari `engines/recap.py`,
  murni transparansi sistem (bukan lomba antar user), halaman sendiri sebelah kiri Learn.
- **Watchlist** — simpan saham per profil, catatan bebas per saham (Notes & target — sudah ada dari
  awal), **alert harga** per saham (baru, lihat bagian 3).
- **Money Management** — Portfolio, Position Sizer, Journal (termasuk grafik equity curve — sudah ada
  dari awal), Settings.
- **Home** — hero, **tip harian** (baru), blok pribadi "Untuk kamu hari ini" (+ **streak hari
  beruntun**, baru), Arah Pasar, Market Pulse, ringkasan Sector Radar, rekap harian & mingguan (semua
  4 oscillator + Trend Scanner terarah), Watchlist count.
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

## 5. Yang DITUNDA sampai user minta lagi
- **Login** — prioritas PALING AKHIR, setelah semua yang lain beres.
- **Alarm bulanan otomatis `sector_map.csv`** — masih manual.
- **Legal OJK** & **lisensi yfinance komersial** — nunggu Login kelar.
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
- Supabase keepalive: `SUPABASE_URL`+`SUPABASE_KEY` (publishable key dari dashboard Supabase, BUKAN
  dari file repo) diisi di GitHub Settings → Secrets and variables → Actions (Repository secrets,
  BUKAN Environment secrets).
- Cek GitHub Actions tidak auto-disable (60 hari tanpa aktivitas, repo public).
- BEI menghapus batas harga minimum Rp50 efektif 28 Sep 2026 — filter `MIN_PRICE = 50` di beberapa
  screener perlu ditinjau ulang setelah tanggal itu.
- Streamlit 1.64.0 terpasang. `library ta==0.11.0` (sudah ada di requirements.txt) dipakai sbg referensi
  tes independen utk MACD/ADX/MFI — bukan dependency runtime app, cuma dipakai pas nulis tes.
- `use_container_width` deprecated, pakai `utils.compat.STRETCH` utk kode baru.
