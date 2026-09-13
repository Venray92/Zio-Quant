import React from 'react';
import {
  SlidersHorizontal,
  TrendingUp,
  Radio,
  Headphones,
  Settings
} from 'lucide-react';
import { SidebarTab } from '../types';

interface SidebarProps {
  activeTab: SidebarTab;
  onSelectTab: (tab: SidebarTab) => void;
  theme?: 'dark' | 'light';
  onLogout?: () => void;
}

interface NavItem {
  id: SidebarTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'Screener', label: 'Screener', icon: SlidersHorizontal },
  { id: 'Markets', label: 'Markets', icon: TrendingUp },
  { id: 'Stream', label: 'Stream', icon: Radio },
  { id: 'Support', label: 'Support', icon: Headphones },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab, theme = 'dark', onLogout }) => {
  const isLight = theme === 'light';

  return (
    <aside className={`w-[60px] border-r flex flex-col justify-between items-center py-2 flex-shrink-0 select-none z-10 transition-colors duration-200 ${
      isLight ? 'bg-white border-[#e2e8f0]' : 'bg-[#0c0e12] border-[#1a1f26]'
    }`}>
      <div className="flex flex-col items-center space-y-1 w-full">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full py-2 px-1 flex flex-col items-center justify-center transition-all group relative ${
                isActive
                  ? 'text-[#00c076]'
                  : isLight
                    ? 'text-[#64748b] hover:text-[#0f172a] hover:bg-[#f1f5f9]'
                    : 'text-[#7e8b9b] hover:text-[#e1e7ec] hover:bg-[#141920]'
              }`}
              title={item.label.replace('\n', ' ')}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-[#00c076] rounded-r" />
              )}
              <Icon
                className={`w-4 h-4 mb-1 transition-transform group-hover:scale-105 ${
                  isActive ? 'fill-[#00c076]/20' : ''
                }`}
              />
              <span
                className={`text-[9px] font-medium leading-tight text-center whitespace-pre-line ${
                  isActive ? 'font-semibold text-[#00c076]' : ''
                }`}
              >
                {item.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* Bottom Settings & Logout */}
      <div className={`w-full pt-2 border-t flex flex-col items-center space-y-1 ${
        isLight ? 'border-[#e2e8f0]' : 'border-[#1a1f26]/80'
      }`}>
        <button
          onClick={() => onSelectTab('Settings')}
          className={`w-full py-2 px-1 flex flex-col items-center justify-center transition-all group ${
            activeTab === 'Settings'
              ? 'text-[#00c076]'
              : isLight
                ? 'text-[#64748b] hover:text-[#0f172a] hover:bg-[#f1f5f9]'
                : 'text-[#7e8b9b] hover:text-[#e1e7ec] hover:bg-[#141920]'
          }`}
          title="Settings"
        >
          <Settings className="w-4 h-4 mb-1 transition-transform group-hover:rotate-45" />
          <span className="text-[9px] font-medium leading-tight text-center">
            Settings
          </span>
        </button>
        
        {onLogout && (
          <button
            onClick={onLogout}
            className={`w-full py-2 px-1 flex flex-col items-center justify-center transition-all group ${
              isLight
                ? 'text-red-500 hover:bg-red-50'
                : 'text-red-500/80 hover:text-red-400 hover:bg-red-500/10'
            }`}
            title="Logout"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 mb-1 transition-transform group-hover:-translate-x-1"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
            <span className="text-[9px] font-medium leading-tight text-center">
              Logout
            </span>
          </button>
        )}
      </div>
    </aside>
  );
};
