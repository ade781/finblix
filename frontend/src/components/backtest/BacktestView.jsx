import React, { useState } from 'react';
import { 
  FlaskConical, 
  TrendingUp, 
  TrendingDown, 
  CheckCircle2, 
  XCircle, 
  ArrowRight, 
  ShieldAlert,
  Percent,
  History,
  Info
} from 'lucide-react';
import { runBacktest } from '../../api';

export default function BacktestView({ tickers = [], defaultSymbol = 'BTC/USDT' }) {
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [strategy, setStrategy] = useState('rsi_reversal');
  const [initialCapital, setInitialCapital] = useState(10000);
  const [feePercent, setFeePercent] = useState(0.1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    try {
      const res = await runBacktest({
        symbol,
        strategy,
        initial_capital: parseFloat(initialCapital),
        fee_percent: parseFloat(feePercent),
      });
      setResult(res.data.data);
    } catch (e) {
      console.error('Error running backtest:', e);
    } finally {
      setLoading(false);
    }
  };

  const getStrategyDescription = () => {
    switch (strategy) {
      case 'rsi_reversal':
        return 'Strategi RSI Reversal: Beli saat RSI 14 menyentuh zona oversold (< 35) dan Jual saat RSI 14 menembus overbought (> 68).';
      case 'ema_cross':
        return 'Strategi EMA Golden Cross: Beli saat EMA 20 memotong ke atas EMA 50 (tren naik baru), dan Jual saat EMA 20 memotong ke bawah EMA 50 (tren turun).';
      case 'macd_cross':
        return 'Strategi MACD Signal Cross: Beli saat garis MACD menembus ke atas Garis Sinyal, dan Jual saat garis MACD memotong ke bawah Garis Sinyal.';
      default:
        return '';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white font-mono flex items-center space-x-2">
            <FlaskConical className="w-5 h-5 text-indigo-400" />
            <span>QUANTITATIVE STRATEGY BACKTESTER</span>
          </h2>
          <p className="text-xs text-slate-400">
            Uji hipotesis dan algoritma trading Anda pada data candlestick historis riil sebelum mempertaruhkan modal.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-4 bg-[#111827] border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-4 font-mono">
            Parameter Backtest
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5 font-mono">
                Pilih Instrumen Aset
              </label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
              >
                {tickers.map(t => (
                  <option key={t.symbol} value={t.symbol}>
                    {t.symbol} - {t.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5 font-mono">
                Pilihan Strategi Trading
              </label>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
              >
                <option value="rsi_reversal">RSI 14 Mean Reversal (Oversold / Overbought)</option>
                <option value="ema_cross">EMA Cross (EMA 20 vs EMA 50 Trend Follow)</option>
                <option value="macd_cross">MACD Momentum Signal Crossover</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5 font-mono">
                Modal Awal Simulasi ($)
              </label>
              <input
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5 font-mono">
                Estimasi Biaya Transaksi / Fee (%)
              </label>
              <input
                type="number"
                step="0.01"
                value={feePercent}
                onChange={(e) => setFeePercent(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 leading-relaxed">
              <div className="flex items-center space-x-1 text-indigo-400 font-semibold mb-1">
                <Info className="w-3.5 h-3.5" />
                <span>Logika Strategi:</span>
              </div>
              {getStrategyDescription()}
            </div>

            <button
              onClick={handleRun}
              disabled={loading}
              className="w-full mt-2 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold text-sm transition-all shadow-lg shadow-indigo-600/30 flex items-center justify-center space-x-2"
            >
              {loading ? (
                <span>Menjalankan Mesin Backtest...</span>
              ) : (
                <>
                  <span>Jalankan Backtesting Historis</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-8 bg-[#111827] border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
          {result ? (
            <div className="space-y-6">
              {/* Summary Scorecard */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
                <div>
                  <span className="text-xs text-slate-500 uppercase font-mono">Hasil Pengujian Historis</span>
                  <h4 className="text-xl font-bold text-white font-mono">{symbol}</h4>
                </div>
                <div className={`px-4 py-2 rounded-xl border font-mono ${
                  result.total_pnl >= 0 
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
                    : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                }`}>
                  <div className="text-[10px] uppercase font-semibold">Total Profit / Loss</div>
                  <div className="text-2xl font-black">
                    {result.total_pnl >= 0 ? '+' : ''}${result.total_pnl?.toLocaleString()} ({result.total_pnl_percent >= 0 ? '+' : ''}{result.total_pnl_percent}%)
                  </div>
                </div>
              </div>

              {/* KPI Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Win Rate (%)</div>
                  <div className="text-xl font-black text-white mt-1">
                    {result.win_rate}%
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    {result.win_trades} Menang / {result.loss_trades} Kalah
                  </div>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Total Eksekusi</div>
                  <div className="text-xl font-black text-blue-400 mt-1">
                    {result.total_trades} Trade
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    Transaksi Lengkap
                  </div>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Max Drawdown</div>
                  <div className="text-xl font-black text-rose-400 mt-1">
                    {result.max_drawdown}%
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    Penurunan Terburuk
                  </div>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Saldo Akhir</div>
                  <div className="text-xl font-black text-emerald-400 mt-1">
                    ${result.final_capital?.toLocaleString()}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    Dari ${result.initial_capital?.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Trade Log Table */}
              <div className="bg-slate-950 rounded-xl border border-slate-800 overflow-hidden">
                <div className="p-3 border-b border-slate-800 text-xs font-mono font-bold text-slate-300 flex items-center justify-between">
                  <div className="flex items-center space-x-1.5">
                    <History className="w-3.5 h-3.5 text-indigo-400" />
                    <span>LOG RIWAYAT TRANSAKSI STRATEGI</span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-normal">
                    {result.trades.length} Catatan
                  </span>
                </div>

                <div className="max-h-56 overflow-y-auto">
                  {result.trades.length > 0 ? (
                    <table className="w-full text-left border-collapse text-xs font-mono">
                      <thead className="bg-slate-900/80 text-[10px] uppercase text-slate-500 sticky top-0">
                        <tr>
                          <th className="py-2 px-3">Tgl Entry</th>
                          <th className="py-2 px-3">Tgl Exit</th>
                          <th className="py-2 px-3 text-right">Harga Beli</th>
                          <th className="py-2 px-3 text-right">Harga Jual</th>
                          <th className="py-2 px-3 text-right">PnL Net</th>
                          <th className="py-2 px-3 text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/40">
                        {result.trades.map((t, idx) => (
                          <tr key={idx} className="hover:bg-slate-800/20">
                            <td className="py-2 px-3 text-slate-300">{t.entry_date}</td>
                            <td className="py-2 px-3 text-slate-400">{t.exit_date}</td>
                            <td className="py-2 px-3 text-right text-slate-300">${t.entry_price?.toLocaleString()}</td>
                            <td className="py-2 px-3 text-right text-slate-300">${t.exit_price?.toLocaleString()}</td>
                            <td className={`py-2 px-3 text-right font-bold ${
                              t.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                            }`}>
                              {t.pnl >= 0 ? '+' : ''}${t.pnl} ({t.pnl_percent >= 0 ? '+' : ''}{t.pnl_percent}%)
                            </td>
                            <td className="py-2 px-3 text-center">
                              {t.is_win ? (
                                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-bold">
                                  <CheckCircle2 className="w-3 h-3" /> WIN
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 text-[10px] text-rose-400 font-bold">
                                  <XCircle className="w-3 h-3" /> LOSS
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div className="p-6 text-center text-xs text-slate-500">
                      Strategi tidak menghasilkan sinyal beli/jual pada rentang waktu data yang tersedia. Coba ganti strategi atau pilih instrumen aset lain.
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-500">
              <FlaskConical className="w-12 h-12 mb-3 text-slate-700" />
              <h5 className="font-semibold text-slate-300 text-sm">Siap untuk Menguji Strategi</h5>
              <p className="text-xs max-w-sm mt-1">
                Pilih aset dan algoritma di panel sebelah kiri lalu klik "Jalankan Backtesting Historis" untuk melihat metrik Win Rate dan kurva performa.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
