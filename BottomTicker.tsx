import React, { useState, useEffect } from 'react';
import { Clock, Moon } from 'lucide-react';

interface BottomTickerProps {
  onSelectStockBySymbol?: (symbol: string) => void;
  activeStockSymbol?: string;
}

export const BottomTicker: React.FC<BottomTickerProps> = ({
  onSelectStockBySymbol,
}) => {
  const [timeString, setTimeString] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      // Format 6:48:24 PM
      const formatted = now.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      });
      setTimeString(formatted);
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-6 bg-[#0a0d11] border-t border-[#191f27] px-3 flex items-center justify-between text-[11px] select-none flex-shrink-0 z-20">
      {/* IHSG Fixed Anchor with Price & % */}
      <div 
        onClick={() => onSelectStockBySymbol?.('IHSG')}
        className="flex items-center space-x-1.5 cursor-pointer flex-shrink-0 hover:bg-[#151c24] px-1.5 py-0.5 rounded transition-colors"
      >
        <span className="font-extrabold text-white">IHSG</span>
        <span className="text-[#e2e8f0] font-semibold">6,541.38</span>
        <span className="text-[#eb5757] font-medium flex items-center">
          ↘ 47.96 (-0.73%)
        </span>
      </div>

      {/* Right section: Moon Icon & Real-time Clock */}
      <div className="flex items-center space-x-1.5 text-white font-mono text-[11px]">
        <Moon className="w-3.5 h-3.5 text-[#f59e0b]" />
        <span>{timeString || '6:48:24 PM'}</span>
      </div>
    </div>
  );
};

