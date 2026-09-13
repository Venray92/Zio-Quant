/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { 
  Stock, 
  MainTab, 
  SidebarTab, 
  OrderItem, 
  PortfolioPosition,
  ApiScreenerItem
} from './types';
import { 
  INITIAL_STOCKS, 
  INITIAL_PORTFOLIO, 
  INITIAL_ORDERS,
  getStochPsarScreenedStocks, 
  getRsiPatternScreenedStocks,
} from './data/stocksData';
import { LoginPage } from './components/LoginPage';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { WatchlistPanel } from './components/WatchlistPanel';
import { SubTabsBar } from './components/SubTabsBar';
import { TradingViewChart } from './components/TradingViewChart';
import { TabPanels } from './components/TabPanels';
import { TradePlanView } from './components/TradePlanView';
import { StockStreamView } from './components/StockStreamView';
import { MarketModal } from './components/MarketModal';
import { StreamModal } from './components/StreamModal';
import { SupportModal } from './components/SupportModal';
import { SettingsModal } from './components/SettingsModal';
import { OrderPadModal } from './components/OrderPadModal';
import { BottomTicker } from './components/BottomTicker';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ScreenerView } from './components/ScreenerView';

function MainApp() {
  const { currentUser, logout } = useAuth();
  const [selectedScreener, setSelectedScreener] = useState<string | null>(null);
  const [previousScreener, setPreviousScreener] = useState<string | null>(null);
  const [stocks, setStocks] = useState<Stock[]>(INITIAL_STOCKS);
  
  // API Screener Data for Trade Plan override
  const [activeScreenerData, setActiveScreenerData] = useState<ApiScreenerItem | null>(null);

  const [activeStock, setActiveStock] = useState<Stock>(
    INITIAL_STOCKS.find((s) => s.symbol === 'IHSG') || INITIAL_STOCKS[0]
  );
  const [activeMainTab, setActiveMainTab] = useState<MainTab>('Chart');
  const [activeSidebarTab, setActiveSidebarTab] = useState<SidebarTab>('Screener');
  const [isWatchlistOpen, setIsWatchlistOpen] = useState(true);
  const [chartTheme, setChartTheme] = useState<'dark' | 'cream'>('cream'); // Cream as shown in screenshot
  const [appTheme, setAppTheme] = useState<'dark' | 'light'>('dark');

  // Modal overlays
  const [isMarketModalOpen, setIsMarketModalOpen] = useState(false);
  const [isStreamModalOpen, setIsStreamModalOpen] = useState(false);
  const [isSupportModalOpen, setIsSupportModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);

  // Portfolio & Orders State
  const [portfolio, setPortfolio] = useState<PortfolioPosition[]>(INITIAL_PORTFOLIO);
  const [orders, setOrders] = useState<OrderItem[]>(INITIAL_ORDERS);

  // Order Pad Modal
  const [isOrderModalOpen, setIsOrderModalOpen] = useState(false);
  const [orderModalSide, setOrderModalSide] = useState<'BUY' | 'SELL'>('BUY');

  // Watchlist & Alert indicators
  const [watchlistSet, setWatchlistSet] = useState<Set<string>>(new Set(['IHSG']));
  const [alertSet, setAlertSet] = useState<Set<string>>(new Set(['IHSG']));

  const applyScreenerStockList = async (screener: string | null) => {
    if (screener === '1. Stoch - Psar') {
      try {
        const apiUrl = localStorage.getItem('ZIO_API_URL') || 'https://hunter-snazzy-sandpaper.ngrok-free.dev';
        const baseUrl = apiUrl.endsWith('/') ? apiUrl.slice(0, -1) : apiUrl;
        const response = await fetch(`${baseUrl}/api/screener/stoch-psar`, {
          headers: {
            "ngrok-skip-browser-warning": "true"
          }
        });
        if (!response.ok) throw new Error('API Error');
        const jsonData = await response.json();
        
        let apiItems: any[] = [];
        if (jsonData.golden_cross) apiItems = [...apiItems, ...jsonData.golden_cross.map((i: any) => ({...i, sourceScreener: 'stoch-psar'}))];
        if (jsonData.dead_cross) apiItems = [...apiItems, ...jsonData.dead_cross.map((i: any) => ({...i, sourceScreener: 'stoch-psar'}))];
        if (apiItems.length === 0 && Array.isArray(jsonData)) apiItems = jsonData.map((i: any) => ({...i, sourceScreener: 'stoch-psar'}));
        
        const mapped = apiItems.map(item => {
          const existingStock = INITIAL_STOCKS.find(s => s.symbol === (item.Ticker || item.ticker));
          return {
            ...(existingStock || {}),
            symbol: item.Ticker || item.ticker || 'UNKNOWN',
            name: existingStock ? existingStock.name : (item.Ticker || item.ticker || 'UNKNOWN'),
            price: item.Harga || item.price || 0,
            change: existingStock ? existingStock.change : 0,
            changePercent: existingStock ? existingStock.changePercent : 0,
            sector: existingStock ? existingStock.sector : 'Screener',
            board: existingStock ? existingStock.board : 'Screener',
            volume: existingStock ? existingStock.volume : '0',
            high: item.Harga || item.price || 0,
            low: item.Harga || item.price || 0,
            open: item.Harga || item.price || 0,
            previousClose: item.Harga || item.price || 0,
            tvSymbol: `IDX:${item.Ticker || item.ticker || 'UNKNOWN'}`,
            apiData: item,
            statusReason: item["Detail Signal"] || item.detail_signal || existingStock?.statusReason,
            specialNotation: item.Action?.includes("BELI") ? "BARU GC" : (item.Action?.includes("JUAL") ? "PAS DC" : existingStock?.specialNotation),
            isLQ45: existingStock ? existingStock.isLQ45 : false,
            stochK: item["Stoch %K"] !== undefined ? item["Stoch %K"] : existingStock?.stochK,
            stochD: item["Stoch %D"] !== undefined ? item["Stoch %D"] : existingStock?.stochD,
            psarBullish: item["Detail Signal"] ? !item["Detail Signal"].includes("Bearish") : existingStock?.psarBullish,
            stochCrossDays: item.Action?.includes("BELI") ? 0 : existingStock?.stochCrossDays,
            isDeadCross: item.Action?.includes("JUAL") ? true : existingStock?.isDeadCross,
            deadCrossDays: item.Action?.includes("JUAL") ? 0 : existingStock?.deadCrossDays,
          };
        });
        
        setStocks([INITIAL_STOCKS[0], ...mapped]);
        if (mapped.length > 0) {
          setActiveStock(mapped[0]);
          setActiveScreenerData(mapped[0].apiData);
        }
      } catch (err) {
        console.error("Failed fetching API, fallback to dummy:", err);
        const screened = getStochPsarScreenedStocks();
        setStocks([INITIAL_STOCKS[0], ...screened]);
        if (screened.length > 0) setActiveStock(screened[0]);
      }
    } else if (screener === '2. RSI + Pattern') {
      try {
        const apiUrl = localStorage.getItem('ZIO_API_URL') || 'https://hunter-snazzy-sandpaper.ngrok-free.dev';
        const baseUrl = apiUrl.endsWith('/') ? apiUrl.slice(0, -1) : apiUrl;
        const response = await fetch(`${baseUrl}/api/screener/rsi-pattern`, {
          headers: {
            "ngrok-skip-browser-warning": "true"
          }
        });
        if (!response.ok) throw new Error('API Error');
        const jsonData = await response.json();
        
        const apiItems = Array.isArray(jsonData) ? jsonData.map((i: any) => ({...i, sourceScreener: 'rsi-pattern'})) : [];
        const mapped = apiItems.map(item => {
          const existingStock = INITIAL_STOCKS.find(s => s.symbol === (item.Ticker || item.ticker));
          return {
            ...(existingStock || {}),
            symbol: item.Ticker || item.ticker || 'UNKNOWN',
            name: existingStock ? existingStock.name : (item.Ticker || item.ticker || 'UNKNOWN'),
            price: item.Harga || item.price || 0,
            change: existingStock ? existingStock.change : 0,
            changePercent: existingStock ? existingStock.changePercent : 0,
            sector: existingStock ? existingStock.sector : 'Screener',
            board: existingStock ? existingStock.board : 'Screener',
            volume: existingStock ? existingStock.volume : '0',
            high: item.Harga || item.price || 0,
            low: item.Harga || item.price || 0,
            open: item.Harga || item.price || 0,
            previousClose: item.Harga || item.price || 0,
            tvSymbol: `IDX:${item.Ticker || item.ticker || 'UNKNOWN'}`,
            apiData: item,
            statusReason: item["Detail Signal"] || item.detail_signal || existingStock?.statusReason,
            specialNotation: item.Action?.includes("BELI") ? "RSI" : (item.Action?.includes("JUAL") ? "SELL" : existingStock?.specialNotation),
            isLQ45: existingStock ? existingStock.isLQ45 : false,
          };
        });

        setStocks([INITIAL_STOCKS[0], ...mapped]);
        if (mapped.length > 0) {
          setActiveStock(mapped[0]);
          setActiveScreenerData(mapped[0].apiData);
        }
      } catch (err) {
        console.error("Failed fetching API, fallback to dummy:", err);
        const screened = getRsiPatternScreenedStocks();
        setStocks([INITIAL_STOCKS[0], ...screened]);
        if (screened.length > 0) setActiveStock(screened[0]);
      }
    } else {
      setStocks(INITIAL_STOCKS);
      setActiveStock(INITIAL_STOCKS[0]);
      setActiveScreenerData(null);
    }
  };

  const handleSelectScreener = (screener: string | null) => {
    if (!screener) {
      if (selectedScreener) {
        setPreviousScreener(selectedScreener);
      }
      setSelectedScreener(null);
      setStocks(INITIAL_STOCKS);
      setActiveStock(INITIAL_STOCKS[0]);
      setActiveScreenerData(null);
      return;
    }
    
    if (screener === selectedScreener) {
      return;
    }

    // Move current screener to history (max 1 history)
    if (selectedScreener) {
      setPreviousScreener(selectedScreener);
    }
    setSelectedScreener(screener);
    
    // Auto-switch to Chart and Watchlist for traditional viewing
    setActiveMainTab('Chart');
    setActiveSidebarTab('Watchlist');
    
    applyScreenerStockList(screener);
  };

  // Swap history screener with active screener
  const handleSelectHistoryScreener = (historyScreener: string) => {
    const current = selectedScreener;
    setPreviousScreener(current);
    setSelectedScreener(historyScreener);
    applyScreenerStockList(historyScreener);
  };

  // Home / Reload: resets everything back to initial state
  const handleReloadHome = () => {
    setSelectedScreener(null);
    setPreviousScreener(null);
    setStocks(INITIAL_STOCKS);
    setActiveStock(INITIAL_STOCKS.find((s) => s.symbol === 'IHSG') || INITIAL_STOCKS[0]);
    setActiveMainTab('Chart');
    setActiveSidebarTab('Screener');
  };

  const handleOpenOrder = (type: 'BUY' | 'SELL') => {
    setOrderModalSide(type);
    setIsOrderModalOpen(true);
  };

  const handleToggleWatchlist = () => {
    setWatchlistSet(prev => {
      const next = new Set(prev);
      if (next.has(activeStock.symbol)) {
        next.delete(activeStock.symbol);
      } else {
        next.add(activeStock.symbol);
      }
      return next;
    });
  };

  const handleToggleAlert = () => {
    setAlertSet(prev => {
      const next = new Set(prev);
      if (next.has(activeStock.symbol)) {
        next.delete(activeStock.symbol);
      } else {
        next.add(activeStock.symbol);
      }
      return next;
    });
  };

  const handleAddStock = (symbol: string) => {
    const existing = stocks.find(s => s.symbol === symbol);
    if (existing) {
      setActiveStock(existing);
      return;
    }
    const newStock: Stock = {
      symbol,
      name: `${symbol} Indonesia Tbk.`,
      price: 1500,
      change: 25,
      changePercent: 1.69,
      sector: 'Industri',
      board: 'Papan Utama',
      volume: '5.2M',
      high: 1550,
      low: 1475,
      open: 1480,
      previousClose: 1475,
      tvSymbol: `IDX:${symbol}`,
    };
    setStocks(prev => [newStock, ...prev]);
    setActiveStock(newStock);
  };

  const handleSelectStockBySymbol = (symbol: string) => {
    const found = stocks.find(s => s.symbol === symbol);
    if (found) {
      setActiveStock(found);
    }
  };

  const handleSubmitOrder = (orderData: Omit<OrderItem, 'id' | 'timestamp'>) => {
    const newOrder: OrderItem = {
      ...orderData,
      id: `ORD-${Math.floor(1000 + Math.random() * 9000)}`,
      timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    };
    setOrders(prev => [newOrder, ...prev]);

    // If BUY, update portfolio
    if (orderData.type === 'BUY') {
      setPortfolio(prev => {
        const existingIdx = prev.findIndex(p => p.symbol === orderData.symbol);
        if (existingIdx >= 0) {
          const item = prev[existingIdx];
          const newLot = item.lot + orderData.lot;
          const newMarketVal = newLot * 100 * activeStock.price;
          const newUnrealized = newMarketVal - (newLot * 100 * item.avgBuyPrice);
          const updated = [...prev];
          updated[existingIdx] = {
            ...item,
            lot: newLot,
            currentPrice: activeStock.price,
            marketValue: newMarketVal,
            unrealizedPnL: newUnrealized,
            unrealizedPnLPercent: Number(((newUnrealized / (newLot * 100 * item.avgBuyPrice)) * 100).toFixed(2)),
          };
          return updated;
        } else {
          return [
            {
              symbol: orderData.symbol,
              name: activeStock.name,
              lot: orderData.lot,
              avgBuyPrice: orderData.price,
              currentPrice: activeStock.price,
              marketValue: orderData.lot * 100 * activeStock.price,
              unrealizedPnL: 0,
              unrealizedPnLPercent: 0,
            },
            ...prev,
          ];
        }
      });
    }
  };

  if (!currentUser) {
    return <LoginPage />;
  }

  return (
    <div className={`flex flex-col h-screen w-screen overflow-hidden select-none transition-colors duration-200 ${
      appTheme === 'light' ? 'bg-[#f1f5f9] text-[#0f172a]' : 'bg-[#0c0e12] text-[#e1e7ec]'
    }`}>
      {/* Top Header Bar */}
      <Header 
        title="Zio - Screaner" 
        selectedScreener={selectedScreener}
        onSelectScreener={handleSelectScreener}
        onReloadHome={handleReloadHome}
      />

      {/* Main Container: Sidebar + Watchlist + Content */}
      <div className="flex flex-1 min-h-0 overflow-hidden relative">
        {/* Leftmost Slim Sidebar */}
        <Sidebar
          activeTab={activeSidebarTab}
          onSelectTab={(tab) => {
            setActiveSidebarTab(tab);
            if (tab === 'Screener') {
              setActiveMainTab('Chart');
              setIsWatchlistOpen(true);
            } else if (tab === 'Markets') {
              setIsMarketModalOpen(true);
            } else if (tab === 'Stream') {
              setIsStreamModalOpen(true);
            } else if (tab === 'Support') {
              setIsSupportModalOpen(true);
            } else if (tab === 'Settings') {
              setIsSettingsModalOpen(true);
            }
          }}
          onLogout={logout}
        />

        {/* Second Column: Watchlist Panel */}
        <WatchlistPanel
          stocks={stocks}
          activeStock={activeStock}
          onSelectStock={(stock) => {
            setActiveStock(stock);
            if (stock.apiData) {
              setActiveScreenerData(stock.apiData);
            } else {
              setActiveScreenerData(null);
            }
          }}
          isOpen={isWatchlistOpen}
          onToggleOpen={() => setIsWatchlistOpen(!isWatchlistOpen)}
          onAddStock={handleAddStock}
          selectedScreener={selectedScreener}
          previousScreener={previousScreener}
          onSelectHistoryScreener={handleSelectHistoryScreener}
        />

        {/* Center Workspace */}
        <main className={`flex-1 flex flex-col min-w-0 overflow-hidden ${
          appTheme === 'light' ? 'bg-[#f8fafc]' : 'bg-[#0e1217]'
        }`}>
          {/* Sub-Tabs Bar: Chart, Trade Plan, Stream */}
          <SubTabsBar
            activeTab={activeMainTab}
            onSelectTab={(tab) => setActiveMainTab(tab)}
            chartTheme={chartTheme}
            onToggleChartTheme={() => setChartTheme(t => t === 'cream' ? 'dark' : 'cream')}
          />

          {/* Active View: Chart, Trade Plan, Stream, etc. */}
          <div className="flex-1 min-h-0 relative flex flex-col overflow-hidden">
            {activeMainTab === 'Screener' ? (
              <ScreenerView
                defaultTab={selectedScreener === '2. RSI + Pattern' ? 'rsi-pattern' : 'stoch-psar'}
                onSelectStock={(symbol, apiData) => {
                  const stockData = stocks.find(s => s.symbol === symbol) || {
                    symbol,
                    name: symbol,
                    price: apiData.price,
                    change: INITIAL_STOCKS.find(s => s.symbol === (apiData.Ticker || apiData.ticker))?.change || 0,
                    changePercent: INITIAL_STOCKS.find(s => s.symbol === (apiData.Ticker || apiData.ticker))?.changePercent || 0,
                    sector: 'Unknown',
                    board: 'Unknown',
                    volume: '0',
                    high: apiData.price,
                    low: apiData.price,
                    open: apiData.price,
                    previousClose: apiData.price,
                    tvSymbol: `IDX:${symbol}`
                  };
                  setActiveStock(stockData as Stock);
                  setActiveScreenerData(apiData);
                  setActiveMainTab('Trade Plan');
                }}
              />
            ) : activeMainTab === 'Chart' ? (
              <TradingViewChart
                stock={activeStock}
                theme={chartTheme}
                selectedScreener={selectedScreener}
              />
            ) : activeMainTab === 'Trade Plan' ? (
              <TradePlanView
                stock={activeStock}
                apiData={activeScreenerData}
                onOpenOrder={handleOpenOrder}
              />
            ) : activeMainTab === 'Stream' ? (
              <StockStreamView
                stock={activeStock}
                onOpenGlobalStream={() => setIsStreamModalOpen(true)}
              />
            ) : (
              <TabPanels
                activeTab={activeMainTab}
                stock={activeStock}
              />
            )}
          </div>
        </main>
      </div>

      {/* Bottom Running Ticker & Real-time Clock */}
      <BottomTicker
        onSelectStockBySymbol={handleSelectStockBySymbol}
      />

      {/* Order Pad Modal for BUY / SELL */}
      <OrderPadModal
        isOpen={isOrderModalOpen}
        onClose={() => setIsOrderModalOpen(false)}
        stock={activeStock}
        initialType={orderModalSide}
        onSubmitOrder={handleSubmitOrder}
      />

      {/* 1. Markets Modal (Non-full screen, overlay with close button) */}
      <MarketModal
        isOpen={isMarketModalOpen}
        onClose={() => {
          setIsMarketModalOpen(false);
          setActiveSidebarTab('Screener');
        }}
        onSelectStock={handleSelectStockBySymbol}
      />

      {/* 2. Stream Modal (Non-full screen, predictions, polling, chat) */}
      <StreamModal
        isOpen={isStreamModalOpen}
        onClose={() => {
          setIsStreamModalOpen(false);
          setActiveSidebarTab('Screener');
        }}
        activeStock={activeStock}
        onSelectStock={handleSelectStockBySymbol}
      />

      {/* 3. Support Modal (Non-full screen, Helpdesk & FAQ) */}
      <SupportModal
        isOpen={isSupportModalOpen}
        onClose={() => {
          setIsSupportModalOpen(false);
          setActiveSidebarTab('Screener');
        }}
      />

      {/* 4. Settings Modal (Light / Dark Background switch with sun/moon icon) */}
      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => {
          setIsSettingsModalOpen(false);
          setActiveSidebarTab('Screener');
        }}
        appTheme={appTheme}
        onSelectAppTheme={(theme) => setAppTheme(theme)}
        chartTheme={chartTheme}
        onSelectChartTheme={(theme) => setChartTheme(theme)}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

