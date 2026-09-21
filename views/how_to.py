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
<h4>Di Home</h4>
<ul>
<li><b>Untuk kamu hari ini</b> (setelah punya profil): watchlist yang masuk zona beli, kondisi portofolio, dan sinyal untuk saham milikmu.</li>
<li><b>Arah Pasar</b>: gambaran kondisi IHSG dan sebaran saham. Lihat tab Arah Pasar untuk cara membacanya.</li>
<li><b>Rekap harian dan mingguan</b>: ringkasan hasil tiap screener dari update data terakhir.</li>
</ul>"""
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
<li><b>Trade Planner</b>: membuat rencana BOW (Buy on Weakness) dan BOB (Buy on Breakout) untuk satu atau banyak saham sekaligus.</li>
</ul>
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
<p>Angka IHSG di pojok kiri bawah berasal dari Yahoo dan delayed (bukan tick real-time). Jam di sebelahnya real-time WIB.</p>"""
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
<li><b>PSAR</b>: titik di bawah atau di atas harga yang menandai arah tren dan tempat tren mungkin berbalik.</li>
<li><b>ATR</b>: rata-rata rentang gerak harian. Dipakai untuk mengukur volatilitas dan jarak stop loss atau target.</li>
<li><b>Vol x MA20</b>: volume hari ini dibanding rata-rata 20 hari. 2x artinya dua kali biasanya.</li>
<li><b>Support / Resisten</b>: area harga tempat harga sering tertahan turun (support) atau naik (resisten).</li>
<li><b>Breadth (sebaran)</b>: berapa banyak saham ikut bergerak, bukan hanya indeksnya.</li>
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
