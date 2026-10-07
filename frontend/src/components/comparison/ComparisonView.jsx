import React, { useEffect, useState } from 'react';
import { GitCompare, TrendingUp, TrendingDown, CheckSquare, Square, RefreshCw, Trophy } from 'lucide-react';
import api from '../../api';

const AVAILABLE_COMPARISON = [
  'BTC/USDT',
  'ETH/USDT',
  'SOL/USDT',
  'BNB/USDT',
  'XRP/USDT',
  'DOGE/USDT',
  'ADA/USDT',
  'AVAX/USDT',
  'LINK/USDT',
  'SUI/USDT'
];

const COLOR_PALETTE = [
  '#3b82f6', // blue
  '#10b981', // emerald
  '#f59e0b', // amber
  '#a855f7', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
];

export default function ComparisonView() {
  const [selectedSymbols, setSelectedSymbols] = useState(['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']);
  const [timeframe, setTimeframe] = useState('1d');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchComparison = async () => {
    if (selectedSymbols.length === 0) return;
    setLoading(true);
    try {
      const res = await api.get('/market/comparison', {
        params: {
          symbols: selectedSymbols.join(','),
          timeframe: timeframe,
          limit: 90
        }
      });
      setData(res.data.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparison();
  }, [selectedSymbols, timeframe]);

  const toggleSymbol = (sym) => {
    if (selectedSymbols.includes(sym)) {
      if (selectedSymbols.length > 1) {
        setSelectedSymbols(selectedSymbols.filter(s => s !== sym));
      }
    } else {
      if (selectedSymbols.length < 5) {
        setSelectedSymbols([...selectedSymbols, sym]);
      }
    }
  };

  // Determine top performer
  let topPerformer = null;
  let topReturn = -Infinity;

  if (data && data.series) {
    Object.entries(data.series).forEach(([sym, points]) => {
      if (points.length > 0) {
        const lastReturn = points[points.length - 1].pct_return;
        if (lastReturn > topReturn) {
          topReturn = lastReturn;
          topPerformer = sym;
        }
      }
    });
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white font-mono flex items-center space-x-2">
            <GitCompare className="w-5 h-5 text-indigo-400" />
            <span>MULTI-ASSET PERFORMANCE COMPARISON OVERLAY</span>
          </h2>
          <p className="text-xs text-slate-400">
            Perbandingan kinerja keuntungan relatif (% Normalized Return) antar aset Kripto teratas.
          </p>
        </div>

        <button
          onClick={fetchComparison}
          disabled={loading}
          className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white flex items-center space-x-1.5 transition-colors font-mono self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          <span>Segarkan Data</span>
        </button>
      </div>

      {/* Asset Selector Chips */}
      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-4">
        <div className="text-xs font-semibold uppercase text-slate-400 mb-2 font-mono">
          Pilih Aset untuk Ditumpuk (Maksimal 5 Aset):
        </div>
        <div className="flex flex-wrap gap-2">
          {AVAILABLE_COMPARISON.map(sym => {
            const isSelected = selectedSymbols.includes(sym);
            const colorIdx = selectedSymbols.indexOf(sym);
            const color = isSelected ? COLOR_PALETTE[colorIdx % COLOR_PALETTE.length] : null;

            return (
              <button
                key={sym}
                onClick={() => toggleSymbol(sym)}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all flex items-center space-x-1.5 border ${
                  isSelected
                    ? 'text-white shadow-md'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
                style={isSelected ? { backgroundColor: `${color}25`, borderColor: color, color: color } : {}}
              >
                {isSelected ? <CheckSquare className="w-3.5 h-3.5" /> : <Square className="w-3.5 h-3.5" />}
                <span>{sym}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Scorecard Comparison Cards */}
      {data && data.series && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Object.entries(data.series).map(([sym, points], idx) => {
            const lastP = points.length > 0 ? points[points.length - 1] : { pct_return: 0, raw_price: 0 };
            const isWinner = sym === topPerformer;
            const color = COLOR_PALETTE[idx % COLOR_PALETTE.length];

            return (
              <div
                key={sym}
                className="bg-[#111827] border rounded-2xl p-4 font-mono relative overflow-hidden"
                style={{ borderColor: isWinner ? color : '#1f2937' }}
              >
                {isWinner && (
                  <div 
                    className="absolute top-0 right-0 px-2 py-0.5 rounded-bl-xl text-[10px] font-bold text-white flex items-center space-x-1"
                    style={{ backgroundColor: color }}
                  >
                    <Trophy className="w-3 h-3" />
                    <span>LEADER</span>
                  </div>
                )}
                <div className="flex items-center space-x-1.5 mb-1">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                  <span className="text-xs font-bold text-slate-300">{sym}</span>
                </div>
                <div className={`text-xl font-black mt-1 ${lastP.pct_return >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {lastP.pct_return >= 0 ? '+' : ''}{lastP.pct_return}%
                </div>
                <div className="text-[11px] text-slate-500 mt-1">
                  Harga Terkini: ${lastP.raw_price?.toLocaleString()}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Normalized Performance Timeline Table */}
      <div className="bg-[#111827] border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 font-mono text-xs font-bold text-slate-300">
          RIWAYAT PERTUMBUHAN NORMALISASI HISTORIS (% DARI TITIK AWAL)
        </div>
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          {data && data.series && Object.keys(data.series).length > 0 ? (
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead className="bg-slate-950/70 text-[10px] uppercase text-slate-500 sticky top-0">
                <tr>
                  <th className="py-2.5 px-4">Tanggal (UTC)</th>
                  {selectedSymbols.map((sym, idx) => (
                    <th key={sym} className="py-2.5 px-4 text-right" style={{ color: COLOR_PALETTE[idx % COLOR_PALETTE.length] }}>
                      {sym} (% Return)
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {/* Take latest 15 points */}
                {data.series[selectedSymbols[0]]?.slice(-15).reverse().map((pt, rIdx) => {
                  const targetTime = pt.time;
                  return (
                    <tr key={rIdx} className="hover:bg-slate-800/20">
                      <td className="py-2.5 px-4 text-slate-400">{pt.date}</td>
                      {selectedSymbols.map(sym => {
                        const sPoints = data.series[sym] || [];
                        const match = sPoints.find(p => p.time === targetTime) || sPoints[sPoints.length - 1 - rIdx] || { pct_return: 0 };
                        const ret = match.pct_return;
                        return (
                          <td key={sym} className={`py-2.5 px-4 text-right font-bold ${
                            ret >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}>
                            {ret >= 0 ? '+' : ''}{ret}%
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center text-xs text-slate-500 font-sans">
              Memuat data perbandingan performa multi-aset...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
