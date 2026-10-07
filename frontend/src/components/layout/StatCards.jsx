import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  ShieldAlert, 
  Compass, 
  Layers 
} from 'lucide-react';

export default function StatCards({ symbol, assetData, indicators, bars = [] }) {
  const lastPrice = indicators?.last_price || assetData?.last_price || 0;
  const change24h = indicators?.change_24h_percent ?? assetData?.change_24h_percent ?? 0;
  const isPositive = change24h >= 0;

  // Signal formatting
  const signal = indicators?.overall_signal || 'neutral';
  const getSignalBadge = (sig) => {
    switch (sig) {
      case 'strong_buy':
        return { label: 'STRONG BUY', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', dot: 'bg-emerald-400' };
      case 'buy':
        return { label: 'BUY', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', dot: 'bg-emerald-400' };
      case 'strong_sell':
        return { label: 'STRONG SELL', color: 'bg-rose-500/10 text-rose-400 border-rose-500/30', dot: 'bg-rose-400' };
      case 'sell':
        return { label: 'SELL', color: 'bg-rose-500/10 text-rose-400 border-rose-500/30', dot: 'bg-rose-400' };
      default:
        return { label: 'NEUTRAL', color: 'bg-slate-500/10 text-slate-400 border-slate-500/30', dot: 'bg-slate-400' };
    }
  };

  const sigBadge = getSignalBadge(signal);

  // 24h High & Low from recent bars
  const recentBars = bars.slice(-24);
  const high24h = recentBars.length ? Math.max(...recentBars.map(b => b.high)) : lastPrice * 1.02;
  const low24h = recentBars.length ? Math.min(...recentBars.map(b => b.low)) : lastPrice * 0.98;
  const rangePct = high24h > low24h ? Math.min(100, Math.max(0, ((lastPrice - low24h) / (high24h - low24h)) * 100)) : 50;

  const rsi = indicators?.rsi_14 ?? 50;
  const rsiStatus = indicators?.rsi_status || 'neutral';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Card 1: Harga Terkini & 24h Change */}
      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all duration-200 hover:-translate-y-0.5 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Harga Terkini</span>
          <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400">
            <Activity className="w-4 h-4" />
          </div>
        </div>
        <div className="text-2xl sm:text-3xl font-bold font-mono text-white mb-2">
          ${lastPrice?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
        </div>
        <div className="flex items-center space-x-2">
          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium font-mono border ${
            isPositive 
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
              : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
          }`}>
            {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {isPositive ? '+' : ''}{change24h}%
          </span>
          <span className="text-xs text-slate-500">24 Jam Terakhir</span>
        </div>
      </div>

      {/* Card 2: Overall Signal */}
      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all duration-200 hover:-translate-y-0.5 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Sinyal Komposit</span>
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
            <Compass className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-center space-x-2.5 mb-2 mt-1">
          <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm font-bold font-mono border ${sigBadge.color}`}>
            <span className={`w-2 h-2 rounded-full ${sigBadge.dot} animate-pulse`} />
            {sigBadge.label}
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-2">
          {signal.includes('buy') ? 'Momentum teknikal dan MA dominan tren naik.' : signal.includes('sell') ? 'Tekanan jual dominan di bawah level resistensi.' : 'Kondisi pasar konsolidasi netral.'}
        </p>
      </div>

      {/* Card 3: RSI (14) Momentum */}
      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all duration-200 hover:-translate-y-0.5 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">RSI 14 Momentum</span>
          <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
            <Layers className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline space-x-2 mb-2">
          <span className="text-2xl sm:text-3xl font-bold font-mono text-white">{rsi}</span>
          <span className="text-xs font-semibold uppercase text-slate-400">
            / 100 ({rsiStatus})
          </span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden mt-1">
          <div 
            className={`h-full rounded-full transition-all duration-500 ${
              rsi > 70 ? 'bg-rose-500' : rsi < 30 ? 'bg-emerald-500' : 'bg-blue-500'
            }`}
            style={{ width: `${Math.min(100, Math.max(0, rsi))}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
          <span>30 (Oversold)</span>
          <span>70 (Overbought)</span>
        </div>
      </div>

      {/* Card 4: 24h High/Low Slider */}
      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all duration-200 hover:-translate-y-0.5 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Rentang 24 Jam</span>
          <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
            <ShieldAlert className="w-4 h-4" />
          </div>
        </div>
        <div className="flex justify-between text-xs font-mono font-medium text-slate-300 mb-1">
          <span>L: {isIdr ? `Rp ${low24h?.toLocaleString('id-ID')}` : `$${low24h?.toFixed(2)}`}</span>
          <span>H: {isIdr ? `Rp ${high24h?.toLocaleString('id-ID')}` : `$${high24h?.toFixed(2)}`}</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-2 relative overflow-hidden my-2">
          <div 
            className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"
            style={{ width: `${rangePct}%` }}
          />
        </div>
        <div className="text-[11px] text-slate-400 text-center font-mono">
          Posisi Harga Saat Ini: <span className="text-white font-semibold">{rangePct.toFixed(0)}%</span> dari rentang harian
        </div>
      </div>
    </div>
  );
}
