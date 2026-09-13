import React, { useState } from 'react';
import { PortfolioPosition, OrderItem } from '../types';
import { ChevronDown, ChevronUp, Clock, CheckCircle, AlertCircle, XCircle } from 'lucide-react';

interface BottomPortfolioDrawerProps {
  portfolio: PortfolioPosition[];
  orders: OrderItem[];
  isOpen: boolean;
  onToggleOpen: () => void;
  activeTab: 'Portfolio' | 'Order' | 'History';
  onSelectTab: (tab: 'Portfolio' | 'Order' | 'History') => void;
}

export const BottomPortfolioDrawer: React.FC<BottomPortfolioDrawerProps> = ({
  portfolio,
  orders,
  isOpen,
  onToggleOpen,
  activeTab,
  onSelectTab,
}) => {
  const totalValue = portfolio.reduce((acc, curr) => acc + curr.marketValue, 0);
  const totalPnL = portfolio.reduce((acc, curr) => acc + curr.unrealizedPnL, 0);
  const totalPnLPercent = totalValue > 0 ? (totalPnL / (totalValue - totalPnL)) * 100 : 0;

  return (
    <div className="w-full bg-[#0d1117] border-t border-[#1c2430] flex flex-col flex-shrink-0 select-none z-20">
      {/* Drawer Header Strip */}
      <div className="h-7 px-3 flex items-center justify-between bg-[#12161f] border-b border-[#1b222d] text-xs">
        <div className="flex items-center space-x-2">
          {/* All Portfolio Dropdown Tab */}
          <button
            onClick={() => {
              onSelectTab('Portfolio');
              if (!isOpen) onToggleOpen();
            }}
            className={`flex items-center space-x-1 px-2.5 py-0.5 rounded text-[11px] font-semibold transition-colors ${
              activeTab === 'Portfolio' && isOpen
                ? 'bg-[#1e2735] text-[#00c076]'
                : 'text-[#cbd5e1] hover:text-white'
            }`}
          >
            <span>All Portfolio</span>
            <ChevronDown className="w-3 h-3" />
          </button>

          {/* Order Tab */}
          <button
            onClick={() => {
              onSelectTab('Order');
              if (!isOpen) onToggleOpen();
            }}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
              activeTab === 'Order' && isOpen
                ? 'bg-[#1e2735] text-[#00c076] font-semibold'
                : 'text-[#8b98a5] hover:text-white'
            }`}
          >
            Order ({orders.filter(o => o.status === 'Open').length})
          </button>

          {/* History Tab */}
          <button
            onClick={() => {
              onSelectTab('History');
              if (!isOpen) onToggleOpen();
            }}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
              activeTab === 'History' && isOpen
                ? 'bg-[#1e2735] text-[#00c076] font-semibold'
                : 'text-[#8b98a5] hover:text-white'
            }`}
          >
            History
          </button>
        </div>

        {/* Right Info: Total PnL & Drawer Toggle */}
        <div className="flex items-center space-x-3 text-[11px]">
          <div className="hidden sm:flex items-center space-x-2">
            <span className="text-[#7e8e9f]">Portfolio Value:</span>
            <span className="font-bold text-white">Rp {totalValue.toLocaleString('id-ID')}</span>
            <span className={`font-semibold ${totalPnL >= 0 ? 'text-[#00c076]' : 'text-[#eb5757]'}`}>
              {totalPnL >= 0 ? `+Rp ${totalPnL.toLocaleString('id-ID')}` : `-Rp ${Math.abs(totalPnL).toLocaleString('id-ID')}`} 
              ({totalPnLPercent.toFixed(2)}%)
            </span>
          </div>

          <button
            onClick={onToggleOpen}
            className="p-1 text-[#8b98a5] hover:text-white rounded hover:bg-[#1e2735] transition-colors"
            title={isOpen ? 'Tutup Panel' : 'Buka Panel'}
          >
            {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Expandable Drawer Content */}
      {isOpen && (
        <div className="h-44 overflow-y-auto bg-[#0f131a] p-3 text-xs">
          {activeTab === 'Portfolio' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-[#212b39] text-[#7e8e9f] text-[11px]">
                    <th className="pb-1.5 font-medium">Saham</th>
                    <th className="pb-1.5 font-medium text-right">Lot</th>
                    <th className="pb-1.5 font-medium text-right">Avg Buy Price</th>
                    <th className="pb-1.5 font-medium text-right">Current Price</th>
                    <th className="pb-1.5 font-medium text-right">Market Value</th>
                    <th className="pb-1.5 font-medium text-right">Unrealized P&L</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1b232e]">
                  {portfolio.map((pos) => {
                    const isProfit = pos.unrealizedPnL >= 0;
                    return (
                      <tr key={pos.symbol} className="hover:bg-[#161d26] transition-colors">
                        <td className="py-2">
                          <span className="font-bold text-white mr-1.5">{pos.symbol}</span>
                          <span className="text-[#7e8e9f] text-[11px] hidden md:inline">{pos.name}</span>
                        </td>
                        <td className="py-2 text-right font-medium">{pos.lot}</td>
                        <td className="py-2 text-right text-[#94a3b8]">Rp {pos.avgBuyPrice.toLocaleString('id-ID')}</td>
                        <td className="py-2 text-right font-semibold text-white">Rp {pos.currentPrice.toLocaleString('id-ID')}</td>
                        <td className="py-2 text-right font-medium">Rp {pos.marketValue.toLocaleString('id-ID')}</td>
                        <td className={`py-2 text-right font-bold ${isProfit ? 'text-[#00c076]' : 'text-[#eb5757]'}`}>
                          {isProfit ? `+${pos.unrealizedPnL.toLocaleString('id-ID')}` : pos.unrealizedPnL.toLocaleString('id-ID')} ({pos.unrealizedPnLPercent > 0 ? `+${pos.unrealizedPnLPercent}%` : `${pos.unrealizedPnLPercent}%`})
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'Order' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-[#212b39] text-[#7e8e9f] text-[11px]">
                    <th className="pb-1.5 font-medium">Order ID</th>
                    <th className="pb-1.5 font-medium">Saham</th>
                    <th className="pb-1.5 font-medium">Sisi</th>
                    <th className="pb-1.5 font-medium">Tipe</th>
                    <th className="pb-1.5 font-medium text-right">Harga</th>
                    <th className="pb-1.5 font-medium text-right">Lot</th>
                    <th className="pb-1.5 font-medium text-right">Total IDR</th>
                    <th className="pb-1.5 font-medium text-center">Status</th>
                    <th className="pb-1.5 font-medium text-right">Waktu</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1b232e]">
                  {orders.map((order) => (
                    <tr key={order.id} className="hover:bg-[#161d26] transition-colors">
                      <td className="py-2 text-[#7e8e9f] font-mono text-[11px]">{order.id}</td>
                      <td className="py-2 font-bold text-white">{order.symbol}</td>
                      <td className="py-2 font-bold">
                        <span className={`px-2 py-0.5 rounded text-[10px] ${order.type === 'BUY' ? 'bg-[#00c076]/20 text-[#00c076]' : 'bg-[#eb5757]/20 text-[#eb5757]'}`}>
                          {order.type}
                        </span>
                      </td>
                      <td className="py-2 text-[#94a3b8]">{order.orderType}</td>
                      <td className="py-2 text-right font-medium">Rp {order.price.toLocaleString('id-ID')}</td>
                      <td className="py-2 text-right">{order.lot}</td>
                      <td className="py-2 text-right font-medium">Rp {order.total.toLocaleString('id-ID')}</td>
                      <td className="py-2 text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          order.status === 'Matched'
                            ? 'bg-[#00c076]/20 text-[#00c076]'
                            : order.status === 'Open'
                            ? 'bg-[#3b82f6]/20 text-[#60a5fa]'
                            : 'bg-[#ef4444]/20 text-[#f87171]'
                        }`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="py-2 text-right text-[#7e8e9f]">{order.timestamp}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'History' && (
            <div className="space-y-2">
              <p className="text-xs text-[#8292a4]">Catatan transaksi eksekusi (Trade Execution Log) hari ini:</p>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between p-2 rounded bg-[#151c25] border border-[#212c39]">
                  <div className="flex items-center space-x-2">
                    <span className="bg-[#00c076]/20 text-[#00c076] font-bold text-[10px] px-1.5 py-0.5 rounded">BUY</span>
                    <span className="font-bold text-white">BMRI</span>
                    <span className="text-[#8b98a5]">20 Lot @ Rp 4.350</span>
                  </div>
                  <span className="text-[#8b98a5] text-[11px]">11:15:04 WIB · Matched</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-[#151c25] border border-[#212c39]">
                  <div className="flex items-center space-x-2">
                    <span className="bg-[#00c076]/20 text-[#00c076] font-bold text-[10px] px-1.5 py-0.5 rounded">BUY</span>
                    <span className="font-bold text-white">COCO</span>
                    <span className="text-[#8b98a5]">50 Lot @ Rp 124</span>
                  </div>
                  <span className="text-[#8b98a5] text-[11px]">09:32:10 WIB · Matched</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
