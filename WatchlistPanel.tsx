import React, { useState, useMemo } from 'react';
import { 
  Plus, 
  SlidersHorizontal, 
  Search, 
  RotateCw, 
  TrendingDown, 
  TrendingUp, 
  ChevronLeft, 
  ChevronRight,
  X,
  CheckCircle2,
  AlertTriangle,
  History
} from 'lucide-react';
import { Stock } from '../types';
import { 
  STOCKS_UNIVERSE, 
  INITIAL_STOCKS, 
  getGoldenCrossScreenedStocks, 
  getPasDeadCrossStocks 
} from '../data/stocksData';

interface WatchlistPanelProps {
  stocks: Stock[];
  activeStock: Stock;
  onSelectStock: (stock: Stock) => void;
  isOpen: boolean;
  onToggleOpen: () => void;
  onAddStock?: (symbol: string) => void;
  selectedScreener?: string | null;
  previousScreener?: string | null;
  onSelectHistoryScreener?: (screener: string) => void;
  theme?: 'dark' | 'light';
}

export const WatchlistPanel: React.FC<WatchlistPanelProps> = ({
  stocks,
  activeStock,
  onSelectStock,
  isOpen,
  onToggleOpen,
  onAddStock,
  selectedScreener,
  previousScreener,
  onSelectHistoryScreener,
  theme = 'dark',
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [newSymbolInput, setNewSymbolInput] = useState('');
  
  // Filter mode when Screener "1. Stoch - Psar" is active
  // 'all_signals': Golden Cross (0-2h) + Pas Dead Cross (0h)
  // 'gc_only': Baru Golden Cross (0h) s/d kelewat maksimal 2 hari saja (0, 1, 2)
  // 'dc_only': Tepat Pas Dead Cross hari ini (0h, tidak boleh lebih / kurang)
  // 'all': Semua Universe
  type ScreenerFilterMode = 'all_signals' | 'gc_only' | 'dc_only' | 'all';
  const [screenerFilter, setScreenerFilter] = useState<ScreenerFilterMode>('all_signals');

  const gcStocks = useMemo(() => {
    if (selectedScreener === '1. Stoch - Psar') {
      return stocks.filter(s => s.apiData && (s.apiData.Action?.includes('BELI') || s.apiData.score! > 0));
    }
    return getGoldenCrossScreenedStocks();
  }, [stocks, selectedScreener]);

  const dcStocks = useMemo(() => {
    if (selectedScreener === '1. Stoch - Psar') {
      return stocks.filter(s => s.apiData && (s.apiData.Action?.includes('JUAL') || s.apiData.score! < 0));
    }
    return getPasDeadCrossStocks();
  }, [stocks, selectedScreener]);
  const allSignalStocks = useMemo(() => [...gcStocks, ...dcStocks], [gcStocks, dcStocks]);

  // Decide display stock list:
  const baseStocks = useMemo(() => {
    if (selectedScreener === '1. Stoch - Psar') {
      if (screenerFilter === 'gc_only') {
        return [INITIAL_STOCKS[0], ...gcStocks];
      }
      if (screenerFilter === 'dc_only') {
        return [INITIAL_STOCKS[0], ...dcStocks];
      }
      if (screenerFilter === 'all_signals') {
        return [INITIAL_STOCKS[0], ...allSignalStocks];
      }
      return [INITIAL_STOCKS[0], ...STOCKS_UNIVERSE];
    }
    return stocks;
  }, [selectedScreener, screenerFilter, gcStocks, dcStocks, allSignalStocks, stocks]);

  const filteredStocks = baseStocks.filter(stock => 
    stock.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
    stock.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newSymbolInput.trim() && onAddStock) {
      onAddStock(newSymbolInput.trim().toUpperCase());
      setNewSymbolInput('');
      setIsAdding(false);
    }
  };

  const isLight = theme === 'light';

  if (!isOpen) {
    return (
      <div className={`w-5 border-r flex items-center justify-center relative select-none transition-colors duration-200 ${
        isLight ? 'bg-[#f8fafc] border-[#e2e8f0]' : 'bg-[#0f1318] border-[#1a212b]'
      }`}>
        <button
          onClick={onToggleOpen}
          className={`w-4 h-12 rounded-r flex items-center justify-center transition-colors shadow-sm ${
            isLight
              ? 'bg-[#e2e8f0] hover:bg-[#cbd5e1] text-[#475569] hover:text-[#0f172a]'
              : 'bg-[#1c2430] hover:bg-[#253040] text-[#8b98a5] hover:text-white'
          }`}
          title="Buka Watchlist"
        >
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  const screenedCount = stocks.filter(s => s.symbol !== 'IHSG').length;

  return (
    <div className={`w-[245px] sm:w-[260px] border-r flex flex-col h-full flex-shrink-0 select-none relative transition-colors duration-200 ${
      isLight ? 'bg-white border-[#e2e8f0] text-[#0f172a]' : 'bg-[#11161d] border-[#1a212b] text-[#e1e7ec]'
    }`}>
      {/* Collapse button on right border */}
      <button
        onClick={onToggleOpen}
        className={`absolute -right-3 top-1/2 -translate-y-1/2 z-30 w-3 h-10 border rounded-r flex items-center justify-center shadow-md transition-colors ${
          isLight
            ? 'bg-[#e2e8f0] hover:bg-[#cbd5e1] text-[#475569] hover:text-[#0f172a] border-[#cbd5e1]'
            : 'bg-[#1e2735] hover:bg-[#283548] text-[#8e9eb0] hover:text-white border-[#2d3748]'
        }`}
        title="Tutup Watchlist"
      >
        <ChevronLeft className="w-2.5 h-2.5" />
      </button>

      {/* Top Controls Header */}
      <div className={`p-2 border-b flex items-center justify-between gap-1.5 ${
        isLight ? 'border-[#e2e8f0] bg-[#f8fafc]' : 'border-[#1c2430] bg-[#11161d]'
      }`}>
        {/* Dynamic Tab Pills: Active Screener (Screening default) & History Tab (replacing W.L) */}
        <div className="flex items-center space-x-1.5 overflow-x-hidden flex-1 min-w-0">
          {/* Active Tab: Displays what was clicked in Choose Screaner, or 'Screening' if unselected */}
          <div
            className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold transition-all border shadow-sm flex items-center space-x-1 truncate flex-shrink-0 ${
              isLight
                ? 'bg-[#e6f4ea] border-[#00c076] text-[#00875a]'
                : 'bg-[#0d3324] border-[#00c076] text-[#00c076]'
            }`}
            title={`Tab Aktif: ${selectedScreener || 'Screening'}`}
          >
            {selectedScreener && (
              <span className="w-1.5 h-1.5 rounded-full bg-[#00c076] animate-pulse flex-shrink-0" />
            )}
            <span className="truncate max-w-[120px]">{selectedScreener || 'Screening'}</span>
          </div>

          {/* History Tab: Replaces W.L. Shows previous screener (max 1 history). Clicking swaps it! */}
          {previousScreener && (
            <button
              onClick={() => onSelectHistoryScreener?.(previousScreener)}
              className={`px-2 py-0.5 rounded-full text-[10.5px] font-semibold transition-all border flex items-center space-x-1 truncate max-w-[110px] group cursor-pointer flex-shrink-0 ${
                isLight
                  ? 'bg-[#f1f5f9] border-[#cbd5e1] text-[#475569] hover:text-[#0f172a] hover:border-[#3b82f6]'
                  : 'bg-[#141c26] border-[#273546] hover:border-[#3b82f6] text-[#8ea5be] hover:text-white'
              }`}
              title={`Riwayat Sebelumnya: ${previousScreener} (Klik untuk berpindah ke screener ini)`}
            >
              <History className="w-3 h-3 text-[#3b82f6] group-hover:rotate-[-45deg] transition-transform flex-shrink-0" />
              <span className="truncate">{previousScreener}</span>
            </button>
          )}
        </div>

        {/* Action icons: + and Filter */}
        <div className={`flex items-center space-x-1 flex-shrink-0 ${isLight ? 'text-[#64748b]' : 'text-[#8b98a5]'}`}>
          <button
            onClick={() => setIsAdding(!isAdding)}
            className={`p-1 rounded transition-colors ${
              isLight ? 'hover:text-[#0f172a] hover:bg-[#e2e8f0]' : 'hover:text-white hover:bg-[#1c2430]'
            }`}
            title="Tambah Saham"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            className={`p-1 rounded transition-colors ${
              isLight ? 'hover:text-[#0f172a] hover:bg-[#e2e8f0]' : 'hover:text-white hover:bg-[#1c2430]'
            }`}
            title="Filter / Sort"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Quick Search Bar or Add Input */}
      {isAdding ? (
        <form onSubmit={handleAddSubmit} className={`p-2 border-b flex items-center space-x-1.5 ${
          isLight ? 'bg-[#f1f5f9] border-[#e2e8f0]' : 'bg-[#161c24] border-[#1c2430]'
        }`}>
          <input
            type="text"
            placeholder="Kode Saham (e.g. ANTM, UNTR)..."
            value={newSymbolInput}
            onChange={(e) => setNewSymbolInput(e.target.value.toUpperCase())}
            autoFocus
            className={`flex-1 border focus:border-[#00c076] rounded px-2 py-1 text-xs focus:outline-none uppercase ${
              isLight ? 'bg-white border-[#cbd5e1] text-[#0f172a]' : 'bg-[#0f1318] border-[#2b3748] text-white'
            }`}
          />
          <button
            type="submit"
            className="bg-[#00c076] text-black font-semibold text-xs px-2.5 py-1 rounded hover:bg-[#00db87]"
          >
            Add
          </button>
          <button
            type="button"
            onClick={() => setIsAdding(false)}
            className={`p-1 ${isLight ? 'text-[#64748b] hover:text-[#0f172a]' : 'text-[#8b98a5] hover:text-white'}`}
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </form>
      ) : (
        <div className={`px-2 py-1.5 border-b flex items-center space-x-1.5 text-xs ${
          isLight ? 'border-[#e2e8f0] bg-white text-[#475569]' : 'border-[#1c2430]/60 bg-[#11161d] text-[#8b98a5]'
        }`}>
          <Search className="w-3.5 h-3.5 text-[#94a3b8]" />
          <input
            type="text"
            placeholder="Cari kode atau nama saham..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={`bg-transparent text-xs focus:outline-none w-full ${
              isLight ? 'text-[#0f172a] placeholder-[#94a3b8]' : 'text-[#e1e7ec] placeholder-[#627182]'
            }`}
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} className={isLight ? 'text-[#64748b] hover:text-[#0f172a]' : 'hover:text-white'}>
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}

      {/* Screener Active Info Banner */}
      {selectedScreener === '1. Stoch - Psar' ? (
        <div className={`px-2 py-2 border-b flex flex-col gap-1.5 ${
          isLight ? 'bg-[#ecfdf5] border-[#a7f3d0]' : 'bg-[#0a2318] border-[#00c076]/30'
        }`}>
          <div className="flex items-center justify-between">
            <div className={`flex items-center space-x-1 text-[11px] font-medium truncate ${
              isLight ? 'text-[#065f46]' : 'text-[#34d399]'
            }`}>
              <span className="w-1.5 h-1.5 rounded-full bg-[#00c076] animate-pulse flex-shrink-0" />
              <span className="truncate font-bold">Stoch(10,5,5) &amp; PSAR</span>
            </div>
            <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ml-1 flex-shrink-0 ${
              isLight ? 'bg-[#bbf7d0] text-[#065f46]' : 'bg-[#00c076]/20 text-[#86efac]'
            }`}>
              {allSignalStocks.length} Sinyal
            </span>
          </div>

          {/* Filter Mode Sub-Tabs: GC 0-2h vs Pas Dead Cross vs Semua */}
          <div className="grid grid-cols-3 gap-1 pt-0.5">
            <button
              onClick={() => setScreenerFilter('gc_only')}
              className={`py-1 px-1 text-[9.5px] rounded transition-all font-semibold flex items-center justify-center gap-0.5 ${
                screenerFilter === 'gc_only'
                  ? 'bg-[#00c076] text-black shadow-sm font-bold'
                  : isLight
                    ? 'bg-[#d1fae5] text-[#065f46] hover:bg-[#a7f3d0]'
                    : 'bg-[#14231b] text-[#82b89a] hover:bg-[#1a3325]'
              }`}
              title="Baru Golden Cross (0h) s/d kelewat maksimal 2 hari saja (0, 1, 2 hari) &amp; PSAR Hijau"
            >
              <span>★ GC 0-2h</span>
              <span className="text-[8.5px] opacity-90 font-mono">({gcStocks.length})</span>
            </button>
            <button
              onClick={() => setScreenerFilter('dc_only')}
              className={`py-1 px-1 text-[9.5px] rounded transition-all font-semibold flex items-center justify-center gap-0.5 ${
                screenerFilter === 'dc_only'
                  ? 'bg-[#ef4444] text-white shadow-sm font-bold'
                  : isLight
                    ? 'bg-[#fee2e2] text-[#991b1b] hover:bg-[#fecaca]'
                    : 'bg-[#261414] text-[#fca5a5] hover:bg-[#3b1c1c]'
              }`}
              title="Tepat pas Dead Cross hari ini (0 hari), tidak boleh lebih &amp; tidak boleh kurang"
            >
              <span>⚠ Pas DC</span>
              <span className="text-[8.5px] opacity-90 font-mono">({dcStocks.length})</span>
            </button>
            <button
              onClick={() => setScreenerFilter('all_signals')}
              className={`py-1 px-1 text-[9.5px] rounded transition-all font-semibold flex items-center justify-center gap-0.5 ${
                screenerFilter === 'all_signals'
                  ? 'bg-[#2563eb] text-white shadow-sm font-bold'
                  : isLight
                    ? 'bg-[#e0e7ff] text-[#3730a3] hover:bg-[#c7d2fe]'
                    : 'bg-[#17202d] text-[#889cb5] hover:bg-[#1f2d40]'
              }`}
              title="Tampilkan semua sinyal (GC 0-2 hari + Pas Dead Cross)"
            >
              <span>Semua</span>
              <span className="text-[8.5px] opacity-90 font-mono">({allSignalStocks.length})</span>
            </button>
          </div>

          <div className="flex items-center justify-between pt-0.5 text-[9.5px]">
            <span className={`truncate ${isLight ? 'text-[#047857]' : 'text-[#8ba298]'}`}>
              {screenerFilter === 'gc_only' && 'Menampilkan GC baru & max 2 hari lalu'}
              {screenerFilter === 'dc_only' && 'Menampilkan tepat pas Dead Cross hari ini'}
              {screenerFilter === 'all_signals' && 'Menampilkan GC (0-2h) & Pas DC (0h)'}
              {screenerFilter === 'all' && 'Menampilkan seluruh saham Universe'}
            </span>
            <button
              onClick={() => setScreenerFilter(screenerFilter === 'all' ? 'all_signals' : 'all')}
              className="text-[#2563eb] hover:underline flex-shrink-0 ml-1 font-medium"
            >
              {screenerFilter === 'all' ? 'Kembali' : 'Cek Universe'}
            </button>
          </div>
        </div>
      ) : selectedScreener ? (
        <div className={`px-2.5 py-2 border-b flex items-center justify-between ${
          isLight ? 'bg-[#eff6ff] border-[#bfdbfe]' : 'bg-[#0e1726] border-[#2563eb]/30'
        }`}>
          <div className={`flex items-center space-x-1.5 text-[11px] font-medium truncate ${
            isLight ? 'text-[#1d4ed8]' : 'text-[#93c5fd]'
          }`}>
            <span className="w-1.5 h-1.5 rounded-full bg-[#3b82f6] animate-pulse flex-shrink-0" />
            <span className="truncate font-bold">{selectedScreener}</span>
          </div>
          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ml-1 flex-shrink-0 ${
            isLight ? 'bg-[#dbeafe] text-[#1e40af]' : 'bg-[#1d4ed8]/30 text-[#93c5fd]'
          }`}>
            {baseStocks.filter(s => s.symbol !== 'IHSG').length} Saham
          </span>
        </div>
      ) : (
        filteredStocks.length === 1 && filteredStocks[0].symbol === 'IHSG' && (
          <div className={`px-2.5 py-2 border-b text-[11px] leading-tight ${
            isLight ? 'bg-[#f8fafc] border-[#e2e8f0] text-[#475569]' : 'bg-[#121820] border-[#1c2430] text-[#8a99a8]'
          }`}>
            <span>Gunakan menu <strong className={isLight ? 'text-[#0f172a]' : 'text-white'}>Choose Screner</strong> di atas untuk menampilkan hasil screening saham sesuai kriteria.</span>
          </div>
        )
      )}

      {/* Stock List Items */}
      <div className={`flex-1 overflow-y-auto divide-y ${
        isLight ? 'divide-[#f1f5f9]' : 'divide-[#18202b]/60'
      }`}>
        {filteredStocks.length === 0 ? (
          <div className={`p-4 text-center text-xs ${isLight ? 'text-[#94a3b8]' : 'text-[#627182]'}`}>
            Tidak ada saham ditemukan
          </div>
        ) : (
          filteredStocks.map((stock) => {
            const isSelected = activeStock.symbol === stock.symbol;
            const isBullish = stock.change >= 0;
            const isBearish = stock.change < 0;

            return (
              <div
                key={stock.symbol}
                onClick={() => onSelectStock(stock)}
                className={`group px-2.5 py-2 cursor-pointer flex items-center justify-between transition-colors ${
                  isSelected
                    ? isLight
                      ? 'bg-[#f1f5f9] border-l-2 border-[#00a86b]'
                      : 'bg-[#192433] border-l-2 border-[#00c076]'
                    : isLight
                      ? 'hover:bg-[#f8fafc]'
                      : 'hover:bg-[#151c26]'
                }`}
              >
                {/* Left column: Badge & Symbol Info */}
                <div className="flex items-center space-x-2 min-w-0">
                  <div
                    className={`w-7 h-7 rounded flex items-center justify-center text-[10px] font-bold flex-shrink-0 shadow-sm ${
                      stock.symbol === 'IHSG'
                        ? 'bg-[#3b82f6]/20 text-[#2563eb] border border-[#3b82f6]/40'
                        : stock.deadCrossDays === 0
                        ? 'bg-[#ef4444] text-white border border-[#f87171]'
                        : stock.isDeadCross
                        ? 'bg-[#ef4444]/15 text-[#dc2626] border border-[#ef4444]/30'
                        : stock.stochCrossDays === 0
                        ? 'bg-[#1d4ed8] text-white border border-[#3b82f6]'
                        : stock.stochCrossDays !== undefined && stock.stochCrossDays <= 2
                        ? isLight
                          ? 'bg-[#dcfce7] text-[#15803d] border border-[#86efac]'
                          : 'bg-[#00c076]/25 text-[#34d399] border border-[#00c076]/50'
                        : isLight
                          ? 'bg-[#f1f5f9] text-[#475569] border border-[#cbd5e1]'
                          : 'bg-[#182330] text-[#a0aec0] border border-[#2d3748]'
                    }`}
                  >
                    {stock.symbol === 'IHSG' ? 'IDX' : stock.symbol.slice(0, 2)}
                  </div>

                  <div className="flex flex-col min-w-0">
                    <div className="flex items-center space-x-1">
                      <span className={`font-bold text-[13px] tracking-wide ${
                        isLight ? 'text-[#0f172a]' : 'text-white'
                      }`}>
                        {stock.symbol}
                      </span>
                      <RotateCw className="w-2.5 h-2.5 text-[#94a3b8] opacity-0 group-hover:opacity-100 transition-opacity" />
                      
                      {stock.isLQ45 && (
                        <span className={`text-[9px] font-semibold px-1 rounded-[2px] leading-none ${
                          isLight ? 'bg-[#f1f5f9] text-[#475569] border border-[#e2e8f0]' : 'bg-[#1e293b] text-[#94a3b8]'
                        }`}>
                          LQ45
                        </span>
                      )}

                      {/* Technical Status Badges */}
                      {stock.deadCrossDays === 0 ? (
                        <span className="bg-[#ef4444] text-white border border-[#fca5a5] text-[8.5px] font-bold px-1 py-0.5 rounded leading-none flex items-center shadow-sm animate-pulse">
                          ⚠ PAS DC
                        </span>
                      ) : stock.isDeadCross && stock.deadCrossDays !== undefined && stock.deadCrossDays > 0 ? (
                        <span className={`border text-[8px] font-medium px-1 rounded-[2px] leading-none ${
                          isLight ? 'bg-[#fee2e2] text-[#991b1b] border-[#fca5a5]' : 'bg-[#3b1616] text-[#f87171] border-[#ef4444]/30'
                        }`}>
                          DC {stock.deadCrossDays}h
                        </span>
                      ) : stock.stochCrossDays === 0 ? (
                        <span className="bg-[#1d4ed8] border border-[#60a5fa] text-white text-[8.5px] font-bold px-1 rounded leading-none shadow-sm">
                          ★ BARU GC
                        </span>
                      ) : stock.stochCrossDays !== undefined && stock.stochCrossDays > 0 && stock.stochCrossDays <= 2 ? (
                        <span className={`border text-[8.5px] font-medium px-1 rounded leading-none ${
                          isLight ? 'bg-[#dcfce7] text-[#166534] border-[#86efac]' : 'bg-[#0f2e22] text-[#34d399] border-[#10b981]/40'
                        }`}>
                          GC +{stock.stochCrossDays}h
                        </span>
                      ) : null}
                    </div>

                    <span className={`text-[11px] truncate max-w-[130px] leading-tight ${
                      isLight ? 'text-[#64748b]' : 'text-[#8292a4]'
                    }`}>
                      {stock.name}
                    </span>

                    {/* Stochastic & PSAR Values Indicator */}
                    {stock.stochK !== undefined && stock.stochD !== undefined && (
                      <div className="flex items-center space-x-1 mt-0.5 text-[9px] font-mono leading-none">
                        <span className={stock.stochK > stock.stochD ? (isLight ? 'text-[#16a34a] font-bold' : 'text-[#34d399] font-bold') : 'text-[#ef4444]'}>
                          K:{stock.stochK}
                        </span>
                        <span className="text-[#94a3b8]">/</span>
                        <span className="text-[#2563eb]">
                          D:{stock.stochD}
                        </span>
                        {stock.psar && (
                          <span className={`ml-1 font-semibold flex items-center ${stock.psarBullish ? (isLight ? 'text-[#16a34a]' : 'text-[#00c076]') : 'text-[#ef4444]'}`}>
                            <span className={`w-1.5 h-1.5 rounded-full inline-block mr-0.5 ${stock.psarBullish ? 'bg-[#16a34a]' : 'bg-[#ef4444]'}`} />
                            {stock.psarBullish ? 'HOLD' : 'BUANG'}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Right column: Price & Change */}
                <div className="flex flex-col items-end flex-shrink-0">
                  <span className={`font-bold text-[13px] ${isLight ? 'text-[#0f172a]' : 'text-[#f0f4f8]'}`}>
                    {stock.symbol === 'IHSG'
                      ? stock.price.toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                      : stock.price.toLocaleString('id-ID')}
                  </span>
                  <div
                    className={`flex items-center text-[11px] font-medium ${
                      isBearish
                        ? 'text-[#eb5757]'
                        : isBullish && stock.change > 0
                        ? isLight ? 'text-[#16a34a]' : 'text-[#00c076]'
                        : 'text-[#94a3b8]'
                    }`}
                  >
                    {isBullish && stock.change > 0 && <TrendingUp className="w-2.5 h-2.5 mr-0.5 inline" />}
                    {isBearish && <TrendingDown className="w-2.5 h-2.5 mr-0.5 inline" />}
                    {stock.apiData ? (
                      <span className="font-bold">
                        <span className="mr-1 text-[9px] opacity-70">
                          {stock.apiData.Score !== undefined ? `Sc:${stock.apiData.Score}` : (stock.apiData.age !== undefined ? `${stock.apiData.age}b` : '')}
                        </span>
                        {stock.change > 0 ? '+' : ''}
                        {stock.changePercent.toFixed(2)}%
                      </span>
                    ) : (
                      <span>
                        {stock.change > 0 ? '+' : ''}
                        {stock.changePercent.toFixed(2)}%
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Bottom Mini Status */}
      <div className={`p-2 border-t flex items-center justify-between text-[11px] ${
        isLight ? 'bg-[#f8fafc] border-[#e2e8f0] text-[#64748b]' : 'bg-[#0c1015] border-[#1c2430] text-[#6b7b8c]'
      }`}>
        <span>Total: {filteredStocks.length}</span>
        <span className={`font-mono text-[10px] font-bold ${isLight ? 'text-[#16a34a]' : 'text-[#00c076]'}`}>IDX LIVE</span>
      </div>
    </div>
  );
};
