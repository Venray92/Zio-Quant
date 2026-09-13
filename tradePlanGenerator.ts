import { Stock, TradePlanData } from '../types';

/**
 * Membulatkan harga sesuai fraksi harga resmi Bursa Efek Indonesia (IDX)
 */
export function roundToIdyTick(price: number): number {
  if (price <= 0) return 1;
  let tick = 1;
  if (price < 200) tick = 1;
  else if (price < 500) tick = 2;
  else if (price < 2000) tick = 5;
  else if (price < 5000) tick = 10;
  else tick = 25;
  return Math.round(price / tick) * tick;
}

/**
 * Generator Trade Plan otomatis dan dinamis berdasarkan data teknikal saham
 */
export function generateTradePlan(stock: Stock): TradePlanData {
  const currentPrice = stock.price || 1000;
  const isDeadCross = stock.isDeadCross || (stock.stochK !== undefined && stock.stochD !== undefined && stock.stochK < stock.stochD);
  const isGoldenCross = stock.stochCrossDays !== undefined && stock.stochCrossDays >= 0 && stock.stochCrossDays <= 3;
  const isPsarBullish = stock.psarBullish ?? (stock.psar ? stock.psar < currentPrice : true);

  // 1. Status Chart Data
  let status = 'BULLISH CONTINUATION';
  let statusType: 'bullish' | 'neutral' | 'bearish' = 'bullish';
  let score = 85;
  let scoreLabel = 'A (Buy Setup)';

  if (stock.symbol === 'IHSG') {
    status = stock.changePercent >= 0 ? 'MARKET CONSOLIDATION UPTREND' : 'MARKET PULLBACK / SUPPORT RETEST';
    statusType = stock.changePercent >= 0 ? 'bullish' : 'neutral';
    score = stock.changePercent >= 0 ? 76 : 64;
    scoreLabel = 'B+ (Market Index)';
  } else if (isDeadCross) {
    status = 'BEARISH / DEAD CROSS (EXIT)';
    statusType = 'bearish';
    score = 38;
    scoreLabel = 'D (Sell / Avoid)';
  } else if (stock.stochCrossDays === 0) {
    status = 'STRONG BUY / FRESH GOLDEN CROSS';
    statusType = 'bullish';
    score = 94;
    scoreLabel = 'A+ (Strong Buy)';
  } else if (stock.stochCrossDays === 1) {
    status = 'BULLISH CONFIRMED (GC +1 HARI)';
    statusType = 'bullish';
    score = 90;
    scoreLabel = 'A+ (Strong Momentum)';
  } else if (stock.stochCrossDays === 2) {
    status = 'BUY ON WEAKNESS (GC +2 HARI)';
    statusType = 'bullish';
    score = 86;
    scoreLabel = 'A (Swing Buy)';
  } else if (isPsarBullish) {
    status = 'UPTREND (PARABOLIC SAR HOLD)';
    statusType = 'bullish';
    score = 82;
    scoreLabel = 'A- (Trend Following)';
  } else {
    status = 'SIDEWAYS ACCUMULATION';
    statusType = 'neutral';
    score = 70;
    scoreLabel = 'B (Wait & See / Spec Buy)';
  }

  // Kategori
  let kategori = 'Swing Trade';
  const bluechips = ['BBCA', 'BMRI', 'BBNI', 'BBRI', 'ASII', 'TLKM', 'ICBP', 'UNTR'];
  if (stock.symbol === 'IHSG') {
    kategori = 'Composite Index';
  } else if (bluechips.includes(stock.symbol)) {
    kategori = 'Bluechip Core Swing';
  } else if (stock.price < 300) {
    kategori = 'Fast Swing / High Beta';
  } else if (stock.stochCrossDays === 0) {
    kategori = 'Breakout Momentum';
  } else if (stock.changePercent > 3) {
    kategori = 'Trend Following';
  } else {
    kategori = 'Swing Trade';
  }

  // 2. Trading Plan Detail Data
  let pattern = 'Stochastic (10,5,5) Hook + PSAR Support';
  if (stock.symbol === 'IHSG') {
    pattern = 'Ascending Channel Retest';
  } else if (stock.stochCrossDays === 0) {
    pattern = 'Double Bottom & Stochastic Hook';
  } else if (stock.stochCrossDays === 1) {
    pattern = 'Cup & Handle Continuation';
  } else if (stock.stochCrossDays === 2) {
    pattern = 'Bull Flag & EMA 20 Pullback';
  } else if (isDeadCross) {
    pattern = 'Lower High Rejection / Death Cross';
  } else if (stock.changePercent > 2) {
    pattern = 'Ascending Triangle Breakout';
  } else {
    pattern = 'Accumulation Range Box Breakout';
  }

  const timeframe = 'Daily (D1)';

  // Entry Area
  // Area Bawah (support entry): ~1.5% - 2.5% di bawah harga sekarang (atau low hari ini)
  // Area Atas (maksimal entry): harga sekarang atau sedikit di atas (0.5% - 1%)
  const entryLowRaw = currentPrice * 0.985;
  const entryHighRaw = currentPrice * 1.008;
  const entryAreaLow = roundToIdyTick(Math.min(entryLowRaw, stock.low || entryLowRaw));
  const entryAreaHigh = roundToIdyTick(Math.max(currentPrice, entryHighRaw));
  const avgEntry = (entryAreaLow + entryAreaHigh) / 2;

  // Stop Loss: ~3.5% - 4.5% di bawah entryAreaLow
  const stopLossRaw = entryAreaLow * 0.962;
  const stopLoss = roundToIdyTick(stopLossRaw);
  const stopLossPercent = Number((((stopLoss - currentPrice) / currentPrice) * 100).toFixed(1));

  // Targets
  // Target 1: ~4.5% - 6% (Resistance Minor / TP Partial)
  const target1Raw = currentPrice * 1.052;
  const target1 = roundToIdyTick(target1Raw);
  const target1Percent = Number((((target1 - currentPrice) / currentPrice) * 100).toFixed(1));

  // Target 2: ~10% - 13% (Resistance Mayor / Fibonacci 0.618 Target)
  const target2Raw = currentPrice * 1.115;
  const target2 = roundToIdyTick(target2Raw);
  const target2Percent = Number((((target2 - currentPrice) / currentPrice) * 100).toFixed(1));

  // Target 3: ~17% - 22% (Longer Swing / ATH / Upper Trendline)
  const target3Raw = currentPrice * 1.185;
  const target3 = roundToIdyTick(target3Raw);
  const target3Percent = Number((((target3 - currentPrice) / currentPrice) * 100).toFixed(1));

  // 3. Rasio R:R (Risk to Reward)
  const riskPerShare = Math.max(1, currentPrice - stopLoss);
  const rewardTarget1 = Math.max(1, target1 - currentPrice);
  const rewardTarget2 = Math.max(1, target2 - currentPrice);
  const rewardTarget3 = Math.max(1, target3 - currentPrice);

  const ratio1 = (rewardTarget1 / riskPerShare).toFixed(1);
  const ratio2 = (rewardTarget2 / riskPerShare).toFixed(1);
  const ratio3 = (rewardTarget3 / riskPerShare).toFixed(1);

  const rrRatioTarget1 = `1 : ${ratio1}`;
  const rrRatioTarget2 = `1 : ${ratio2}`;
  const rrRatioTarget3 = `1 : ${ratio3}`;
  const primaryRR = rrRatioTarget2;

  let rrRating: 'Sangat Menarik' | 'Menarik' | 'Cukup' | 'Kurang Disarankan' = 'Sangat Menarik';
  const numRatio2 = parseFloat(ratio2);
  if (numRatio2 >= 2.5) {
    rrRating = 'Sangat Menarik';
  } else if (numRatio2 >= 1.8) {
    rrRating = 'Menarik';
  } else if (numRatio2 >= 1.2) {
    rrRating = 'Cukup';
  } else {
    rrRating = 'Kurang Disarankan';
  }

  let notes = 'Beli bertahap di area entry. Pasang trailing stop jika target 1 tercapai.';
  if (isDeadCross) {
    notes = 'Indikator Stochastic Dead Cross. Hindari posisi beli baru atau tunggu pembentukan support baru.';
  } else if (stock.stochCrossDays === 0) {
    notes = 'Golden Cross baru terkonfirmasi hari ini. Potensi momentum awal sangat tinggi dengan resiko terukur.';
  } else if (isPsarBullish) {
    notes = 'Posisi titik Parabolic SAR berada di bawah candlestick ("HIJAU HOLD"), mendukung tren naik aktif.';
  }

  return {
    symbol: stock.symbol,
    name: stock.name,
    lastPrice: currentPrice,
    change: stock.change,
    changePercent: stock.changePercent,
    sector: stock.sector,
    status,
    statusType,
    kategori,
    score,
    scoreLabel,
    pattern,
    timeframe,
    entryAreaLow,
    entryAreaHigh,
    stopLoss,
    stopLossPercent,
    target1,
    target1Percent,
    target2,
    target2Percent,
    target3,
    target3Percent,
    riskPerShare,
    rewardTarget1,
    rewardTarget2,
    rewardTarget3,
    rrRatioTarget1,
    rrRatioTarget2,
    rrRatioTarget3,
    primaryRR,
    rrRating,
    notes,
  };
}
