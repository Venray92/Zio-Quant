import React, { useState } from 'react';
import { PINE_SCRIPT_CODE } from '../data/pineScript';
import { Check, Copy, X, Terminal, Sparkles, ExternalLink, HelpCircle } from 'lucide-react';

interface PineScriptModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PineScriptModal: React.FC<PineScriptModalProps> = ({ isOpen, onClose }) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(PINE_SCRIPT_CODE);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div 
        className="relative w-full max-w-2xl bg-[#0f141c] border border-[#26354a] rounded-xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#141b26] border-b border-[#222e40]">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 rounded-lg bg-[#00c076]/15 text-[#00c076]">
              <Terminal className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center space-x-2">
                <span>TradingView Pine Script v5</span>
                <span className="bg-[#00c076]/20 text-[#34d399] text-[10px] font-mono px-2 py-0.5 rounded-full border border-[#00c076]/30">
                  || STOCH + PSAR || HIJAU HOLD MERAH BUANG
                </span>
              </h2>
              <p className="text-[11px] text-[#8696a7]">
                Stochastic (10, 5, 5) &amp; Parabolic SAR (0.02, 0.02, 0.20)
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopy}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shadow-sm ${
                copied
                  ? 'bg-[#00c076] text-black ring-2 ring-[#00c076]/40'
                  : 'bg-[#2563eb] hover:bg-[#1d4ed8] text-white'
              }`}
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>Tersalin ke Clipboard!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Salin Script (Copy)</span>
                </>
              )}
            </button>
            <button
              onClick={onClose}
              className="text-[#7e8e9f] hover:text-white p-1 rounded hover:bg-[#1f2937]"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Rule explanation pills */}
        <div className="px-4 py-2 bg-[#0d121a] border-b border-[#1f2937] flex flex-wrap gap-2 text-[11px]">
          <span className="flex items-center space-x-1 text-[#60a5fa] bg-[#1e2d42] px-2 py-0.5 rounded border border-[#2b4162]">
            <span className="font-semibold">%K Period:</span> 10 (Smooth %K: 5, Smooth %D: 5)
          </span>
          <span className="flex items-center space-x-1 text-[#34d399] bg-[#0c2e20] px-2 py-0.5 rounded border border-[#10b981]/30">
            <span className="font-semibold">PSAR:</span> Start 0.02, Inc 0.02, Max 0.20
          </span>
          <span className="flex items-center space-x-1 text-[#f59e0b] bg-[#31230e] px-2 py-0.5 rounded border border-[#f59e0b]/30">
            <span className="font-semibold">Aturan:</span> Golden Cross 0-3 Hari &amp; PSAR &lt; Close (Hijau Hold)
          </span>
        </div>

        {/* Code View Area */}
        <div className="flex-1 overflow-auto p-4 bg-[#0a0d14] font-mono text-[11.5px] leading-relaxed text-[#c9d1d9]">
          <pre className="whitespace-pre overflow-x-auto selection:bg-[#1f6feb] selection:text-white">
            {PINE_SCRIPT_CODE}
          </pre>
        </div>

        {/* Modal Footer with quick instructions */}
        <div className="px-4 py-2.5 bg-[#111622] border-t border-[#222e40] flex items-center justify-between text-[11px] text-[#8696a7]">
          <div className="flex items-center space-x-1.5">
            <Sparkles className="w-3.5 h-3.5 text-[#00c076]" />
            <span>
              <strong>Cara pakai di TradingView:</strong> Buka tab <em>Pine Editor</em> di bawah chart TradingView &rarr; Paste kode di atas &rarr; Klik <em>Add to Chart</em>.
            </span>
          </div>
          <button
            onClick={onClose}
            className="px-3 py-1 bg-[#1e2838] hover:bg-[#2b394e] text-white rounded text-xs font-medium transition-colors"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
};
