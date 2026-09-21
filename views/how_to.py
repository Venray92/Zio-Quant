"""Halaman How To: panduan pakai Z-QUANT."""
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
<h1>{svg_icon("book-2", 24, "#00F3FF", 2, margin_right=8)}HOW TO USE</h1>
<p>Panduan singkat memakai Z-QUANT, dari screening sampai atur risiko.</p>
</div>"""
        ),
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Quick Start", "Screeners", "Trade Plan", "Data & Timing", "Risk", "FAQ"])

    with tabs[0]:
        _doc(
            """<h4>4 langkah dasar</h4>
<ol>
<li><b>Pilih screener</b> di menu <code>Screeners</code>, lalu klik <code>Run Screening</code>.</li>
<li><b>Klik saham</b> di daftar hasil. Panel kanan menampilkan Live Trade Plan: area buy, stop loss, target, dan grade.</li>
<li><b>Simpan</b> saham yang menarik dengan <code>Add to Watchlist</code>, lalu pantau di halaman Watchlist.</li>
<li><b>Hitung lot</b> di Money Management supaya kerugian jika kena SL tetap sesuai batas risiko kamu.</li>
</ol>
<p>Tips: jalankan screening setelah 17:40 WIB supaya semua candle hari itu sudah final.</p>"""
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
</ul>"""
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
            """<h4>Sumber data</h4>
<ul>
<li><b>Jam bursa (09:00 sampai 17:40 WIB)</b>: data diambil langsung dari Yahoo Finance.</li>
<li><b>Di luar jam itu</b>: memakai file harian yang diperbarui otomatis sekitar 17:30 WIB, jadi lebih cepat.</li>
<li>Sumber yang dipakai selalu ditulis di atas daftar hasil (<code>Sumber data: ...</code>).</li>
</ul>
<h4>Candle belum final</h4>
<p>Sebelum 16:15 WIB, candle hari ini masih bergerak. Volume hari itu belum dihitung dan kartu diberi label <code>Candle belum final</code>. Sinyal bisa berubah sampai pasar tutup.</p>
<h4>IHSG di footer</h4>
<p>Angka IHSG di pojok kiri bawah berasal dari Yahoo dan delayed (bukan tick real-time). Jam di sebelahnya real-time WIB.</p>"""
        )

    with tabs[4]:
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

    with tabs[5]:
        _doc(
            """<h4>FAQ</h4>
<p><b>Hasil screening kosong?</b> Bisa memang tidak ada saham yang lolos kriteria hari itu. Coba mode atau screener lain.</p>
<p><b>Kenapa hasil siang dan malam beda?</b> Siang hari candle belum final. Hasil setelah 17:40 WIB lebih stabil.</p>
<p><b>Watchlist hilang?</b> Penyimpanan per pengguna sedang disiapkan. Untuk sementara, export CSV dari halaman Watchlist.</p>
<h4>Disclaimer</h4>
<p>Z-QUANT adalah alat bantu analisa. Semua angka hasil perhitungan sistem dan bisa salah. Bukan rekomendasi beli atau jual. Keputusan dan risiko sepenuhnya milik pengguna (DYOR, DWYOR).</p>"""
        )
