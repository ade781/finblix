import React from 'react';
import { Clock, RefreshCw, SlidersHorizontal, Download } from 'lucide-react';

export default function ChartToolbar({
  symbol,
  assetName,
  timeframe,
  setTimeframe,
  overlays,
  setOverlays,
  onRefresh,
  loading
}) {
  const timeframes = [
    { id: '15m', label: '15M' },
    { id: '1h', label: '1H' },
    { id: '4h', label: '4H' },
    { id: '1d', label: '1D' },
    { id: '1w', label: '1W' },
  ];

  const toggleOverlay = (key) => {
    setOverlays(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-900/80 border-b border-slate-800 rounded-t-2xl">
      {/* Symbol Title & Timeframe Selector */}
      <div className="flex items-center space-x-3">
        <div>
          <span className="text-base font-bold text-white font-mono tracking-tight mr-2">{symbol}</span>
          <span className="text-xs text-slate-400 hidden sm:inline">{assetName}</span>
        </div>

        <div className="flex items-center bg-slate-950 rounded-xl p-1 border border-slate-800">
          {timeframes.map(tf => (
            <button
              key={tf.id}
              onClick={() => setTimeframe(tf.id)}
              className={`px-2.5 py-1 text-xs font-mono font-medium rounded-lg transition-all ${
                timeframe === tf.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {/* Indicator Overlay Toggles & Refresh */}
      <div className="flex items-center space-x-2">
        <div className="hidden md:flex items-center space-x-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => toggleOverlay('ema20')}
            className={`px-2 py-1 rounded-lg font-mono transition-all flex items-center space-x-1 ${
              overlays.ema20 
                ? 'bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/40' 
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span>EMA 20</span>
          </button>

          <button
            onClick={() => toggleOverlay('ema50')}
            className={`px-2 py-1 rounded-lg font-mono transition-all flex items-center space-x-1 ${
              overlays.ema50 
                ? 'bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/40' 
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>EMA 50</span>
          </button>

          <button
            onClick={() => toggleOverlay('ema200')}
            className={`px-2 py-1 rounded-lg font-mono transition-all flex items-center space-x-1 ${
              overlays.ema200 
                ? 'bg-purple-500/20 text-purple-300 font-semibold border border-purple-500/40' 
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-purple-400" />
            <span>EMA 200</span>
          </button>

          <button
            onClick={() => toggleOverlay('bollinger')}
            className={`px-2 py-1 rounded-lg font-mono transition-all flex items-center space-x-1 ${
              overlays.bollinger 
                ? 'bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/40' 
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-indigo-400" />
            <span>Bollinger Bands</span>
          </button>
        </div>

          <button
            onClick={() => {
              const enc = encodeURIComponent(symbol);
              window.open(`/api/v1/market/export/${enc}?timeframe=${timeframe}`, '_blank');
            }}
            className="p-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-colors flex items-center space-x-1.5 text-xs font-mono"
            title="Unduh Data Candlestick CSV"
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            <span className="hidden sm:inline">Export CSV</span>
          </button>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-400 hover:text-slate-100 hover:border-slate-700 transition-colors"
            title="Segarkan Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
      </div>
    </div>
  );
}
