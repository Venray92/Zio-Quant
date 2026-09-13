import React from 'react';
import { MainTab } from '../types';
import { Palette, Sparkles } from 'lucide-react';

interface SubTabsBarProps {
  activeTab: MainTab;
  onSelectTab: (tab: MainTab) => void;
  chartTheme: 'dark' | 'cream';
  onToggleChartTheme: () => void;
}

const TABS: MainTab[] = [
  'Chart',
  'Screener',
  'Trade Plan',
  'Stream',
];

export const SubTabsBar: React.FC<SubTabsBarProps> = ({
  activeTab,
  onSelectTab,
  chartTheme,
  onToggleChartTheme,
}) => {
  return (
    <div className="h-9 bg-[#0e1217] border-b border-[#1c2430] px-3 flex items-center justify-between select-none overflow-x-auto flex-shrink-0">
      {/* Tab Buttons */}
      <div className="flex items-center space-x-1 overflow-x-auto no-scrollbar py-1">
        {TABS.map((tab) => {
          const isActive = activeTab === tab;
          return (
            <button
              key={tab}
              onClick={() => onSelectTab(tab)}
              className={`px-3 py-1 text-xs transition-all whitespace-nowrap rounded-[4px] font-medium ${
                isActive
                  ? 'bg-[#1c2430] text-white font-bold shadow-sm'
                  : 'text-[#8292a4] hover:text-[#f0f4f8] hover:bg-[#151c24]'
              }`}
            >
              {tab}
            </button>
          );
        })}
      </div>

      {/* Quick Theme / Style Switcher for Chart */}
      {activeTab === 'Chart' && (
        <div className="hidden sm:flex items-center space-x-2 pl-2">
          <button
            onClick={onToggleChartTheme}
            className={`flex items-center space-x-1 text-[11px] px-2 py-0.5 rounded border transition-colors ${
              chartTheme === 'cream'
                ? 'bg-[#fff9e6] text-[#332a00] border-[#ecd88d] font-semibold'
                : 'bg-[#18202b] text-[#93a4b7] border-[#293648] hover:text-white'
            }`}
            title="Ganti Tema Chart: Stockbit Cream / Modern Dark"
          >
            <Palette className="w-3 h-3" />
            <span>{chartTheme === 'cream' ? 'Classic Cream' : 'Dark Theme'}</span>
          </button>
        </div>
      )}
    </div>
  );
};
