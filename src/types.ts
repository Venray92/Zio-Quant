export interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  sector: string;
  board: string;
  specialNotation?: string;
  tags?: string[];
  volume: string;
  frequency?: string;
  high: number;
  low: number;
  open: number;
  previousClose: number;
  marketCap?: string;
  peRatio?: number;
  pbvRatio?: number;
  roe?: number;
  dividendYield?: number;
  tvSymbol: string;
  ema10?: number;
  stochK?: number;
  stochD?: number;
  stochCrossDays?: number; // 0 = Baru Golden Cross (Hari Ini), 1 = 1 hari lalu, 2 = 2 hari lalu (maksimal 2 hari)
  deadCrossDays?: number; // 0 = Pas Dead Cross Hari Ini (tidak boleh lebih tidak boleh kurang)
  psar?: number;
  psarBullish?: boolean; // true = psar < close ("HIJAU HOLD"), false = psar > close ("MERAH BUANG")
  isDeadCross?: boolean; // true if %K < %D
  statusReason?: string; // e.g. "Golden Cross +2h & PSAR Hijau Hold" or "Death Cross (%K < %D)"
  isLQ45?: boolean;
  apiData?: ApiScreenerItem; // Attached data from API if it came from screener
}

export type MainTab = 
  | 'Chart' 
  | 'Screener'
  | 'Trade Plan'
  | 'Keystats' 
  | 'Analysis' 
  | 'Financials' 
  | 'Comparison' 
  | 'Seasonality' 
  | 'Corp. Action' 
  | 'Insider' 
  | 'Profile' 
  | 'Stream';

export interface ApiScreenerItem {
  ticker?: string;
  Ticker?: string;
  price?: number;
  Harga?: number;
  score?: number;
  Score?: number;
  pattern?: string;
  buy_area?: string | number;
  stop_loss?: number;
  target_profit?: number;
  target_profit_1?: number;
  status?: string;
  Action?: string;
  "Detail Signal"?: string;
  TradePlan?: {
    Entry?: number;
    StopLoss?: number;
    TakeProfit?: number;
    ActionType?: string;
    ExitPrice?: number;
  };
  age?: number;
  // Metadata for which screener this came from
  sourceScreener?: 'stoch-psar' | 'rsi-pattern';
  // UI Grouping
  groupName?: string;
}

export interface TradePlanData {
  symbol: string;
  name: string;
  lastPrice: number;
  change: number;
  changePercent: number;
  sector: string;
  
  // 1. Status Chart
  status: string;
  statusType: 'bullish' | 'neutral' | 'bearish';
  kategori: string;
  score: number; // 0 - 100
  scoreLabel: string;
  
  // 2. Trading Plan Detail
  pattern: string;
  timeframe: string;
  entryAreaLow: number;
  entryAreaHigh: number;
  stopLoss: number;
  stopLossPercent: number;
  target1: number;
  target1Percent: number;
  target2: number;
  target2Percent: number;
  target3: number;
  target3Percent: number;

  // 3. Rasio R:R
  riskPerShare: number;
  rewardTarget1: number;
  rewardTarget2: number;
  rewardTarget3: number;
  rrRatioTarget1: string; // e.g. "1 : 1.4"
  rrRatioTarget2: string; // e.g. "1 : 2.8"
  rrRatioTarget3: string; // e.g. "1 : 4.5"
  primaryRR: string; // Main RR (ke TP 2)
  rrRating: 'Sangat Menarik' | 'Menarik' | 'Cukup' | 'Kurang Disarankan';
  notes: string;
}

export type SidebarTab =
  | 'Watchlist'
  | 'Layout'
  | 'Portfolio'
  | 'Markets'
  | 'Stream'
  | 'Screener'
  | 'e-IPO'
  | 'Broker Analysis'
  | 'Chat'
  | 'Support'
  | 'Settings';

export interface OrderItem {
  id: string;
  symbol: string;
  type: 'BUY' | 'SELL';
  orderType: 'LIMIT' | 'MARKET';
  price: number;
  lot: number;
  total: number;
  status: 'Open' | 'Matched' | 'Rejected' | 'Cancelled';
  timestamp: string;
}

export interface PortfolioPosition {
  symbol: string;
  name: string;
  lot: number;
  avgBuyPrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
}
