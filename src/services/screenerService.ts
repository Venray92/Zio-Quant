export interface StockData {
  symbol: string;
  name: string;
  price: number;
  changePercent: number;
  volume: number;
  valueM: number;
  stochK: number;
  stochD: number;
  score: number;
  action: 'BUY' | 'SELL' | 'HOLD';
  detailSignal: string;
  stochCrossDays?: number;
  deadCrossDays?: number;
  psarBullish: boolean;
  isLQ45?: boolean;
}

// Logika Kalkulasi Stochastic (10,5,5) & PSAR persis seperti skrip Python
export function calculateStochPsar(prices: number[], highs: number[], lows: number[], volumes: number[]) {
  const len = prices.length;
  if (len < 15) return null;

  // 1. Stochastic Fast K (10)
  const kPeriod = 10;
  const smoothK = 5;
  const smoothD = 5;

  let rawK: number[] = [];
  for (let i = 0; i < len; i++) {
    if (i < kPeriod - 1) {
      rawK.push(50);
      continue;
    }
    const subLow = Math.min(...lows.slice(i - kPeriod + 1, i + 1));
    const subHigh = Math.max(...highs.slice(i - kPeriod + 1, i + 1));
    const k = subHigh === subLow ? 50 : 100 * ((prices[i] - subLow) / (subHigh - subLow));
    rawK.push(k);
  }

  // Smooth K & D (SMA 5)
  const stochK = rawK.map((_, idx, arr) => {
    if (idx < smoothK - 1) return 50;
    const sub = arr.slice(idx - smoothK + 1, idx + 1);
    return sub.reduce((a, b) => a + b, 0) / smoothK;
  });

  const stochD = stochK.map((_, idx, arr) => {
    if (idx < smoothD - 1) return 50;
    const sub = arr.slice(idx - smoothD + 1, idx + 1);
    return sub.reduce((a, b) => a + b, 0) / smoothD;
  });

  const c0 = prices[len - 1];
  const l0 = lows[len - 1];
  const h0 = highs[len - 1];
  const v0 = volumes[len - 1];
  const val0 = (c0 * v0) / 1_000_000_000;

  // Vol MA20
  const vol20 = volumes.slice(-20).reduce((a, b) => a + b, 0) / 20;

  const k0 = stochK[len - 1], d0 = stochD[len - 1];
  const k1 = stochK[len - 2], d1 = stochD[len - 2];
  const k2 = stochK[len - 3], d2 = stochD[len - 3];
  const k3 = stochK[len - 4], d3 = stochD[len - 4];
  const k4 = stochK[len - 5], d4 = stochD[len - 5];

  // Simple PSAR Check (Close > Low offset approximation)
  const psarBullish = c0 > (l0 + h0) / 2;

  let score = 0;
  let action: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
  let detailSignal = '';
  let stochCrossDays: number | undefined = undefined;
  let deadCrossDays: number | undefined = undefined;

  // --- GOLDEN CROSS CHECK (k0 < 35) ---
  if (k0 < 35) {
    if (k1 < d1 && k0 >= d0) { stochCrossDays = 0; score = 80; detailSignal = "GC Hari Ini (H-0)"; }
    else if (k2 < d2 && k1 >= d1 && k0 >= d0) { stochCrossDays = 1; score = 70; detailSignal = "GC Kemarin (H-1)"; }
    else if (k3 < d3 && k2 >= d2 && k0 >= d0) { stochCrossDays = 2; score = 70; detailSignal = "GC 2 Hari Lalu (H-2)"; }
    else if (k4 < d4 && k3 >= d3 && k0 >= d0) { stochCrossDays = 3; score = 70; detailSignal = "GC 3 Hari Lalu (H-3)"; }
    else if (k0 <= d0 && (d0 - k0) <= 3.0) { score = 55; detailSignal = "Early Signal (Merapat)"; }

    if (detailSignal) {
      action = 'BUY';
      if (psarBullish) { score += 20; detailSignal += " | PSAR Bullish (+20)"; }
      if (v0 > vol20) { score += (stochCrossDays === 0 ? 10 : 5); detailSignal += " | Vol > MA20"; }
    }
  }

  // --- DEAD CROSS CHECK (k0 >= 75) ---
  if (k0 >= 75) {
    if (k1 > d1 && k0 <= d0) { deadCrossDays = 0; score = -80; detailSignal = "DC Hari Ini (H-0)"; }
    else if (k2 > d2 && k1 <= d1 && k0 <= d0) { deadCrossDays = 1; score = -70; detailSignal = "DC Kemarin (H-1)"; }
    else if (k3 > d3 && k2 <= d2 && k0 <= d0) { deadCrossDays = 2; score = -70; detailSignal = "DC 2 Hari Lalu (H-2)"; }
    else if (k4 > d4 && k3 >= d3 && k0 <= d0) { deadCrossDays = 3; score = -70; detailSignal = "DC 3 Hari Lalu (H-3)"; }
    else if (k0 >= d0 && (k0 - d0) <= 3.0) { score = -55; detailSignal = "Early DC Signal (Merapat)"; }

    if (detailSignal) {
      action = 'SELL';
      if (!psarBullish) { score -= 20; detailSignal += " | PSAR Bearish (-20)"; }
      if (v0 > vol20) { score -= (deadCrossDays === 0 ? 10 : 5); detailSignal += " | High Vol Sell"; }
    }
  }

  return { stochK: Math.round(k0 * 10) / 10, stochD: Math.round(d0 * 10) / 10, score, action, detailSignal, stochCrossDays, deadCrossDays, psarBullish, valueM: Math.round(val0 * 100) / 100 };
}
