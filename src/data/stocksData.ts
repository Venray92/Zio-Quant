import { Stock, PortfolioPosition, OrderItem } from '../types';

export const INITIAL_STOCKS: Stock[] = [
  {
    symbol: 'IHSG',
    name: 'Index Harga Saham Gabungan',
    price: 6541.38,
    change: -47.96,
    changePercent: -0.73,
    sector: 'Indeks Utama',
    board: 'Papan Utama',
    tags: ['IDX COMPOSITE'],
    volume: '16.8B',
    frequency: '1,280,412',
    high: 6610.12,
    low: 6535.80,
    open: 6595.20,
    previousClose: 6589.34,
    tvSymbol: 'IDX:COMPOSITE',
  },
];

/**
 * Universe Saham IDX dengan status real-time Technical Analysis:
 * Formula:
 * - Stochastic (10, 5, 5): k = sma(stoch(close, high, low, 10), 5), d = sma(k, 5)
 * - Parabolic SAR (0.02, 0.02, 0.20): psar < close = HIJAU HOLD
 * - Golden Cross: k cross over d dalam kurun 0-3 hari terakhir (%K > %D)
 */
export const STOCKS_UNIVERSE: Stock[] = [
  // =========================================================================
  // KELOMPOK MEMENUHI SYARAT: STOCH (10,5,5) GOLDEN CROSS 0-3 HARI & PSAR HIJAU HOLD
  // =========================================================================
  {
    symbol: 'IPTV',
    name: 'MNC Vision Networks Tbk.',
    price: 32,
    change: 0,
    changePercent: 0.0,
    sector: 'Media & Hiburan',
    board: 'Papan Utama',
    tags: ['KOMPAS100'],
    volume: '6.0M',
    high: 32,
    low: 31,
    open: 32,
    previousClose: 32,
    tvSymbol: 'IDX:IPTV',
    stochK: 46.7,
    stochD: 42.7,
    stochCrossDays: 0, // ★ BARU GOLDEN CROSS HARI INI (0 Hari Lalu)
    psar: 30,
    psarBullish: true, // 30 < 32 (HIJAU HOLD)
    isDeadCross: false,
    statusReason: '★ Baru Golden Cross Hari Ini (%K 46.7 > %D 42.7) & PSAR 30 Hijau Hold',
    isLQ45: false,
  },
  {
    symbol: 'ANTM',
    name: 'Aneka Tambang Tbk.',
    price: 3270,
    change: 0,
    changePercent: 0.0,
    sector: 'Tambang Logam & Emas',
    board: 'Papan Utama',
    tags: ['LQ45', 'IDX30'],
    volume: '135.7M',
    high: 3270,
    low: 3140,
    open: 3230,
    previousClose: 3270,
    tvSymbol: 'IDX:ANTM',
    stochK: 60.1,
    stochD: 42.0,
    stochCrossDays: 2, // Golden Cross 2 Hari Lalu
    psar: 3036,
    psarBullish: true, // 3036 < 3270 (HIJAU HOLD)
    isDeadCross: false,
    statusReason: 'Golden Cross 2 hari lalu (%K 60.1 > %D 42.0) & PSAR 3.036 Hijau Hold',
    isLQ45: true,
  },
  {
    symbol: 'UNTR',
    name: 'United Tractors Tbk.',
    price: 26300,
    change: -75,
    changePercent: -0.28,
    sector: 'Alat Berat & Tambang',
    board: 'Papan Utama',
    tags: ['LQ45', 'IDX30'],
    volume: '2.7M',
    high: 26550,
    low: 26000,
    open: 26400,
    previousClose: 26375,
    tvSymbol: 'IDX:UNTR',
    stochK: 83.9,
    stochD: 75.1,
    stochCrossDays: 2, // Golden Cross 2 Hari Lalu
    psar: 25133,
    psarBullish: true, // 25133 < 26300 (HIJAU HOLD)
    isDeadCross: false,
    statusReason: 'Golden Cross 2 hari lalu (%K 83.9 > %D 75.1) & PSAR 25.133 Hijau Hold',
    isLQ45: true,
  },
  {
    symbol: 'MDKA',
    name: 'Merdeka Copper Gold Tbk.',
    price: 3050,
    change: -10,
    changePercent: -0.33,
    sector: 'Tambang Logam & Tembaga',
    board: 'Papan Utama',
    tags: ['LQ45'],
    volume: '32.5M',
    high: 3050,
    low: 2940,
    open: 3000,
    previousClose: 3060,
    tvSymbol: 'IDX:MDKA',
    stochK: 62.0,
    stochD: 40.0,
    stochCrossDays: 2, // Golden Cross 2 Hari Lalu
    psar: 2835,
    psarBullish: true, // 2835 < 3050 (HIJAU HOLD)
    isDeadCross: false,
    statusReason: 'Golden Cross 2 hari lalu (%K 62.0 > %D 40.0) & PSAR 2.835 Hijau Hold',
    isLQ45: true,
  },
  {
    symbol: 'BFIN',
    name: 'BFI Finance Indonesia Tbk.',
    price: 1005,
    change: -5,
    changePercent: -0.50,
    sector: 'Pembiayaan Konsumen',
    board: 'Papan Utama',
    tags: ['KOMPAS100'],
    volume: '15.0M',
    high: 1015,
    low: 975,
    open: 1000,
    previousClose: 1010,
    tvSymbol: 'IDX:BFIN',
    stochK: 83.8,
    stochD: 83.4,
    stochCrossDays: 2, // Golden Cross 2 Hari Lalu
    psar: 908,
    psarBullish: true, // 908 < 1005 (HIJAU HOLD)
    isDeadCross: false,
    statusReason: 'Golden Cross 2 hari lalu (%K 83.8 > %D 83.4) & PSAR 908 Hijau Hold',
    isLQ45: false,
  },
  {
    symbol: 'AMMN',
    name: 'Amman Mineral Internasional Tbk.',
    price: 4860,
    change: 50,
    changePercent: 1.04,
    sector: 'Tambang Tembaga & Emas',
    board: 'Papan Utama',
    tags: ['LQ45'],
    volume: '89.5M',
    high: 4920,
    low: 4650,
    open: 4710,
    previousClose: 4810,
    tvSymbol: 'IDX:AMMN',
    stochK: 80.3,
    stochD: 61.5,
    stochCrossDays: 3, // Golden Cross 3 Hari Lalu
    psar: 4337,
    psarBullish: true, // 4337 < 4860 (HIJAU HOLD)
    isDeadCross: false,
    statusReason: 'Golden Cross 3 hari lalu (%K 80.3 > %D 61.5) & PSAR 4.337 Hijau Hold',
    isLQ45: true,
  },
  {
    symbol: 'INDF',
    name: 'Indofood Sukses Makmur Tbk.',
    price: 7300,
    change: -25,
    changePercent: -0.34,
    sector: 'Barang Konsumen Primer',
    board: 'Papan Utama',
    tags: ['LQ45'],
    volume: '5.0M',
    high: 7375,
    low: 7225,
    open: 7325,
    previousClose: 7325,
    tvSymbol: 'IDX:INDF',
    stochK: 63.4,
    stochD: 53.6,
    stochCrossDays: 3, // Golden Cross 3 Hari Lalu
    psar: 7106,
    psarBullish: true, // 7106 < 7300 (HIJAU HOLD)
    isDeadCross: false,
    statusReason: 'Golden Cross 3 hari lalu (%K 63.4 > %D 53.6) & PSAR 7.106 Hijau Hold',
    isLQ45: true,
  },
  {
    symbol: 'KINO',
    name: 'Kino Indonesia Tbk.',
    price: 1355,
    change: -45,
    changePercent: -3.21,
    sector: 'Barang Konsumen',
    board: 'Papan Utama',
    tags: ['KOMPAS100'],
    volume: '0.8M',
    high: 1415,
    low: 1355,
    open: 1415,
    previousClose: 1400,
    tvSymbol: 'IDX:KINO',
    stochK: 67.5,
    stochD: 60.7,
    stochCrossDays: 3, // Golden Cross 3 Hari Lalu
    psar: 1314,
    psarBullish: true, // 1314 < 1355 (HIJAU HOLD)
    isDeadCross: false,
    statusReason: 'Golden Cross 3 hari lalu (%K 67.5 > %D 60.7) & PSAR 1.314 Hijau Hold',
    isLQ45: false,
  },

  // =========================================================================
  // KELOMPOK PAS DEADCROSS HARI INI (TEPAT 0 HARI, TIDAK BOLEH LEBIH & TIDAK BOLEH KURANG)
  // %K Menyilang ke bawah %D hari ini
  // =========================================================================
  {
    symbol: 'TLKM',
    name: 'Telkom Indonesia (Persero) Tbk.',
    price: 2600,
    change: -30,
    changePercent: -1.14,
    sector: 'Telekomunikasi',
    board: 'Papan Utama',
    tags: ['LQ45', 'IDX30'],
    volume: '88.5M',
    high: 2630,
    low: 2590,
    open: 2620,
    previousClose: 2630,
    tvSymbol: 'IDX:TLKM',
    stochK: 66.9,
    stochD: 68.0,
    isDeadCross: true,
    deadCrossDays: 0, // ★ PAS DEADCROSS HARI INI (0 Hari)
    psar: 2701,
    psarBullish: false, // SAR 2701 > 2600 (MERAH BUANG)
    statusReason: '⚠ PAS Dead Cross Hari Ini (%K 66.9 < %D 68.0) & PSAR Merah 2.701',
    isLQ45: true,
  },
  {
    symbol: 'CPIN',
    name: 'Charoen Pokphand Indonesia Tbk.',
    price: 3160,
    change: -120,
    changePercent: -3.66,
    sector: 'Peternakan & Pakan',
    board: 'Papan Utama',
    tags: ['LQ45'],
    volume: '52.8M',
    high: 3250,
    low: 3140,
    open: 3250,
    previousClose: 3280,
    tvSymbol: 'IDX:CPIN',
    stochK: 70.3,
    stochD: 74.3,
    isDeadCross: true,
    deadCrossDays: 0, // ★ PAS DEADCROSS HARI INI (0 Hari)
    psar: 3080,
    psarBullish: true,
    statusReason: '⚠ PAS Dead Cross Hari Ini (%K 70.3 < %D 74.3)',
    isLQ45: true,
  },
  {
    symbol: 'JPFA',
    name: 'Japfa Comfeed Indonesia Tbk.',
    price: 2250,
    change: -70,
    changePercent: -3.02,
    sector: 'Peternakan & Pakan',
    board: 'Papan Utama',
    tags: ['KOMPAS100'],
    volume: '21.4M',
    high: 2290,
    low: 2230,
    open: 2280,
    previousClose: 2320,
    tvSymbol: 'IDX:JPFA',
    stochK: 64.9,
    stochD: 71.8,
    isDeadCross: true,
    deadCrossDays: 0, // ★ PAS DEADCROSS HARI INI (0 Hari)
    psar: 2186,
    psarBullish: true,
    statusReason: '⚠ PAS Dead Cross Hari Ini (%K 64.9 < %D 71.8)',
    isLQ45: false,
  },
  {
    symbol: 'KLBF',
    name: 'Kalbe Farma Tbk.',
    price: 735,
    change: -20,
    changePercent: -2.65,
    sector: 'Kesehatan & Farmasi',
    board: 'Papan Utama',
    tags: ['LQ45'],
    volume: '108.3M',
    high: 755,
    low: 730,
    open: 755,
    previousClose: 755,
    tvSymbol: 'IDX:KLBF',
    stochK: 22.4,
    stochD: 28.4,
    isDeadCross: true,
    deadCrossDays: 0, // ★ PAS DEADCROSS HARI INI (0 Hari)
    psar: 824,
    psarBullish: false, // SAR 824 > 735 (MERAH BUANG)
    statusReason: '⚠ PAS Dead Cross Hari Ini (%K 22.4 < %D 28.4) & PSAR Merah 824',
    isLQ45: true,
  },
  {
    symbol: 'MEDC',
    name: 'Medco Energi Internasional Tbk.',
    price: 1555,
    change: -15,
    changePercent: -0.96,
    sector: 'Minyak & Gas Bumi',
    board: 'Papan Utama',
    tags: ['LQ45'],
    volume: '55.0M',
    high: 1645,
    low: 1535,
    open: 1630,
    previousClose: 1570,
    tvSymbol: 'IDX:MEDC',
    stochK: 82.4,
    stochD: 83.1,
    isDeadCross: true,
    deadCrossDays: 0, // ★ PAS DEADCROSS HARI INI (0 Hari)
    psar: 1476,
    psarBullish: true,
    statusReason: '⚠ PAS Dead Cross Hari Ini (%K 82.4 < %D 83.1)',
    isLQ45: true,
  },
  {
    symbol: 'SMGR',
    name: 'Semen Indonesia (Persero) Tbk.',
    price: 1695,
    change: -35,
    changePercent: -2.02,
    sector: 'Semen & Bahan Bangunan',
    board: 'Papan Utama',
    tags: ['LQ45'],
    volume: '20.9M',
    high: 1730,
    low: 1670,
    open: 1715,
    previousClose: 1730,
    tvSymbol: 'IDX:SMGR',
    stochK: 71.2,
    stochD: 77.5,
    isDeadCross: true,
    deadCrossDays: 0, // ★ PAS DEADCROSS HARI INI (0 Hari)
    psar: 1556,
    psarBullish: true,
    statusReason: '⚠ PAS Dead Cross Hari Ini (%K 71.2 < %D 77.5)',
    isLQ45: true,
  },
  {
    symbol: 'HMSP',
    name: 'Hanjaya Mandala Sampoerna Tbk.',
    price: 730,
    change: -10,
    changePercent: -1.35,
    sector: 'Rokok & Tembakau',
    board: 'Papan Utama',
    tags: ['LQ45'],
    volume: '6.2M',
    high: 740,
    low: 730,
    open: 740,
    previousClose: 740,
    tvSymbol: 'IDX:HMSP',
    stochK: 54.4,
    stochD: 59.8,
    isDeadCross: true,
    deadCrossDays: 0, // ★ PAS DEADCROSS HARI INI (0 Hari)
    psar: 724,
    psarBullish: true,
    statusReason: '⚠ PAS Dead Cross Hari Ini (%K 54.4 < %D 59.8)',
    isLQ45: true,
  },
  {
    symbol: 'SMRA',
    name: 'Summarecon Agung Tbk.',
    price: 332,
    change: 0,
    changePercent: 0.0,
    sector: 'Properti & Real Estate',
    board: 'Papan Utama',
    tags: ['KOMPAS100'],
    volume: '21.0M',
    high: 336,
    low: 328,
    open: 334,
    previousClose: 332,
    tvSymbol: 'IDX:SMRA',
    stochK: 78.8,
    stochD: 79.0,
    isDeadCross: true,
    deadCrossDays: 0, // ★ PAS DEADCROSS HARI INI (0 Hari)
    psar: 311,
    psarBullish: true,
    statusReason: '⚠ PAS Dead Cross Hari Ini (%K 78.8 < %D 79.0)',
    isLQ45: false,
  },

  // =========================================================================
  // KELOMPOK DEADCROSS LAMA (SUDAH LEWAT BEBERAPA HARI LALU - BUKAN PAS DEADCROSS)
  // Tidak boleh muncul di "Pas Dead Cross" karena sudah lewat hari H
  // =========================================================================
  {
    symbol: 'BBCA',
    name: 'Bank Central Asia Tbk.',
    price: 6325,
    change: -100,
    changePercent: -1.56,
    sector: 'Keuangan & Perbankan',
    board: 'Papan Utama',
    tags: ['LQ45', 'IDX30'],
    volume: '187.9M',
    high: 6400,
    low: 6250,
    open: 6400,
    previousClose: 6425,
    tvSymbol: 'IDX:BBCA',
    stochK: 36.0,
    stochD: 61.5,
    isDeadCross: true,
    deadCrossDays: 6, // Dead Cross sudah 6 hari lalu (BUKAN pas dead cross)
    psar: 6842,
    psarBullish: false,
    statusReason: 'Death Cross sudah 6 hari lalu (%K 36.0 < %D 61.5)',
    isLQ45: true,
  },
  {
    symbol: 'BBRI',
    name: 'Bank Rakyat Indonesia (Persero) Tbk.',
    price: 3270,
    change: -50,
    changePercent: -1.51,
    sector: 'Keuangan & Perbankan',
    board: 'Papan Utama',
    tags: ['LQ45', 'IDX30'],
    volume: '217.3M',
    high: 3320,
    low: 3250,
    open: 3320,
    previousClose: 3320,
    tvSymbol: 'IDX:BBRI',
    stochK: 71.8,
    stochD: 84.5,
    isDeadCross: true,
    deadCrossDays: 5, // Dead Cross sudah 5 hari lalu (BUKAN pas dead cross)
    psar: 3437,
    psarBullish: false,
    statusReason: 'Death Cross sudah 5 hari lalu (%K 71.8 < %D 84.5)',
    isLQ45: true,
  },
  {
    symbol: 'BMRI',
    name: 'Bank Mandiri (Persero) Tbk.',
    price: 4360,
    change: -40,
    changePercent: -0.91,
    sector: 'Keuangan & Perbankan',
    board: 'Papan Utama',
    tags: ['LQ45', 'IDX30'],
    volume: '112.4M',
    high: 4420,
    low: 4340,
    open: 4400,
    previousClose: 4400,
    tvSymbol: 'IDX:BMRI',
    stochK: 70.4,
    stochD: 81.0,
    isDeadCross: true,
    deadCrossDays: 4, // Dead Cross sudah 4 hari lalu
    psar: 4480,
    psarBullish: false,
    statusReason: 'Death Cross sudah 4 hari lalu (%K 70.4 < %D 81.0)',
    isLQ45: true,
  },
  {
    symbol: 'BBNI',
    name: 'Bank Negara Indonesia (Persero) Tbk.',
    price: 3750,
    change: -50,
    changePercent: -1.32,
    sector: 'Keuangan & Perbankan',
    board: 'Papan Utama',
    tags: ['LQ45', 'IDX30'],
    volume: '27.9M',
    high: 3800,
    low: 3720,
    open: 3800,
    previousClose: 3800,
    tvSymbol: 'IDX:BBNI',
    stochK: 47.3,
    stochD: 70.0,
    isDeadCross: true,
    deadCrossDays: 7, // Dead Cross sudah 7 hari lalu
    psar: 3987,
    psarBullish: false,
    statusReason: 'Death Cross sudah 7 hari lalu (%K 47.3 < %D 70.0)',
    isLQ45: true,
  },
  {
    symbol: 'ASII',
    name: 'Astra International Tbk.',
    price: 4910,
    change: 40,
    changePercent: 0.82,
    sector: 'Otomotif & Konglomerat',
    board: 'Papan Utama',
    tags: ['LQ45', 'IDX30'],
    volume: '42.1M',
    high: 4910,
    low: 4810,
    open: 4870,
    previousClose: 4870,
    tvSymbol: 'IDX:ASII',
    stochK: 47.9,
    stochD: 58.6,
    isDeadCross: true, // Dead Cross!
    psar: 4803,
    psarBullish: true,
    statusReason: 'Death Cross (%K 47.9 < %D 58.6)',
    isLQ45: true,
  },
  {
    symbol: 'ADRO',
    name: 'Alamtri Resources Indonesia Tbk.',
    price: 2640,
    change: -30,
    changePercent: -1.12,
    sector: 'Energi & Batubara',
    board: 'Papan Utama',
    tags: ['LQ45', 'IDX30'],
    volume: '28.6M',
    high: 2680,
    low: 2640,
    open: 2670,
    previousClose: 2670,
    tvSymbol: 'IDX:ADRO',
    stochK: 31.2,
    stochD: 45.0,
    isDeadCross: true, // Dead Cross!
    psar: 2833,
    psarBullish: false,
    statusReason: 'Death Cross (%K 31.2 < %D 45.0) & PSAR Merah (2.833)',
    isLQ45: true,
  },
  {
    symbol: 'GOTO',
    name: 'GoTo Gojek Tokopedia Tbk.',
    price: 50,
    change: 0,
    changePercent: 0.0,
    sector: 'Teknologi',
    board: 'Papan Ekonomi Baru',
    tags: ['LQ45'],
    volume: '150.2M',
    high: 51,
    low: 50,
    open: 50,
    previousClose: 50,
    tvSymbol: 'IDX:GOTO',
    stochK: 50.0,
    stochD: 50.0,
    isDeadCross: true,
    psar: 50,
    psarBullish: false,
    statusReason: 'Tidak Ada Golden Cross',
    isLQ45: true,
  },
  {
    symbol: 'BUKA',
    name: 'Bukalapak.com Tbk.',
    price: 107,
    change: -2,
    changePercent: -1.83,
    sector: 'Teknologi',
    board: 'Papan Pengembangan',
    tags: ['LQ45'],
    volume: '24.1M',
    high: 110,
    low: 106,
    open: 109,
    previousClose: 109,
    tvSymbol: 'IDX:BUKA',
    stochK: 52.7,
    stochD: 68.3,
    isDeadCross: true,
    psar: 118,
    psarBullish: false,
    statusReason: 'Death Cross (%K 52.7 < %D 68.3) & PSAR Merah (118)',
    isLQ45: true,
  },
  {
    symbol: 'UNVR',
    name: 'Unilever Indonesia Tbk.',
    price: 1630,
    change: -25,
    changePercent: -1.51,
    sector: 'Barang Konsumen',
    board: 'Papan Utama',
    tags: ['LQ45'],
    volume: '14.8M',
    high: 1665,
    low: 1625,
    open: 1655,
    previousClose: 1655,
    tvSymbol: 'IDX:UNVR',
    stochK: 26.1,
    stochD: 33.4,
    isDeadCross: true,
    psar: 1803,
    psarBullish: false,
    statusReason: 'Death Cross (%K 26.1 < %D 33.4) & PSAR Merah (1.803)',
    isLQ45: true,
  },
  {
    symbol: 'BRIS',
    name: 'Bank Syariah Indonesia Tbk.',
    price: 1720,
    change: -30,
    changePercent: -1.71,
    sector: 'Keuangan & Perbankan',
    board: 'Papan Utama',
    tags: ['LQ45'],
    volume: '28.1M',
    high: 1760,
    low: 1715,
    open: 1750,
    previousClose: 1750,
    tvSymbol: 'IDX:BRIS',
    stochK: 6.0,
    stochD: 21.0,
    isDeadCross: true,
    psar: 1833,
    psarBullish: false,
    statusReason: 'Death Cross (%K 6.0 < %D 21.0) & PSAR Merah (1.833)',
    isLQ45: true,
  },
  {
    symbol: 'AKRA',
    name: 'AKR Corporindo Tbk.',
    price: 1520,
    change: 0,
    changePercent: 0.0,
    sector: 'Logistik & Distribusi Energi',
    board: 'Papan Utama',
    tags: ['LQ45'],
    volume: '20.3M',
    high: 1530,
    low: 1500,
    open: 1520,
    previousClose: 1520,
    tvSymbol: 'IDX:AKRA',
    stochK: 89.3,
    stochD: 71.5,
    stochCrossDays: 9, // GC sudah 9 hari lalu (lewat dari batas 3 hari)
    psar: 1393,
    psarBullish: true,
    isDeadCross: false,
    statusReason: 'Golden Cross sudah lewat 9 hari (di luar rentang 0-3 hari)',
    isLQ45: true,
  },
];

/**
 * Filter logika screener "1. Stoch - Psar":
 * Sesuai instruksi dan Pine Script "|| STOCH + PSAR || HIJAU HOLD MERAH BUANG":
 * 1. Golden Cross:
 *    - Baru Golden Cross (0 hari) s/d maksimal kelewat 2 hari saja (0, 1, 2 hari lalu)
 *    - %K > %D (Garis K di atas D)
 *    - Parabolic SAR (0.02, 0.02, 0.20) < close (Status HIJAU HOLD)
 *    - isDeadCross !== true
 * 2. Pas Dead Cross:
 *    - Tepat pas deadcross hari ini (0 hari, tidak boleh lebih tidak boleh kurang)
 *    - %K <= %D (Garis K menyilang ke bawah D)
 *    - isDeadCross === true && deadCrossDays === 0
 */

// 1. Yang lolos screener Golden Cross: baru golden cross s/d kelewat maksimal 2 hari & PSAR Hijau Hold
export function getGoldenCrossScreenedStocks(): Stock[] {
  return STOCKS_UNIVERSE.filter(stock => {
    if (stock.isDeadCross === true) {
      return false;
    }
    // Maksimal 2 hari saja (0, 1, 2)
    const isStochGcInRange = 
      stock.stochCrossDays !== undefined && 
      stock.stochCrossDays >= 0 && 
      stock.stochCrossDays <= 2;

    const isKAboveD = 
      stock.stochK !== undefined && 
      stock.stochD !== undefined && 
      stock.stochK > stock.stochD;

    const isPsarBullish = 
      stock.psarBullish === true || 
      (stock.psar !== undefined && stock.psar < stock.price);

    return isStochGcInRange && isKAboveD && isPsarBullish;
  });
}

// 2. Yang lolos screener Pas Dead Cross: tepat pas dead cross hari ini (0 hari, tidak boleh lebih tidak boleh kurang)
export function getPasDeadCrossStocks(): Stock[] {
  return STOCKS_UNIVERSE.filter(stock => {
    return stock.isDeadCross === true && stock.deadCrossDays === 0;
  });
}

// 3. Gabungan sinyal aktif screener
export function getStochPsarScreenedStocks(filterMode: 'all' | 'gc' | 'dc' = 'all'): Stock[] {
  if (filterMode === 'gc') {
    return getGoldenCrossScreenedStocks();
  }
  if (filterMode === 'dc') {
    return getPasDeadCrossStocks();
  }
  return [
    ...getGoldenCrossScreenedStocks(),
    ...getPasDeadCrossStocks(),
  ];
}

// Screener 2: RSI + Pattern (RSI Divergence, Reversal & Chart Patterns)
export function getRsiPatternScreenedStocks(): Stock[] {
  return STOCKS_UNIVERSE.filter(stock => 
    ['ANTM', 'MDKA', 'AMMN', 'UNTR', 'BBCA', 'BMRI', 'ASII', 'INDF', 'BFIN', 'KLBF'].includes(stock.symbol)
  );
}

export const INITIAL_PORTFOLIO: PortfolioPosition[] = [
  {
    symbol: 'ANTM',
    name: 'Aneka Tambang Tbk.',
    lot: 50,
    avgBuyPrice: 3100,
    currentPrice: 3270,
    marketValue: 16350000,
    unrealizedPnL: 850000,
    unrealizedPnLPercent: 5.48,
  },
  {
    symbol: 'AMMN',
    name: 'Amman Mineral Internasional Tbk.',
    lot: 20,
    avgBuyPrice: 4700,
    currentPrice: 4860,
    marketValue: 9720000,
    unrealizedPnL: 320000,
    unrealizedPnLPercent: 3.40,
  }
];

export const INITIAL_ORDERS: OrderItem[] = [
  {
    id: 'ORD-8921',
    symbol: 'ANTM',
    type: 'BUY',
    orderType: 'LIMIT',
    price: 3200,
    lot: 25,
    total: 8000000,
    status: 'Matched',
    timestamp: '14:28:12',
  },
  {
    id: 'ORD-8919',
    symbol: 'AMMN',
    type: 'BUY',
    orderType: 'LIMIT',
    price: 4750,
    lot: 20,
    total: 9500000,
    status: 'Matched',
    timestamp: '11:15:04',
  }
];

export const TICKER_ITEMS = [
  { symbol: 'IHSG', price: '6,541.38', change: '-47.96 (-0.73%)', isUp: false },
  { symbol: 'ANTM', price: '3,270', change: '+0 (0.00%)', isUp: true },
  { symbol: 'AMMN', price: '4,860', change: '+50 (+1.04%)', isUp: true },
  { symbol: 'UNTR', price: '26,300', change: '-75 (-0.28%)', isUp: false },
  { symbol: 'INDF', price: '7,300', change: '-25 (-0.34%)', isUp: false },
];
