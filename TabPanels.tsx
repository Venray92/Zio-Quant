import React, { useState } from 'react';
import { MainTab, Stock } from '../types';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  BarChart2, 
  Users, 
  FileText, 
  Calendar, 
  Share2, 
  MessageCircle,
  ThumbsUp,
  Award
} from 'lucide-react';

interface TabPanelsProps {
  activeTab: MainTab;
  stock: Stock;
}

export const TabPanels: React.FC<TabPanelsProps> = ({ activeTab, stock }) => {
  const [commentInput, setCommentInput] = useState('');
  const [comments, setComments] = useState([
    {
      id: '1',
      author: 'BudiInvestor',
      avatar: 'B',
      time: '15m lalu',
      sentiment: 'BULLISH',
      content: `$${stock.symbol} sideways akumulasi rapi di support area. Volume mulai naik, target breakout terdekat ke resistance minor.`,
      likes: 24,
    },
    {
      id: '2',
      author: 'TraderSantai99',
      avatar: 'T',
      time: '1h lalu',
      sentiment: 'NEUTRAL',
      content: `Waspada volatilitas pasar menjelang rilis data inflasi dan suku bunga BI. Tetap pasang trailing stop ketat di $${stock.symbol}.`,
      likes: 12,
    },
    {
      id: '3',
      author: 'SwingTraderPro',
      avatar: 'S',
      time: '3h lalu',
      sentiment: 'BULLISH',
      content: `Foreign flow mulai mencatatkan net buy tipis hari ini. Indikator MACD golden cross di timeframe 4H.`,
      likes: 41,
    }
  ]);

  const handlePostComment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentInput.trim()) return;
    setComments([
      {
        id: Date.now().toString(),
        author: 'Swing Porto (You)',
        avatar: 'V',
        time: 'Baru saja',
        sentiment: 'BULLISH',
        content: commentInput,
        likes: 0
      },
      ...comments
    ]);
    setCommentInput('');
  };

  switch (activeTab) {
    case 'Keystats':
      return (
        <div className="p-4 overflow-y-auto h-full bg-[#11161d] text-[#e1e7ec]">
          <div className="max-w-5xl mx-auto space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#212a36]">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  Key Statistics <span className="text-[#00c076]">{stock.symbol}</span>
                </h2>
                <p className="text-xs text-[#8292a4]">Ringkasan rasio valuasi, profitabilitas, dan neraca keuangan</p>
              </div>
              <div className="text-right">
                <span className="text-xs text-[#8292a4]">Market Cap:</span>
                <span className="ml-1 text-sm font-bold text-white">{stock.marketCap || '124.5B'} IDR</span>
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-[#171d26] p-3 rounded border border-[#232c39]">
                <span className="text-[11px] text-[#8b98a5]">Price / Earnings (P/E)</span>
                <p className="text-lg font-bold text-white mt-1">{stock.peRatio ? `${stock.peRatio}x` : '18.4x'}</p>
                <span className="text-[10px] text-[#00c076]">Industri: 21.2x</span>
              </div>
              <div className="bg-[#171d26] p-3 rounded border border-[#232c39]">
                <span className="text-[11px] text-[#8b98a5]">Price / Book Value (PBV)</span>
                <p className="text-lg font-bold text-white mt-1">{stock.pbvRatio ? `${stock.pbvRatio}x` : '1.12x'}</p>
                <span className="text-[10px] text-[#00c076]">Industri: 1.8x</span>
              </div>
              <div className="bg-[#171d26] p-3 rounded border border-[#232c39]">
                <span className="text-[11px] text-[#8b98a5]">Return on Equity (ROE)</span>
                <p className="text-lg font-bold text-[#00c076] mt-1">{stock.roe ? `${stock.roe}%` : '6.8%'}</p>
                <span className="text-[10px] text-[#8b98a5]">TTM Basis</span>
              </div>
              <div className="bg-[#171d26] p-3 rounded border border-[#232c39]">
                <span className="text-[11px] text-[#8b98a5]">Dividend Yield</span>
                <p className="text-lg font-bold text-[#f59e0b] mt-1">{stock.dividendYield ? `${stock.dividendYield}%` : '1.5%'}</p>
                <span className="text-[10px] text-[#8b98a5]">Terakhir Dividen 2024</span>
              </div>
            </div>

            {/* Detailed Table */}
            <div className="bg-[#171d26] rounded border border-[#232c39] p-4">
              <h3 className="text-sm font-semibold text-white mb-3">Valuasi & Harga Saham</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2 text-xs">
                <div className="flex justify-between py-1.5 border-b border-[#212b38]">
                  <span className="text-[#8b98a5]">Current Price</span>
                  <span className="font-semibold text-white">Rp {stock.price.toLocaleString('id-ID')}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-[#212b38]">
                  <span className="text-[#8b98a5]">52 Week High / Low</span>
                  <span className="font-semibold text-white">Rp {stock.low} - Rp {stock.high * 1.4}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-[#212b38]">
                  <span className="text-[#8b98a5]">Volume Transaksi Harian</span>
                  <span className="font-semibold text-white">{stock.volume}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-[#212b38]">
                  <span className="text-[#8b98a5]">Frekuensi Harian</span>
                  <span className="font-semibold text-white">{stock.frequency || '1,420x'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-[#212b38]">
                  <span className="text-[#8b98a5]">Free Float Ratio</span>
                  <span className="font-semibold text-white">28.4%</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-[#212b38]">
                  <span className="text-[#8b98a5]">Debt to Equity Ratio (DER)</span>
                  <span className="font-semibold text-white">0.68x</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      );

    case 'Analysis':
      return (
        <div className="p-4 overflow-y-auto h-full bg-[#11161d] text-[#e1e7ec]">
          <div className="max-w-5xl mx-auto space-y-4">
            <h2 className="text-lg font-bold text-white">
              Teknikal & Broker Flow Analysis <span className="text-[#00c076]">{stock.symbol}</span>
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="bg-[#171d26] p-3.5 rounded border border-[#232c39]">
                <span className="text-xs text-[#8b98a5]">Signal Indikator (RSI 14)</span>
                <p className="text-xl font-bold text-[#00c076] mt-1">Bullish Divergence</p>
                <p className="text-xs text-[#8292a4] mt-1">RSI level 44.8 - keluar dari zona oversold</p>
              </div>
              <div className="bg-[#171d26] p-3.5 rounded border border-[#232c39]">
                <span className="text-xs text-[#8b98a5]">Bandar Movement (Broker Summary)</span>
                <p className="text-xl font-bold text-[#00c076] mt-1">Normal Akumulasi</p>
                <p className="text-xs text-[#8292a4] mt-1">Top Buyer: YP, CC, XC (Net Rp 480 jt)</p>
              </div>
              <div className="bg-[#171d26] p-3.5 rounded border border-[#232c39]">
                <span className="text-xs text-[#8b98a5]">Support & Resistance (Pivot)</span>
                <p className="text-sm font-semibold text-white mt-1">S1: 125 | R1: 138</p>
                <p className="text-xs text-[#8292a4] mt-1">S2: 120 | R2: 145</p>
              </div>
            </div>

            {/* Broker Summary Table */}
            <div className="bg-[#171d26] rounded border border-[#232c39] p-4">
              <h3 className="text-sm font-semibold text-white mb-3">Broker Summary (Top 5 Buyer vs Seller)</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-xs font-bold text-[#00c076] pb-1 border-b border-[#212b38]">TOP BUYER</h4>
                  <div className="divide-y divide-[#212b38] text-xs">
                    <div className="flex justify-between py-1.5"><span className="font-semibold">YP (Mirae)</span><span>3,410 Lot @ 129</span></div>
                    <div className="flex justify-between py-1.5"><span className="font-semibold">CC (Mandiri)</span><span>2,180 Lot @ 130</span></div>
                    <div className="flex justify-between py-1.5"><span className="font-semibold">XC (Ajaib)</span><span>1,420 Lot @ 131</span></div>
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#eb5757] pb-1 border-b border-[#212b38]">TOP SELLER</h4>
                  <div className="divide-y divide-[#212b38] text-xs">
                    <div className="flex justify-between py-1.5"><span className="font-semibold">PD (Indo Premier)</span><span>2,890 Lot @ 131</span></div>
                    <div className="flex justify-between py-1.5"><span className="font-semibold">XL (Stockbit)</span><span>1,650 Lot @ 132</span></div>
                    <div className="flex justify-between py-1.5"><span className="font-semibold">DR (Rhb)</span><span>980 Lot @ 130</span></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      );

    case 'Financials':
      return (
        <div className="p-4 overflow-y-auto h-full bg-[#11161d] text-[#e1e7ec]">
          <div className="max-w-5xl mx-auto space-y-4">
            <h2 className="text-lg font-bold text-white">Laporan Keuangan (Financial Statements) - {stock.symbol}</h2>
            <div className="bg-[#171d26] rounded border border-[#232c39] p-4">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-[#242e3d] text-[#8b98a5]">
                      <th className="py-2">Item (dalam Miliar IDR)</th>
                      <th className="py-2 text-right">Q1 2024</th>
                      <th className="py-2 text-right">Q2 2024</th>
                      <th className="py-2 text-right">Q3 2024</th>
                      <th className="py-2 text-right">Q4 2024</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#212b38]">
                    <tr><td className="py-2 font-medium">Pendapatan Bersih (Revenue)</td><td className="text-right">54.2 B</td><td className="text-right">58.8 B</td><td className="text-right">62.1 B</td><td className="text-right text-[#00c076]">68.5 B</td></tr>
                    <tr><td className="py-2 font-medium">Laba Kotor (Gross Profit)</td><td className="text-right">16.4 B</td><td className="text-right">18.2 B</td><td className="text-right">19.5 B</td><td className="text-right">21.8 B</td></tr>
                    <tr><td className="py-2 font-medium">Laba Bersih (Net Income)</td><td className="text-right">4.1 B</td><td className="text-right">4.8 B</td><td className="text-right">5.3 B</td><td className="text-right text-[#00c076]">6.9 B</td></tr>
                    <tr><td className="py-2 font-medium">Total Aset</td><td className="text-right">210.4 B</td><td className="text-right">215.1 B</td><td className="text-right">220.0 B</td><td className="text-right">228.4 B</td></tr>
                    <tr><td className="py-2 font-medium">Total Liabilitas</td><td className="text-right">85.2 B</td><td className="text-right">86.0 B</td><td className="text-right">87.5 B</td><td className="text-right">88.1 B</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      );

    case 'Seasonality':
      return (
        <div className="p-4 overflow-y-auto h-full bg-[#11161d] text-[#e1e7ec]">
          <div className="max-w-5xl mx-auto space-y-4">
            <h2 className="text-lg font-bold text-white">Seasonality Historical Performance ({stock.symbol})</h2>
            <p className="text-xs text-[#8292a4]">Rata-rata kenaikan dan probabilitas return bulanan selama 5 tahun terakhir.</p>
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2 text-center text-xs">
              {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((month, idx) => {
                const positive = idx % 2 === 0;
                return (
                  <div key={month} className={`p-3 rounded border ${positive ? 'bg-[#0b2b20] border-[#009b66]/50 text-[#00c076]' : 'bg-[#2a171b] border-[#ef4444]/40 text-[#f87171]'}`}>
                    <div className="font-bold text-white mb-1">{month}</div>
                    <div className="text-sm font-semibold">{positive ? `+${(idx + 1) * 1.8}%` : `-${(idx + 1) * 0.9}%`}</div>
                    <div className="text-[10px] opacity-75 mt-1">Win: {positive ? '60%' : '40%'}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      );

    case 'Profile':
      return (
        <div className="p-4 overflow-y-auto h-full bg-[#11161d] text-[#e1e7ec]">
          <div className="max-w-5xl mx-auto space-y-4">
            <div className="bg-[#171d26] p-4 rounded border border-[#232c39]">
              <h2 className="text-lg font-bold text-white mb-2">{stock.symbol} - {stock.name}</h2>
              <div className="flex flex-wrap gap-2 mb-3">
                <span className="bg-[#0b2b20] text-[#00c076] text-xs px-2.5 py-0.5 rounded border border-[#009b66]/60 font-semibold">{stock.sector}</span>
                <span className="bg-[#1e2735] text-white text-xs px-2.5 py-0.5 rounded border border-[#303e54] font-medium">{stock.board}</span>
              </div>
              <p className="text-xs text-[#a0aec0] leading-relaxed">
                {stock.symbol} ({stock.name}) adalah perusahaan publik yang tercatat di Bursa Efek Indonesia (BEI). 
                Fokus operasi pada pengolahan makanan dan minuman bernilai tambah, distribusi ritel, serta jaringan suplai industri terintegrasi.
              </p>
            </div>
          </div>
        </div>
      );

    case 'Stream':
    default:
      return (
        <div className="p-4 overflow-y-auto h-full bg-[#11161d] text-[#e1e7ec]">
          <div className="max-w-3xl mx-auto space-y-4">
            {/* Post input box */}
            <form onSubmit={handlePostComment} className="bg-[#171d26] p-3 rounded-lg border border-[#232c39]">
              <textarea
                value={commentInput}
                onChange={(e) => setCommentInput(e.target.value)}
                placeholder={`Tulis opini, analisa teknikal, atau ide trading tentang $${stock.symbol}...`}
                className="w-full bg-[#0f1318] border border-[#2a3646] rounded p-2.5 text-xs text-white placeholder-[#627182] focus:outline-none focus:border-[#00c076] min-h-[60px]"
              />
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-[#232c39]">
                <span className="text-[11px] text-[#8292a4]">Kategori: Diskusi Saham Komunitas</span>
                <button
                  type="submit"
                  className="bg-[#00c076] hover:bg-[#00db87] text-black font-bold text-xs px-4 py-1.5 rounded transition-colors"
                >
                  Post ke Stream
                </button>
              </div>
            </form>

            {/* Stream comments list */}
            <div className="space-y-3">
              {comments.map((item) => (
                <div key={item.id} className="bg-[#171d26] p-3.5 rounded-lg border border-[#232c39] space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-7 h-7 rounded-full bg-[#2a3648] text-white flex items-center justify-center text-xs font-bold">
                        {item.avatar}
                      </div>
                      <div>
                        <span className="font-semibold text-xs text-white">{item.author}</span>
                        <span className="text-[10px] text-[#6b7c91] ml-2">{item.time}</span>
                      </div>
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${item.sentiment === 'BULLISH' ? 'bg-[#0d3324] text-[#00c076]' : 'bg-[#2a3648] text-[#9bb0c7]'}`}>
                      {item.sentiment}
                    </span>
                  </div>
                  <p className="text-xs text-[#cbd5e1] leading-relaxed">{item.content}</p>
                  <div className="flex items-center space-x-4 text-xs text-[#8292a4] pt-1">
                    <button className="flex items-center space-x-1 hover:text-[#00c076] transition-colors">
                      <ThumbsUp className="w-3.5 h-3.5" />
                      <span>{item.likes}</span>
                    </button>
                    <button className="flex items-center space-x-1 hover:text-white transition-colors">
                      <MessageCircle className="w-3.5 h-3.5" />
                      <span>Balas</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
  }
};
