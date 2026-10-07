import React from 'react';

/**
 * FINBLIX BESPOKE SVG ICONS & LOGO SUITE
 * 100% Hand-crafted vector graphics with precision mathematical geometry.
 * Zero emojis, zero external font dependencies.
 */

/**
 * Official Finblix Brand Logo Mark
 * Represents algorithmic foresight, ascending alpha vectors, and institutional precision.
 */
export function FinblixLogo({ className = "w-8 h-8", size }) {
  const style = size ? { width: size, height: size } : undefined;
  return (
    <svg 
      viewBox="0 0 48 48" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
    >
      <defs>
        <linearGradient id="finblix-primary" x1="4" y1="4" x2="44" y2="44" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#06B6D4" />
          <stop offset="50%" stopColor="#3B82F6" />
          <stop offset="100%" stopColor="#6366F1" />
        </linearGradient>
        <linearGradient id="finblix-accent" x1="16" y1="8" x2="36" y2="28" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="100%" stopColor="#2563EB" />
        </linearGradient>
        <filter id="finblix-glow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#3B82F6" floodOpacity="0.35" />
        </filter>
      </defs>

      {/* Hexagonal Outer Shield Frame */}
      <polygon 
        points="24,3 43,13.5 43,34.5 24,45 5,34.5 5,13.5" 
        stroke="url(#finblix-primary)" 
        strokeWidth="2.5" 
        strokeLinejoin="round"
        fill="#0b0f19"
        fillOpacity="0.85"
      />

      {/* Precision Geometric Grid Lines */}
      <line x1="24" y1="3" x2="24" y2="17" stroke="url(#finblix-primary)" strokeWidth="1.2" strokeOpacity="0.4" />
      <line x1="5" y1="34.5" x2="19" y2="27" stroke="url(#finblix-primary)" strokeWidth="1.2" strokeOpacity="0.4" />
      <line x1="43" y1="34.5" x2="29" y2="27" stroke="url(#finblix-primary)" strokeWidth="1.2" strokeOpacity="0.4" />

      {/* Interlocking Monogram 'F' + Upward Alpha Trend Arrow */}
      <path 
        d="M17 34V14H31M17 23H27M24 14L32 6M32 6H24M32 6V14" 
        stroke="url(#finblix-accent)" 
        strokeWidth="3.2" 
        strokeLinecap="round" 
        strokeLinejoin="round" 
        filter="url(#finblix-glow)"
      />

      {/* Predictive Core Quantum Diamond Node */}
      <polygon points="24,20 27,24 24,28 21,24" fill="#38BDF8" />
      <circle cx="32" cy="6" r="2.2" fill="#E0F2FE" />
    </svg>
  );
}


/**
 * Crypto Orbit & 24/7 Liquidity Mesh Icon
 * Decentralized cryptographic hash node wrapped in perpetual 24/7 liquidity orbital rings.
 */
export function CryptoOrbitIcon({ className = "w-5 h-5", size }) {
  const style = size ? { width: size, height: size } : undefined;
  return (
    <svg 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
    >
      {/* Outer 24/7 Orbital Ring */}
      <ellipse cx="12" cy="12" rx="9.5" ry="4" transform="rotate(-30 12 12)" stroke="currentColor" strokeWidth="1.4" strokeDasharray="3 2" opacity="0.65" />
      <ellipse cx="12" cy="12" rx="9.5" ry="4" transform="rotate(30 12 12)" stroke="currentColor" strokeWidth="1.4" opacity="0.85" />
      
      {/* Central Hexagonal Cryptographic Core */}
      <polygon points="12,7 16,9.5 16,14.5 12,17 8,14.5 8,9.5" stroke="#A855F7" strokeWidth="1.6" strokeLinejoin="round" fill="#7E22CE" fillOpacity="0.2" />
      <circle cx="12" cy="12" r="1.8" fill="#E9D5FF" />

      {/* Satellite Validator Nodes */}
      <circle cx="19.5" cy="8" r="1.5" fill="#C084FC" />
      <circle cx="4.5" cy="16" r="1.5" fill="#C084FC" />
    </svg>
  );
}

/**
 * Global Wall Street & US Equities Icon
 * Meridian financial globe with cross-market institutional capital transmission vectors.
 */
export function GlobalMarketIcon({ className = "w-5 h-5", size }) {
  const style = size ? { width: size, height: size } : undefined;
  return (
    <svg 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
    >
      {/* Globe Sphere Bounds */}
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5" />
      
      {/* Latitudes & Longitudes */}
      <ellipse cx="12" cy="12" rx="4.5" ry="9" stroke="currentColor" strokeWidth="1.2" opacity="0.75" />
      <line x1="3" y1="12" x2="21" y2="12" stroke="currentColor" strokeWidth="1.2" opacity="0.75" />
      
      {/* Diagonal Transatlantic Capital Vector */}
      <path d="M5 19L19 5M19 5H14M19 5V10" stroke="#38BDF8" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}


/**
 * Crypto Microstructure Candlestick Wick Icon
 * Candlestick body with extended upper/lower liquidity absorption wicks and orderbook boundary brackets.
 */
export function MicrostructureWickIcon({ className = "w-5 h-5", size }) {
  const style = size ? { width: size, height: size } : undefined;
  return (
    <svg 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
    >
      {/* Extended Upper & Lower Rejection Wicks */}
      <line x1="12" y1="2" x2="12" y2="22" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      
      {/* Candlestick Real Body */}
      <rect x="8.5" y="8" width="7" height="8" rx="1.2" stroke="currentColor" strokeWidth="1.5" fill="currentColor" fillOpacity="0.2" />

      {/* Liquidity Absorption Brackets */}
      <path d="M5 4H7M5 20H7" stroke="#F59E0B" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M19 4H17M19 20H17" stroke="#F59E0B" strokeWidth="1.5" strokeLinecap="round" />

      {/* Horizontal Reversal Trigger Line */}
      <line x1="3" y1="12" x2="6" y2="12" stroke="#F59E0B" strokeWidth="1.4" strokeDasharray="1 1" />
      <line x1="18" y1="12" x2="21" y2="12" stroke="#F59E0B" strokeWidth="1.4" strokeDasharray="1 1" />
    </svg>
  );
}

/**
 * Three Hour Intraday Horizon Radar Icon
 * 3-hour temporal arc dial with forward prediction vector and micro-momentum quadrant sweeps.
 */
export function ThreeHourRadarIcon({ className = "w-5 h-5", size }) {
  const style = size ? { width: size, height: size } : undefined;
  return (
    <svg 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
    >
      <defs>
        <linearGradient id="three-hour-grad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="100%" stopColor="#6366F1" />
        </linearGradient>
      </defs>
      {/* Outer Chronometer Bezel */}
      <circle cx="12" cy="12" r="9.5" stroke="currentColor" strokeWidth="1.4" strokeDasharray="1.5 1.5" opacity="0.6" />
      {/* 3-Hour Horizon Swept Sector (from 12 to 3 o'clock / 90 deg arc) */}
      <path d="M12 12L12 3.5 A8.5 8.5 0 0 1 20.5 12 Z" fill="url(#three-hour-grad)" fillOpacity="0.25" stroke="#38BDF8" strokeWidth="1.4" />
      {/* Central Chrono Axis Node */}
      <circle cx="12" cy="12" r="2.2" fill="#38BDF8" />
      <circle cx="12" cy="12" r="0.8" fill="#FFFFFF" />
      {/* Forward Impulse Arrow towards 3-Hour Target */}
      <path d="M12 12L18.5 8.5" stroke="#FFFFFF" strokeWidth="1.6" strokeLinecap="round" />
      <circle cx="18.5" cy="8.5" r="1.4" fill="#38BDF8" />
      {/* Intraday Tick Marks */}
      <line x1="12" y1="2.5" x2="12" y2="4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="21.5" y1="12" x2="19.5" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="12" y1="21.5" x2="12" y2="19.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="2.5" y1="12" x2="4.5" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

