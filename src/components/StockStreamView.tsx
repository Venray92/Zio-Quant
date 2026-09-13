import React, { useState } from 'react';
import { Stock } from '../types';
import { 
  Radio, 
  Target, 
  TrendingUp, 
  TrendingDown, 
  CheckCircle2, 
  Clock, 
  BarChart2, 
  ThumbsUp, 
  Plus, 
  Sparkles,
  ExternalLink
} from 'lucide-react';

interface StockStreamViewProps {
  stock: Stock;
  onOpenGlobalStream?: () => void;
}

interface StockComment {
  id: string;
  author: string;
  avatar: string;
  badge?: string;
  sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  time: string;
  content: string;
  likes: number;
  userLiked?: boolean;
  prediction?: {
    targetPrice: number;
    initialPrice: number;
    direction: 'NAIK' | 'TURUN';
    changePercent: number;
    isAchieved: boolean;
    timeframe: string;
  };
  poll?: {
    question: string;
    options: { id: number; text: string; votes: number }[];
    totalVotes: number;
    userVotedId?: number | null;
  };
}

export const StockStreamView: React.FC<StockStreamViewProps> = ({ 
  stock,
  onOpenGlobalStream
}) => {
  const [commentInput, setCommentInput] = useState('');
  const [direction, setDirection] = useState<'NAIK' | 'TURUN'>('NAIK');
  const [targetPrice, setTargetPrice] = useState<string>('');
  const [isPredictionMode, setIsPredictionMode] = useState<boolean>(false);
  const [activeFilter, setActiveFilter] = useState<'ALL' | 'PREDICTION' | 'POLL'>('ALL');

  const [comments, setComments] = useState<StockComment[]>([
    {
      id: 'c-1',
      author: 'Reza TraderSantuy',
      avatar: 'RT',
      badge: 'Top Forecaster',
      sentiment: 'BULLISH',
      time: '15m lalu',
      content: `Setup Stochastic Golden Cross & Breakout neckline di $${stock.symbol}. Akumulasi di area support terdekat.`,
      likes: 29,
      prediction: {
        targetPrice: Math.round(stock.price * 1.08 / 5) * 5,
        initialPrice: stock.price,
        direction: 'NAIK',
        changePercent: 8.0,
        isAchieved: false,
        timeframe: 'Swing 2 Pekan'
      }
    },
    {
      id: 'c-2',
      author: 'Hendro InvestorMuda',
      avatar: 'HI',
      sentiment: 'BULLISH',
      time: '1h lalu',
      content: `Testimoni: Signal screener di $${stock.symbol} akurat banget. Udah floating cuan dan siap pasang stop loss disiplin sesuai Trade Plan.`,
      likes: 18,
    },
    {
      id: 'c-3',
      author: 'Komunitas Zio Polls',
      avatar: 'ZP',
      badge: 'Official',
      sentiment: 'NEUTRAL',
      time: '3h lalu',
      content: `Bagaimana ekspektasi Anda terhadap $${stock.symbol} menjelang penutupan sesi 2 hari ini?`,
      likes: 45,
      poll: {
        question: `Target $${stock.symbol} minggu ini:`,
        options: [
          { id: 1, text: '🚀 Breakout Resisten Kuat', votes: 52 },
          { id: 2, text: '⚖️ Konsolidasi Menguji Support', votes: 28 },
          { id: 3, text: '🔻 Koreksi Sehat', votes: 11 },
        ],
        totalVotes: 91,
        userVotedId: null,
      }
    }
  ]);

  const handlePost = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentInput.trim()) return;

    let pred = undefined;
    if (isPredictionMode && targetPrice) {
      const target = Number(targetPrice);
      const diff = Number((((target - stock.price) / stock.price) * 100).toFixed(1));
      pred = {
        targetPrice: target,
        initialPrice: stock.price,
        direction: direction,
        changePercent: Math.abs(diff),
        isAchieved: false,
        timeframe: 'Swing 1-2 Minggu'
      };
    }

    const newComment: StockComment = {
      id: Date.now().toString(),
      author: 'Anda (Trader Zio)',
      avatar: 'ME',
      sentiment: direction === 'NAIK' ? 'BULLISH' : 'BEARISH',
      time: 'Baru saja',
      content: commentInput,
      likes: 0,
      prediction: pred,
    };

    setComments([newComment, ...comments]);
    setCommentInput('');
    setTargetPrice('');
    setIsPredictionMode(false);
  };

  const handleVote = (commentId: string, optionId: number) => {
    setComments(prev => prev.map(c => {
      if (c.id !== commentId || !c.poll || c.poll.userVotedId) return c;
      const updated = c.poll.options.map(opt => opt.id === optionId ? { ...opt, votes: opt.votes + 1 } : opt);
      return {
        ...c,
        poll: {
          ...c.poll,
          options: updated,
          totalVotes: c.poll.totalVotes + 1,
          userVotedId: optionId,
        }
      };
    }));
  };

  const handleLike = (id: string) => {
    setComments(prev => prev.map(c => {
      if (c.id !== id) return c;
      return {
        ...c,
        likes: c.userLiked ? c.likes - 1 : c.likes + 1,
        userLiked: !c.userLiked,
      };
    }));
  };

  const filteredComments = comments.filter(c => {
    if (activeFilter === 'PREDICTION') return !!c.prediction;
    if (activeFilter === 'POLL') return !!c.poll;
    return true;
  });

  return (
    <div className="flex-1 h-full overflow-y-auto bg-[#0a0d12] text-[#e1e7ec] p-3 sm:p-5 select-text">
      <div className="max-w-4xl mx-auto space-y-4 pb-10">

        {/* TOP CONTEXT BAR */}
        <div className="bg-[#0f141c] border border-[#1d2634] rounded-xl p-3.5 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-lg bg-[#182230] border border-[#26354a] flex items-center justify-center font-black text-base text-[#38bdf8] tracking-wider">
              {stock.symbol.slice(0, 4)}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-lg font-extrabold text-white tracking-wide">${stock.symbol} Stream</h1>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-[#16212e] text-[#7ea2ca] border border-[#233347]">
                  Rp {stock.price.toLocaleString('id-ID')}
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#0d2a1d] text-[#00c076] border border-[#00c076]/40">
                  Live Komunitas
                </span>
              </div>
              <p className="text-xs text-[#8a9bb0]">Diskusi, tebak harga, dan opini khusus emiten {stock.name}</p>
            </div>
          </div>

          {onOpenGlobalStream && (
            <button
              onClick={onOpenGlobalStream}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#182332] hover:bg-[#25364d] border border-[#27384e] text-xs font-semibold text-[#a4bed9] hover:text-white transition-all cursor-pointer"
            >
              <Radio className="w-3.5 h-3.5 text-[#38bdf8]" />
              <span>Buka Stream Global</span>
              <ExternalLink className="w-3 h-3 opacity-70" />
            </button>
          )}
        </div>

        {/* POST CREATOR BOX */}
        <form onSubmit={handlePost} className="bg-[#0f141d] border border-[#1c2636] rounded-xl p-4 space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white flex items-center space-x-1.5">
              <Sparkles className="w-4 h-4 text-[#00c076]" />
              <span>Posting Analisa / Tebakan Harga ${stock.symbol}</span>
            </span>

            <button
              type="button"
              onClick={() => setIsPredictionMode(!isPredictionMode)}
              className={`text-[11px] font-bold px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
                isPredictionMode
                  ? 'bg-[#132838] border-[#38bdf8] text-[#38bdf8]'
                  : 'bg-[#151c27] border-[#222d3d] text-[#869ab0] hover:text-white'
              }`}
            >
              🎯 {isPredictionMode ? 'Mode Tebak Harga Aktif' : '+ Pasang Tebak Harga'}
            </button>
          </div>

          <textarea
            rows={2}
            value={commentInput}
            onChange={(e) => setCommentInput(e.target.value)}
            placeholder={`Bagikan pandangan teknikal, katalis, atau target harga untuk $${stock.symbol}...`}
            className="w-full p-2.5 rounded-lg bg-[#141b25] border border-[#233144] text-xs text-white placeholder-[#5e7186] focus:outline-none focus:border-[#00c076]"
            required
          />

          {/* Prediction inputs if enabled */}
          {isPredictionMode && (
            <div className="p-3 rounded-lg bg-[#121924] border border-[#1f2c3d] grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div>
                <label className="block text-[11px] text-[#7d92a9] mb-1">Arah Tebakan:</label>
                <div className="grid grid-cols-2 gap-1">
                  <button
                    type="button"
                    onClick={() => setDirection('NAIK')}
                    className={`py-1 rounded font-bold border transition-colors ${
                      direction === 'NAIK'
                        ? 'bg-[#0d2e20] text-[#00c076] border-[#00c076]'
                        : 'bg-[#182230] text-[#7e92a8] border-[#25364c]'
                    }`}
                  >
                    🚀 Naik
                  </button>
                  <button
                    type="button"
                    onClick={() => setDirection('TURUN')}
                    className={`py-1 rounded font-bold border transition-colors ${
                      direction === 'TURUN'
                        ? 'bg-[#2e1418] text-[#ff4d4f] border-[#ff4d4f]'
                        : 'bg-[#182230] text-[#7e92a8] border-[#25364c]'
                    }`}
                  >
                    🔻 Turun
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-[11px] text-[#7d92a9] mb-1">Harga Target Tebakan (Rp):</label>
                <input
                  type="number"
                  value={targetPrice}
                  onChange={(e) => setTargetPrice(e.target.value)}
                  placeholder={`Contoh: ${Math.round(stock.price * 1.08 / 5) * 5}`}
                  className="w-full px-2.5 py-1 rounded bg-[#182230] border border-[#25364c] text-xs text-white font-bold focus:outline-none focus:border-[#00c076]"
                />
              </div>
            </div>
          )}

          <div className="flex items-center justify-between pt-1">
            <span className="text-[11px] text-[#6d7f94]">
              Harga saat ini: <strong>Rp {stock.price.toLocaleString('id-ID')}</strong>
            </span>
            <button
              type="submit"
              className="px-4 py-1.5 rounded-lg bg-[#00c076] hover:bg-[#00db87] active:scale-95 text-black font-extrabold text-xs shadow-md transition-all cursor-pointer"
            >
              Kirim ke Stream ${stock.symbol}
            </button>
          </div>
        </form>

        {/* FILTER BAR */}
        <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
          <div className="flex items-center space-x-1.5">
            {[
              { id: 'ALL', label: 'Semua Diskusi' },
              { id: 'PREDICTION', label: '🎯 Tebak Harga' },
              { id: 'POLL', label: '📊 Polling' },
            ].map(f => (
              <button
                key={f.id}
                onClick={() => setActiveFilter(f.id as any)}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                  activeFilter === f.id
                    ? 'bg-[#1e293b] text-white border border-[#3b82f6]'
                    : 'bg-[#121822] text-[#869ab0] hover:text-white border border-[#1f2a3a]'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <span className="text-[11px] text-[#697c91]">
            {filteredComments.length} Kiriman
          </span>
        </div>

        {/* STREAM FEED ITEMS */}
        <div className="space-y-3">
          {filteredComments.map(item => (
            <div key={item.id} className="bg-[#0f141d] border border-[#1b2534] rounded-xl p-4 space-y-2.5 shadow-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#1e293b] text-white font-bold text-xs flex items-center justify-center border border-[#33445c]">
                    {item.avatar}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-extrabold text-white">{item.author}</span>
                      {item.badge && (
                        <span className="text-[9.5px] font-semibold px-1.5 py-0.5 rounded bg-[#1e2a3b] text-[#93c5fd]">
                          {item.badge}
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-[#6b7d91]">{item.time}</span>
                  </div>
                </div>

                <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full ${
                  item.sentiment === 'BULLISH' ? 'bg-[#0d2a1d] text-[#00c076]' :
                  item.sentiment === 'BEARISH' ? 'bg-[#2b1619] text-[#ff4d4f]' :
                  'bg-[#1e2530] text-[#8ea0b3]'
                }`}>
                  {item.sentiment}
                </span>
              </div>

              <p className="text-xs text-[#cbd6e2] leading-relaxed">
                {item.content}
              </p>

              {/* Prediction Display */}
              {item.prediction && (
                <div className="bg-[#121822] border border-[#202d3e] rounded-xl p-3 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[#8fa7c3] flex items-center space-x-1.5">
                      <Target className="w-3.5 h-3.5 text-[#38bdf8]" />
                      <span>Prediksi Tebakan Harga</span>
                    </span>
                    {item.prediction.isAchieved ? (
                      <span className="text-[11px] font-bold text-[#00c076] bg-[#0d2a1d] px-2 py-0.5 rounded-full">
                        ✓ Target Tercapai
                      </span>
                    ) : (
                      <span className="text-[10.5px] text-[#60a5fa] bg-[#16273c] px-2 py-0.5 rounded-full">
                        Proses Swing
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="bg-[#0b0e14] p-2 rounded-lg border border-[#1b2534]">
                      <span className="text-[10px] text-[#6b7d91] block">Arah</span>
                      <span className="font-bold text-[#00c076]">{item.prediction.direction}</span>
                    </div>
                    <div className="bg-[#0b0e14] p-2 rounded-lg border border-[#1b2534]">
                      <span className="text-[10px] text-[#6b7d91] block">Harga Target</span>
                      <span className="font-black text-white">Rp {item.prediction.targetPrice.toLocaleString('id-ID')}</span>
                    </div>
                    <div className="bg-[#0b0e14] p-2 rounded-lg border border-[#1b2534]">
                      <span className="text-[10px] text-[#6b7d91] block">Persentase</span>
                      <span className="font-mono font-bold text-[#00c076]">+{item.prediction.changePercent}%</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Poll Display */}
              {item.poll && (
                <div className="bg-[#121822] border border-[#202d3e] rounded-xl p-3 space-y-2">
                  <div className="flex items-center justify-between text-xs font-bold text-white">
                    <div className="flex items-center space-x-1.5">
                      <BarChart2 className="w-3.5 h-3.5 text-[#eab308]" />
                      <span>{item.poll.question}</span>
                    </div>
                    <span className="text-[10.5px] text-[#71859b]">{item.poll.totalVotes} Suara</span>
                  </div>
                  <div className="space-y-1.5">
                    {item.poll.options.map(opt => {
                      const pct = item.poll?.totalVotes ? Math.round((opt.votes / item.poll.totalVotes) * 100) : 0;
                      const isVoted = item.poll?.userVotedId === opt.id;
                      return (
                        <button
                          key={opt.id}
                          onClick={() => handleVote(item.id, opt.id)}
                          className={`w-full text-left p-2 rounded-lg border relative overflow-hidden text-xs transition-all ${
                            isVoted ? 'border-[#00c076] bg-[#0d291d]/40' : 'border-[#222d3e] bg-[#0c1017]'
                          }`}
                        >
                          <div className="absolute top-0 bottom-0 left-0 bg-[#3b82f6]/20 transition-all" style={{ width: `${pct}%` }} />
                          <div className="relative flex justify-between z-10">
                            <span className={isVoted ? 'text-[#00c076] font-bold' : 'text-white'}>{opt.text} {isVoted && '✓'}</span>
                            <span className="font-mono text-[#869ab0]">{pct}% ({opt.votes})</span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="pt-2 border-t border-[#17212e] flex items-center justify-between text-xs text-[#7e92a8]">
                <button
                  onClick={() => handleLike(item.id)}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
                    item.userLiked ? 'bg-[#102a3a] border-[#38bdf8] text-[#38bdf8]' : 'bg-[#121822] border-[#1d2737] text-[#869cb3] hover:text-white'
                  }`}
                >
                  <ThumbsUp className={`w-3.5 h-3.5 ${item.userLiked ? 'fill-current' : ''}`} />
                  <span>{item.likes} Suka</span>
                </button>
                <span className="text-[11px] text-[#607489]">Emiten ${stock.symbol} Komunitas</span>
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
};
