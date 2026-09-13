import React from 'react';
import { motion } from 'motion/react';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
}

export const Logo: React.FC<LogoProps> = ({ size = 'sm', animated = false }) => {
  const containerClasses = 
    size === 'sm' ? 'w-7 h-7 rounded-lg' : 
    size === 'md' ? 'w-10 h-10 rounded-xl' : 
    'w-14 h-14 rounded-2xl';

  const Content = (
    <div className={`relative flex items-center justify-center flex-shrink-0 bg-gradient-to-br from-[#0B1319] to-[#152330] border border-white/10 shadow-[0_0_15px_rgba(0,192,118,0.2)] overflow-hidden group ${containerClasses}`}>
      <div className="absolute inset-0 bg-gradient-to-tr from-[#00c076]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      
      {/* Background Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:4px_4px] opacity-20"></div>

      <svg 
        viewBox="0 0 24 24" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg" 
        className="w-[60%] h-[60%] z-10 drop-shadow-[0_0_6px_rgba(0,192,118,0.6)]"
      >
        <motion.path 
          d="M5 7H11L7 17H13" 
          stroke="url(#z-gradient)" 
          strokeWidth="2.5" 
          strokeLinecap="round" 
          strokeLinejoin="round"
          initial={animated ? { pathLength: 0 } : { pathLength: 1 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.5, ease: "easeInOut" }}
        />
        <motion.path 
          d="M13 13L16 10L19 13" 
          stroke="#00c076" 
          strokeWidth="2.5" 
          strokeLinecap="round" 
          strokeLinejoin="round"
          initial={animated ? { opacity: 0, y: 5 } : { opacity: 1, y: 0 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: animated ? 1 : 0 }}
        />
        <motion.circle
          cx="19"
          cy="13"
          r="1.5"
          fill="#00c076"
          initial={animated ? { scale: 0 } : { scale: 1 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.3, delay: animated ? 1.3 : 0 }}
        />
        <defs>
          <linearGradient id="z-gradient" x1="5" y1="7" x2="13" y2="17" gradientUnits="userSpaceOnUse">
            <stop stopColor="#00db87" />
            <stop offset="1" stopColor="#007a4b" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );

  return Content;
};
