import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check, SlidersHorizontal, Activity } from 'lucide-react';
import { Logo } from './Logo';

interface HeaderProps {
  title?: string;
  selectedScreener?: string | null;
  onSelectScreener?: (screener: string | null) => void;
  onReloadHome?: () => void;
  theme?: 'dark' | 'light';
}

export const Header: React.FC<HeaderProps> = ({
  title = 'Zio - Screaner',
  selectedScreener = null,
  onSelectScreener,
  onReloadHome,
  theme = 'dark',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentScreener, setCurrentScreener] = useState<string | null>(selectedScreener);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setCurrentScreener(selectedScreener);
  }, [selectedScreener]);

  const screenerOptions = [
    {
      id: 'stoch-psar',
      label: '1. Stoch - Psar',
      description: 'Stoch (10,5,5) GC (0-2 Hari) & Pas Dead Cross (0 Hari)',
    },
    {
      id: 'rsi-pattern',
      label: '2. RSI + Pattern',
      description: 'RSI Divergence & Chart Pattern Breakout / Reversal',
    },
  ];

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (label: string) => {
    const nextVal = currentScreener === label ? null : label;
    setCurrentScreener(nextVal);
    onSelectScreener?.(nextVal);
    setIsOpen(false);
  };

  const isLight = theme === 'light';

  return (
    <header
      className={`h-11 border-b px-3.5 flex items-center justify-between select-none z-30 transition-colors duration-200 ${
        isLight ? 'bg-white border-[#e2e8f0] text-[#0f172a]' : 'bg-[#0e1217] border-[#1d242e] text-[#e1e7ec]'
      }`}
    >
      {/* Left: Brand with Lightning Icon + Title */}
      <div className="flex items-center space-x-2.5">
        <button
          onClick={onReloadHome}
          className="flex-shrink-0 transition-all hover:scale-105 active:scale-95 cursor-pointer"
          title="Reload / Home (Klik untuk reset kembali ke awal)"
          aria-label="Reload Home"
        >
          <Logo size="sm" />
        </button>
        <button
          onClick={onReloadHome}
          className={`font-extrabold text-[15px] tracking-wide hover:text-[#00c076] transition-colors text-left cursor-pointer ${
            isLight ? 'text-[#0f172a]' : 'text-white'
          }`}
          title="Reload / Home (Klik untuk reset kembali ke awal)"
        >
          {title}
        </button>
      </div>

      {/* Right End: Dynamic 'Choose Screener' Dropdown */}
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-semibold border transition-all duration-150 shadow-sm active:scale-[0.98] ${
            isOpen
              ? isLight
                ? 'bg-[#e2e8f0] border-[#00c076] text-[#0f172a] ring-1 ring-[#00c076]/40'
                : 'bg-[#18202c] border-[#00c076] text-white ring-1 ring-[#00c076]/40'
              : currentScreener
              ? isLight
                ? 'bg-[#e6f4ea] border-[#00c076] text-[#00875a]'
                : 'bg-[#0e271c] border-[#00c076] text-[#00c076]'
              : isLight
                ? 'bg-[#f8fafc] border-[#cbd5e1] text-[#334155] hover:text-[#0f172a] hover:bg-[#f1f5f9]'
                : 'bg-[#12161e] border-[#222b37] text-[#cbd5e1] hover:text-white hover:bg-[#19212c]'
          }`}
          aria-haspopup="true"
          aria-expanded={isOpen}
        >
          <SlidersHorizontal className="w-3.5 h-3.5 text-[#00c076]" />
          <span className="tracking-wide">
            {currentScreener ? currentScreener : 'Choose Screener'}
          </span>
          <ChevronDown
            className={`w-3.5 h-3.5 transition-transform duration-200 ${
              isOpen ? 'rotate-180 text-[#00c076]' : isLight ? 'text-[#64748b]' : 'text-[#8b98a5]'
            }`}
          />
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div
            className={`absolute right-0 top-full mt-1.5 w-64 border rounded-lg shadow-2xl py-1.5 z-50 animate-in fade-in slide-in-from-top-1 duration-150 ${
              isLight ? 'bg-white border-[#cbd5e1] text-[#0f172a]' : 'bg-[#11161e] border-[#232c3a] text-white'
            }`}
          >
            <div
              className={`px-3 py-1.5 border-b flex items-center justify-between text-[10px] font-bold tracking-wider uppercase ${
                isLight ? 'border-[#e2e8f0] text-[#64748b]' : 'border-[#1c2430] text-[#64748b]'
              }`}
            >
              <span>Preset Screener</span>
              <span className="text-[#00c076]">{screenerOptions.length} Available</span>
            </div>

            <div className="p-1">
              {screenerOptions.map((opt) => {
                const isSelected = currentScreener === opt.label;
                return (
                  <button
                    key={opt.id}
                    onClick={() => handleSelect(opt.label)}
                    className={`w-full text-left px-2.5 py-2 rounded-md transition-all flex items-start justify-between group ${
                      isSelected
                        ? isLight
                          ? 'bg-[#e6f4ea] text-[#00875a] border border-[#00c076]'
                          : 'bg-[#0e271c] text-white border border-[#00c076]'
                        : isLight
                          ? 'text-[#334155] hover:bg-[#f1f5f9] hover:text-[#0f172a]'
                          : 'text-[#cbd5e1] hover:bg-[#18212d] hover:text-white'
                    }`}
                  >
                    <div className="flex flex-col">
                      <div className="flex items-center space-x-1.5">
                        <Activity
                          className={`w-3.5 h-3.5 ${
                            isSelected
                              ? 'text-[#00c076]'
                              : isLight
                              ? 'text-[#64748b] group-hover:text-[#00c076]'
                              : 'text-[#8b98a5] group-hover:text-[#00c076]'
                          }`}
                        />
                        <span
                          className={`text-xs font-bold ${
                            isSelected ? 'text-[#00c076]' : isLight ? 'text-[#1e293b]' : 'text-[#e2e8f0]'
                          }`}
                        >
                          {opt.label}
                        </span>
                        {isSelected && (
                          <span className="text-[9px] bg-[#00c076]/20 text-[#00c076] border border-[#00c076]/40 px-1 py-0.5 rounded font-bold">
                            Active
                          </span>
                        )}
                      </div>
                      <span className={`text-[10px] mt-0.5 pl-5 ${isLight ? 'text-[#64748b]' : 'text-[#718096]'}`}>
                        {opt.description}
                      </span>
                    </div>

                    {isSelected && (
                      <div className="w-4 h-4 rounded-full bg-[#00c076] flex items-center justify-center flex-shrink-0 mt-0.5 ml-1 shadow-sm shadow-[#00c076]/40">
                        <Check className="w-3 h-3 text-black stroke-[3]" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
