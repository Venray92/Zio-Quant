import React, { useState, useEffect } from 'react';
import { ApiScreenerItem } from '../types';
import { RefreshCw, TrendingUp, Activity, AlertTriangle, ArrowRight, Settings } from 'lucide-react';

interface ScreenerViewProps {
  onSelectStock: (symbol: string, apiData: ApiScreenerItem) => void;
  defaultTab?: 'stoch-psar' | 'rsi-pattern';
}

export const ScreenerView: React.FC<ScreenerViewProps> = ({ onSelectStock, defaultTab = 'stoch-psar' }) => {
  const [activeTab, setActiveTab] = useState<'stoch-psar' | 'rsi-pattern'>(defaultTab);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ApiScreenerItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  // State for user-configurable API URL
  const [apiUrl, setApiUrl] = useState<string>(
    localStorage.getItem('ZIO_API_URL') || 'https://hunter-snazzy-sandpaper.ngrok-free.dev'
  );

  const fetchScreenerData = async (endpoint: string, type: 'stoch-psar' | 'rsi-pattern') => {
    setLoading(true);
    setError(null);
    try {
      const baseUrl = apiUrl.endsWith('/') ? apiUrl.slice(0, -1) : apiUrl;
      const response = await fetch(`${baseUrl}${endpoint}`, {
        headers: {
          "ngrok-skip-browser-warning": "true"
        }
      });
      
      if (!response.ok) {
        throw new Error(`Gagal mengambil data dari API (${response.status})`);
      }
      
      const jsonData = await response.json();
      
      let mappedData: ApiScreenerItem[] = [];

      if (type === 'stoch-psar') {
        // Handle nested JSON for Stoch-PSAR format: {"golden_cross": [...], "dead_cross": [...]}
        if (jsonData.golden_cross && Array.isArray(jsonData.golden_cross)) {
          const gcData = jsonData.golden_cross.map((item: any) => ({
            ...item,
            sourceScreener: type,
            groupName: 'Golden Cross (Buy)',
          }));
          mappedData = [...mappedData, ...gcData];
        }
        if (jsonData.dead_cross && Array.isArray(jsonData.dead_cross)) {
          const dcData = jsonData.dead_cross.map((item: any) => ({
            ...item,
            sourceScreener: type,
            groupName: 'Dead Cross (Sell/Exit)',
          }));
          mappedData = [...mappedData, ...dcData];
        }
        // Fallback if it's a flat array
        if (mappedData.length === 0 && Array.isArray(jsonData)) {
           mappedData = jsonData.map((item: any) => ({
             ...item,
             sourceScreener: type
           }));
        }
      } else {
        // Assume flat array for RSI Pattern for now
        if (Array.isArray(jsonData)) {
          mappedData = jsonData.map((item: any) => ({
            ...item,
            sourceScreener: type
          }));
        }
      }

      setData(mappedData);
    } catch (err: any) {
      console.error(err);
      setError(`Gagal terhubung ke API Python (${err.message}). Pastikan URL API benar dan CORS diaktifkan.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setActiveTab(defaultTab);
  }, [defaultTab]);

  useEffect(() => {
    if (activeTab === 'stoch-psar') {
      fetchScreenerData('/api/screener/stoch-psar', 'stoch-psar');
    } else {
      fetchScreenerData('/api/screener/rsi-pattern', 'rsi-pattern');
    }
  }, [activeTab]);

  const handleSaveApiUrl = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('ZIO_API_URL', apiUrl);
    // Re-fetch data with new URL
    if (activeTab === 'stoch-psar') {
      fetchScreenerData('/api/screener/stoch-psar', 'stoch-psar');
    } else {
      fetchScreenerData('/api/screener/rsi-pattern', 'rsi-pattern');
    }
  };

  const [isConfigOpen, setIsConfigOpen] = useState(false);

  return (
    <div className="flex flex-col h-full bg-[#0e1217] text-[#e1e7ec]">
      {/* Header Tabs */}
      <div className="flex items-center space-x-1 p-3 border-b border-[#1c2430]">
        <button
          onClick={() => setActiveTab('stoch-psar')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
            activeTab === 'stoch-psar'
              ? 'bg-[#00c076]/10 text-[#00c076] border border-[#00c076]/20'
              : 'text-[#8b9cb0] hover:text-white hover:bg-[#1a212b]'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Stoch - PSAR</span>
        </button>
        <button
          onClick={() => setActiveTab('rsi-pattern')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
            activeTab === 'rsi-pattern'
              ? 'bg-[#3b82f6]/10 text-[#3b82f6] border border-[#3b82f6]/20'
              : 'text-[#8b9cb0] hover:text-white hover:bg-[#1a212b]'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          <span>RSI Divergence</span>
        </button>
        
        <div className="flex-1"></div>
        
        <button 
          onClick={() => setIsConfigOpen(!isConfigOpen)}
          className={`flex items-center justify-center p-2 rounded-lg mr-2 transition-colors ${
            isConfigOpen ? 'bg-[#00c076]/10 text-[#00c076]' : 'bg-[#1a212b] hover:bg-[#252f3d] text-[#8b9cb0] hover:text-white'
          }`}
          title="Konfigurasi URL API Python"
        >
          <Settings className="w-4 h-4" />
        </button>

        <button 
          onClick={() => {
            if (activeTab === 'stoch-psar') fetchScreenerData('/api/screener/stoch-psar', 'stoch-psar');
            else fetchScreenerData('/api/screener/rsi-pattern', 'rsi-pattern');
          }}
          className="flex items-center justify-center p-2 rounded-lg bg-[#1a212b] hover:bg-[#252f3d] text-[#8b9cb0] hover:text-white transition-colors"
          title="Refresh Data"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* API Config Panel */}
      {isConfigOpen && (
        <div className="p-3 bg-[#13171e] border-b border-[#1c2430]">
          <form onSubmit={handleSaveApiUrl} className="flex items-center space-x-3">
            <div className="flex-1">
              <label className="block text-[10px] font-bold text-[#8b9cb0] uppercase mb-1">Python API URL (FastAPI / Ngrok)</label>
              <input
                type="url"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="https://xxxx.ngrok-free.dev"
                className="w-full bg-[#0c0e12] border border-[#2c3746] rounded-md px-3 py-1.5 text-sm text-white focus:outline-none focus:border-[#00c076] transition-colors placeholder-[#4b5563]"
                required
              />
            </div>
            <button
              type="submit"
              className="mt-4 px-4 py-1.5 bg-[#00c076] hover:bg-[#00a86b] text-black font-semibold rounded-md text-sm transition-colors"
            >
              Simpan & Reload
            </button>
          </form>
          <p className="text-xs text-[#8b9cb0] mt-2">
            Tip: Jika Web ini diakses lewat internet (Cloud/AI Studio) sedangkan Python jalan di laptop Anda, Anda wajib menggunakan <strong>Ngrok</strong> (contoh: <em>https://xxxx.ngrok.app</em>) agar web bisa mengakses localhost Anda, atau <em>Disable Web Security (CORS)</em> di browser Anda sementara.
          </p>
        </div>
      )}

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-4 relative">
        {error ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center text-red-400">
              <AlertTriangle className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white mb-1">Koneksi API Terputus / Diblokir Browser</h3>
              <p className="text-[#8b9cb0] text-sm max-w-md">{error}</p>
            </div>
            <div className="bg-[#1a212b] border border-[#2c3746] rounded-lg p-4 text-left text-sm text-[#8b9cb0] max-w-lg mt-4 font-mono">
              <p className="text-white mb-2 font-sans font-medium">Langkah perbaikan:</p>
              <ol className="list-decimal pl-4 space-y-1 font-sans">
                <li>Klik tombol <Settings className="w-3 h-3 inline mx-1" /> di pojok kanan atas.</li>
                <li>Ubah <code>http://127.0.0.1:8000</code> menjadi link <strong>Ngrok HTTPS</strong> (misal: <em>https://1a2b3c.ngrok.app</em>) karena browser memblokir HTTPS ke HTTP.</li>
                <li>Pastikan FastAPI mengizinkan CORS.</li>
              </ol>
            </div>
          </div>
        ) : loading ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-8 h-8 border-2 border-[#00c076] border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-[#8b9cb0] text-sm font-medium animate-pulse">Menjalankan screener Python...</p>
          </div>
        ) : data.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-16 h-16 bg-[#1a212b] rounded-full flex items-center justify-center text-[#8b9cb0] mb-4">
              <Activity className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Tidak Ada Sinyal</h3>
            <p className="text-[#8b9cb0] text-sm">Belum ada saham yang memenuhi kriteria screener saat ini.</p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-[#2c3746]">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#13171e] text-[10px] uppercase tracking-wider text-[#8b9cb0]">
                  <th className="px-4 py-3 font-semibold border-b border-[#2c3746]">Ticker</th>
                  <th className="px-4 py-3 font-semibold border-b border-[#2c3746]">Harga</th>
                  {activeTab === 'stoch-psar' && <th className="px-4 py-3 font-semibold border-b border-[#2c3746]">Status</th>}
                  {activeTab === 'rsi-pattern' && <th className="px-4 py-3 font-semibold border-b border-[#2c3746]">Pattern</th>}
                  {activeTab === 'stoch-psar' && <th className="px-4 py-3 font-semibold border-b border-[#2c3746]">Score</th>}
                  {activeTab === 'rsi-pattern' && <th className="px-4 py-3 font-semibold border-b border-[#2c3746]">Age</th>}
                  <th className="px-4 py-3 font-semibold border-b border-[#2c3746]">Buy Area</th>
                  <th className="px-4 py-3 font-semibold border-b border-[#2c3746] text-red-400">Stop Loss</th>
                  <th className="px-4 py-3 font-semibold border-b border-[#2c3746] text-emerald-400">Target Profit</th>
                  <th className="px-4 py-3 font-semibold border-b border-[#2c3746]">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item, idx) => {
                  const ticker = item.Ticker || item.ticker || 'UNKNOWN';
                  const price = item.Harga || item.price || 0;
                  const score = item.Score !== undefined ? item.Score : item.score;
                  const detailSignal = item["Detail Signal"] || item.pattern || item.status || '-';
                  const action = item.Action || '-';
                  const tpData = item.TradePlan || {};
                  
                  // For displaying Trade Plan in table
                  const buyArea = item.buy_area || tpData.Entry || '-';
                  const stopLoss = item.stop_loss || tpData.StopLoss || tpData.ExitPrice || '-';
                  const targetProfit = item.target_profit || item.target_profit_1 || tpData.TakeProfit || '-';
                  
                  // Check if we need to render a group header
                  const showGroupHeader = idx === 0 || data[idx - 1].groupName !== item.groupName;

                  return (
                    <React.Fragment key={ticker + idx + (item.groupName || '')}>
                      {showGroupHeader && item.groupName && (
                        <tr className="bg-[#18212c]">
                          <td colSpan={8} className="px-4 py-2 text-xs font-bold text-white uppercase tracking-widest border-b border-[#2c3746]">
                            <div className="flex items-center space-x-2">
                              {item.groupName.includes('Buy') ? (
                                <div className="w-2 h-2 rounded-full bg-[#00c076] shadow-[0_0_8px_#00c076]" />
                              ) : (
                                <div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_#ef4444]" />
                              )}
                              <span>{item.groupName}</span>
                            </div>
                          </td>
                        </tr>
                      )}
                      <tr 
                        className="border-b border-[#1c2430] hover:bg-[#1a212b] transition-colors cursor-pointer group"
                        onClick={() => onSelectStock(ticker, item)}
                      >
                        <td className="px-4 py-3">
                          <span className="font-bold text-white bg-[#252f3d] px-2 py-1 rounded">{ticker}</span>
                        </td>
                        <td className="px-4 py-3 font-mono font-medium">{price.toLocaleString('id-ID')}</td>
                        
                        {/* Status/Pattern Column */}
                        {activeTab === 'stoch-psar' && (
                          <td className="px-4 py-3 text-xs">
                            <span className={`px-2 py-1 rounded border whitespace-nowrap ${action.includes('BELI') ? 'bg-[#00c076]/10 text-[#00c076] border-[#00c076]/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                              {detailSignal}
                            </span>
                          </td>
                        )}
                        {activeTab === 'rsi-pattern' && (
                          <td className="px-4 py-3 text-xs">
                            <span className="px-2 py-1 rounded bg-[#3b82f6]/10 text-[#3b82f6] border border-[#3b82f6]/20 whitespace-nowrap">
                              {detailSignal}
                            </span>
                          </td>
                        )}

                        {/* Score/Age Column */}
                        {activeTab === 'stoch-psar' && (
                          <td className={`px-4 py-3 text-sm font-bold ${score !== undefined && score < 0 ? 'text-red-400' : 'text-white'}`}>
                            {score !== undefined ? score : '-'}
                          </td>
                        )}
                        {activeTab === 'rsi-pattern' && (
                          <td className="px-4 py-3 text-sm text-[#8b9cb0]">
                            {item.age !== undefined ? `${item.age} bar` : '-'}
                          </td>
                        )}

                        {/* Trade Plan Columns */}
                        <td className="px-4 py-3 font-mono text-xs">{buyArea}</td>
                        <td className="px-4 py-3 font-mono text-xs text-red-400">
                          {typeof stopLoss === 'number' ? stopLoss.toLocaleString('id-ID') : stopLoss}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-emerald-400">
                          {typeof targetProfit === 'number' ? targetProfit.toLocaleString('id-ID') : targetProfit}
                        </td>
                        
                        {/* Action */}
                        <td className="px-4 py-3">
                          <div className={`flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity text-xs font-semibold ${action.includes('JUAL') ? 'text-red-400' : 'text-[#00c076]'}`}>
                            <span>Trade Plan</span>
                            <ArrowRight className="w-3 h-3" />
                          </div>
                        </td>
                      </tr>
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
