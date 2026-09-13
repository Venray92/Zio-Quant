export interface ScreenerStock {
  ticker: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  valueM: number;
  stochK: number;
  stochD: number;
  score: number;
  action: 'BUY' | 'SELL';
  detailSignal: string;
}

// Mock Data Hasil Screener Python kamu (Stoch 10,5,5 + PSAR)
export const mockStochPsarResults: ScreenerStock[] = [
  {
    ticker: 'ISAT',
    name: 'Indosat Tbk',
    price: 2450,
    change: 50,
    changePercent: 2.08,
    valueM: 12.5,
    stochK: 24.5,
    stochD: 18.2,
    score: 110,
    action: 'BUY',
    detailSignal: 'GC Hari Ini (H-0) | PSAR Bullish (+20) | Vol > MA20',
  },
  {
    ticker: 'ACES',
    name: 'Aspirasi Hidup Indonesia Tbk',
    price: 820,
    change: 15,
    changePercent: 1.86,
    valueM: 8.4,
    stochK: 28.1,
    stochD: 22.0,
    score: 95,
    action: 'BUY',
    detailSignal: 'GC Kemarin (H-1) | PSAR Bullish (+20) | Vol > MA20',
  },
  {
    ticker: 'BBRI',
    name: 'Bank Rakyat Indonesia Tbk',
    price: 5125,
    change: -75,
    changePercent: -1.44,
    valueM: 145.2,
    stochK: 82.4,
    stochD: 85.1,
    score: -110,
    action: 'SELL',
    detailSignal: 'DC Hari Ini (H-0) | PSAR Bearish (-20) | High Vol Sell',
  },
];
