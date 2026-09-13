import React, { useState } from 'react';
import { Mail, Lock, LogIn, ChevronRight, TrendingUp } from 'lucide-react';
import { motion } from 'motion/react';
import { auth, db } from '../lib/firebase';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';
import { doc, setDoc } from 'firebase/firestore';
import { Logo } from './Logo';

export const LoginPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    
    try {
      if (isLogin) {
        await signInWithEmailAndPassword(auth, email, password);
      } else {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        // Create user profile document in Firestore
        await setDoc(doc(db, 'users', userCredential.user.uid), {
          email: userCredential.user.email,
          createdAt: new Date().toISOString()
        });
      }
    } catch (error: any) {
      console.error("Auth error:", error);
      if (error.code === 'auth/invalid-credential' || error.code === 'auth/wrong-password') {
        setErrorMsg('Email atau password salah.');
      } else if (error.code === 'auth/email-already-in-use') {
        setErrorMsg('Email sudah terdaftar. Silakan login.');
      } else if (error.code === 'auth/weak-password') {
        setErrorMsg('Password terlalu lemah. Minimal 6 karakter.');
      } else {
        setErrorMsg('Terjadi kesalahan. Coba lagi.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#0c0e12] flex flex-col md:flex-row font-sans text-[#e1e7ec]">
      {/* Left section - Branding & Visuals (Hidden on small screens) */}
      <div className="hidden md:flex md:w-1/2 relative bg-[#13171e] flex-col justify-between p-12 overflow-hidden">
        {/* Animated Background blobs */}
        <motion.div 
          animate={{ scale: [1, 1.1, 1], rotate: [0, 45, 0], opacity: [0.15, 0.25, 0.15] }}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
          className="absolute -top-40 -left-40 w-[500px] h-[500px] bg-blue-500 rounded-full mix-blend-multiply filter blur-[128px]"
        />
        <motion.div 
          animate={{ scale: [1, 1.3, 1], x: [0, -30, 0], y: [0, 40, 0], opacity: [0.15, 0.3, 0.15] }}
          transition={{ duration: 15, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          className="absolute top-1/3 -right-40 w-[500px] h-[500px] bg-emerald-500 rounded-full mix-blend-multiply filter blur-[128px]"
        />
        <motion.div 
          animate={{ scale: [1, 1.2, 1], x: [0, 30, 0], y: [0, -30, 0], opacity: [0.15, 0.25, 0.15] }}
          transition={{ duration: 18, repeat: Infinity, ease: "easeInOut", delay: 4 }}
          className="absolute -bottom-40 left-20 w-[500px] h-[500px] bg-purple-500 rounded-full mix-blend-multiply filter blur-[128px]"
        />

        {/* Floating Decorative Elements */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-80 z-0">
           <motion.div 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: [0, -15, 0], opacity: 1 }}
              transition={{ y: { duration: 6, repeat: Infinity, ease: "easeInOut" }, opacity: { duration: 1 } }}
              className="absolute left-[15%] top-[25%] w-52 bg-[#1a1f28]/60 backdrop-blur-xl rounded-2xl border border-white/10 p-4 shadow-2xl"
           >
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <TrendingUp className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white">BBCA</div>
                  <div className="text-[10px] text-[#8b9cb0]">Bank Central Asia</div>
                </div>
                <div className="text-xs font-semibold text-emerald-400 ml-auto">+2.4%</div>
              </div>
              <div className="flex items-end gap-1.5 h-16">
                 <div className="w-full bg-emerald-500/20 rounded-sm h-[30%]"></div>
                 <div className="w-full bg-emerald-500/40 rounded-sm h-[45%]"></div>
                 <div className="w-full bg-red-500/40 rounded-sm h-[25%]"></div>
                 <div className="w-full bg-emerald-500/60 rounded-sm h-[60%]"></div>
                 <div className="w-full bg-emerald-500/80 rounded-sm h-[80%]"></div>
                 <div className="w-full bg-emerald-500 rounded-sm h-[100%] shadow-[0_0_12px_rgba(16,185,129,0.4)]"></div>
              </div>
           </motion.div>

           <motion.div 
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: [0, 20, 0], opacity: 1 }}
              transition={{ y: { duration: 7, repeat: Infinity, ease: "easeInOut", delay: 1 }, opacity: { duration: 1, delay: 0.3 } }}
              className="absolute right-[10%] bottom-[35%] w-48 p-4 bg-[#1a1f28]/60 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl"
           >
              <div className="text-xs text-[#8b9cb0] mb-1">Total Portfolio</div>
              <div className="text-xl font-bold text-white mb-3">Rp 1.245 M</div>
              <div className="w-full h-2 bg-[#0c0e12] rounded-full overflow-hidden">
                 <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: "75%" }}
                    transition={{ duration: 1.5, delay: 0.5, ease: "easeOut" }}
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full"
                 />
              </div>
           </motion.div>
        </div>
        
        <div className="relative z-10 flex items-center gap-3">
          <Logo size="md" animated />
          <span className="text-2xl font-semibold tracking-tight text-white">Zio Screaner</span>
        </div>

        <div className="relative z-10 max-w-md">
          <h1 className="text-4xl lg:text-5xl font-bold leading-tight text-white mb-6">
            Analisa saham cerdas,<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
              keputusan tepat.
            </span>
          </h1>
          <p className="text-[#8b9cb0] text-lg leading-relaxed">
            Platform trading dan analisis teknikal, eksekusi rencana trading anda dengan presisi.
          </p>
        </div>

        <div className="relative z-10 flex items-center gap-4 text-sm text-[#5d6a7d]">
          <span>© 2026 Zio Screaner</span>
          <span className="w-1 h-1 rounded-full bg-[#3d495a]"></span>
          <span>Hak Cipta Dilindungi</span>
        </div>
      </div>

      {/* Right section - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 sm:p-12 lg:p-24 relative bg-[#0c0e12]">
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="w-full max-w-md space-y-8 relative z-10"
        >
          
          <div className="md:hidden flex items-center gap-3 mb-12">
            <Logo size="md" animated />
            <span className="text-2xl font-semibold tracking-tight text-white">Zio Screaner</span>
          </div>

          <div className="text-center md:text-left space-y-2">
            <h2 className="text-3xl font-bold text-white tracking-tight">
              {isLogin ? 'Selamat Datang' : 'Buat Akun Baru'}
            </h2>
            <p className="text-[#8b9cb0]">
              {isLogin ? 'Masuk ke akun Anda untuk melanjutkan' : 'Daftar untuk mengakses platform Zio Screaner'}
            </p>
          </div>

          {errorMsg && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-400 text-sm p-3 rounded-xl">
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-[#b0bdcc] ml-1">Email</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-[#5d6a7d]" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 bg-[#13171e] border border-[#2b3341] rounded-xl text-white placeholder-[#5d6a7d] focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
                    placeholder="nama@email.com"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between ml-1">
                  <label className="text-sm font-medium text-[#b0bdcc]">Kata Sandi</label>
                  {isLogin && (
                    <a href="#" className="text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors">
                      Lupa sandi?
                    </a>
                  )}
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-[#5d6a7d]" />
                  </div>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 bg-[#13171e] border border-[#2b3341] rounded-xl text-white placeholder-[#5d6a7d] focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
                    placeholder="••••••••"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full relative group bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 rounded-xl transition-all duration-200 overflow-hidden flex items-center justify-center disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span className="relative z-10">{isLogin ? 'Masuk ke Dashboard' : 'Daftar Akun'}</span>
                  <ChevronRight className="w-4 h-4 ml-1.5 relative z-10 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          <p className="text-center text-sm text-[#8b9cb0]">
            {isLogin ? 'Belum punya akun?' : 'Sudah punya akun?'}
            <button 
              type="button" 
              onClick={() => {
                setIsLogin(!isLogin);
                setErrorMsg('');
              }}
              className="font-medium text-blue-400 hover:text-blue-300 transition-colors ml-1"
            >
              {isLogin ? 'Daftar sekarang' : 'Masuk di sini'}
            </button>
          </p>

        </motion.div>
      </div>
    </div>
  );
};
