import React from 'react';
import { 
  Settings as SettingsIcon, 
  Sun, 
  Moon, 
  X, 
  Check, 
  Monitor, 
  Sparkles,
  Sliders,
  Eye
} from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  appTheme: 'dark' | 'light';
  onSelectAppTheme: (theme: 'dark' | 'light') => void;
  chartTheme: 'dark' | 'cream';
  onSelectChartTheme: (theme: 'dark' | 'cream') => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  appTheme,
  onSelectAppTheme,
  chartTheme,
  onSelectChartTheme,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="absolute inset-0" onClick={onClose} />

      {/* Modal Dialog */}
      <div 
        className="relative w-full max-w-lg bg-[#0c1016] border border-[#1e2736] rounded-2xl shadow-2xl flex flex-col overflow-hidden z-10"
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-5 py-4 bg-[#101620] border-b border-[#1c2432] flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#eab308] to-[#ca8a04] text-black flex items-center justify-center shadow-md">
              <SettingsIcon className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-black text-white tracking-wide">
                Pengaturan Tampilan
              </h2>
              <p className="text-xs text-[#8094ab]">
                Sesuaikan tema warna latar belakang gelap atau terang.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-[#182230] hover:bg-[#28364a] text-[#8ea3ba] hover:text-white transition-colors cursor-pointer"
            title="Tutup (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Area */}
        <div className="p-5 space-y-6 bg-[#0a0d12]">
          
          {/* SECTION 1: TEMA UTAMA APLIKASI (GELAP / TERANG) */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Eye className="w-4 h-4 text-[#eab308]" />
              <label className="text-xs font-bold text-[#b5c7da] uppercase tracking-wider">
                Tema Background Aplikasi
              </label>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {/* Dark Theme Button */}
              <button
                onClick={() => onSelectAppTheme('dark')}
                className={`p-4 rounded-xl border flex flex-col items-center text-center space-y-2.5 transition-all cursor-pointer relative overflow-hidden group ${
                  appTheme === 'dark'
                    ? 'bg-[#121924] border-[#00c076] ring-1 ring-[#00c076] shadow-lg'
                    : 'bg-[#0f141c] border-[#1d2634] hover:border-[#2d3a4d]'
                }`}
              >
                <div className="w-10 h-10 rounded-full bg-[#182332] text-[#eab308] flex items-center justify-center border border-[#26374f] shadow">
                  <Moon className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-black text-white flex items-center justify-center space-x-1">
                    <span>Tema Gelap (Dark)</span>
                    {appTheme === 'dark' && <Check className="w-4 h-4 text-[#00c076]" />}
                  </div>
                  <p className="text-[11px] text-[#71859b] mt-0.5">
                    Terminal pro, nyaman di mata saat malam hari.
                  </p>
                </div>
              </button>

              {/* Light Theme Button */}
              <button
                onClick={() => onSelectAppTheme('light')}
                className={`p-4 rounded-xl border flex flex-col items-center text-center space-y-2.5 transition-all cursor-pointer relative overflow-hidden group ${
                  appTheme === 'light'
                    ? 'bg-[#18212e] border-[#eab308] ring-1 ring-[#eab308] shadow-lg'
                    : 'bg-[#0f141c] border-[#1d2634] hover:border-[#2d3a4d]'
                }`}
              >
                <div className="w-10 h-10 rounded-full bg-[#f8fafc] text-[#ca8a04] flex items-center justify-center border border-[#e2e8f0] shadow">
                  <Sun className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-black text-white flex items-center justify-center space-x-1">
                    <span>Tema Terang (Light)</span>
                    {appTheme === 'light' && <Check className="w-4 h-4 text-[#eab308]" />}
                  </div>
                  <p className="text-[11px] text-[#71859b] mt-0.5">
                    Kontras tajam & cerah untuk ruangan terang.
                  </p>
                </div>
              </button>
            </div>
          </div>

          {/* SECTION 2: TEMA KANVAS GRAFIK (CHART) */}
          <div className="space-y-3 pt-3 border-t border-[#1a222e]">
            <div className="flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-[#38bdf8]" />
              <label className="text-xs font-bold text-[#b5c7da] uppercase tracking-wider">
                Palet Warna Chart
              </label>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => onSelectChartTheme('dark')}
                className={`p-3 rounded-xl border flex items-center space-x-3 transition-all cursor-pointer ${
                  chartTheme === 'dark'
                    ? 'bg-[#121924] border-[#38bdf8] text-white font-bold'
                    : 'bg-[#0f141c] border-[#1d2634] text-[#869ab0] hover:text-white'
                }`}
              >
                <div className="w-6 h-6 rounded bg-[#0b0e14] border border-[#233144] flex-shrink-0" />
                <div className="text-left text-xs">
                  <div className="font-bold">Modern Onyx Dark</div>
                  <div className="text-[10px] text-[#6d7f94]">Standar TradingView</div>
                </div>
              </button>

              <button
                onClick={() => onSelectChartTheme('cream')}
                className={`p-3 rounded-xl border flex items-center space-x-3 transition-all cursor-pointer ${
                  chartTheme === 'cream'
                    ? 'bg-[#121924] border-[#ecd88d] text-white font-bold'
                    : 'bg-[#0f141c] border-[#1d2634] text-[#869ab0] hover:text-white'
                }`}
              >
                <div className="w-6 h-6 rounded bg-[#fff9e6] border border-[#e4d49a] flex-shrink-0" />
                <div className="text-left text-xs">
                  <div className="font-bold">Classic Cream</div>
                  <div className="text-[10px] text-[#6d7f94]">Gaya Khas Stockbit</div>
                </div>
              </button>
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 bg-[#101620] border-t border-[#1c2432] flex items-center justify-between flex-shrink-0">
          <span className="text-[11px] text-[#71859c]">Pengaturan otomatis tersimpan di preferensi browser Anda.</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-[#00c076] hover:bg-[#00db87] text-black font-extrabold text-xs transition-all shadow cursor-pointer"
          >
            Selesai
          </button>
        </div>
      </div>
    </div>
  );
};
