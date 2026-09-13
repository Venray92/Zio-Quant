import React, { useState } from 'react';
import { 
  Radio, 
  MessageSquare, 
  TrendingUp, 
  TrendingDown, 
  CheckCircle2, 
  Sparkles, 
  BarChart2, 
  ThumbsUp, 
  Award, 
  Share2, 
  X, 
  Plus, 
  Target, 
  Clock, 
  Flame,
  Check
} from 'lucide-react';
import { Stock } from '../types';

export interface PricePrediction {
  id: string;
  author: string;
  authorBadge?: string;
  stockSymbol: string;
  targetPrice: number;
  initialPrice: number;
  direction: 'NAIK' | 'TURUN';
  changePercentTarget: number;
  timeframe: string;
  reason: string;
  isAchieved: boolean;
  achievedAt?: string;
  likes: number;
  userLiked?: boolean;
  createdAt: string;
}

export interface CommunityPoll {
  id: string;
  question: string;
  stockSymbol: string;
  options: { id: number; text: string; votes: number }[];
  totalVotes: number;
  userVotedOptionId?: number | null;
}

export interface CommunityPost {
  id: string;
  type: 'PREDICTION' | 'POLL' | 'TESTIMONI' | 'CHAT';
  author: string;
  avatar: string;
  authorBadge?: string;
  stockSymbol: string;
  content: string;
  sentiment?: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  time: string;
  likes: number;
  userLiked?: boolean;
  prediction?: PricePrediction;
  poll?: CommunityPoll;
}

const INITIAL_POSTS: CommunityPost[] = [
  {
    id: 'p-1',
    type: 'PREDICTION',
    author: 'Reza TraderSantuy',
    avatar: 'RT',
    authorBadge: 'Top Forecaster',
    stockSymbol: 'ANTM',
    sentiment: 'BULLISH',
    content: 'Setup Stochastic Golden Cross & Breakout neckline double bottom di timeframe Daily. Komoditas nikel lagi hot!',
    time: '20 menit yang lalu',
    likes: 42,
    prediction: {
      id: 'pred-1',
      author: 'Reza TraderSantuy',
      stockSymbol: 'ANTM',
      targetPrice: 1720,
      initialPrice: 1540,
      direction: 'NAIK',
      changePercentTarget: 11.6,
      timeframe: 'Swing 2-4 Minggu',
      reason: 'Volume spike signifikan di area support 1.500',
      isAchieved: true,
      achievedAt: 'Kemarin (Tercapai di 1.725! 🎉)',
      likes: 42,
      createdAt: '3 hari lalu',
    },
  },
  {
    id: 'p-2',
    type: 'PREDICTION',
    author: 'Diana CuanMax',
    avatar: 'DC',
    authorBadge: 'Swing Pro',
    stockSymbol: 'BBCA',
    sentiment: 'BULLISH',
    content: 'Tebakan harga BBCA menjelang rilis laporan keuangan Q3 dan dividen interim!',
    time: '1 jam yang lalu',
    likes: 28,
    prediction: {
      id: 'pred-2',
      author: 'Diana CuanMax',
      stockSymbol: 'BBCA',
      targetPrice: 10800,
      initialPrice: 10250,
      direction: 'NAIK',
      changePercentTarget: 5.3,
      timeframe: 'Swing Akhir Bulan',
      reason: 'Foreign flow terus konsisten akumulasi di atas MA50',
      isAchieved: false,
      likes: 28,
      createdAt: '1 jam lalu',
    },
  },
  {
    id: 'p-3',
    type: 'POLL',
    author: 'Admin Zio Community',
    avatar: 'ZC',
    authorBadge: 'Official',
    stockSymbol: 'ADRO',
    sentiment: 'NEUTRAL',
    content: 'Polling mingguan: Bagaimana pandangan kalian terhadap saham ADRO pasca rencana spin-off dan pelemahan harga batubara dunia?',
    time: '2 jam yang lalu',
    likes: 64,
    poll: {
      id: 'poll-1',
      question: 'Arah gerak ADRO dalam 2 pekan ke depan?',
      stockSymbol: 'ADRO',
      options: [
        { id: 1, text: '🚀 Rebound kuat ke area 3.800+ (Undervalued)', votes: 84 },
        { id: 2, text: '⚖️ Konsolidasi sideway di 3.400 - 3.650', votes: 46 },
        { id: 3, text: '🔻 Koreksi uji support 3.200 (Wait & See)', votes: 23 },
      ],
      totalVotes: 153,
      userVotedOptionId: null,
    },
  },
  {
    id: 'p-4',
    type: 'TESTIMONI',
    author: 'Hendro InvestorMuda',
    avatar: 'HI',
    stockSymbol: 'ASII',
    sentiment: 'BULLISH',
    content: 'Testimoni: Screener Stochastic + Psar di Zio beneran ngebantu nemu bottoming ASII di 4.800 kemarin. Hari ini udah floating cuan +7.5% dan pasang trailing stop sesuai Trade Plan!',
    time: '3 jam yang lalu',
    likes: 39,
  },
  {
    id: 'p-5',
    type: 'CHAT',
    author: 'KevinScalper',
    avatar: 'KS',
    stockSymbol: 'GOTO',
    sentiment: 'NEUTRAL',
    content: 'Ada yang mantau antrian bid-offer GOTO di 65? Kayaknya ada ganjalan tebal di area support psikologis.',
    time: '4 jam yang lalu',
    likes: 15,
  }
];

interface StreamModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeStock?: Stock;
  onSelectStock?: (symbol: string) => void;
}

export const StreamModal: React.FC<StreamModalProps> = ({
  isOpen,
  onClose,
  activeStock,
  onSelectStock,
}) => {
  const [posts, setPosts] = useState<CommunityPost[]>(INITIAL_POSTS);
  const [activeTabFilter, setActiveTabFilter] = useState<'ALL' | 'PREDICTION' | 'POLL' | 'TESTIMONI' | 'THIS_STOCK'>('ALL');
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  
  // State form pembuatan
  const [createType, setCreateType] = useState<'PREDICTION' | 'POLL' | 'TESTIMONI' | 'CHAT'>('PREDICTION');
  const [selectedStockInput, setSelectedStockInput] = useState<string>(activeStock?.symbol || 'BBCA');
  const [contentText, setContentText] = useState<string>('');
  const [targetPriceInput, setTargetPriceInput] = useState<string>('');
  const [directionInput, setDirectionInput] = useState<'NAIK' | 'TURUN'>('NAIK');
  const [timeframeInput, setTimeframeInput] = useState<string>('Swing 1-2 Minggu');
  const [pollOptionsInput, setPollOptionsInput] = useState<string[]>(['Bakal Naik Kuat', 'Sideway Dulu', 'Koreksi']);

  if (!isOpen) return null;

  const currentStockSymbol = activeStock?.symbol || 'BBCA';
  const currentStockPrice = activeStock?.price || 10000;

  const handleVotePoll = (postId: string, optionId: number) => {
    setPosts(prev => prev.map(p => {
      if (p.id !== postId || !p.poll) return p;
      if (p.poll.userVotedOptionId) return p; // sudah vote

      const updatedOptions = p.poll.options.map(opt => {
        if (opt.id === optionId) {
          return { ...opt, votes: opt.votes + 1 };
        }
        return opt;
      });

      return {
        ...p,
        poll: {
          ...p.poll,
          options: updatedOptions,
          totalVotes: p.poll.totalVotes + 1,
          userVotedOptionId: optionId,
        }
      };
    }));
  };

  const handleLikePost = (postId: string) => {
    setPosts(prev => prev.map(p => {
      if (p.id !== postId) return p;
      const isLiked = p.userLiked;
      return {
        ...p,
        likes: isLiked ? p.likes - 1 : p.likes + 1,
        userLiked: !isLiked,
      };
    }));
  };

  const handleCreatePost = (e: React.FormEvent) => {
    e.preventDefault();
    if (!contentText.trim()) return;

    const symbol = selectedStockInput.toUpperCase().trim() || 'BBCA';

    let newPost: CommunityPost;

    if (createType === 'PREDICTION') {
      const target = Number(targetPriceInput) || (currentStockPrice * 1.08);
      const estInit = currentStockPrice;
      const diffPct = Number((((target - estInit) / estInit) * 100).toFixed(1));

      newPost = {
        id: `post-${Date.now()}`,
        type: 'PREDICTION',
        author: 'Anda (Trader Zio)',
        avatar: 'ME',
        stockSymbol: symbol,
        sentiment: directionInput === 'NAIK' ? 'BULLISH' : 'BEARISH',
        content: contentText,
        time: 'Baru saja',
        likes: 0,
        prediction: {
          id: `pred-${Date.now()}`,
          author: 'Anda (Trader Zio)',
          stockSymbol: symbol,
          targetPrice: target,
          initialPrice: estInit,
          direction: directionInput,
          changePercentTarget: Math.abs(diffPct),
          timeframe: timeframeInput,
          reason: contentText,
          isAchieved: false,
          likes: 0,
          createdAt: 'Baru saja',
        }
      };
    } else if (createType === 'POLL') {
      newPost = {
        id: `post-${Date.now()}`,
        type: 'POLL',
        author: 'Anda (Trader Zio)',
        avatar: 'ME',
        stockSymbol: symbol,
        sentiment: 'NEUTRAL',
        content: contentText,
        time: 'Baru saja',
        likes: 0,
        poll: {
          id: `poll-${Date.now()}`,
          question: contentText,
          stockSymbol: symbol,
          options: pollOptionsInput.filter(Boolean).map((opt, idx) => ({
            id: idx + 1,
            text: opt,
            votes: 0,
          })),
          totalVotes: 0,
          userVotedOptionId: null,
        }
      };
    } else {
      newPost = {
        id: `post-${Date.now()}`,
        type: createType,
        author: 'Anda (Trader Zio)',
        avatar: 'ME',
        stockSymbol: symbol,
        sentiment: createType === 'TESTIMONI' ? 'BULLISH' : 'NEUTRAL',
        content: contentText,
        time: 'Baru saja',
        likes: 0,
      };
    }

    setPosts(prev => [newPost, ...prev]);
    setShowCreateModal(false);
    setContentText('');
    setTargetPriceInput('');
  };

  const filteredPosts = posts.filter(p => {
    if (activeTabFilter === 'PREDICTION') return p.type === 'PREDICTION';
    if (activeTabFilter === 'POLL') return p.type === 'POLL';
    if (activeTabFilter === 'TESTIMONI') return p.type === 'TESTIMONI';
    if (activeTabFilter === 'THIS_STOCK') return p.stockSymbol === currentStockSymbol;
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="absolute inset-0" onClick={onClose} />

      {/* Modal Dialog (Not full screen) */}
      <div 
        className="relative w-full max-w-4xl max-h-[88vh] bg-[#0c1016] border border-[#1e2736] rounded-2xl shadow-2xl flex flex-col overflow-hidden z-10"
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-5 py-4 bg-[#101620] border-b border-[#1c2432] flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#3b82f6] to-[#1d4ed8] text-white flex items-center justify-center shadow-md">
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base sm:text-lg font-black text-white tracking-wide">
                  Zio Community Stream
                </h2>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#16273c] text-[#60a5fa] border border-[#3b82f6]/40">
                  Tebak Harga & Polling
                </span>
              </div>
              <p className="text-xs text-[#8094ab]">
                Prediksi harga saham, polling sentimen komunitas, dan diskusi trading room.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#00c076] hover:bg-[#00db87] active:scale-95 text-black font-extrabold text-xs shadow-md transition-all cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Buat Tebakan / Post</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-[#182230] hover:bg-[#28364a] text-[#8ea3ba] hover:text-white transition-colors cursor-pointer"
              title="Tutup (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filter Navigation Bar */}
        <div className="px-5 py-2.5 bg-[#0e131b] border-b border-[#1a222e] flex items-center justify-between flex-wrap gap-2 flex-shrink-0">
          <div className="flex items-center space-x-1.5 overflow-x-auto no-scrollbar">
            {[
              { id: 'ALL', label: 'Semua Stream' },
              { id: 'PREDICTION', label: '🎯 Tebak Harga' },
              { id: 'POLL', label: '📊 Polling' },
              { id: 'TESTIMONI', label: '⭐ Testimoni Cuan' },
              { id: 'THIS_STOCK', label: `Saham Aktif ($${currentStockSymbol})` },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTabFilter(tab.id as any)}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                  activeTabFilter === tab.id
                    ? 'bg-[#1e293b] text-white border border-[#3b82f6] shadow-sm font-bold'
                    : 'bg-[#151c26] text-[#869ab0] hover:text-white hover:bg-[#1f2a3a] border border-[#222d3d]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="text-[11px] text-[#6e8297]">
            Fokus: <span className="font-bold text-[#00c076]">${currentStockSymbol}</span> (Rp {currentStockPrice.toLocaleString('id-ID')})
          </div>
        </div>

        {/* Stream List Scrollable Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4 bg-[#0a0d12]">
          {filteredPosts.map((post) => (
            <div 
              key={post.id}
              className="bg-[#0f141d] border border-[#1b2534] hover:border-[#2b3a4f] rounded-xl p-4 transition-all space-y-3 shadow-md"
            >
              {/* User info & badge */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#1e293b] to-[#334155] text-white font-bold text-xs flex items-center justify-center border border-[#3b4b62]">
                    {post.avatar}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-extrabold text-white">{post.author}</span>
                      {post.authorBadge && (
                        <span className="text-[9.5px] font-semibold px-1.5 py-0.5 rounded bg-[#1e2a3b] text-[#93c5fd] border border-[#2e3e55]">
                          {post.authorBadge}
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-[#6c7f94]">{post.time}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {
                      onSelectStock?.(post.stockSymbol);
                    }}
                    className="px-2.5 py-1 rounded-lg bg-[#151f2d] hover:bg-[#00c076] text-[#60a5fa] hover:text-black font-extrabold text-xs border border-[#243449] transition-all cursor-pointer"
                    title={`Fokuskan ke $${post.stockSymbol}`}
                  >
                    ${post.stockSymbol}
                  </button>
                  {post.sentiment && (
                    <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full ${
                      post.sentiment === 'BULLISH' ? 'bg-[#0d2a1d] text-[#00c076]' :
                      post.sentiment === 'BEARISH' ? 'bg-[#2a1417] text-[#ff4d4f]' :
                      'bg-[#1e2530] text-[#8ea0b3]'
                    }`}>
                      {post.sentiment}
                    </span>
                  )}
                </div>
              </div>

              {/* Main Text Content */}
              <p className="text-xs sm:text-sm text-[#cbd6e2] leading-relaxed">
                {post.content}
              </p>

              {/* SPECIAL BLOCK 1: PRICE PREDICTION (TEBAKAN HARGA) */}
              {post.prediction && (
                <div className="bg-[#121822] border-2 border-[#202d3e] rounded-xl p-3.5 space-y-2.5">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center space-x-1.5 text-xs font-bold text-[#8fa7c3]">
                      <Target className="w-4 h-4 text-[#38bdf8]" />
                      <span>Prediksi Target Harga:</span>
                    </div>

                    {/* Status Tercapai / Pending badge */}
                    {post.prediction.isAchieved ? (
                      <span className="inline-flex items-center space-x-1 text-xs font-extrabold px-2.5 py-0.5 rounded-full bg-[#0d2e20] text-[#00c076] border border-[#00c076]/40 shadow-sm animate-pulse">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>TARGET TERCAPAI! 🎉</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-[#1b2533] text-[#93c5fd] border border-[#2a3a50]">
                        <Clock className="w-3 h-3 text-[#60a5fa]" />
                        <span>Dalam Proses Evaluasi</span>
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                    <div className="bg-[#0b0e14] p-2 rounded-lg border border-[#1b2534]">
                      <span className="text-[10px] text-[#6d7f94] block">Arah Prediksi</span>
                      <span className={`font-black text-sm flex items-center space-x-1 ${
                        post.prediction.direction === 'NAIK' ? 'text-[#00c076]' : 'text-[#ff4d4f]'
                      }`}>
                        {post.prediction.direction === 'NAIK' ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                        <span>{post.prediction.direction}</span>
                      </span>
                    </div>

                    <div className="bg-[#0b0e14] p-2 rounded-lg border border-[#1b2534]">
                      <span className="text-[10px] text-[#6d7f94] block">Harga Tebakan</span>
                      <span className="font-black text-sm text-white">
                        Rp {post.prediction.targetPrice.toLocaleString('id-ID')}
                      </span>
                    </div>

                    <div className="bg-[#0b0e14] p-2 rounded-lg border border-[#1b2534]">
                      <span className="text-[10px] text-[#6d7f94] block">Persentase Target</span>
                      <span className={`font-mono font-black text-sm ${
                        post.prediction.direction === 'NAIK' ? 'text-[#00c076]' : 'text-[#ff4d4f]'
                      }`}>
                        {post.prediction.direction === 'NAIK' ? '+' : '-'}{post.prediction.changePercentTarget}%
                      </span>
                    </div>

                    <div className="bg-[#0b0e14] p-2 rounded-lg border border-[#1b2534]">
                      <span className="text-[10px] text-[#6d7f94] block">Timeframe</span>
                      <span className="font-semibold text-xs text-[#cbd6e2] truncate">
                        {post.prediction.timeframe}
                      </span>
                    </div>
                  </div>

                  {post.prediction.achievedAt && (
                    <div className="text-[11px] text-[#00c076] font-semibold bg-[#0d2a1d] px-2.5 py-1 rounded border border-[#00c076]/30">
                      Tercatat: {post.prediction.achievedAt}
                    </div>
                  )}
                </div>
              )}

              {/* SPECIAL BLOCK 2: COMMUNITY POLL */}
              {post.poll && (
                <div className="bg-[#121822] border border-[#202d3e] rounded-xl p-3.5 space-y-2.5">
                  <div className="flex items-center justify-between text-xs font-bold text-[#e1e7ec]">
                    <div className="flex items-center space-x-1.5">
                      <BarChart2 className="w-4 h-4 text-[#eab308]" />
                      <span>{post.poll.question}</span>
                    </div>
                    <span className="text-[10.5px] text-[#788ca2]">{post.poll.totalVotes} Suara</span>
                  </div>

                  <div className="space-y-2">
                    {post.poll.options.map(option => {
                      const pct = post.poll?.totalVotes 
                        ? Math.round((option.votes / post.poll.totalVotes) * 100) 
                        : 0;
                      const isUserVoted = post.poll?.userVotedOptionId === option.id;

                      return (
                        <button
                          key={option.id}
                          onClick={() => handleVotePoll(post.id, option.id)}
                          className={`w-full text-left p-2.5 rounded-lg border relative overflow-hidden transition-all group ${
                            isUserVoted 
                              ? 'border-[#00c076] bg-[#0d291d]/40' 
                              : 'border-[#222d3e] bg-[#0c1017] hover:border-[#384c66]'
                          }`}
                        >
                          {/* Percentage Fill Bar */}
                          <div 
                            className={`absolute top-0 bottom-0 left-0 opacity-20 transition-all ${
                              isUserVoted ? 'bg-[#00c076]' : 'bg-[#3b82f6]'
                            }`}
                            style={{ width: `${pct}%` }}
                          />

                          <div className="relative flex items-center justify-between text-xs z-10">
                            <span className={`font-medium ${isUserVoted ? 'text-[#00c076] font-bold' : 'text-white'}`}>
                              {option.text} {isUserVoted && '✓'}
                            </span>
                            <span className="font-mono font-bold text-[#869ab0] ml-2">
                              {pct}% ({option.votes})
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Action Buttons: Like, Comment, Share */}
              <div className="pt-2 border-t border-[#17212e] flex items-center justify-between text-xs text-[#7e92a8]">
                <button
                  onClick={() => handleLikePost(post.id)}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
                    post.userLiked 
                      ? 'bg-[#102a3a] border-[#38bdf8] text-[#38bdf8]' 
                      : 'bg-[#121822] border-[#1d2737] text-[#869cb3] hover:text-white'
                  }`}
                >
                  <ThumbsUp className={`w-3.5 h-3.5 ${post.userLiked ? 'fill-current' : ''}`} />
                  <span>{post.likes} Dukung</span>
                </button>

                <span className="text-[11px] text-[#62768b]">
                  Zio Trading Room • Diskusi Publik
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 bg-[#0d1219] border-t border-[#1a222e] flex items-center justify-between text-[11px] text-[#697d92] flex-shrink-0">
          <span>🎯 Pasang prediksi tebakan harga Anda sekarang dan raih reputasi Top Forecaster di komunitas Zio!</span>
          <button
            onClick={onClose}
            className="text-xs font-bold text-[#38bdf8] hover:underline cursor-pointer"
          >
            Tutup Jendela
          </button>
        </div>
      </div>

      {/* SUB-MODAL: BUAT TEBAKAN / POLLING / TESTIMONI */}
      {showCreateModal && (
        <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="w-full max-w-lg bg-[#0e131b] border border-[#243347] rounded-2xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#1c2738] pb-3">
              <h3 className="text-base font-extrabold text-white flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-[#00c076]" />
                <span>Buat Postingan Baru di Stream</span>
              </h3>
              <button 
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded bg-[#182332] text-[#869ab0] hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Type selector */}
            <div className="grid grid-cols-4 gap-1.5 p-1 bg-[#090c10] rounded-xl border border-[#1b2534]">
              {[
                { id: 'PREDICTION', label: '🎯 Tebakan' },
                { id: 'POLL', label: '📊 Polling' },
                { id: 'TESTIMONI', label: '⭐ Testimoni' },
                { id: 'CHAT', label: '💬 Chat' },
              ].map(t => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setCreateType(t.id as any)}
                  className={`py-1.5 rounded-lg text-xs font-bold transition-all ${
                    createType === t.id 
                      ? 'bg-[#00c076] text-black shadow' 
                      : 'text-[#879bb0] hover:text-white'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <form onSubmit={handleCreatePost} className="space-y-3">
              {/* Kode Saham */}
              <div>
                <label className="block text-xs font-semibold text-[#869ab0] mb-1">
                  Ticker Saham IDX:
                </label>
                <input
                  type="text"
                  maxLength={5}
                  value={selectedStockInput}
                  onChange={(e) => setSelectedStockInput(e.target.value.toUpperCase())}
                  placeholder="Contoh: BBCA, ANTM, ADRO"
                  className="w-full px-3 py-2 rounded-lg bg-[#141b25] border border-[#233144] text-sm text-white font-bold tracking-wider focus:outline-none focus:border-[#00c076]"
                  required
                />
              </div>

              {/* Form Tebak Harga */}
              {createType === 'PREDICTION' && (
                <div className="p-3 rounded-xl bg-[#121924] border border-[#202e42] space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-[11px] text-[#7e92a8] mb-1">Arah Tebakan:</label>
                      <div className="grid grid-cols-2 gap-1">
                        <button
                          type="button"
                          onClick={() => setDirectionInput('NAIK')}
                          className={`py-1.5 rounded text-xs font-bold border transition-colors ${
                            directionInput === 'NAIK'
                              ? 'bg-[#0d2e20] text-[#00c076] border-[#00c076]'
                              : 'bg-[#182230] text-[#7e92a8] border-[#25364c]'
                          }`}
                        >
                          🚀 Naik
                        </button>
                        <button
                          type="button"
                          onClick={() => setDirectionInput('TURUN')}
                          className={`py-1.5 rounded text-xs font-bold border transition-colors ${
                            directionInput === 'TURUN'
                              ? 'bg-[#2e1418] text-[#ff4d4f] border-[#ff4d4f]'
                              : 'bg-[#182230] text-[#7e92a8] border-[#25364c]'
                          }`}
                        >
                          🔻 Turun
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-[11px] text-[#7e92a8] mb-1">Harga Target (Rp):</label>
                      <input
                        type="number"
                        value={targetPriceInput}
                        onChange={(e) => setTargetPriceInput(e.target.value)}
                        placeholder="Misal: 10800"
                        className="w-full px-2.5 py-1.5 rounded bg-[#182230] border border-[#25364c] text-xs text-white font-bold focus:outline-none focus:border-[#00c076]"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[11px] text-[#7e92a8] mb-1">Perkiraan Waktu (Timeframe):</label>
                    <select
                      value={timeframeInput}
                      onChange={(e) => setTimeframeInput(e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded bg-[#182230] border border-[#25364c] text-xs text-white focus:outline-none focus:border-[#00c076]"
                    >
                      <option value="Intraday Hari Ini">Intraday Hari Ini</option>
                      <option value="Swing 1-2 Minggu">Swing 1-2 Minggu</option>
                      <option value="Akhir Bulan Ini">Akhir Bulan Ini</option>
                      <option value="Hold 1-3 Bulan">Hold 1-3 Bulan</option>
                    </select>
                  </div>
                </div>
              )}

              {/* Content Textarea */}
              <div>
                <label className="block text-xs font-semibold text-[#869ab0] mb-1">
                  {createType === 'PREDICTION' ? 'Alasan / Analisa Teknis Pendukung:' :
                   createType === 'POLL' ? 'Pertanyaan Polling:' :
                   createType === 'TESTIMONI' ? 'Cerita Testimoni Cuan / Pengalaman:' :
                   'Pesan Chat / Opini:'}
                </label>
                <textarea
                  rows={3}
                  value={contentText}
                  onChange={(e) => setContentText(e.target.value)}
                  placeholder="Tuliskan ulasan atau pandangan Anda..."
                  className="w-full p-2.5 rounded-lg bg-[#141b25] border border-[#233144] text-xs text-white placeholder-[#5e7186] focus:outline-none focus:border-[#00c076]"
                  required
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-[#1c2738]">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-[#182230] hover:bg-[#223044] text-xs text-[#879bb0] hover:text-white"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-[#00c076] hover:bg-[#00db87] text-black font-extrabold text-xs shadow-md transition-all cursor-pointer"
                >
                  Publikasikan ke Stream
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
