import React, { useState } from 'react';
import { 
  Headphones, 
  X, 
  HelpCircle, 
  Send, 
  CheckCircle, 
  BookOpen, 
  FileText, 
  Clock, 
  ShieldCheck, 
  Sparkles,
  ExternalLink,
  PhoneCall
} from 'lucide-react';

interface SupportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SupportModal: React.FC<SupportModalProps> = ({ isOpen, onClose }) => {
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketMessage, setTicketMessage] = useState('');
  const [ticketCategory, setTicketCategory] = useState('Teknis & Screener');
  const [ticketSubmitted, setTicketSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleSubmitTicket = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketMessage.trim()) return;

    setTicketSubmitted(true);
    setTimeout(() => {
      setTicketSubmitted(false);
      setTicketSubject('');
      setTicketMessage('');
    }, 4000);
  };

  const FAQS = [
    {
      q: 'Bagaimana cara membaca screener Stochastic + Parabolic SAR?',
      a: 'Ketika garis %K memotong ke atas garis %D di area oversold (< 20) dan titik Parabolic SAR berpindah ke bawah candlestick, sinyal Bullish Golden Cross terbentuk dengan probabilitas pantulan tinggi.',
    },
    {
      q: 'Apakah Trade Plan memperhitungkan fraksi harga resmi BEI?',
      a: 'Ya, seluruh target harga, area entry, dan level stop loss telah dibulatkan sesuai fraksi harga resmi Bursa Efek Indonesia (Rp 1, Rp 2, Rp 5, Rp 10, Rp 25).',
    },
    {
      q: 'Berapa rasio Risk to Reward (R:R) yang direkomendasikan?',
      a: 'Sistem Zio merekomendasikan setup trading dengan rasio minimal 1 : 2 ke Target 2 untuk menjaga pertumbuhan modal jangka panjang.',
    },
    {
      q: 'Kapan data saham diperbarui?',
      a: 'Data diperbarui secara real-time mengikuti jam operasional bursa IDX (Sesi 1: 09:00 - 12:00, Sesi 2: 13:30 - 16:00 WIB).',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="absolute inset-0" onClick={onClose} />

      {/* Modal Dialog */}
      <div 
        className="relative w-full max-w-3xl max-h-[88vh] bg-[#0c1016] border border-[#1e2736] rounded-2xl shadow-2xl flex flex-col overflow-hidden z-10"
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-5 py-4 bg-[#101620] border-b border-[#1c2432] flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#8b5cf6] to-[#6d28d9] text-white flex items-center justify-center shadow-md">
              <Headphones className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base sm:text-lg font-black text-white tracking-wide">
                  Pusat Bantuan & Support Zio
                </h2>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#1e1738] text-[#c4b5fd] border border-[#8b5cf6]/40">
                  Helpdesk 24/7
                </span>
              </div>
              <p className="text-xs text-[#8094ab]">
                Panduan screener, troubleshooting aplikasi, dan layanan konsultasi tim support.
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
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-5 bg-[#0a0d12]">
          
          {/* Support Channels Banner */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-[#0f141e] border border-[#1d2636] rounded-xl p-3.5 space-y-1">
              <div className="flex items-center space-x-2 text-[#00c076] text-xs font-bold">
                <Clock className="w-4 h-4" />
                <span>Response Time</span>
              </div>
              <div className="text-sm font-black text-white">&lt; 15 Menit</div>
              <p className="text-[11px] text-[#71859c]">Layanan fast response saat jam bursa aktif.</p>
            </div>

            <div className="bg-[#0f141e] border border-[#1d2636] rounded-xl p-3.5 space-y-1">
              <div className="flex items-center space-x-2 text-[#38bdf8] text-xs font-bold">
                <ShieldCheck className="w-4 h-4" />
                <span>Status Sistem</span>
              </div>
              <div className="text-sm font-black text-[#00c076] flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-[#00c076] animate-ping" />
                <span>All Systems Operational</span>
              </div>
              <p className="text-[11px] text-[#71859c]">Feed IDX & Algoritma Screener normal.</p>
            </div>

            <div className="bg-[#0f141e] border border-[#1d2636] rounded-xl p-3.5 space-y-1">
              <div className="flex items-center space-x-2 text-[#eab308] text-xs font-bold">
                <BookOpen className="w-4 h-4" />
                <span>Dokumentasi</span>
              </div>
              <div className="text-sm font-black text-white">Versi v2.4 Pro</div>
              <p className="text-[11px] text-[#71859c]">Modul Trade Plan & Algoritma V3.</p>
            </div>
          </div>

          {/* Form Kirim Pertanyaan / Tiket */}
          <div className="bg-[#0f1520] border border-[#1e2838] rounded-xl p-4 sm:p-5 space-y-3">
            <div className="flex items-center space-x-2">
              <HelpCircle className="w-4 h-4 text-[#8b5cf6]" />
              <h3 className="text-xs sm:text-sm font-extrabold text-white">
                Kirim Pertanyaan / Request Fitur Baru
              </h3>
            </div>

            {ticketSubmitted ? (
              <div className="p-4 rounded-xl bg-[#0d2a1d] border border-[#00c076]/40 text-center space-y-1.5 animate-in fade-in">
                <CheckCircle className="w-8 h-8 text-[#00c076] mx-auto" />
                <h4 className="text-sm font-bold text-white">Tiket Berhasil Terkirim!</h4>
                <p className="text-xs text-[#8cb8a3]">
                  Tim support teknis Zio akan segera meninjau pesan Anda. Nomor Tiket: #{Math.floor(100000 + Math.random() * 900000)}
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmitTicket} className="space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#869cb3] mb-1">
                      Kategori Masalah:
                    </label>
                    <select
                      value={ticketCategory}
                      onChange={(e) => setTicketCategory(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-[#141b26] border border-[#243346] text-xs text-white focus:outline-none focus:border-[#8b5cf6]"
                    >
                      <option value="Teknis & Screener">Indikator & Algoritma Screener</option>
                      <option value="Trade Plan & Rasio R:R">Formula Trade Plan & Rasio R:R</option>
                      <option value="Saran Fitur Baru">Saran & Ide Fitur Tambahan</option>
                      <option value="Akun & Komunitas">Komunitas Stream & Prediksi</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-[#869cb3] mb-1">
                      Judul Singkat:
                    </label>
                    <input
                      type="text"
                      value={ticketSubject}
                      onChange={(e) => setTicketSubject(e.target.value)}
                      placeholder="Contoh: Pertanyaan indikator BBCA"
                      className="w-full px-3 py-2 rounded-lg bg-[#141b26] border border-[#243346] text-xs text-white focus:outline-none focus:border-[#8b5cf6]"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-[#869cb3] mb-1">
                    Detail Pertanyaan:
                  </label>
                  <textarea
                    rows={3}
                    value={ticketMessage}
                    onChange={(e) => setTicketMessage(e.target.value)}
                    placeholder="Tulis kendala atau pertanyaan yang ingin Anda tanyakan..."
                    className="w-full p-2.5 rounded-lg bg-[#141b26] border border-[#243346] text-xs text-white focus:outline-none focus:border-[#8b5cf6]"
                    required
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold text-xs shadow-md transition-all cursor-pointer"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Kirim ke Tim Support</span>
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Frequently Asked Questions */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-[#869cb3] uppercase tracking-wider px-1">
              Pertanyaan yang Sering Diajukan (FAQ)
            </h3>
            <div className="space-y-2">
              {FAQS.map((faq, idx) => (
                <div key={idx} className="bg-[#0f141d] border border-[#1a2331] rounded-xl p-3.5 space-y-1">
                  <h4 className="text-xs font-bold text-white flex items-center space-x-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#8b5cf6]" />
                    <span>{faq.q}</span>
                  </h4>
                  <p className="text-xs text-[#899db4] leading-relaxed pl-3.5">
                    {faq.a}
                  </p>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 bg-[#0d1219] border-t border-[#1a222e] flex items-center justify-between text-[11px] text-[#697d92] flex-shrink-0">
          <span>Official Support Desk • Melayani trader saham seluruh Indonesia</span>
          <button
            onClick={onClose}
            className="text-xs font-bold text-[#8b5cf6] hover:underline cursor-pointer"
          >
            Tutup Jendela
          </button>
        </div>
      </div>
    </div>
  );
};
