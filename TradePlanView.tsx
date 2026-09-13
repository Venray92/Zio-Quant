import React, { useState } from 'react';
import { Stock, ApiScreenerItem } from '../types';
import { generateTradePlan } from '../utils/tradePlanGenerator';
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  ShieldAlert, 
  Compass, 
  Award, 
  Percent, 
  ArrowUpRight, 
  ArrowDownRight, 
  CheckCircle2, 
  AlertTriangle, 
  Zap, 
  Layers, 
  BarChart3, 
  Calculator,
  Copy,
  Check,
  ShoppingCart
} from 'lucide-react';

interface TradePlanViewProps {
  stock: Stock;
  apiData?: ApiScreenerItem | null;
  onOpenOrder?: (type: 'BUY' | 'SELL') => void;
}

export const TradePlanView: React.FC<TradePlanViewProps> = ({ stock, apiData, onOpenOrder }) => {
  const basePlan = generateTradePlan(stock);
  
  // Override basePlan with API data if available
  const plan = { ...basePlan };
  if (apiData && (apiData.ticker === stock.symbol || apiData.Ticker === stock.symbol)) {
    if (apiData.sourceScreener === 'stoch-psar') {
      const isBuy = apiData.Action?.includes('BELI') || apiData.score! > 0;
      plan.statusType = isBuy ? 'bullish' : 'bearish';
      plan.status = isBuy ? 'STOCH - PSAR BUY SETUP' : 'DEAD CROSS (EXIT)';
      plan.pattern = apiData["Detail Signal"] || (isBuy ? 'Golden Cross' : 'Dead Cross');
      plan.score = apiData.Score || apiData.score || (isBuy ? 80 : 20);
      plan.scoreLabel = 'Screener Match';
    } else if (apiData.sourceScreener === 'rsi-pattern') {
      plan.statusType = 'bullish';
      plan.status = apiData.pattern || apiData["Detail Signal"] || 'RSI DIVERGENCE';
      plan.pattern = apiData.pattern || apiData["Detail Signal"] || 'Divergence';
      plan.score = 85;
      plan.scoreLabel = `Active (${apiData.age || 0} bars)`;
    }

    const buyArea = apiData.buy_area || apiData.TradePlan?.Entry;
    if (buyArea) {
      if (typeof buyArea === 'string' && buyArea.includes('-')) {
        const parts = buyArea.split('-');
        plan.entryAreaLow = parseFloat(parts[0]);
        plan.entryAreaHigh = parseFloat(parts[1]);
      } else {
        plan.entryAreaLow = Number(buyArea);
        plan.entryAreaHigh = Number(buyArea);
      }
    }
    
    const stopLoss = apiData.stop_loss || apiData.TradePlan?.StopLoss || apiData.TradePlan?.ExitPrice;
    if (stopLoss) {
      plan.stopLoss = stopLoss;
      plan.stopLossPercent = ((plan.lastPrice - plan.stopLoss) / plan.lastPrice) * 100;
    }

    const targetProfit = apiData.target_profit || apiData.target_profit_1 || apiData.TradePlan?.TakeProfit;
    if (targetProfit) {
      plan.target1 = targetProfit;
      plan.target1Percent = ((plan.target1 - plan.lastPrice) / plan.lastPrice) * 100;
    }

    // Recalculate Risk Reward Ratios
    const entryAvg = (plan.entryAreaLow + plan.entryAreaHigh) / 2 || plan.lastPrice;
    plan.riskPerShare = entryAvg - plan.stopLoss;
    plan.rewardTarget1 = plan.target1 - entryAvg;
    
    if (plan.riskPerShare > 0) {
      const rr1 = plan.rewardTarget1 / plan.riskPerShare;
      plan.rrRatioTarget1 = `1 : ${rr1.toFixed(1)}`;
      plan.primaryRR = plan.rrRatioTarget1;
      
      if (rr1 >= 2) plan.rrRating = 'Sangat Menarik';
      else if (rr1 >= 1) plan.rrRating = 'Menarik';
      else plan.rrRating = 'Kurang Disarankan';
    }
  }

  const [lotCount, setLotCount] = useState<number>(50);
  const [copied, setCopied] = useState(false);

  // Perhitungan modal & simulasi
  const totalModal = lotCount * 100 * plan.lastPrice;
  const maxRiskNominal = lotCount * 100 * plan.riskPerShare;
  const rewardTP1Nominal = lotCount * 100 * plan.rewardTarget1;
  const rewardTP2Nominal = lotCount * 100 * plan.rewardTarget2;
  const rewardTP3Nominal = lotCount * 100 * plan.rewardTarget3;

  const handleCopyPlan = () => {
    const text = `📊 TRADE PLAN $${plan.symbol}
Harga: Rp ${plan.lastPrice.toLocaleString('id-ID')} (${plan.changePercent >= 0 ? '+' : ''}${plan.changePercent}%)
Status: ${plan.status}
Kategori: ${plan.kategori}
Score: ${plan.score}/100 (${plan.scoreLabel})
Pattern: ${plan.pattern} (${plan.timeframe})

🎯 Area Entry: Rp ${plan.entryAreaLow.toLocaleString('id-ID')} - ${plan.entryAreaHigh.toLocaleString('id-ID')}
🛡️ Stop Loss: Rp ${plan.stopLoss.toLocaleString('id-ID')} (${plan.stopLossPercent}%)
🚀 Target 1: Rp ${plan.target1.toLocaleString('id-ID')} (+${plan.target1Percent}%)
🚀 Target 2: Rp ${plan.target2.toLocaleString('id-ID')} (+${plan.target2Percent}%)
🚀 Target 3: Rp ${plan.target3.toLocaleString('id-ID')} (+${plan.target3Percent}%)

⚖️ RASIO R:R: ${plan.primaryRR} (${plan.rrRating})`;

    navigator.clipboard?.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex-1 h-full overflow-y-auto bg-[#0a0d12] text-[#e1e7ec] p-3 sm:p-5 select-text">
      <div className="max-w-6xl mx-auto space-y-4 pb-8">

        {/* TOP BAR / CONTEXT HEADER */}
        <div className="bg-[#0f141c] border border-[#1d2634] rounded-xl p-3.5 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg">
          <div className="flex items-center space-x-3.5">
            <div className="w-11 h-11 rounded-lg bg-[#182230] border border-[#26354a] flex items-center justify-center font-black text-base text-[#00c076] tracking-wider shadow-inner">
              {plan.symbol.slice(0, 4)}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-extrabold text-white tracking-wide">{plan.symbol}</h1>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-[#16212e] text-[#7ea2ca] border border-[#233347]">
                  {plan.sector}
                </span>
                <span className="hidden sm:inline-flex items-center space-x-1 text-[10px] font-medium px-2 py-0.5 rounded bg-[#0d2a1d] text-[#00c076] border border-[#00c076]/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#00c076] animate-ping" />
                  <span>Auto-sync Screener</span>
                </span>
              </div>
              <p className="text-xs text-[#8a9bb0] truncate max-w-[280px] sm:max-w-md">{plan.name}</p>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex items-center space-x-2 self-stretch sm:self-auto justify-end">
            <button
              onClick={handleCopyPlan}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-[#16202d] hover:bg-[#202d40] border border-[#26374e] text-xs font-semibold text-[#a5bad2] hover:text-white transition-colors cursor-pointer"
              title="Salin ringkasan Trade Plan"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-[#00c076]" />
                  <span className="text-[#00c076]">Tersalin</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Plan</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* 1. STATUS CHART SECTION                                                  */}
        {/* ========================================================================= */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-xs font-bold text-[#8fa7c3] uppercase tracking-wider px-1">
            <Compass className="w-4 h-4 text-[#00c076]" />
            <span>1. Status Chart</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {/* Ticker Card */}
            <div className="bg-[#0f141c] border border-[#1d2634] rounded-xl p-3.5 space-y-1 relative overflow-hidden group hover:border-[#2d3b4e] transition-colors">
              <div className="text-[11px] font-semibold text-[#718296]">Ticker IDX</div>
              <div className="text-xl font-black text-white">{plan.symbol}</div>
              <div className="text-[11px] text-[#556980] flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00c076]" />
                <span>Papan Utama</span>
              </div>
            </div>

            {/* Last Price Card */}
            <div className="bg-[#0f141c] border border-[#1d2634] rounded-xl p-3.5 space-y-1 relative overflow-hidden hover:border-[#2d3b4e] transition-colors">
              <div className="text-[11px] font-semibold text-[#718296]">Last Price</div>
              <div className="text-xl font-black text-white flex items-baseline space-x-1">
                <span>Rp {plan.lastPrice.toLocaleString('id-ID')}</span>
              </div>
              <div className="flex items-center space-x-1.5 text-xs font-bold">
                <span className={`inline-flex items-center space-x-0.5 px-1.5 py-0.5 rounded text-[11px] ${
                  plan.changePercent >= 0 ? 'bg-[#0d2e20] text-[#00c076]' : 'bg-[#2b161a] text-[#ff4d4f]'
                }`}>
                  {plan.changePercent >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                  <span>{plan.changePercent >= 0 ? '+' : ''}{plan.changePercent}%</span>
                </span>
                <span className="text-[11px] text-[#718296]">
                  ({plan.change >= 0 ? '+' : ''}{plan.change})
                </span>
              </div>
            </div>

            {/* Status Card */}
            <div className="bg-[#0f141c] border border-[#1d2634] rounded-xl p-3.5 space-y-1 relative overflow-hidden hover:border-[#2d3b4e] transition-colors sm:col-span-2 lg:col-span-1">
              <div className="text-[11px] font-semibold text-[#718296]">Status Teknikal</div>
              <div className="flex items-center space-x-1.5 pt-0.5">
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  plan.statusType === 'bullish' 
                    ? 'bg-[#00c076] animate-pulse' 
                    : plan.statusType === 'bearish'
                    ? 'bg-[#ff4d4f] animate-pulse'
                    : 'bg-[#eab308]'
                }`} />
                <span className={`text-xs font-extrabold leading-tight truncate ${
                  plan.statusType === 'bullish' 
                    ? 'text-[#00c076]' 
                    : plan.statusType === 'bearish'
                    ? 'text-[#ff4d4f]'
                    : 'text-[#eab308]'
                }`}>
                  {plan.status}
                </span>
              </div>
              <div className="text-[10.5px] text-[#6d8096] truncate">
                {plan.statusType === 'bullish' ? 'Tren Naik Terkonfirmasi' : 'Perhatikan Support'}
              </div>
            </div>

            {/* Kategori Card */}
            <div className="bg-[#0f141c] border border-[#1d2634] rounded-xl p-3.5 space-y-1 relative overflow-hidden hover:border-[#2d3b4e] transition-colors">
              <div className="text-[11px] font-semibold text-[#718296]">Kategori Setup</div>
              <div className="text-sm font-bold text-[#60a5fa] truncate pt-0.5">
                {plan.kategori}
              </div>
              <div className="text-[11px] text-[#62778f] flex items-center space-x-1">
                <Layers className="w-3 h-3 text-[#3b82f6]" />
                <span>Timeframe Daily</span>
              </div>
            </div>

            {/* Score Card */}
            <div className="bg-[#0f141c] border border-[#1d2634] rounded-xl p-3.5 space-y-1 relative overflow-hidden hover:border-[#2d3b4e] transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-[#718296]">Technical Score</span>
                <span className="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-[#1e2d40] text-[#93c5fd]">
                  {plan.scoreLabel.split(' ')[0]}
                </span>
              </div>
              <div className="flex items-baseline space-x-1.5">
                <span className="text-xl font-black text-white">{plan.score}</span>
                <span className="text-xs text-[#62778f]">/ 100</span>
              </div>
              {/* Visual Progress Bar */}
              <div className="w-full bg-[#1b2533] h-1.5 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ${
                    plan.score >= 80 
                      ? 'bg-gradient-to-r from-[#00b074] to-[#00e68d]' 
                      : plan.score >= 60 
                      ? 'bg-gradient-to-r from-[#3b82f6] to-[#60a5fa]' 
                      : 'bg-gradient-to-r from-[#ef4444] to-[#f87171]'
                  }`}
                  style={{ width: `${plan.score}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* 2. TRADING PLAN DETAIL SECTION                                           */}
        {/* ========================================================================= */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-xs font-bold text-[#8fa7c3] uppercase tracking-wider px-1">
            <Target className="w-4 h-4 text-[#3b82f6]" />
            <span>2. Trading Plan Detail</span>
          </div>

          <div className="bg-[#0f141c] border border-[#1d2634] rounded-xl p-4 sm:p-5 space-y-4">
            
            {/* Pattern & Setup Banner */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#1c2432]">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 rounded-lg bg-[#182433] text-[#60a5fa]">
                  <BarChart3 className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[11px] font-semibold text-[#6e8196] block">Chart Pattern</span>
                  <span className="text-sm font-extrabold text-white">{plan.pattern}</span>
                </div>
              </div>
              <div className="flex items-center space-x-2 self-start sm:self-auto">
                <span className="text-[11px] font-medium px-2.5 py-1 rounded bg-[#182330] text-[#93c5fd] border border-[#27384e]">
                  Timeframe: <strong className="text-white">{plan.timeframe}</strong>
                </span>
              </div>
            </div>

            {/* Trading Levels Grid (Entry, Stop Loss, Target 1, Target 2, Target 3) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
              
              {/* AREA ENTRY */}
              <div className="bg-[#121924] border-2 border-[#00c076]/40 hover:border-[#00c076] rounded-xl p-3.5 space-y-1.5 transition-all shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-[#00c076] uppercase tracking-wide flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Area Entry</span>
                  </span>
                  <span className="text-[9.5px] px-1.5 py-0.5 rounded bg-[#0d2a1d] text-[#00c076] font-semibold">
                    Buy Zone
                  </span>
                </div>
                <div className="text-base sm:text-lg font-black text-white">
                  {plan.entryAreaLow.toLocaleString('id-ID')} - {plan.entryAreaHigh.toLocaleString('id-ID')}
                </div>
                <p className="text-[10.5px] text-[#7b92ab] leading-snug">
                  Akumulasi bertahap di area support terdekat.
                </p>
              </div>

              {/* STOP LOSS */}
              <div className="bg-[#1a1215] border-2 border-[#ff4d4f]/40 hover:border-[#ff4d4f] rounded-xl p-3.5 space-y-1.5 transition-all shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-[#ff4d4f] uppercase tracking-wide flex items-center space-x-1">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span>Stop Loss</span>
                  </span>
                  <span className="text-[10.5px] px-1.5 py-0.5 rounded bg-[#331418] text-[#ff6b6d] font-mono font-bold">
                    {plan.stopLossPercent}%
                  </span>
                </div>
                <div className="text-base sm:text-lg font-black text-[#ff8082]">
                  Rp {plan.stopLoss.toLocaleString('id-ID')}
                </div>
                <p className="text-[10.5px] text-[#9e767b] leading-snug">
                  Cut loss disiplin bila closing candle di bawah level ini.
                </p>
              </div>

              {/* TARGET 1 */}
              <div className="bg-[#121822] border border-[#233143] hover:border-[#388bfd] rounded-xl p-3.5 space-y-1.5 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-[#93c5fd] uppercase tracking-wide">
                    Target 1 (TP 1)
                  </span>
                  <span className="text-[10.5px] px-1.5 py-0.5 rounded bg-[#16273c] text-[#60a5fa] font-mono font-bold">
                    +{plan.target1Percent}%
                  </span>
                </div>
                <div className="text-base sm:text-lg font-black text-white">
                  Rp {plan.target1.toLocaleString('id-ID')}
                </div>
                <p className="text-[10.5px] text-[#71869e] leading-snug">
                  Resistance minor. Ambil profit sebagian (30-50%).
                </p>
              </div>

              {/* TARGET 2 */}
              <div className="bg-[#0f1f18] border-2 border-[#00c076]/40 hover:border-[#00c076] rounded-xl p-3.5 space-y-1.5 transition-all shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-[#00c076] uppercase tracking-wide">
                    Target 2 (TP 2)
                  </span>
                  <span className="text-[10.5px] px-1.5 py-0.5 rounded bg-[#0d2a1d] text-[#00c076] font-mono font-bold">
                    +{plan.target2Percent}%
                  </span>
                </div>
                <div className="text-base sm:text-lg font-black text-[#00e68d]">
                  Rp {plan.target2.toLocaleString('id-ID')}
                </div>
                <p className="text-[10.5px] text-[#689b83] leading-snug">
                  Target utama swing (Fibonacci 0.618 / Resistance kuat).
                </p>
              </div>

              {/* TARGET 3 */}
              <div className="bg-[#141b25] border border-[#293b52] hover:border-[#38bdf8] rounded-xl p-3.5 space-y-1.5 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-[#38bdf8] uppercase tracking-wide">
                    Target 3 (TP 3)
                  </span>
                  <span className="text-[10.5px] px-1.5 py-0.5 rounded bg-[#102a3a] text-[#38bdf8] font-mono font-bold">
                    +{plan.target3Percent}%
                  </span>
                </div>
                <div className="text-base sm:text-lg font-black text-white">
                  Rp {plan.target3.toLocaleString('id-ID')}
                </div>
                <p className="text-[10.5px] text-[#6f89a8] leading-snug">
                  Runner profit / All Time High dengan trailing stop.
                </p>
              </div>
            </div>

            {/* VISUAL PRICE LADDER ROADMAP */}
            <div className="pt-2">
              <div className="text-[11px] font-semibold text-[#6e8196] mb-2">
                Roadmap Eksekusi Harga:
              </div>
              <div className="bg-[#0b0e14] p-3 rounded-lg border border-[#1a2330] flex flex-wrap sm:flex-nowrap items-center justify-between gap-2 text-xs">
                <div className="flex items-center space-x-2 text-[#ff4d4f]">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#ff4d4f]" />
                  <span>SL: <strong>{plan.stopLoss.toLocaleString('id-ID')}</strong> ({plan.stopLossPercent}%)</span>
                </div>
                <span className="text-[#334255]">➔</span>
                <div className="flex items-center space-x-2 text-[#00c076]">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#00c076]" />
                  <span>Entry: <strong>{plan.entryAreaLow.toLocaleString('id-ID')}-{plan.entryAreaHigh.toLocaleString('id-ID')}</strong></span>
                </div>
                <span className="text-[#334255]">➔</span>
                <div className="flex items-center space-x-2 text-[#60a5fa]">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#60a5fa]" />
                  <span>TP1: <strong>{plan.target1.toLocaleString('id-ID')}</strong> (+{plan.target1Percent}%)</span>
                </div>
                <span className="text-[#334255]">➔</span>
                <div className="flex items-center space-x-2 text-[#00e68d]">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#00e68d]" />
                  <span>TP2: <strong>{plan.target2.toLocaleString('id-ID')}</strong> (+{plan.target2Percent}%)</span>
                </div>
                <span className="text-[#334255]">➔</span>
                <div className="flex items-center space-x-2 text-[#38bdf8]">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#38bdf8]" />
                  <span>TP3: <strong>{plan.target3.toLocaleString('id-ID')}</strong> (+{plan.target3Percent}%)</span>
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* ========================================================================= */}
        {/* 3. RASIO R:R (RISK TO REWARD) SECTION                                    */}
        {/* ========================================================================= */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-xs font-bold text-[#8fa7c3] uppercase tracking-wider px-1">
            <Zap className="w-4 h-4 text-[#eab308]" />
            <span>3. Rasio R:R (Risk to Reward Ratio)</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
            
            {/* Primary R:R Highlight Card */}
            <div className="bg-[#0f141c] border-2 border-[#eab308]/40 hover:border-[#eab308] rounded-xl p-5 flex flex-col justify-between space-y-4 shadow-lg">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider">
                    Rasio Utama (Ke TP 2)
                  </span>
                  <span className="text-[11px] font-extrabold px-2 py-0.5 rounded bg-[#2e2612] text-[#facc15] border border-[#eab308]/30">
                    {plan.rrRating}
                  </span>
                </div>
                
                {/* BIG PROMINENT R:R NUMBER */}
                <div className="py-2">
                  <div className="text-4xl sm:text-5xl font-black tracking-tight text-white flex items-baseline space-x-2">
                    <span className="text-[#eab308]">{plan.primaryRR}</span>
                  </div>
                  <p className="text-xs text-[#94a3b8] mt-1">
                    Setiap resiko <strong>1x</strong> menawarkan potensi imbal hasil <strong>{plan.primaryRR.replace('1 : ', '')}x</strong> lipat ke Target 2.
                  </p>
                </div>
              </div>

              {/* Visual Split Ratio Bar */}
              <div className="space-y-1.5 pt-2 border-t border-[#1c2432]">
                <div className="flex items-center justify-between text-[11px] font-semibold">
                  <span className="text-[#ff4d4f]">Resiko: Rp {plan.riskPerShare.toLocaleString('id-ID')}</span>
                  <span className="text-[#00c076]">Reward: Rp {plan.rewardTarget2.toLocaleString('id-ID')}</span>
                </div>
                <div className="h-3 w-full bg-[#1b2330] rounded-full overflow-hidden flex">
                  <div 
                    className="bg-[#ff4d4f] h-full transition-all"
                    style={{ 
                      width: `${(plan.riskPerShare / (plan.riskPerShare + plan.rewardTarget2)) * 100}%` 
                    }}
                    title="Risk Proportion"
                  />
                  <div 
                    className="bg-[#00c076] h-full transition-all"
                    style={{ 
                      width: `${(plan.rewardTarget2 / (plan.riskPerShare + plan.rewardTarget2)) * 100}%` 
                    }}
                    title="Reward Proportion"
                  />
                </div>
                <div className="flex justify-between text-[10px] text-[#6d7e92]">
                  <span>Stop Loss ({plan.stopLossPercent}%)</span>
                  <span>Target 2 (+{plan.target2Percent}%)</span>
                </div>
              </div>
            </div>

            {/* Target Breakdown Card */}
            <div className="bg-[#0f141c] border border-[#1d2634] rounded-xl p-5 flex flex-col justify-between space-y-3">
              <div>
                <span className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider block mb-3">
                  Rasio R:R Tiap Target
                </span>

                <div className="space-y-2.5">
                  {/* Target 1 RR */}
                  <div className="flex items-center justify-between p-2 rounded-lg bg-[#141b25] border border-[#1f2b3b]">
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-[#60a5fa]" />
                      <span className="text-xs font-semibold text-white">Target 1 (Konservatif)</span>
                    </div>
                    <span className="font-mono font-bold text-xs text-[#93c5fd]">
                      {plan.rrRatioTarget1}
                    </span>
                  </div>

                  {/* Target 2 RR */}
                  <div className="flex items-center justify-between p-2 rounded-lg bg-[#0e231b] border border-[#00c076]/40">
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-[#00c076]" />
                      <span className="text-xs font-bold text-white">Target 2 (Swing Utama)</span>
                    </div>
                    <span className="font-mono font-black text-sm text-[#00c076]">
                      {plan.rrRatioTarget2}
                    </span>
                  </div>

                  {/* Target 3 RR */}
                  <div className="flex items-center justify-between p-2 rounded-lg bg-[#141b25] border border-[#1f2b3b]">
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-[#38bdf8]" />
                      <span className="text-xs font-semibold text-white">Target 3 (Runner Profit)</span>
                    </div>
                    <span className="font-mono font-bold text-xs text-[#38bdf8]">
                      {plan.rrRatioTarget3}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-2.5 rounded bg-[#131b26] text-[11px] text-[#869ab0] leading-relaxed border border-[#1d2737]">
                💡 <strong>Tips Money Management:</strong> Jika R:R minimal 1:2 tercapai, Anda hanya membutuhkan win rate 40% untuk tetap menghasilkan profit jangka panjang yang konsisten!
              </div>
            </div>

            {/* Money Management Simulator (Lot Size) */}
            <div className="bg-[#0f141c] border border-[#1d2634] rounded-xl p-5 flex flex-col justify-between space-y-3">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider flex items-center space-x-1.5">
                    <Calculator className="w-3.5 h-3.5 text-[#00c076]" />
                    <span>Simulasi Nominal (Lot)</span>
                  </span>
                  <span className="text-xs font-mono font-bold text-white bg-[#172230] px-2 py-0.5 rounded border border-[#26374d]">
                    {lotCount} Lot
                  </span>
                </div>

                {/* Slider for Lot */}
                <input
                  type="range"
                  min="1"
                  max="500"
                  step="5"
                  value={lotCount}
                  onChange={(e) => setLotCount(Number(e.target.value))}
                  className="w-full accent-[#00c076] cursor-pointer mb-3"
                />

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-[#1b2432]">
                    <span className="text-[#718296]">Estimasi Modal:</span>
                    <span className="font-semibold text-white">
                      Rp {totalModal.toLocaleString('id-ID')}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#1b2432]">
                    <span className="text-[#ff4d4f] font-medium">Maksimal Resiko (SL):</span>
                    <span className="font-bold text-[#ff4d4f]">
                      -Rp {maxRiskNominal.toLocaleString('id-ID')}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#1b2432]">
                    <span className="text-[#00c076] font-medium">Potensi Cuan (TP 2):</span>
                    <span className="font-bold text-[#00c076]">
                      +Rp {rewardTP2Nominal.toLocaleString('id-ID')}
                    </span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-[#38bdf8] font-medium">Potensi Cuan (TP 3):</span>
                    <span className="font-bold text-[#38bdf8]">
                      +Rp {rewardTP3Nominal.toLocaleString('id-ID')}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-[#141d28] border border-[#233144] text-xs text-[#9bb2cb] flex items-center justify-between">
                <span>Rekomendasi Max Resiko:</span>
                <span className="font-bold text-[#facc15]">1 - 2% dari Total Portfolio</span>
              </div>
            </div>

          </div>
        </div>

        {/* Technical Notes Footer */}
        <div className="p-3.5 rounded-xl bg-[#0e131b] border border-[#1c2432] flex items-start space-x-2.5 text-xs text-[#7e92a8]">
          <AlertTriangle className="w-4 h-4 text-[#eab308] flex-shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            {plan.notes} Data rencana trading ini otomatis diperbarui sesuai pergerakan harga terkini saham <strong>{plan.symbol}</strong> dan hasil screener teknikal Stochastic & Parabolic SAR.
          </p>
        </div>

      </div>
    </div>
  );
};
