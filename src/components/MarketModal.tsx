import React, { useState } from 'react';
import { 
  Globe, 
  RefreshCw, 
  ExternalLink, 
  X, 
  Heart, 
  ThumbsUp, 
  ThumbsDown, 
  Flame, 
  TrendingUp, 
  TrendingDown, 
  Filter, 
  Sparkles,
  Layers
} from 'lucide-react';

export interface MarketNewsItem {
  id: string;
  title: string;
  snippet: string;
  source: string;
  sourceUrl: string;
  category: 'GLOBAL' | 'KOMODITAS' | 'IHSG & REGULASI' | 'EMITEN IMPACT';
  impact: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  impactStocks: string[];
  impactReason: string;
  timeAgo: string;
  reactions: {
    love: number;
    like: number;
    down: number;
    fire: number;
  };
  userReaction?: 'love' | 'like' | 'down' | 'fire' | null;
}

const INITIAL_NEWS: MarketNewsItem[] = [
  {
    id: 'n-1',
    title: 'Harga Nikel London Metal Exchange (LME) Melonjak 4.2% Didorong Pemangkasan Suku Bunga The Fed',
    snippet: 'Pelemahan indeks dollar AS dan stimulus industri baja nirkarat global memicu reli harga nikel di pasar komoditas London ke posisi tertinggi dalam 3 bulan terakhir.',
    source: 'Bloomberg Commodity & Reuters Market',
    sourceUrl: 'https://www.reuters.com/markets/commodities/nickel-surges',
    category: 'KOMODITAS',
    impact: 'BULLISH',
    impactStocks: ['ANTM', 'INCO', 'MBMA', 'NCKL'],
    impactReason: 'Kenaikan ASP (Average Selling Price) nikel secara langsung mendongkrak margin laba bersih emiten tambang nikel Indonesia.',
    timeAgo: '12 menit yang lalu',
    reactions: { love: 24, like: 45, down: 2, fire: 38 },
    userReaction: null,
  },
  {
    id: 'n-2',
    title: 'The Federal Reserve Pertahankan Sikap Dovish, Arus Modal Asing (Net Buy) Mengalir Deras ke Big Banks',
    snippet: 'Ketua The Fed mengindikasikan potensi kelonggaran moneter lanjutan di paruh kedua tahun ini. Investor institusi global mencatat net inflow Rp 1.4 Triliun di bursa saham RI.',
    source: 'CNBC Indonesia / Market Watch',
    sourceUrl: 'https://www.cnbcindonesia.com/market',
    category: 'GLOBAL',
    impact: 'BULLISH',
    impactStocks: ['BBCA', 'BMRI', 'BBRI', 'BBNI'],
    impactReason: 'Penurunan suku bunga global mengurangi cost of fund bank dan mendorong inflow dana asing ke aset pasar berkembang.',
    timeAgo: '35 menit yang lalu',
    reactions: { love: 52, like: 67, down: 3, fire: 41 },
    userReaction: null,
  },
  {
    id: 'n-3',
    title: 'Harga Batubara Newcastle Melemah ke $128/Ton Akibat Penumpukan Stok Pembangkit Listrik China',
    snippet: 'Permintaan musiman di Asia Timur mulai melandai saat produksi batubara domestik China dan India mencapai rekor tertinggi, menekan harga spot global.',
    source: 'Koran Kontan / Coal Price Daily',
    sourceUrl: 'https://investasi.kontan.co.id/news/batubara',
    category: 'KOMODITAS',
    impact: 'BEARISH',
    impactStocks: ['ADRO', 'PTBA', 'ITMG', 'UNTR'],
    impactReason: 'Sentimen koreksi jangka pendek pada royalti dan dividen emiten batubara, mendorong rotasi sektor ke perbankan dan konsumer.',
    timeAgo: '1 jam yang lalu',
    reactions: { love: 5, like: 14, down: 29, fire: 8 },
    userReaction: null,
  },
  {
    id: 'n-4',
    title: 'Minyak Mentah Brent Bertahan di $82/Barel Menyusul Ketegangan Geopolitik Jalur Maritim Laut Merah',
    snippet: 'OPEC+ menegaskan kepatuhan kuota pengurangan produksi sukarela di tengah kekhawatiran disrupsi pasokan minyak mentah internasional.',
    source: 'Financial Times / OilPrice.com',
    sourceUrl: 'https://oilprice.com/Energy/Crude-Oil',
    category: 'GLOBAL',
    impact: 'BULLISH',
    impactStocks: ['MEDC', 'PGAS', 'ELSA', 'AKRA'],
    impactReason: 'Stabilitas harga minyak bumi menopang pendapatan hulu migas dan efisiensi margin distribusi gas alam.',
    timeAgo: '2 jam yang lalu',
    reactions: { love: 18, like: 32, down: 4, fire: 22 },
    userReaction: null,
  },
  {
    id: 'n-5',
    title: 'Indeks Kepercayaan Konsumen RI Naik ke 124.8, Daya Beli Sektor Consumer Goods Menguat',
    snippet: 'Bank Indonesia melaporkan optimisme konsumen terhadap kondisi ekonomi dan ketersediaan lapangan kerja tetap solid di zona ekspansif.',
    source: 'Bisnis.com / Bank Indonesia Survey',
    sourceUrl: 'https://ekonomi.bisnis.com/makro',
    category: 'IHSG & REGULASI',
    impact: 'BULLISH',
    impactStocks: ['ICBP', 'INDF', 'MYOR', 'KLBF'],
    impactReason: 'Kenaikan volume penjualan barang konsumen dan ketahanan daya beli masyarakat menjelang periode belanja nasional.',
    timeAgo: '3 jam yang lalu',
    reactions: { love: 31, like: 48, down: 1, fire: 19 },
    userReaction: null,
  },
  {
    id: 'n-6',
    title: 'Permintaan Pulp & Kertas Global Rebound: Harga Kayu Lunak Ekspor Naik 3.8%',
    snippet: 'Restocking industri kemasan e-commerce di Amerika Utara dan Eropa mengangkat margin laba produsen bubur kertas Asia Tenggara.',
    source: 'Fastmarkets RISI / Investor Daily',
    sourceUrl: 'https://investor.id/market-and-corporate',
    category: 'KOMODITAS',
    impact: 'BULLISH',
    impactStocks: ['INKP', 'TKIM'],
    impactReason: 'Kenaikan harga jual rata-rata pulp dan ekspor kertas kemasan meningkatkan proyeksi EBITDA emiten Grup Sinarmas.',
    timeAgo: '5 jam yang lalu',
    reactions: { love: 14, like: 26, down: 2, fire: 15 },
    userReaction: null,
  },
];

interface MarketModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectStock?: (symbol: string) => void;
}

export const MarketModal: React.FC<MarketModalProps> = ({
  isOpen,
  onClose,
  onSelectStock,
}) => {
  const [news, setNews] = useState<MarketNewsItem[]>(INITIAL_NEWS);
  const [filterCategory, setFilterCategory] = useState<string>('ALL');
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [lastRefreshedTime, setLastRefreshedTime] = useState<string>('Baru saja');

  if (!isOpen) return null;

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      // Tambahkan update berita terbaru dinamis
      const newUpdate: MarketNewsItem = {
        id: `n-${Date.now()}`,
        title: `UPDATE PASAR: Transaksi Harian IHSG Tembus Rp 12.8T, Sektor Keuangan & Tambang Memimpin Reli`,
        snippet: 'Aktivitas bursa terpantau semarak dengan volume beli agresif pada saham-saham perbankan buku IV dan komoditas energi terbarukan.',
        source: 'Bursa Efek Indonesia / RTI Live',
        sourceUrl: 'https://www.idx.co.id/id/berita/berita',
        category: 'IHSG & REGULASI',
        impact: 'BULLISH',
        impactStocks: ['BBCA', 'BMRI', 'ANTM', 'ASII'],
        impactReason: 'Likuiditas pasar yang melimpah mempertegas tren bullish IHSG untuk menembus resisten kunci 7.450.',
        timeAgo: '1 menit yang lalu',
        reactions: { love: 12, like: 20, down: 0, fire: 25 },
        userReaction: null,
      };

      setNews(prev => [newUpdate, ...prev.filter(item => item.id !== newUpdate.id)]);
      setIsRefreshing(false);
      setLastRefreshedTime(new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }));
    }, 600);
  };

  const handleReact = (id: string, reactionType: 'love' | 'like' | 'down' | 'fire') => {
    setNews(prev => prev.map(item => {
      if (item.id !== id) return item;

      const currentReaction = item.userReaction;
      const newReactions = { ...item.reactions };

      if (currentReaction === reactionType) {
        // batalkan reaksi
        newReactions[reactionType] = Math.max(0, newReactions[reactionType] - 1);
        return { ...item, reactions: newReactions, userReaction: null };
      } else {
        if (currentReaction) {
          newReactions[currentReaction] = Math.max(0, newReactions[currentReaction] - 1);
        }
        newReactions[reactionType] = (newReactions[reactionType] || 0) + 1;
        return { ...item, reactions: newReactions, userReaction: reactionType };
      }
    }));
  };

  const categories = ['ALL', 'KOMODITAS', 'GLOBAL', 'IHSG & REGULASI'];

  const filteredNews = filterCategory === 'ALL'
    ? news
    : news.filter(n => n.category === filterCategory);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      {/* Click outside backdrop to close */}
      <div className="absolute inset-0" onClick={onClose} />

      {/* Modal Dialog (Not full screen, sleek modal) */}
      <div 
        className="relative w-full max-w-4xl max-h-[88vh] bg-[#0c1016] border border-[#1e2736] rounded-2xl shadow-2xl flex flex-col overflow-hidden z-10"
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-5 py-4 bg-[#101620] border-b border-[#1c2432] flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#00b074] to-[#008253] text-white flex items-center justify-center shadow-md">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base sm:text-lg font-black text-white tracking-wide">
                  Market & Global Commodity Radar
                </h2>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#0d2a1d] text-[#00c076] border border-[#00c076]/40">
                  Live Feed
                </span>
              </div>
              <p className="text-xs text-[#8094ab]">
                Berita global, komoditas, dan sentimen penggerak saham Indonesia (IHSG).
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Reload Button */}
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#182230] hover:bg-[#233144] border border-[#27374d] text-xs font-semibold text-[#a3bad1] hover:text-white transition-all cursor-pointer ${
                isRefreshing ? 'opacity-70 pointer-events-none' : ''
              }`}
              title="Perbarui berita terkini"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-[#00c076] ${isRefreshing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-[#182230] hover:bg-[#28364a] text-[#8ea3ba] hover:text-white transition-colors cursor-pointer"
              title="Tutup (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Category Filter Pills & Refreshed Status */}
        <div className="px-5 py-2.5 bg-[#0e131b] border-b border-[#1a222e] flex items-center justify-between flex-wrap gap-2 flex-shrink-0">
          <div className="flex items-center space-x-1.5 overflow-x-auto no-scrollbar">
            <span className="text-[11px] font-semibold text-[#6d7e93] mr-1 flex items-center">
              <Filter className="w-3 h-3 mr-1" /> Filter:
            </span>
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setFilterCategory(cat)}
                className={`px-2.5 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                  filterCategory === cat
                    ? 'bg-[#00c076] text-black shadow-sm font-bold'
                    : 'bg-[#151c26] text-[#869ab0] hover:text-white hover:bg-[#1f2a3a] border border-[#222d3d]'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
          <span className="text-[10.5px] text-[#6a7d92] ml-auto">
            Terakhir diupdate: <strong className="text-[#a4b8cd]">{lastRefreshedTime}</strong>
          </span>
        </div>

        {/* News Feed Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4 bg-[#0a0d12]">
          {filteredNews.map((item) => (
            <article 
              key={item.id}
              className="bg-[#0f141d] border border-[#1b2534] hover:border-[#2b3a4f] rounded-xl p-4 transition-all space-y-3 shadow-md group"
            >
              {/* Category, Impact badge, and time */}
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#182332] text-[#8bb4df] border border-[#26374f]">
                    {item.category}
                  </span>
                  <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full flex items-center space-x-1 ${
                    item.impact === 'BULLISH'
                      ? 'bg-[#0d2a1d] text-[#00c076] border border-[#00c076]/40'
                      : item.impact === 'BEARISH'
                      ? 'bg-[#2b1619] text-[#ff5252] border border-[#ff5252]/40'
                      : 'bg-[#23272e] text-[#93a4b8]'
                  }`}>
                    {item.impact === 'BULLISH' && <TrendingUp className="w-3 h-3" />}
                    {item.impact === 'BEARISH' && <TrendingDown className="w-3 h-3" />}
                    <span>{item.impact} IMPACT</span>
                  </span>
                </div>
                <span className="text-[11px] text-[#697c91]">{item.timeAgo}</span>
              </div>

              {/* Title & Snippet */}
              <div>
                <h3 className="text-sm sm:text-base font-bold text-white group-hover:text-[#60a5fa] transition-colors leading-snug">
                  {item.title}
                </h3>
                <p className="text-xs text-[#9cb0c5] mt-1.5 leading-relaxed">
                  {item.snippet}
                </p>
              </div>

              {/* Impact to Indonesian Stocks */}
              <div className="p-2.5 rounded-lg bg-[#131a24] border border-[#1d2737] space-y-1.5">
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-3.5 h-3.5 text-[#eab308]" />
                  <span className="text-[11px] font-bold text-[#e1e7ec]">Saham RI Terdampak:</span>
                  <div className="flex items-center space-x-1 flex-wrap gap-1">
                    {item.impactStocks.map(stockCode => (
                      <button
                        key={stockCode}
                        onClick={() => {
                          onSelectStock?.(stockCode);
                          onClose();
                        }}
                        className="px-2 py-0.5 rounded bg-[#1a2536] hover:bg-[#00c076] text-white hover:text-black font-extrabold text-[10.5px] border border-[#2b3a4f] transition-all cursor-pointer"
                        title={`Buka chart & trade plan $${stockCode}`}
                      >
                        ${stockCode}
                      </button>
                    ))}
                  </div>
                </div>
                <p className="text-[11px] text-[#7d92a9] leading-tight pl-5">
                  {item.impactReason}
                </p>
              </div>

              {/* Footer: Small Source Link & Reaction Buttons */}
              <div className="pt-2 border-t border-[#1a2330] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                {/* Source attribution to prevent copyright */}
                <div className="flex items-center space-x-1.5 text-[10.5px] text-[#6a7c90] truncate max-w-sm">
                  <span>Sumber:</span>
                  <a
                    href={item.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[#60a5fa] hover:underline flex items-center space-x-1 truncate"
                    title="Buka sumber berita asli"
                  >
                    <span className="truncate">{item.source}</span>
                    <ExternalLink className="w-2.5 h-2.5 flex-shrink-0 ml-0.5 opacity-75" />
                  </a>
                </div>

                {/* Reaction Emoji Buttons */}
                <div className="flex items-center space-x-1.5 self-start sm:self-auto">
                  {/* Love */}
                  <button
                    onClick={() => handleReact(item.id, 'love')}
                    className={`flex items-center space-x-1 px-2 py-1 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
                      item.userReaction === 'love'
                        ? 'bg-[#3b1822] border-[#ff477e] text-[#ff477e]'
                        : 'bg-[#141b25] border-[#222d3e] text-[#8195ac] hover:text-white hover:border-[#33445c]'
                    }`}
                    title="Suka / Cinta info ini"
                  >
                    <Heart className={`w-3.5 h-3.5 ${item.userReaction === 'love' ? 'fill-current' : ''}`} />
                    <span>{item.reactions.love}</span>
                  </button>

                  {/* Like */}
                  <button
                    onClick={() => handleReact(item.id, 'like')}
                    className={`flex items-center space-x-1 px-2 py-1 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
                      item.userReaction === 'like'
                        ? 'bg-[#102a3a] border-[#38bdf8] text-[#38bdf8]'
                        : 'bg-[#141b25] border-[#222d3e] text-[#8195ac] hover:text-white hover:border-[#33445c]'
                    }`}
                    title="Setuju / Bullish"
                  >
                    <ThumbsUp className={`w-3.5 h-3.5 ${item.userReaction === 'like' ? 'fill-current' : ''}`} />
                    <span>{item.reactions.like}</span>
                  </button>

                  {/* Fire */}
                  <button
                    onClick={() => handleReact(item.id, 'fire')}
                    className={`flex items-center space-x-1 px-2 py-1 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
                      item.userReaction === 'fire'
                        ? 'bg-[#331e10] border-[#f97316] text-[#f97316]'
                        : 'bg-[#141b25] border-[#222d3e] text-[#8195ac] hover:text-white hover:border-[#33445c]'
                    }`}
                    title="Hot Topic / Berita Panas"
                  >
                    <Flame className={`w-3.5 h-3.5 ${item.userReaction === 'fire' ? 'fill-current' : ''}`} />
                    <span>{item.reactions.fire}</span>
                  </button>

                  {/* Down */}
                  <button
                    onClick={() => handleReact(item.id, 'down')}
                    className={`flex items-center space-x-1 px-2 py-1 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
                      item.userReaction === 'down'
                        ? 'bg-[#2b1719] border-[#ef4444] text-[#ef4444]'
                        : 'bg-[#141b25] border-[#222d3e] text-[#8195ac] hover:text-white hover:border-[#33445c]'
                    }`}
                    title="Kurang setuju / Bearish"
                  >
                    <ThumbsDown className={`w-3.5 h-3.5 ${item.userReaction === 'down' ? 'fill-current' : ''}`} />
                    <span>{item.reactions.down}</span>
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>

        {/* Modal Footer Tip */}
        <div className="px-5 py-3 bg-[#0d1219] border-t border-[#1a222e] flex items-center justify-between text-[11px] text-[#697d92] flex-shrink-0">
          <span>💡 Klik kode saham pada berita untuk langsung menganalisis teknikal & trade plan emiten tersebut.</span>
          <button
            onClick={onClose}
            className="text-xs font-bold text-[#00c076] hover:underline cursor-pointer"
          >
            Tutup Jendela
          </button>
        </div>
      </div>
    </div>
  );
};
