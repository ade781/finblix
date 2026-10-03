import React from 'react';
import { Gauge, Cpu, TrendingUp } from 'lucide-react';

export default function IndicatorSubChart({ indicators }) {
  if (!indicators) return null;

  const { rsi_14, rsi_status, macd, ema, bollinger, last_price } = indicators;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
      {/* 1. RSI Indicator Panel */}
      <div className="bg-[#0c1220] border border-slate-800/80 rounded-2xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Gauge className="w-4 h-4 text-emerald-400" />
            <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-300">RSI 14 (Oscillator)</h4>
          </div>
          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
            rsi_status === 'overbought' ? 'bg-rose-500/10 text-rose-300 border-rose-500/20' :
            rsi_status === 'oversold' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' :
            'bg-slate-800/60 text-slate-300 border-slate-700/40'
          }`}>
            {rsi_status}
          </span>
        </div>
        <div className="flex items-baseline space-x-2 mb-2 font-mono">
          <span className="text-2xl font-black text-white">{rsi_14 ?? '--'}</span>
          <span className="text-xs text-slate-500">/ 100</span>
        </div>
        <div className="w-full bg-slate-900 rounded-full h-2 relative overflow-hidden mb-2 border border-slate-800/80">
          {/* 30 line */}
          <div className="absolute left-[30%] top-0 bottom-0 w-0.5 bg-slate-700 z-10" />
          {/* 70 line */}
          <div className="absolute left-[70%] top-0 bottom-0 w-0.5 bg-slate-700 z-10" />
          <div 
            className={`h-full rounded-full transition-all duration-500 ${
              rsi_14 > 70 ? 'bg-rose-500' : rsi_14 < 30 ? 'bg-emerald-500' : 'bg-blue-500'
            }`}
            style={{ width: `${Math.min(100, Math.max(0, rsi_14 || 50))}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>Oversold &lt; 30</span>
          <span>Netral 40-60</span>
          <span>Overbought &gt; 70</span>
        </div>
      </div>

      {/* 2. MACD Panel */}
      <div className="bg-[#0c1220] border border-slate-800/80 rounded-2xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-300">MACD (12, 26, 9)</h4>
          </div>
          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
            (macd?.histogram || 0) >= 0 
              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' 
              : 'bg-rose-500/10 text-rose-300 border-rose-500/20'
          }`}>
            {(macd?.histogram || 0) >= 0 ? 'Bullish Cross' : 'Bearish Cross'}
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2 font-mono text-center">
          <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800/80">
            <div className="text-[10px] text-slate-500 mb-0.5">MACD</div>
            <div className="text-xs font-bold text-cyan-300">{macd?.macd_line ?? '--'}</div>
          </div>
          <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800/80">
            <div className="text-[10px] text-slate-500 mb-0.5">Signal</div>
            <div className="text-xs font-bold text-amber-300">{macd?.signal_line ?? '--'}</div>
          </div>
          <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800/80">
            <div className="text-[10px] text-slate-500 mb-0.5">Hist</div>
            <div className={`text-xs font-bold ${
              (macd?.histogram || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}>
              {macd?.histogram ?? '--'}
            </div>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 mt-3 font-mono leading-relaxed">
          {(macd?.histogram || 0) >= 0 
            ? 'Histogram positif: Tekanan beli meningkat terhadap garis sinyal.'
            : 'Histogram negatif: Momentum jual sedang terjadi di bawah rata-rata gerak.'
          }
        </p>
      </div>

      {/* 3. Moving Averages & Bollinger Panel */}
      <div className="bg-[#0c1220] border border-slate-800/80 rounded-2xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-purple-400" />
            <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-300">Tren EMA & BB</h4>
          </div>
          <span className="text-[11px] font-mono text-slate-500">
            Ref: {last_price}
          </span>
        </div>

        <div className="space-y-2 text-xs font-mono">
          <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
            <span className="text-amber-400 font-medium">EMA 20</span>
            <span className="text-slate-200 font-bold">{ema?.ema_20 ?? '--'}</span>
          </div>
          <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
            <span className="text-cyan-400 font-medium">EMA 50</span>
            <span className="text-slate-200 font-bold">{ema?.ema_50 ?? '--'}</span>
          </div>
          <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
            <span className="text-purple-400 font-medium">EMA 200</span>
            <span className="text-slate-200 font-bold">{ema?.ema_200 ?? '--'}</span>
          </div>
          <div className="flex justify-between items-center py-1">
            <span className="text-indigo-400 font-medium">BB Bands [L-U]</span>
            <span className="text-slate-300 font-bold">
              {bollinger?.lower ?? '--'} - {bollinger?.upper ?? '--'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
