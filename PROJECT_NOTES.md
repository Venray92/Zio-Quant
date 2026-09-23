# PROJECT NOTES: Z-QUANT — Dashboard Screener Saham IDX (Streamlit)

Dokumen serah-terima. Chat baru di Claude Project tidak melihat chat lama, jadi semua keputusan penting
harus ada di sini. Update file ini di akhir sesi kalau ada perubahan berarti (user yang minta, atau tanya
di akhir sesi).

Terakhir diperbarui: 23 Sep 2026 (lanjutan: Trend Scanner -- Breakout Surge & Trend Reset -- masuk rekap
harian/mingguan Home).

Repo GitHub: `Venray92/Zio-Quant` (public, cabang `main` + cabang `data` khusus data harian).
Deploy: Streamlit Cloud, path server `/mount/src/zio-quant/`.

## 1. Apa isi app ini sekarang

Halaman yang sudah ada (menu atas): **Home**, **Screeners** (dropdown: RSI Reversal, Stoch Momentum,
Trend Scanner, Sector Radar, Trade Planner), **Watchlist**, **Money** (Money Management), **Learn**.

- **RSI Reversal** — divergence RSI(10) + pola candle, bullish & bearish.
- **Stoch Momentum** — Stochastic 10,5,5 + PSAR, Golden/Dead Cross.
- **Trend Scanner** — 3 mode berbasis struktur harga & volume (bukan oscillator): **Breakout Surge**
  (tembus resistance + volume meledak), **Trend Reset** (pullback sehat di tren naik), **Quiet
  Accumulation** (harga menyempit + volume naik, watchlist tanpa skor/arah).
- **Sector Radar** — 11 sektor IDX-IC, cari sektor mana yang lagi ramai dana dibanding kebiasaan
  sektor itu sendiri (bukan angka mutlak antar sektor).
- **Trade Planner** — area beli (BOW/BOB), SL, TP1/TP2, RR, grade, untuk satu atau banyak saham.
- **Watchlist** — simpan saham per profil (nama, tanpa password), status zona beli otomatis.
- **Money Management** — Portfolio (equity/cash/risk, posisi), Position Sizer (ukuran lot dari Trade
  Plan), Journal (statistik trade tertutup), Settings (preset risiko).
- **Home** — hero, blok pribadi "Untuk kamu hari ini" (kalau sudah punya profil), Arah Pasar IHSG,
  Market Pulse, ringkasan Sector Radar, rekap harian & mingguan RSI/Stoch, jumlah Watchlist.
- **Learn** (dulu "How To") — panduan, kamus istilah, cara baca tiap fitur, FAQ. Alamat lama `/how-to`
  otomatis redirect ke `/learn`.

## 2. Aturan kerja (wajib, tidak berubah dari awal)
- Jangan ubah nama fungsi, nama variabel, atau format kolom hasil yang tidak berhubungan. Kolom baru
  boleh ditambah, kolom lama tetap ada.
- Jangan ubah desain halaman tanpa persetujuan. Perubahan kecil (teks, warna status, satu elemen
  tambahan) boleh kalau sudah dibahas dan di-acc.
- Bahasa: jawaban santai (Jaksel), singkat. Teks UI untuk pengguna: Bahasa Indonesia; grade tetap
  singkat English (Strong/Good/Fair/Weak).
- Cara kerja: diskusi dulu sampai user acc, JANGAN mulai ngoding sebelum acc. Setelah acc, kerjakan
  langsung, tidak usah tanya ulang tiap langkah kecuali memang perlu klarifikasi teknis.
- Sebelum mengubah file, sebutkan file apa yang akan diubah. Setelah selesai, laporkan hasil tes dan
  batasan dengan jujur.
- Tes: dites lawan referensi independen (loop manual / pandas / rumus dari sumber lain), bukan cuma
  konsistensi internal. Ratusan kasus + beberapa ratus skenario acak biasanya cukup.
- **Verifikasi visual wajib untuk halaman baru/berubah**: jalankan di browser sungguhan (Playwright),
  desktop DAN mobile (390px). Sudah beberapa kali menemukan bug nyata yang tidak kelihatan dari AppTest
  saja (CSS, overflow, kolom tidak stack di HP, dll).
- Hasil akhir dikirim sebagai file lengkap (bukan potongan), CRLF untuk file Python (ikuti line ending
  file yang sudah ada — `data/daftar_saham.txt` dan `data/sector_map.csv` sama-sama CRLF).
- Semua bobot skor dan ambang (2.0x ATR, ATR 8%, Rp1 miliar, dst) adalah titik awal ("best effort"),
  perlu divalidasi lewat data riil / backtest.
- Jangan sentuh file rahasia (.env, kunci API). Repo public, jangan taruh rahasia di repo.
- Akhir sesi: tanya apakah PROJECT_NOTES.md perlu diupdate.

## 3. Peta file

| File | Peran |
|---|---|
| `engines/market_data.py` | Kalender bursa IDX (`IDX_HOLIDAYS`, `IDX_HOLIDAY_YEARS` — **2026 & 2027 sudah terisi**, isi 2028 akhir 2027), jam live, `candle_is_final`, pembaca file data harian, `download_daily_batch`, `find_ticker_file`/`read_ticker_file`, `calendar_alert` (pengingat isi kalender tahun depan). |
| `engines/market_view.py` | Arah Pasar IHSG: EMA/RSI/ATR, swing high/low, support/resisten, `compute_breadth`, `market_mode` (Agresif/Netral/Defensif dari skor faktor transparan), `build_outlook` (kalimat deskriptif). Dipakai juga oleh Trend Scanner & Sector Radar untuk `atr_pct`. |
| `engines/recap.py` | Rekap harian & mingguan untuk Home (`SCREENERS` tuple sendiri, BEDA dari `utils/screeners.py`). Sekarang **4 entri**: RSI, Stoch, **Breakout Surge, Trend Reset** (Trend Scanner). Quiet Accumulation SENGAJA tidak direkap (watchlist tanpa skor/arah, tidak bisa diukur 'searah sinyal'). Breakout Surge & Trend Reset ada di `SINGLE_DIRECTION` (selalu Bullish, baris Bearish disembunyikan di kartu Home). |
| `engines/trade_planner.py` | Class `TradePlanner` (BOW/BOB, SL/TP, grade). `HIGH_VOL_ATR_PCT = 8.0` — definisi "saham liar" dipakai ulang di RSI, Stoch, Trend Scanner, Sector Radar (satu sumber, jangan duplikat angka). |
| `engines/screener_rsi_divergence.py` | RSI(10) divergence. **Bug lama diperbaiki**: RSI T1/T2 dulu dicari-cari dalam window ±2 candle (bisa "nyolong" RSI dari tanggal lain), sekarang PERSIS di candle T1/T2. Cek garis RSI: bullish=lantai, bearish=plafon (SENGAJA asimetris — pullback/rally wajar di antara dua swing tidak boleh menggugurkan pola). Sudah ada tag **Volatilitas Tinggi**. |
| `engines/screener_stoch_psar.py` | Stochastic 10,5,5 + PSAR. Sudah ada field `ATR % Now` / `Volatile Tinggi` (sama definisi dgn Trade Planner). |
| `engines/screener_trend.py` | **Baru.** 3 mode: `detect_breakout_surge`, `detect_trend_reset`, `detect_quiet_accumulation`, runner `run_trend_screener`. Reuse Bollinger/Keltner (TTM Squeeze) utk Quiet Accumulation. Filter overlap: saham yg lolos Breakout Surge TIDAK dobel muncul di Quiet Accumulation (dua status kontradiktif). Threshold & rumus lengkap ada di docstring file ini. |
| `engines/sector_map.py` | **Baru.** Loader `data/sector_map.csv` (962 saham → sektor + nama perusahaan + papan pencatatan, dari IDX-IC 22 Sep 2026). `get_sector`, `get_company_name`, `display_name`, `coverage_stats`. **Perlu diperbarui manual ~bulanan** kalau ada IPO/delisting (belum ada alarm otomatis, lihat bagian 7). |
| `engines/sector_radar.py` | **Baru.** `compute_sector_radar` (per sektor: % naik, % volume tinggi, median return, persentil nilai transaksi vs 60 hari sendiri, deteksi konsentrasi 1 saham dominan, streak "menyala"), `sector_detail` (drill-down per saham + Volatilitas Tinggi). |
| `engines/money.py` | Mesin Money Management murni (tanpa Streamlit): fraksi harga BEI, `size_position`, `portfolio_summary`, `scenarios`, `risk_checks`, transaksi (`add_position`/`sell_position`/`delete_position`), `journal_stats`. Preset risiko: Scalping/Swing/Trend Following/Investing. |
| `utils/money_store.py` | Penyimpanan & aksi Money Management per profil (Supabase/local), pembersihan data rusak. |
| `utils/watchlist_store.py`, `utils/storage.py`, `utils/profile.py` | Watchlist per profil (nama, tanpa password — **login belum ada**, siapa pun yg tau nama profil bisa buka datanya), storage backend (Supabase/local), kartu profil. |
| `utils/card_html.py` | HTML kartu bersama (`build_card`, `pill`, `info_row`, dst) dipakai RSI/Stoch/Watchlist/Trend/Money. **`company_name_html` disisipkan otomatis di `build_card`** — sekali ubah, semua kartu ikut nampilin nama perusahaan. |
| `utils/compat.py` | **Baru.** `STRETCH` — helper `width="stretch"` (Streamlit baru) dgn fallback `use_container_width` (versi lama). Pakai ini utk elemen baru, jangan `use_container_width` langsung lagi. |
| `utils/theme.py` | CSS global satu file. Termasuk: border kontras semua kotak input (selectbox/number/text/date — dulu border sewarna background, sudah diperbaiki global), gaya Mode Trend Scanner, dan **CSS stack workspace 2 kolom** (`st-key-zworkspace_*` → `flex-direction:column` di layar <900px; dipakai RSI/Stoch/Trend/Sector Radar, wajib pakai `keyed_container("zworkspace_xxx")` di sekitar `st.columns([1.3,2.7])` biar CSS ini kena). |
| `utils/pages.py`, `utils/screeners.py` | Satu sumber kebenaran daftar screener (`SCREENERS` list) → menu, URL, Home ikut otomatis kalau nambah entri baru di `utils/screeners.py`. |
| `utils/ui_helpers.py` | `render_inline_trade_planner` — panel "Live Trade Plan" dipakai semua screener. Nama perusahaan sudah muncul di header. |
| `views/tab_rsi.py`, `views/tab_stoch_psar.py` | Halaman RSI/Stoch, layout 2 kolom (`col_left`/`col_right` dibungkus `keyed_container("zworkspace_rsi"/"zworkspace_stoch")`). |
| `views/tab_trend.py` | Halaman Trend Scanner, 2 kolom (kiri list+mode, kanan statistik+Trade Plan — dulu 1 kolom panjang, sudah diperbaiki). |
| `views/tab_sector_radar.py` | Halaman Sector Radar, 2 kolom (kiri list sektor, kanan detail+tabel). `render_sector_summary()` dipanggil dari Home. |
| `views/home.py`, `views/home_today.py` | Home: Arah Pasar (cache key ikut tanggal IHSG sendiri, bukan cuma meta saham utama — supaya kalau IHSG telat update, blok ini ikut nunggu, bukan nampilin data lama diam-diam), Market Pulse, `render_sector_summary`, rekap RSI/Stoch, blok pribadi. |
| `views/watchlist.py`, `views/tab_trade_planner.py`, `views/money_management.py` | Halaman-halaman lain, semua sudah pakai `STRETCH` (bukan `use_container_width` lagi). |
| `views/top_nav.py` | Menu atas. Dropdown "Screeners" auto-close tiap pindah halaman (Streamlit 1.64: popover `key`+`on_change="rerun"`, dipaksa `False` kalau `current_page` berubah). |
| `data/daftar_saham.txt` | Daftar ticker (CRLF). **921 saham** (41 saham delisted/suspend dibuang 22 Sep 2026 berdasar log gagal-download nyata: ARMY, BTEL, CPRI, WSKT, dst — lihat commit/riwayat kalau perlu daftar lengkap). |
| `data/sector_map.csv` | **Baru.** `Kode,Sektor,Nama Perusahaan,Papan Pencatatan`, 962 baris, dari 11 file Excel resmi IDX (per 22 Sep 2026). CRLF. |
| `scripts/update_market_data.py` | Job harian: unduh semua saham (1 tahun), IHSG (`ihsg_history.csv`), jalankan RSI+Stoch+Trend Scanner (Breakout Surge & Trend Reset) dgn setting bawaan → `screener_history.json`. Kegagalan IHSG/rekap/Trend Scanner TIDAK menggagalkan job utama (file lama dibawa/carry-forward). |
| `.github/workflows/update_market_data.yml` | **Jadwal baru (22 Sep 2026): 8 titik cron, tiap 30 menit dari 17:05–20:35 WIB** (dulu cuma 2 titik 17:30 & 20:00 — sering molor jam karena jadwal GitHub "best effort", kadang beberapa jam). Titik yang sudah dapat data hari itu otomatis "lewati" (~30 detik), jadi aman ditambah banyak. Juga: keepalive Supabase, alarm kalender libur tahun depan, alarm kalau job gagal di percobaan terakhir. |

## 4. Data pipeline — ringkas
- File di cabang `data`: `market_data.csv.gz` + `market_data_meta.json` (1 tahun histori, ~921 saham),
  `ihsg_history.csv` (IHSG 1 tahun), `screener_history.json` (hasil RSI/Stoch 40 hari terakhir,
  setting bawaan).
- **Screener manual (RSI/Stoch/Trend Scanner) TIDAK menulis balik ke file ini.** Semua screener cuma
  BACA. Di luar jam bursa (09:00–17:40 WIB), semua screener (termasuk RSI/Stoch/Trend Scanner) jatuh
  ke file harian juga — jadi kalau file belum ke-update hari itu, hasil scan manual JUGA ikut pakai
  data lama, bukan cuma Home/Sector Radar.
- Sector Radar SELALU pakai file harian (tidak pernah live-fetch), karena butuh histori 60 hari
  banyak saham sekaligus.
- Cara cek job jalan/gagal: tab **Actions** di GitHub → klik run terakhir → step "Download market
  data" → cari baris "IHSG: XXX candle..." (sukses) atau "IHSG tidak diperbarui..." (gagal, file lama
  dipertahankan).

## 5. Yang DITUNDA sampai user minta lagi (jangan dikerjakan tanpa diminta ulang)
- **Legal/OJK** soal menampilkan area beli/SL/TP ke publik — user cek sendiri, jangan diingatkan lagi
  sampai Login selesai.
- **Lisensi yfinance** untuk pemakaian komersial — sama, jangan diingatkan sampai Login selesai.
- **Login** (email+password, approve admin, halaman Admin) — prioritas SETELAH user puas dengan
  screener & bug fix. Ini juga yang akan menyelesaikan risiko keamanan Watchlist/Money tanpa password.
- **Alarm bulanan otomatis untuk `sector_map.csv`** (IPO/delisting baru) — belum dibikin, `sector_map.py`
  perlu diperbarui manual sampai ini dikerjakan.

## 6. Backlog aktif (belum dikerjakan, TIDAK ditunda — bisa diangkat kapan saja)
- Bersihkan 41 kode delisted juga dari riwayat/tempat lain kalau ketemu (belum diaudit penuh di luar
  `data/daftar_saham.txt`).
- Volatilitas Tinggi & nama saham sudah merata di semua screener utama; kalau ada halaman baru nanti,
  ingat pola yang sama (`HIGH_VOL_ATR_PCT` dari `engines/trade_planner.py`, nama dari
  `engines/sector_map.py` via `build_card`).

## 7. Cara tes yang disepakati
A. Tes kode oleh Claude: referensi independen (loop manual/pandas/rumus lain), ratusan kasus + skenario
acak, dilaporkan jujur (termasuk keterbatasan). B. Verifikasi visual browser (desktop + mobile 390px)
untuk apapun yang mengubah tampilan. C. User forward-test manual di market asli (dicatat sendiri per
minggu/bulan) — belum ada proses otomatis untuk ini.

## 8. Info lain yang perlu diingat
- Supabase keepalive: perlu secret `SUPABASE_URL` + `SUPABASE_KEY` (publishable key, dari dashboard
  Supabase → Settings → API, BUKAN dari file di repo) diisi di GitHub Settings → Secrets and variables
  → Actions. Kalau kosong, langkah keepalive di workflow cuma dilewati diam-diam (job tetap sukses).
- Cek GitHub Actions tidak auto-disable (repo public non-aktif otomatis kalau 60 hari tanpa aktivitas):
  buka tab Actions → workflow "Update market data" → kalau ada banner "This scheduled workflow is
  disabled", klik Enable.
- BEI menghapus batas harga minimum Rp50 efektif 28 Sep 2026 — filter harga minimum di beberapa
  tempat (`MIN_PRICE = 50` di `screener_trend.py`/`sector_radar.py`, dan tempat lain) perlu ditinjau
  ulang setelah tanggal itu.
- Streamlit versi terpasang: 1.64.0. `use_container_width` sudah deprecated (masih jalan, warning),
  pakai `utils.compat.STRETCH` untuk kode baru.
