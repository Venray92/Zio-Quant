"""Tip harian singkat utk Home. Murni fungsi tanggal -> index (deterministik, sama utk semua
orang di hari yang sama, ganti tiap hari kalender -- tidak butuh penyimpanan apa pun)."""

TIPS = (
    "RSI di bawah 30 bukan otomatis 'beli sekarang' -- di tren turun kuat, RSI bisa nyangkut di area oversold lama sebelum benar-benar balik arah.",
    "Volume yang menegaskan pergerakan harga itu penting: kenaikan harga tanpa kenaikan volume gampang berbalik arah.",
    "Base yang sempit sebelum breakout biasanya lebih meyakinkan daripada base yang lebar -- artinya penjual sudah kehabisan tenaga.",
    "Stop loss bukan tanda kalah, itu biaya asuransi supaya satu kesalahan tidak menghapus banyak keuntungan sebelumnya.",
    "Posisi yang lebih kecil dari rencana bukan masalah -- posisi yang lebih besar dari rencana yang biasanya jadi masalah.",
    "Golden Cross yang muncul di saham sideways sering kali cuma noise -- cek dulu ada tren yang jelas atau tidak.",
    "PSAR titik di bawah harga menandakan tren naik, tapi PSAR sendirian gampang kena whipsaw di pasar sideways.",
    "Divergence RSI paling kuat ketika harga bikin extreme baru (high/low baru) tapi RSI tidak ikut membuat extreme baru.",
    "Saham dengan rata-rata transaksi harian kecil gampang bergerak liar dari selisih order kecil -- ukuran posisi perlu disesuaikan.",
    "Trailing stop membantu mengunci untung berjalan, tapi terlalu ketat bisa bikin kamu keluar duluan sebelum tren lanjut.",
    "Risk per trade yang konsisten (misal 1% dari equity) lebih penting jangka panjang daripada menang di satu trade besar.",
    "Sektor yang 'menyala' karena satu saham dominan itu beda cerita dari sektor yang kompak naik bersama -- cek konsentrasinya.",
    "Pullback ke area EMA20 di tren naik yang mapan sering jadi area entry yang lebih rapi daripada mengejar harga yang sudah naik jauh.",
    "Squeeze (harga menyempit + volume naik) itu tanda 'siap-siap', bukan sinyal beli -- arah pergerakannya belum tentu ke atas.",
    "Win rate tinggi tidak selalu berarti sistem bagus -- payoff ratio (rata-rata untung vs rata-rata rugi) sama pentingnya.",
    "Journal trading yang jujur (termasuk yang rugi) adalah cara paling murah untuk belajar dari kesalahan sendiri.",
    "Candle final baru bisa dipercaya setelah 16:15 WIB -- sebelum itu, volume dan bentuk candle masih bisa berubah.",
    "Support dan resistance itu area, bukan garis presisi satu angka -- beri sedikit ruang toleransi.",
    "Menambah posisi yang sudah rugi (averaging down) tanpa rencana jelas adalah cara populer memperbesar kerugian kecil jadi besar.",
    "Breakout yang langsung diikuti candle merah besar dengan volume tinggi kadang tanda breakout palsu (bull trap).",
    "Money management yang disiplin bisa menyelamatkan strategi yang biasa-biasa saja, tapi tidak bisa menyelamatkan strategi tanpa disiplin.",
    "Overtrading -- entry hanya karena bosan menunggu -- biasanya lebih merusak return daripada melewatkan satu peluang bagus.",
    "Dua indikator berbeda yang menunjukkan sinyal sama (confluence) biasanya lebih meyakinkan daripada satu indikator sendirian.",
    "Rata-rata volume 20 hari yang dipakai sebagai pembanding 'volume tinggi' bisa berubah kalau ada hari libur di antaranya -- wajar kalau angkanya sedikit bergeser.",
    "Cut loss cepat saat salah itu skill yang lebih jarang dibicarakan tapi sama pentingnya dengan skill mencari entry bagus.",
    "Saham dengan ATR tinggi (bergerak liar) butuh stop loss yang lebih lebar -- stop yang terlalu ketat di saham begini gampang kena duluan sebelum arahnya benar.",
    "Rekap mingguan (searah sinyal, rata-rata edge) itu cara paling jujur menilai apakah suatu screener memang berguna, bukan cuma terasa berguna.",
    "IHSG naik bukan berarti semua saham ikut naik -- itu kenapa Sector Radar membandingkan tiap sektor ke kebiasaannya sendiri, bukan ke IHSG.",
    "Fraksi harga (kelipatan minimum kenaikan/penurunan) beda-beda tergantung harga saham di BEI -- itu kenapa target harga kadang perlu dibulatkan.",
    "Menunggu konfirmasi candle balik arah sebelum masuk itu mengorbankan sedikit harga demi mengurangi false signal -- biasanya worth it.",
)


def tip_of_day(today):
    """today: date/datetime atau string 'YYYY-MM-DD'. Return teks tip (deterministik per hari)."""
    if isinstance(today, str):
        from datetime import date

        today = date.fromisoformat(today[:10])
    return TIPS[today.toordinal() % len(TIPS)]
