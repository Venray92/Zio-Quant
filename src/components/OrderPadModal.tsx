import React, { useState, useEffect } from 'react';
import { Stock, OrderItem } from '../types';
import { X, Minus, Plus, AlertCircle, CheckCircle2 } from 'lucide-react';

interface OrderPadModalProps {
  isOpen: boolean;
  onClose: () => void;
  stock: Stock;
  initialType: 'BUY' | 'SELL';
  onSubmitOrder: (order: Omit<OrderItem, 'id' | 'timestamp'>) => void;
}

export const OrderPadModal: React.FC<OrderPadModalProps> = ({
  isOpen,
  onClose,
  stock,
  initialType,
  onSubmitOrder,
}) => {
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>(initialType);
  const [orderType, setOrderType] = useState<'LIMIT' | 'MARKET'>('LIMIT');
  const [price, setPrice] = useState<number>(stock.price);
  const [lot, setLot] = useState<number>(10);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  useEffect(() => {
    setOrderSide(initialType);
    setPrice(stock.price);
  }, [initialType, stock.price, isOpen]);

  if (!isOpen) return null;

  // Calculate IDX tick size
  const getTickSize = (p: number) => {
    if (p < 200) return 1;
    if (p < 500) return 2;
    if (p < 2000) return 5;
    if (p < 5000) return 10;
    return 25;
  };

  const handlePriceStep = (direction: 'up' | 'down') => {
    const step = getTickSize(price);
    if (direction === 'up') {
      setPrice(prev => prev + step);
    } else {
      setPrice(prev => Math.max(step, prev - step));
    }
  };

  const totalShares = lot * 100;
  const grossTotal = price * totalShares;
  const feeRate = orderSide === 'BUY' ? 0.0015 : 0.0025; // 0.15% Buy, 0.25% Sell
  const fee = Math.round(grossTotal * feeRate);
  const netTotal = orderSide === 'BUY' ? grossTotal + fee : grossTotal - fee;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (lot <= 0) return;

    onSubmitOrder({
      symbol: stock.symbol,
      type: orderSide,
      orderType,
      price,
      lot,
      total: netTotal,
      status: 'Open',
    });

    setFeedbackMessage(`Order ${orderSide} ${lot} lot ${stock.symbol} @ Rp ${price.toLocaleString('id-ID')} berhasil dikirim ke antrian IDX!`);
    setTimeout(() => {
      setFeedbackMessage(null);
      onClose();
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-[2px] flex items-center justify-center p-4">
      <div className="bg-[#141a22] border border-[#232d3b] rounded-lg w-full max-w-md shadow-2xl overflow-hidden select-none">
        {/* Modal Header */}
        <div className="px-4 py-3 border-b border-[#212b38] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="font-extrabold text-white text-base tracking-wide">
              {stock.symbol}
            </span>
            <span className="text-xs text-[#8292a4] truncate max-w-[180px]">
              {stock.name}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-[#8b98a5] hover:text-white p-1 rounded hover:bg-[#1f2835]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Side Selector Tabs (BUY / SELL) */}
        <div className="grid grid-cols-2 p-1 bg-[#0d1217] border-b border-[#212b38]">
          <button
            type="button"
            onClick={() => setOrderSide('BUY')}
            className={`py-2 text-xs font-bold uppercase tracking-wider rounded transition-all ${
              orderSide === 'BUY'
                ? 'bg-[#00b074] text-white shadow'
                : 'text-[#8b98a5] hover:text-white'
            }`}
          >
            BUY / Beli
          </button>
          <button
            type="button"
            onClick={() => setOrderSide('SELL')}
            className={`py-2 text-xs font-bold uppercase tracking-wider rounded transition-all ${
              orderSide === 'SELL'
                ? 'bg-[#eb5757] text-white shadow'
                : 'text-[#8b98a5] hover:text-white'
            }`}
          >
            SELL / Jual
          </button>
        </div>

        {/* Order Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-3.5">
          {/* Order Type (Limit vs Market) */}
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#8b98a5]">Tipe Order:</span>
            <div className="flex space-x-1 bg-[#0c1016] p-0.5 rounded border border-[#232d3b]">
              <button
                type="button"
                onClick={() => setOrderType('LIMIT')}
                className={`px-3 py-1 rounded text-xs font-semibold ${
                  orderType === 'LIMIT'
                    ? 'bg-[#232e3d] text-white'
                    : 'text-[#7e8e9f] hover:text-white'
                }`}
              >
                Limit
              </button>
              <button
                type="button"
                onClick={() => {
                  setOrderType('MARKET');
                  setPrice(stock.price);
                }}
                className={`px-3 py-1 rounded text-xs font-semibold ${
                  orderType === 'MARKET'
                    ? 'bg-[#232e3d] text-white'
                    : 'text-[#7e8e9f] hover:text-white'
                }`}
              >
                Market
              </button>
            </div>
          </div>

          {/* Price Input with +/- Ticks */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-[#8b98a5]">Harga (Price) IDR:</span>
              <span className="text-[#64748b] text-[11px]">Tick: Rp {getTickSize(price)}</span>
            </div>
            <div className="flex items-center">
              <button
                type="button"
                onClick={() => handlePriceStep('down')}
                disabled={orderType === 'MARKET'}
                className="w-10 h-9 bg-[#1b232e] hover:bg-[#253040] disabled:opacity-40 text-white rounded-l border border-r-0 border-[#2b3748] flex items-center justify-center"
              >
                <Minus className="w-3.5 h-3.5" />
              </button>
              <input
                type="number"
                value={price}
                disabled={orderType === 'MARKET'}
                onChange={(e) => setPrice(Number(e.target.value))}
                className="flex-1 h-9 bg-[#0e1218] border border-[#2b3748] text-center text-white font-bold text-sm focus:outline-none focus:border-[#00c076]"
              />
              <button
                type="button"
                onClick={() => handlePriceStep('up')}
                disabled={orderType === 'MARKET'}
                className="w-10 h-9 bg-[#1b232e] hover:bg-[#253040] disabled:opacity-40 text-white rounded-r border border-l-0 border-[#2b3748] flex items-center justify-center"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Lot Input */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-[#8b98a5]">Jumlah (Lot):</span>
              <span className="text-[#8b98a5]">{totalShares.toLocaleString('id-ID')} Lembar</span>
            </div>
            <div className="flex items-center">
              <button
                type="button"
                onClick={() => setLot(prev => Math.max(1, prev - 1))}
                className="w-10 h-9 bg-[#1b232e] hover:bg-[#253040] text-white rounded-l border border-r-0 border-[#2b3748] flex items-center justify-center"
              >
                <Minus className="w-3.5 h-3.5" />
              </button>
              <input
                type="number"
                min="1"
                value={lot}
                onChange={(e) => setLot(Math.max(1, Number(e.target.value)))}
                className="flex-1 h-9 bg-[#0e1218] border border-[#2b3748] text-center text-white font-bold text-sm focus:outline-none focus:border-[#00c076]"
              />
              <button
                type="button"
                onClick={() => setLot(prev => prev + 1)}
                className="w-10 h-9 bg-[#1b232e] hover:bg-[#253040] text-white rounded-r border border-l-0 border-[#2b3748] flex items-center justify-center"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Quick Lot Buttons */}
            <div className="flex gap-1.5 mt-2">
              {[1, 5, 10, 50, 100].map(val => (
                <button
                  key={val}
                  type="button"
                  onClick={() => setLot(val)}
                  className={`flex-1 py-1 rounded text-[11px] font-medium border transition-colors ${
                    lot === val
                      ? 'bg-[#232e3d] text-white border-[#00c076]'
                      : 'bg-[#12171f] text-[#8b98a5] border-[#253040] hover:border-[#38495e]'
                  }`}
                >
                  {val}
                </button>
              ))}
            </div>
          </div>

          {/* Breakdown summary */}
          <div className="bg-[#0e1319] p-3 rounded border border-[#202937] text-xs space-y-1.5">
            <div className="flex justify-between text-[#8b98a5]">
              <span>Nilai Saham</span>
              <span className="text-white">Rp {grossTotal.toLocaleString('id-ID')}</span>
            </div>
            <div className="flex justify-between text-[#8b98a5]">
              <span>Biaya Transaksi (Est. {orderSide === 'BUY' ? '0.15%' : '0.25%'})</span>
              <span className="text-white">Rp {fee.toLocaleString('id-ID')}</span>
            </div>
            <div className="flex justify-between pt-1.5 border-t border-[#1e2734] font-bold">
              <span className="text-white">Total Estimasi</span>
              <span className={orderSide === 'BUY' ? 'text-[#00c076]' : 'text-[#eb5757]'}>
                Rp {netTotal.toLocaleString('id-ID')}
              </span>
            </div>
          </div>

          {/* Feedback message banner */}
          {feedbackMessage && (
            <div className="flex items-center space-x-2 p-2.5 bg-[#0e3324] border border-[#00c076] text-[#00c076] text-xs rounded animate-fadeIn">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{feedbackMessage}</span>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            className={`w-full py-2.5 rounded font-bold text-xs uppercase tracking-wider text-white shadow-lg transition-all ${
              orderSide === 'BUY'
                ? 'bg-[#00b074] hover:bg-[#009e66] active:scale-[0.99]'
                : 'bg-[#eb5757] hover:bg-[#d94444] active:scale-[0.99]'
            }`}
          >
            Konfirmasi {orderSide} {lot} Lot
          </button>
        </form>
      </div>
    </div>
  );
};
