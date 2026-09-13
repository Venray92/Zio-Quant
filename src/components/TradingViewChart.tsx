import React, { useEffect, useRef, useState } from 'react';
import { Stock } from '../types';
import { RefreshCw, ExternalLink, Maximize2, Sliders, Code2, Copy, Check, Info } from 'lucide-react';
import { PINE_SCRIPT_CODE } from '../data/pineScript';
import { PineScriptModal } from './PineScriptModal';

interface TradingViewChartProps {
  stock: Stock;
  theme: 'dark' | 'cream';
  selectedScreener?: string | null;
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({ stock, theme, selectedScreener }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [key, setKey] = useState(0);
  const [chartMode, setChartMode] = useState<'embed' | 'iframe'>('embed');
  const [isLoading, setIsLoading] = useState(true);
  const [copiedScript, setCopiedScript] = useState(false);
  const [isScriptModalOpen, setIsScriptModalOpen] = useState(false);

  const tvTheme = theme === 'cream' ? 'light' : 'dark';
  const isStochPsarActive = selectedScreener === '1. Stoch - Psar';
  const isRsiPatternActive = selectedScreener === '2. RSI + Pattern';

  const handleCopyScript = () => {
    navigator.clipboard.writeText(PINE_SCRIPT_CODE);
    setCopiedScript(true);
    setTimeout(() => setCopiedScript(false), 2200);
  };

  const currentSymbol = stock.tvSymbol || `IDX:${stock.symbol}`;

  // Studies definition for modern Embed widget
  const studiesList = isStochPsarActive
    ? ['STD;Stochastic', 'STD;PSAR']
    : isRsiPatternActive
    ? ['STD;Relative_Strength_Index']
    : [];

  const studiesOverrides = isStochPsarActive
    ? {
        "stochastic.length": 10,
        "stochastic.smoothK": 5,
        "stochastic.smoothD": 5,
      }
    : {};

  useEffect(() => {
    if (chartMode !== 'embed' || !containerRef.current) return;

    setIsLoading(true);
    containerRef.current.innerHTML = '';

    const widgetContainer = document.createElement('div');
    widgetContainer.className = 'tradingview-widget-container';
    widgetContainer.style.width = '100%';
    widgetContainer.style.height = '100%';

    const widgetInner = document.createElement('div');
    widgetInner.className = 'tradingview-widget-container__widget';
    widgetInner.style.width = '100%';
    widgetInner.style.height = '100%';
    widgetContainer.appendChild(widgetInner);

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.type = 'text/javascript';
    script.async = true;
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: currentSymbol,
      interval: 'D',
      timezone: 'Asia/Jakarta',
      theme: tvTheme,
      style: '1',
      locale: 'id',
      enable_publishing: false,
      allow_symbol_change: true,
      calendar: false,
      hide_top_toolbar: false,
      hide_side_toolbar: false,
      hide_legend: false,
      hide_volume: true,
      save_image: true,
      withdateranges: true,
      details: false,
      hotlist: false,
      support_host: 'https://www.tradingview.com',
      studies: studiesList,
      studies_overrides: Object.keys(studiesOverrides).length > 0 ? studiesOverrides : undefined,
    });

    widgetContainer.appendChild(script);
    containerRef.current.appendChild(widgetContainer);

    // Auto clear loading state after short buffer to prevent perpetual spinner
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1200);

    return () => {
      clearTimeout(timer);
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [currentSymbol, tvTheme, isStochPsarActive, isRsiPatternActive, key, chartMode]);

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  };

  const iframeSettings = {
    symbol: currentSymbol,
    interval: 'D',
    timezone: 'Asia/Jakarta',
    theme: tvTheme,
    style: '1',
    locale: 'id',
    enable_publishing: false,
    allow_symbol_change: true,
    hide_volume: true,
    support_host: 'https://www.tradingview.com',
    ...(studiesList.length > 0 && { studies: studiesList }),
    ...(Object.keys(studiesOverrides).length > 0 && { studies_overrides: studiesOverrides }),
  };

  const iframeUrl = `https://www.tradingview-widget.com/embed-widget/advanced-chart/?locale=id#${encodeURIComponent(JSON.stringify(iframeSettings))}`;

  return (
    <div 
      className={`relative w-full h-full flex flex-col flex-1 overflow-hidden select-none ${
        theme === 'cream' ? 'bg-[#fffdf2]' : 'bg-[#131722]'
      }`}
    >
      {/* Top Banner: Pine Script Indicator Active Bar */}
      {isStochPsarActive && (
        <div className="px-3 py-1.5 bg-[#0a1e16] border-b border-[#00c076]/40 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center space-x-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00c076] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00c076]"></span>
            </span>
            <span className="font-bold text-[#34d399] tracking-wide text-[11.5px]">
              || STOCH + PSAR || HIJAU HOLD MERAH BUANG
            </span>
            <span className="bg-[#10b981]/20 border border-[#10b981]/40 text-[#6ee7b7] text-[10px] px-1.5 py-0.5 rounded font-mono">
              Stoch(10,5,5) + PSAR(0.02, 0.02, 0.20)
            </span>
          </div>

          <div className="flex items-center space-x-2">
            {/* Live Indicator Readout for Active Stock */}
            {stock.stochK !== undefined && stock.stochD !== undefined && (
              <div className="flex items-center space-x-1 text-[11px] font-mono bg-[#11261e] px-2 py-0.5 rounded border border-[#1b4332]">
                <span className="text-[#f87171] font-semibold">%K: {stock.stochK}</span>
                <span className="text-[#8899a6]">|</span>
                <span className="text-[#60a5fa] font-semibold">%D: {stock.stochD}</span>
                {stock.deadCrossDays === 0 ? (
                  <span className="bg-[#ef4444] text-white px-1 py-0.5 rounded text-[10px] font-bold ml-1 animate-pulse">
                    ⚠ PAS Dead Cross
                  </span>
                ) : stock.isDeadCross ? (
                  <span className="text-[#ef4444] font-bold ml-1">▼ Death Cross</span>
                ) : stock.stochCrossDays === 0 ? (
                  <span className="bg-[#1d4ed8] text-white px-1 py-0.5 rounded text-[10px] font-bold ml-1">
                    ★ Baru GC (Hari Ini)
                  </span>
                ) : (
                  <span className="text-[#34d399] font-bold ml-1">
                    ▲ GC +{stock.stochCrossDays}h
                  </span>
                )}
              </div>
            )}

            {stock.psar && (
              <div className="flex items-center space-x-1 text-[11px] font-mono bg-[#11261e] px-2 py-0.5 rounded border border-[#1b4332]">
                <span className="text-[#94a3b8]">PSAR:</span>
                <span className="font-bold text-white">{stock.psar.toLocaleString('id-ID')}</span>
                {stock.psarBullish ? (
                  <span className="text-[#00c076] font-bold flex items-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#00c076] inline-block mr-0.5" />
                    HIJAU HOLD
                  </span>
                ) : (
                  <span className="text-[#ef4444] font-bold flex items-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#ef4444] inline-block mr-0.5" />
                    MERAH BUANG
                  </span>
                )}
              </div>
            )}

            {/* Copy Script Button */}
            <button
              onClick={handleCopyScript}
              className="flex items-center space-x-1 px-2 py-0.5 rounded bg-[#1e2d42] hover:bg-[#2b4162] text-white text-[11px] font-medium border border-[#3b82f6]/40 transition-colors"
              title="Salin kode Pine Script ke Clipboard"
            >
              {copiedScript ? (
                <>
                  <Check className="w-3 h-3 text-[#00c076]" />
                  <span className="text-[#00c076] font-bold">Tersalin!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3 text-[#60a5fa]" />
                  <span>Salin Script</span>
                </>
              )}
            </button>

            {/* View Script Modal Button */}
            <button
              onClick={() => setIsScriptModalOpen(true)}
              className="flex items-center space-x-1 px-2 py-0.5 rounded bg-[#1e2d42] hover:bg-[#2b4162] text-white text-[11px] font-medium border border-[#3b82f6]/40 transition-colors"
              title="Lihat kode Pine Script lengkap"
            >
              <Code2 className="w-3 h-3 text-[#60a5fa]" />
              <span>Lihat Kode</span>
            </button>
          </div>
        </div>
      )}

      {/* Top Banner: RSI + Pattern Screener Banner */}
      {isRsiPatternActive && (
        <div className="px-3 py-1.5 bg-[#0e1726] border-b border-[#2563eb]/40 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center space-x-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#3b82f6] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#3b82f6]"></span>
            </span>
            <span className="font-bold text-[#93c5fd] tracking-wide text-[11.5px]">
              || RSI + PATTERN || DIVERGENCE &amp; REVERSAL
            </span>
            <span className="bg-[#1d4ed8]/20 border border-[#3b82f6]/40 text-[#bfdbfe] text-[10px] px-1.5 py-0.5 rounded font-mono">
              RSI(14) + Chart Pattern Setup
            </span>
          </div>

          <div className="flex items-center space-x-2 text-[11px]">
            <span className="text-[#94a3b8]">Saham Terpilih:</span>
            <span className="font-bold text-white px-2 py-0.5 rounded bg-[#1e293b] border border-[#334155]">
              {stock.symbol} ({stock.sector})
            </span>
          </div>
        </div>
      )}

      {/* Chart Overlay Header Indicator */}
      <div 
        className={`h-7 px-3 flex items-center justify-between border-b text-[11px] ${
          theme === 'cream' 
            ? 'bg-[#fcf8e8] border-[#e8dfc3] text-[#554d38]' 
            : 'bg-[#121620] border-[#1d2432] text-[#8e9eb0]'
        }`}
      >
        <div className="flex items-center space-x-2 overflow-hidden">
          <span className="font-semibold text-white bg-[#00c076] px-1.5 py-0.5 rounded text-[10px] flex-shrink-0">
            REAL-TIME
          </span>
          <span className="font-bold text-[#e1e7ec] truncate">
            {stock.symbol} ({stock.name})
          </span>
          {stock.stochCrossDays !== undefined && (
            <span className="hidden md:inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] bg-[#2563eb]/20 text-[#60a5fa] border border-[#2563eb]/40 font-mono">
              <span>{stock.stochCrossDays === 0 ? '★ Baru Golden Cross (0d)' : `Golden Cross (+${stock.stochCrossDays}d)`}</span>
            </span>
          )}
          {stock.stochK !== undefined && stock.stochD !== undefined && (
            <span className="hidden lg:inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] bg-[#1e293b] text-[#cbd5e1] border border-[#334155] font-mono">
              <span>Stoch (10,5,5): %K {stock.stochK} / %D {stock.stochD}</span>
            </span>
          )}
          {stock.psar && (
            <span className="hidden xl:inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] bg-[#00c076]/15 text-[#00c076] border border-[#00c076]/30 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00c076]" />
              <span>PSAR: {stock.psar.toLocaleString('id-ID')} ({stock.psarBullish ? 'HIJAU HOLD' : 'MERAH BUANG'})</span>
            </span>
          )}
          <span className="hidden 2xl:inline text-[10px] opacity-60">
            {isStochPsarActive ? '1D · IDX · Stoch (10,5,5) & PSAR Aktif' : '1D · IDX · Default Chart (Clean)'}
          </span>
        </div>

        <div className="flex items-center space-x-1.5">
          {/* Toggle between Modern Embed and Direct Iframe */}
          <button
            onClick={() => {
              setChartMode(m => m === 'embed' ? 'iframe' : 'embed');
              setKey(k => k + 1);
            }}
            className="px-2 py-0.5 text-[10px] font-medium rounded bg-[#1e293b] hover:bg-[#334155] text-[#94a3b8] hover:text-white border border-[#334155] transition-colors"
            title="Ganti engine chart jika salah satu mode lambat atau terkendala"
          >
            {chartMode === 'embed' ? 'Mode: Widget' : 'Mode: Direct'}
          </button>

          <a
            href={`https://id.tradingview.com/chart/?symbol=${encodeURIComponent(currentSymbol)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 hover:text-white rounded hover:bg-black/20 transition-colors text-[#94a3b8]"
            title="Buka chart di TradingView tab baru"
          >
            <ExternalLink className="w-3 h-3" />
          </a>

          <button
            onClick={() => {
              setIsLoading(true);
              setKey(k => k + 1);
            }}
            className="p-1 hover:text-white rounded hover:bg-black/20 transition-colors text-[#94a3b8]"
            title="Reload Chart"
          >
            <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin text-[#38bdf8]' : ''}`} />
          </button>

          <button
            onClick={toggleFullscreen}
            className="p-1 hover:text-white rounded hover:bg-black/20 transition-colors text-[#94a3b8]"
            title="Fullscreen Chart"
          >
            <Maximize2 className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Main Chart Frame */}
      <div className="relative flex-1 w-full h-full bg-[#131722]">
        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-[#131722]/80 backdrop-blur-[1px] pointer-events-none transition-opacity duration-300">
            <div className="flex items-center space-x-2 text-xs text-[#38bdf8] font-medium bg-[#0f172a] px-3 py-1.5 rounded border border-[#1e293b] shadow-lg">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#38bdf8]" />
              <span>Memuat Chart TradingView ({currentSymbol})...</span>
            </div>
          </div>
        )}

        {chartMode === 'embed' ? (
          /* Modern TradingView Advanced Real-Time Chart Container */
          <div
            key={`embed-${currentSymbol}-${theme}-${key}`}
            ref={containerRef}
            className="w-full h-full min-h-[400px]"
          />
        ) : (
          /* Direct TradingView Responsive Iframe */
          <iframe
            key={`iframe-${currentSymbol}-${theme}-${key}`}
            title={`TradingView Chart ${stock.symbol}`}
            src={iframeUrl}
            onLoad={() => setIsLoading(false)}
            className="w-full h-full border-0 min-h-[400px]"
            allow="fullscreen; clipboard-read; clipboard-write;"
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
          />
        )}
      </div>

      {/* Pine Script Modal Popup */}
      <PineScriptModal
        isOpen={isScriptModalOpen}
        onClose={() => setIsScriptModalOpen(false)}
      />
    </div>
  );
};
