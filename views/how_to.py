"""Halaman Learn: panduan pakai Z-QUANT, arti istilah, dan cara membaca hasil."""
import streamlit as st

from utils.card_html import compact_html
from utils.icons import svg_icon
from utils.screeners import SCREENERS


def _doc(html):
    st.markdown(compact_html(f'<div class="zq-doc">{html}</div>'), unsafe_allow_html=True)


def render_page_how_to():
    st.markdown(
        compact_html(
            f"""<div class="zq-hero">
<h1>{svg_icon("book-2", 24, "#00F3FF", 2, margin_right=8)}LEARN</h1>
<p>Cara memakai Z-QUANT, arti istilah, dan cara membaca hasilnya, dari screening sampai atur risiko.</p>
</div>"""
        ),
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Quick Start", "Screeners", "Trade Plan", "Arah Pasar", "Data & Timing", "Risk", "Istilah", "FAQ"])

    with tabs[0]:
        _doc(
            """<h4>4 langkah dasar</h4>
<ol>
<li><b>Pilih screener</b> di menu <code>Screeners</code>, lalu klik <code>Run Screening</code>.</li>
<li><b>Klik saham</b> di daftar hasil. Panel kanan menampilkan Live Trade Plan: area buy, stop loss, target, dan grade.</li>
<li><b>Simpan</b> saham yang menarik dengan <code>Add to Watchlist</code>, lalu pantau di halaman Watchlist.</li>
<li><b>Hitung lot</b> di Money Management supaya kerugian jika kena SL tetap sesuai batas risiko kamu.</li>
</ol>
<p>Tips: jalankan screening setelah 17:40 WIB supaya semua candle hari itu sudah final.</p>

<h4>Alur lengkap: dari scan sampai eksekusi</h4>
<p><b>Skor BUKAN target beli.</b> Skor cuma menunjukkan seberapa bersih suatu setup sesuai definisi screener itu -- angka transaksi yang sebenarnya (area beli, stop loss, target) ada di panel <b>Live Trade Plan</b>, bukan di angka skornya. Skor 90 di satu screener juga TIDAK BISA dibandingkan ke skor 90 di screener lain -- keduanya mengukur hal yang berbeda. Untuk tahu screener mana yang belakangan ini paling akurat, lihat <b>Leaderboard Screener</b>, bukan menyusun skor semua screener jadi satu ranking.</p>
<p>Alur yang disarankan:</p>
<ol>
<li>Scan (lihat "Kapan waktu paling pas" di bawah), lalu urutkan skor DALAM satu screener yang sama.</li>
<li>Untuk kandidat teratas, buka Live Trade Plan-nya. Perhatikan juga <b>Age</b> (H+0 lebih fresh dari H+2) dan pill <b>Volatilitas Tinggi</b> kalau ada.</li>
<li>Cek chart sendiri -- pola kelihatan bersih? Ada berita atau aksi korporasi yang bisa mengganggu?</li>
<li>Cek <b>Arah Pasar</b> dan <b>Sector Radar</b> -- apakah kondisi market/sektornya searah sama sinyal yang ditemukan?</li>
<li>Hitung ukuran posisi di <b>Money Management</b> supaya kerugian kalau kena stop loss tetap sesuai batas risiko.</li>
<li>Eksekusi sesuai jam pasar (lihat tabel di bawah) -- di dalam rentang Area Beli yang direncanakan, bukan asal ikut harga sekarang.</li>
</ol>
<p><b>Sinyal bukan perintah</b> -- screener menyaring saham yang memenuhi kriteria teknikal, bukan jaminan hasil. Selalu putuskan sendiri.</p>

<h4>Kapan waktu paling pas buat screening</h4>
<table style="width:100%; border-collapse:collapse; font-size:13px;">
<tr style="text-align:left; color:#8B949E;"><th style="padding:4px 8px 4px 0;">Waktu</th><th style="padding:4px 8px;">Bisa dipakai?</th><th style="padding:4px 0;">Catatan</th></tr>
<tr><td style="padding:4px 8px 4px 0; white-space:nowrap;">09:00-16:15 WIB</td><td style="padding:4px 8px;">Bisa, hati-hati</td><td style="padding:4px 0;">Candle hari itu <b>belum final</b> -- volume masih berjalan. Screener yang mengandalkan volume (Breakout Surge, MACD, dst) bisa memberi sinyal yang masih berubah. <b>Kecuali BPJS</b> -- mode ini justru DIRANCANG utk dijalankan live di jam pembukaan (09:00-10:00 WIB), lihat halaman BSJP/BPJS.</td></tr>
<tr><td style="padding:4px 8px 4px 0; white-space:nowrap;">16:15-17:40 WIB</td><td style="padding:4px 8px; color:#00FF66;">Paling pas utk live</td><td style="padding:4px 0;">Candle hari itu sudah dianggap final, market masih buka kalau mau eksekusi hari itu juga. Ini jendela waktu yang dirancang khusus utk mode <b>BSJP</b>.</td></tr>
<tr><td style="padding:4px 8px 4px 0; white-space:nowrap;">Setelah 17:40 (malam)</td><td style="padding:4px 8px;">Paling stabil, buat rencana besok</td><td style="padding:4px 0;">Data paling stabil, tapi market sudah tutup -- eksekusi baru bisa besok pagi.</td></tr>
</table>
<p class="zq-muted" style="font-size:12px;">Sector Radar dan Rekap Screener SELALU pakai file harian (bukan data live), jadi baru ter-update setelah job harian jalan (~17:30 WIB) -- tidak bisa dipakai utk "sektor mana yang lagi ramai SEKARANG JUGA" pas market masih siang hari.</p>

<h4>Di Home</h4>
<ul>
<li><b>Untuk kamu hari ini</b> (setelah punya profil): watchlist yang masuk zona beli, kondisi portofolio, dan sinyal untuk saham milikmu. Muncul juga "X hari beruntun" kalau kamu buka app beberapa hari berturut-turut.</li>
<li><b>Tip hari ini</b>: satu tip singkat yang berganti tiap hari.</li>
<li><b>Arah Pasar</b>: gambaran kondisi IHSG dan sebaran saham. Lihat tab Arah Pasar untuk cara membacanya.</li>
<li><b>Sector Radar</b>: ringkasan sektor yang lagi "menyala" hari ini.</li>
</ul>
<h4>Rekap Screener & Leaderboard</h4>
<p>Menu <b>Leaderboard</b> di navbar sekarang dropdown isi 2 halaman: <b>Leaderboard Screener</b> (ranking win rate tiap screener) dan <b>Rekap Screener</b> (rekap harian & mingguan tiap screener -- dulu ada di Home, sekarang halaman sendiri biar Home tidak kepanjangan).</p>
<h4>Lonceng notifikasi</h4>
<p>Ikon lonceng di sebelah nama profil (perlu profil dulu) merangkum: saham watchlist yang masuk zona beli, sinyal baru, sektor yang baru menyala, alert harga yang kena, dan status stop loss/target posisi. Dicek ulang tiap kali halaman dibuka -- <b>bukan</b> pesan yang dikirim ke HP walau app sedang tertutup.</p>
<h4>Alert harga per saham</h4>
<p>Di panel Live Trade Plan, tombol <code>Set Alert</code> memasang pengingat "kasih tahu kalau harga tembus/turun ke angka X". Sama seperti lonceng, ini dicek ulang tiap halaman dibuka, bukan notifikasi yang dikirim otomatis.</p>"""
        )

    with tabs[1]:
        _doc(
            "".join(
                f"<h4>{s['name']} <span class='zq-chip'>{s['category']}</span></h4><p>{s['desc']}.</p>"
                for s in SCREENERS
            )
            + """<h4>Cara membaca hasil</h4>
<ul>
<li><b>RSI Reversal</b>: mencari divergence antara harga dan RSI (T1 ke T2). Label <code>T2 belum terkonfirmasi</code> artinya titik T2 baru terbentuk dan masih bisa berubah.</li>
<li><b>Stoch Momentum</b>: Golden Cross (bullish) dan Dead Cross (bearish) Stochastic, dibantu PSAR dan tren. Angka bintang = kekuatan sinyal.</li>
<li><b>MACD Momentum</b>: Golden/Dead Cross garis MACD terhadap garis Sinyal, hanya diambil kalau searah tren EMA dan dikonfirmasi volume. Pill <code>Tren baru lahir (ADX)</code> artinya ADX baru naik dari kondisi choppy -- tanda tren ini benar-benar baru terbentuk, bukan tren tua yang sudah lama jalan dan mulai capek.</li>
<li><b>MFI Reversal</b>: mesin yang sama persis dengan RSI Reversal, cuma oscillator-nya diganti MFI (Money Flow Index) -- "RSI yang ikut menghitung volume". Bisa menangkap saham yang RSI-nya biasa saja tapi arus uangnya (volume) sudah mulai berubah duluan.</li>
<li><b>BSJP (Beli Sore Jual Pagi)</b>: mencari saham yang nutup kuat menjelang closing (closing strength tinggi), naiknya dalam rentang sehat relatif ke ATR saham itu sendiri (bukan angka tetap -- naik dikit cukup buat saham tenang, saham liar butuh naik lebih banyak), dikonfirmasi ADX (bukan tren yang sudah terlalu tua/kuat) dan volume. Dijalankan menjelang closing (16:00-17:40 WIB).</li>
<li><b>BPJS (Beli Pagi Jual Sore)</b>: mencari saham yang gap pembukaannya bertahan (belum "diisi balik"), dibandingkan ke gap IHSG hari itu (biar bukan cuma ikut market). <b>Lebih kasar</b> dari BSJP karena app ini pakai data candle harian, bukan data intraday -- hanya benar-benar berarti kalau dijalankan LIVE jam 09:00-10:00 WIB.</li>
<li><b>Trade Planner</b>: membuat rencana BOW (Buy on Weakness) dan BOB (Buy on Breakout) untuk satu atau banyak saham sekaligus.</li>
<li><b>Trend Scanner</b>: 3 mode berbasis struktur harga & volume (bukan RSI/Stochastic). <b>Breakout Surge</b> mencari saham yang baru tembus level tertinggi beberapa minggu disertai lonjakan volume, dan breakout-nya masih bertahan (bukan sudah gagal balik ke bawah level). <b>Trend Reset</b> mencari saham tren naik yang sedang koreksi sehat ke area support, siap lanjut naik lagi. <b>Quiet Accumulation</b> mencari saham yang harganya menyempit (squeeze) sambil volume naik -- istilah tradernya "akumulasi diam-diam" atau "tanam bibit", tanda ada yang mengumpulkan posisi sebelum harga biasanya bergerak. Saham yang baru saja jebol support/turun tajam tidak dihitung, walau sekarang kelihatan "diam" di level barunya. Mode ini tidak berskor dan tidak menunjukkan arah beli/jual, murni daftar pantau.</li>
<li><b>Sector Radar</b>: sektor dianggap "menyala" hari itu kalau nilai transaksinya masuk 30% teratas dibanding kebiasaan 60 hari sektor itu sendiri, mayoritas sahamnya naik, dan tidak didominasi satu saham saja. Heatmap 90 hari terakhir menunjukkan pola sektor mana yang sering menyala.</li>
</ul>
<h4>Leaderboard Screener</h4>
<p>Bukan alat cari sinyal baru -- ini ringkasan transparansi: dari sinyal 20 hari bursa terakhir tiap screener, berapa persen yang harganya benar-benar bergerak searah prediksi (win rate) dan berapa rata-rata pergerakannya (edge). Berguna untuk melihat screener mana yang belakangan ini paling akurat, bukan lomba antar pengguna. Sampel bisa masih kecil di awal, hasil masa lalu bukan jaminan ke depan.</p>
<h4>Sinyal bukan perintah</h4>
<p>Screener hanya menyaring saham yang memenuhi kriteria teknikal pada candle terakhir. Tetap cek chart, berita, dan risiko sebelum bertindak.</p>"""
        )

    with tabs[2]:
        _doc(
            """<h4>Isi kartu Trade Plan</h4>
<ul>
<li><b>Area Buy</b>: rentang harga beli yang direncanakan.</li>
<li><b>Stop Loss</b>: batas keluar jika analisa salah. Wajib dipasang.</li>
<li><b>Target 1 / Target 2</b>: area ambil untung. Sumbernya ditulis di bawah angka (resistance, swing high, atau proyeksi ATR).</li>
<li><b>R:R</b>: perbandingan risiko dan potensi untung. 1 : 2 artinya potensi untung 2x dari risiko.</li>
<li><b>Grade dan Score</b>: kualitas setup (Strong, Good, Fair, Weak). Dinilai per rencana, jadi BOW dan BOB saham yang sama bisa beda grade.</li>
<li><b>Best Fit</b>: rencana yang paling sesuai dengan posisi harga saat ini, selalu tampil paling atas.</li>
<li><b>Warning</b>: catatan risiko, misalnya volatilitas tinggi atau likuiditas rendah.</li>
</ul>"""
        )

    with tabs[3]:
        _doc(
            """<h4>Mode pasar di Home</h4>
<p>Mode pasar (<b>Agresif</b>, <b>Netral</b>, <b>Defensif</b>) adalah ringkasan dari beberapa faktor teknikal yang ditampilkan terbuka di Home. Tidak ada faktor tersembunyi.</p>
<ul>
<li><b>Harga vs EMA50</b>: IHSG di atas EMA50 diberi +1, di bawahnya -1.</li>
<li><b>EMA50 vs EMA200</b>: EMA50 di atas EMA200 = tren menengah naik (+1), sebaliknya -1.</li>
<li><b>RSI 14</b>: di atas 55 diberi +1, di bawah 45 diberi -1.</li>
<li><b>Return 20 sesi</b>: naik lebih dari 2% diberi +1, turun lebih dari 2% diberi -1.</li>
<li><b>Saham di atas EMA50 dan EMA20</b>: dihitung dari saham likuid. 55% atau lebih diberi +1, 40% atau kurang diberi -1.</li>
<li><b>Reli sempit</b>: -1 jika indeks dekat puncak 20 sesi tetapi kurang dari 45% saham di atas EMA50. Artinya kenaikan indeks ditopang segelintir saham.</li>
<li><b>Volatilitas</b>: -1 jika gerak harian lebih dari 1,5 kali biasanya.</li>
</ul>
<p>Skor +3 atau lebih = Agresif, -3 atau kurang = Defensif, selain itu Netral.</p>
<h4>Level penting (support dan resisten)</h4>
<p>Dihitung dari titik balik harga (swing high dan low) selama 1 tahun, EMA50 dan EMA200, dan angka bulat yang berdekatan, lalu digabung. Angka <b>kekuatan</b> menunjukkan berapa banyak petunjuk yang jatuh di area itu. Ini perkiraan area, bukan garis pasti.</p>
<h4>Pandangan otomatis</h4>
<p>Kalimat dibuat otomatis dari angka-angka di atas, termasuk skenario bersyarat ("kalau bertahan di atas X dan tembus Y..."). Ini pandangan teknikal, <b>bukan prediksi dan bukan rekomendasi</b>.</p>
<h4>Rekap harian dan mingguan</h4>
<p>Tiap hari bursa, sistem menjalankan tiap screener dengan pengaturan bawaan dan menyimpan hasilnya. Rekap harian menunjukkan jumlah sinyal dan mana yang baru. Rekap mingguan menghitung perubahan harga dari harga sinyal sampai penutupan terakhir. Hasilnya belum termasuk biaya, sampelnya kecil, dan hasil masa lalu bukan jaminan.</p>"""
        )

    with tabs[4]:
        _doc(
            """<h4>Sumber data</h4>
<ul>
<li><b>Jam bursa (09:00 sampai 17:40 WIB)</b>: data diambil langsung dari Yahoo Finance.</li>
<li><b>Di luar jam itu</b>: memakai file harian yang diperbarui otomatis sekitar 17:30 WIB, jadi lebih cepat.</li>
<li>Sumber yang dipakai selalu ditulis di atas daftar hasil (<code>Sumber data: ...</code>).</li>
<li>Arah pasar dan rekap screener selalu memakai file harian, jadi angkanya tetap sampai update berikutnya.</li>
</ul>
<h4>Candle belum final</h4>
<p>Sebelum 16:15 WIB, candle hari ini masih bergerak. Volume hari itu belum dihitung dan kartu diberi label <code>Candle belum final</code>. Sinyal bisa berubah sampai pasar tutup.</p>
<h4>IHSG di footer</h4>
<p>Angka IHSG di pojok kiri bawah berasal dari Yahoo dan delayed (bukan tick real-time). Jam di sebelahnya real-time WIB.</p>
<h4>Kenapa angka RSI/MFI bisa beda sedikit dari platform lain?</h4>
<p>Selisih 1-2 poin dibanding chart lain (TradingView, dsb.) itu wajar, karena beda waktu pengambilan data antara server kami dan pasar. Selisih yang jauh lebih besar biasanya bukan salah hitung, tapi tanda sahamnya bergerak sangat liar (naik/turun tajam dalam sehari) — untuk saham begini, sedikit saja beda harga antar sumber data bisa membuat RSI/MFI ikut bergeser jauh. Kartu screener RSI Reversal dan MFI Reversal memberi label <code>Volatilitas tinggi</code> untuk saham semacam ini.</p>"""
        )

    with tabs[5]:
        _doc(
            """<h4>Dasar money management</h4>
<ul>
<li><b>Risiko per trade</b>: berapa persen modal yang siap hilang jika SL kena. Umumnya 0,5% sampai 2%.</li>
<li><b>Jumlah lot</b> = risiko rupiah dibagi (harga entry dikurangi SL), lalu dibulatkan ke bawah per 100 lembar.</li>
<li><b>Batas alokasi</b>: jangan taruh terlalu besar di satu saham, walau risikonya kecil.</li>
<li><b>Total risiko terbuka</b>: jumlah risiko semua posisi. Batasi supaya satu hari buruk tidak menghapus banyak modal.</li>
</ul>
<p>Halaman Money Management menghitung semua ini termasuk fee broker.</p>"""
        )

    with tabs[6]:
        _doc(
            """<h4>Istilah dasar</h4>
<ul>
<li><b>Screener</b>: alat yang memindai banyak saham sekaligus dan menampilkan yang memenuhi kriteria tertentu.</li>
<li><b>Sinyal</b>: saham yang lolos kriteria screener pada candle terakhir. Bukan perintah beli atau jual.</li>
<li><b>Bullish / Bearish</b>: kecenderungan harga naik / turun menurut sinyal itu.</li>
<li><b>Candle</b>: satu batang harga untuk satu hari (harga buka, tertinggi, terendah, dan tutup).</li>
<li><b>Lot</b>: 1 lot = 100 lembar saham.</li>
<li><b>Fraksi harga</b>: kelipatan harga yang diizinkan bursa. Makin mahal harganya, makin besar kelipatannya.</li>
<li><b>ARA / ARB</b>: batas kenaikan dan penurunan harga harian otomatis. Besarnya mengikuti aturan BEI yang berlaku.</li>
<li><b>Likuiditas</b>: seberapa mudah saham dibeli dan dijual tanpa menggeser harga. Di sini diukur dari rata-rata nilai transaksi 20 hari.</li>
</ul>
<h4>Indikator</h4>
<ul>
<li><b>EMA</b>: rata-rata harga yang lebih menekankan harga terbaru. EMA20, EMA50, dan EMA200 kira-kira menggambarkan tren 1 bulan, 2,5 bulan, dan 10 bulan.</li>
<li><b>RSI</b>: angka 0 sampai 100 yang membandingkan kekuatan kenaikan dan penurunan terakhir. Di bawah 30 sering disebut jenuh jual, di atas 70 jenuh beli.</li>
<li><b>Divergence</b>: harga membuat titik rendah baru tetapi RSI tidak (bullish), atau harga membuat titik tinggi baru tetapi RSI tidak (bearish). Tandanya tenaga arah sebelumnya melemah.</li>
<li><b>Stochastic</b>: posisi harga tutup terhadap rentang harga beberapa hari. <b>Golden Cross</b>: garis %K memotong %D dari bawah (bullish). <b>Dead Cross</b>: sebaliknya (bearish).</li>
<li><b>MACD</b>: selisih dua EMA (12 dan 26 hari), dibandingkan ke rata-ratanya sendiri (garis Sinyal, EMA 9 hari). Garis MACD memotong ke atas garis Sinyal = Golden Cross, ke bawah = Dead Cross.</li>
<li><b>ADX / +DI / -DI</b>: mengukur seberapa <i>kuat</i> tren berjalan, bukan arahnya. Di bawah 20 = pasar belum jelas arahnya (choppy). +DI dan -DI menunjukkan dorongan naik vs turun; +DI di atas -DI = dorongan naik lebih dominan.</li>
<li><b>MFI (Money Flow Index)</b>: seperti RSI, tapi ikut menghitung volume selain harga -- kadang disebut "RSI yang lebih jujur soal partisipasi pasar".</li>
<li><b>PSAR</b>: titik di bawah atau di atas harga yang menandai arah tren dan tempat tren mungkin berbalik.</li>
<li><b>ATR</b>: rata-rata rentang gerak harian. Dipakai untuk mengukur volatilitas dan jarak stop loss atau target.</li>
<li><b>Vol x MA20</b>: volume hari ini dibanding rata-rata 20 hari. 2x artinya dua kali biasanya.</li>
<li><b>Support / Resisten</b>: area harga tempat harga sering tertahan turun (support) atau naik (resisten).</li>
<li><b>Breadth (sebaran)</b>: berapa banyak saham ikut bergerak, bukan hanya indeksnya.</li>
<li><b>Squeeze</b>: rentang harga menyempit dibanding biasanya (dipakai Quiet Accumulation) -- tanda volatilitas sedang rendah, bukan sinyal arah.</li>
<li><b>Win rate</b>: dari semua sinyal yang keluar, berapa persen yang harganya benar-benar bergerak searah prediksi (dipakai Leaderboard Screener).</li>
</ul>
<h4>Trade plan dan risiko</h4>
<ul>
<li><b>BOW</b> (Buy on Weakness): rencana beli saat harga melemah ke area tertentu. <b>BOB</b> (Buy on Breakout): rencana beli saat harga menembus level tertentu.</li>
<li><b>Stop Loss (SL)</b>: harga keluar jika analisa salah. <b>Take Profit (TP)</b>: area ambil untung. <b>R:R</b>: perbandingan potensi untung dan risiko.</li>
<li><b>Grade</b>: Strong, Good, Fair, atau Weak, penilaian kualitas satu rencana.</li>
<li><b>Equity</b>: total nilai akun (cash + nilai posisi). <b>Open risk</b>: total kerugian jika semua stop loss kena.</li>
<li><b>Mode pasar</b>: Agresif, Netral, atau Defensif, ringkasan kondisi pasar di Home.</li>
</ul>"""
        )

    with tabs[7]:
        _doc(
            """<h4>FAQ</h4>
<p><b>Hasil screening kosong?</b> Bisa memang tidak ada saham yang lolos kriteria hari itu. Coba mode atau screener lain.</p>
<p><b>Kenapa hasil siang dan malam beda?</b> Siang hari candle belum final. Hasil setelah 17:40 WIB lebih stabil.</p>
<p><b>Kenapa rekap di Home beda dengan hasil di halaman screener?</b> Rekap memakai pengaturan bawaan dan data update terakhir. Halaman screener bisa memakai data live dan pilihanmu sendiri.</p>
<p><b>Watchlist hilang?</b> Data tersimpan per profil. Pakai nama profil yang sama di perangkat lain, dan cek <code>Storage status</code> di kartu profil. Kalau statusnya sementara, data bisa hilang saat app restart, jadi export CSV dulu dari halaman Watchlist.</p>
<h4>Disclaimer</h4>
<p>Z-QUANT adalah alat bantu analisa. Semua angka hasil perhitungan sistem dan bisa salah. Bukan rekomendasi beli atau jual. Keputusan dan risiko sepenuhnya milik pengguna (DYOR, DWYOR).</p>"""
        )
