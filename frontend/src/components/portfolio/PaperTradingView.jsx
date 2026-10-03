import React, { useEffect, useState } from 'react';
import { 
  Briefcase, 
  TrendingUp, 
  TrendingDown, 
  Wallet, 
  PlusCircle, 
  X, 
  RotateCcw,
  RefreshCw,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { getPortfolioSummary, buyAsset, closeTrade, resetPortfolio } from '../../api';

export default function PaperTradingView({ tickers = [], defaultSymbol = 'BTC/USDT' }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [buySymbol, setBuySymbol] = useState(defaultSymbol);
  const [buyAmount, setBuyAmount] = useState(0.05);
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const res = await getPortfolioSummary();
      setSummary(res.data.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const selectedTicker = tickers.find(t => t.symbol === buySymbol) || { last_price: 1000 };
  const estimatedCost = (buyAmount || 0) * (selectedTicker.last_price || 0);

  const handleBuy = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    setNotification(null);
    try {
      const res = await buyAsset({ symbol: buySymbol, amount: parseFloat(buyAmount) });
      setNotification({ type: 'success', text: res.data.message });
      await fetchSummary();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Gagal mengeksekusi pembelian';
      setNotification({ type: 'error', text: msg });
    } finally {
      setActionLoading(false);
    }
  };

  const handleClose = async (tradeId) => {
    setActionLoading(true);
    setNotification(null);
    try {
      const res = await closeTrade(tradeId);
      setNotification({ type: 'success', text: res.data.message });
      await fetchSummary();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Gagal menutup posisi';
      setNotification({ type: 'error', text: msg });
    } finally {
      setActionLoading(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Apakah Anda yakin ingin mereset portofolio simulasi ke saldo awal $10,000?')) return;
    setActionLoading(true);
    try {
      const res = await resetPortfolio();
      setNotification({ type: 'success', text: res.data.message });
      await fetchSummary();
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white font-mono flex items-center space-x-2">
            <Briefcase className="w-5 h-5 text-emerald-400" />
            <span>PAPER TRADING VIRTUAL PORTFOLIO</span>
          </h2>
          <p className="text-xs text-slate-400">
            Latihan trading saham dan kripto bebas risiko secara live dengan saldo virtual $10,000.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={fetchSummary}
            disabled={loading}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white flex items-center space-x-1.5 transition-colors font-mono"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-400' : ''}`} />
            <span>Segarkan Nilai</span>
          </button>

          <button
            onClick={handleReset}
            className="px-3 py-1.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 hover:bg-rose-500/20 flex items-center space-x-1.5 transition-colors font-mono font-semibold"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset ($10k)</span>
          </button>
        </div>
      </div>

      {notification && (
        <div className={`p-4 rounded-xl border text-xs flex items-center justify-between font-mono ${
          notification.type === 'success' 
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' 
            : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
        }`}>
          <div className="flex items-center space-x-2">
            {notification.type === 'success' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
            <span>{notification.text}</span>
          </div>
          <button onClick={() => setNotification(null)}>
            <X className="w-3.5 h-3.5 opacity-60 hover:opacity-100" />
          </button>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5 font-mono shadow-sm">
          <div className="text-xs text-slate-500 uppercase">Total Nilai Portofolio</div>
          <div className="text-2xl font-black text-white mt-1">
            ${summary?.total_portfolio_value?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Saldo Kas: <strong className="text-slate-200">${summary?.cash_balance?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</strong>
          </div>
        </div>

        <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5 font-mono shadow-sm">
          <div className="text-xs text-slate-500 uppercase">Total Return (ROI)</div>
          <div className={`text-2xl font-black mt-1 ${
            (summary?.total_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
          }`}>
            {(summary?.total_pnl || 0) >= 0 ? '+' : ''}${summary?.total_pnl?.toLocaleString()} ({(summary?.total_roi_percent || 0) >= 0 ? '+' : ''}{summary?.total_roi_percent}%)
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Dari Modal Awal $10,000.00
          </div>
        </div>

        <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5 font-mono shadow-sm">
          <div className="text-xs text-slate-500 uppercase">Unrealized PnL (Posisi Aktif)</div>
          <div className={`text-2xl font-black mt-1 ${
            (summary?.unrealized_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
          }`}>
            {(summary?.unrealized_pnl || 0) >= 0 ? '+' : ''}${summary?.unrealized_pnl?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {summary?.open_trades?.length || 0} Posisi Terbuka
          </div>
        </div>

        <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5 font-mono shadow-sm">
          <div className="text-xs text-slate-500 uppercase">Win Rate Transaksi Selesai</div>
          <div className="text-2xl font-black text-blue-400 mt-1">
            {summary?.win_rate || 0}%
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {summary?.closed_trades?.length || 0} Trade Terealisasi
          </div>
        </div>
      </div>

      {/* Main Trading Action Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Order Form */}
        <div className="lg:col-span-4 bg-[#111827] border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-4 font-mono flex items-center space-x-2">
            <PlusCircle className="w-4 h-4 text-blue-400" />
            <span>Eksekusi Order Beli</span>
          </h3>

          <form onSubmit={handleBuy} className="space-y-4 font-mono">
            <div>
              <label className="block text-xs uppercase text-slate-400 mb-1.5">Pilih Aset</label>
              <select
                value={buySymbol}
                onChange={(e) => setBuySymbol(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
              >
                {tickers.map(t => (
                  <option key={t.symbol} value={t.symbol}>
                    {t.symbol} - ${t.last_price?.toLocaleString()}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs uppercase text-slate-400 mb-1.5">Jumlah Unit / Lot</label>
              <input
                type="number"
                step="any"
                min="0.0001"
                value={buyAmount}
                onChange={(e) => setBuyAmount(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-1">
              <div className="flex justify-between text-slate-400">
                <span>Harga Pasar:</span>
                <span className="text-slate-200 font-bold">${selectedTicker.last_price?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Estimasi Biaya:</span>
                <span className="text-emerald-400 font-bold">${estimatedCost?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between text-slate-400 pt-1 border-t border-slate-800">
                <span>Sisa Kas Anda:</span>
                <span className="text-slate-300 font-semibold">${summary?.cash_balance?.toLocaleString()}</span>
              </div>
            </div>

            <button
              type="submit"
              disabled={actionLoading || estimatedCost > (summary?.cash_balance || 0)}
              className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-xl font-bold text-sm transition-all shadow-lg shadow-emerald-600/20"
            >
              {actionLoading ? 'Mengeksekusi...' : `Beli ${buyAmount} ${buySymbol}`}
            </button>
          </form>
        </div>

        {/* Positions & Trade Tables */}
        <div className="lg:col-span-8 space-y-6">
          {/* Open Positions */}
          <div className="bg-[#111827] border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-800 font-mono text-xs font-bold text-slate-300 flex items-center justify-between">
              <span>POSISI TERBUKA SAAT INI ({summary?.open_trades?.length || 0})</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs font-mono">
                <thead className="bg-slate-950/70 text-[10px] uppercase text-slate-500">
                  <tr>
                    <th className="py-2.5 px-4">Aset</th>
                    <th className="py-2.5 px-4 text-right">Unit</th>
                    <th className="py-2.5 px-4 text-right">Harga Beli</th>
                    <th className="py-2.5 px-4 text-right">Harga Live</th>
                    <th className="py-2.5 px-4 text-right">Unrealized PnL</th>
                    <th className="py-2.5 px-4 text-center">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {summary?.open_trades && summary.open_trades.length > 0 ? (
                    summary.open_trades.map(t => (
                      <tr key={t.id} className="hover:bg-slate-800/30">
                        <td className="py-3 px-4 font-bold text-white">{t.symbol}</td>
                        <td className="py-3 px-4 text-right text-slate-300">{t.amount}</td>
                        <td className="py-3 px-4 text-right text-slate-400">${t.entry_price?.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-slate-200 font-semibold">${t.current_price?.toLocaleString()}</td>
                        <td className={`py-3 px-4 text-right font-bold ${
                          t.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}>
                          {t.unrealized_pnl >= 0 ? '+' : ''}${t.unrealized_pnl} ({t.unrealized_pnl_percent >= 0 ? '+' : ''}{t.unrealized_pnl_percent}%)
                        </td>
                        <td className="py-3 px-4 text-center">
                          <button
                            onClick={() => handleClose(t.id)}
                            disabled={actionLoading}
                            className="px-2.5 py-1 rounded-lg bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 text-[11px] font-bold border border-rose-500/30 transition-colors"
                          >
                            Tutup Posisi
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" className="p-6 text-center text-xs text-slate-500 font-sans">
                        Tidak ada posisi terbuka saat ini. Masukkan order beli di panel sebelah kiri untuk memulai.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Closed Trades History */}
          <div className="bg-[#111827] border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-800 font-mono text-xs font-bold text-slate-300">
              <span>RIWAYAT TRANSAKSI DITUTUP ({summary?.closed_trades?.length || 0})</span>
            </div>

            <div className="overflow-x-auto max-h-56 overflow-y-auto">
              <table className="w-full text-left border-collapse text-xs font-mono">
                <thead className="bg-slate-950/70 text-[10px] uppercase text-slate-500 sticky top-0">
                  <tr>
                    <th className="py-2 px-4">Aset</th>
                    <th className="py-2 px-4 text-right">Unit</th>
                    <th className="py-2 px-4 text-right">Harga Beli</th>
                    <th className="py-2 px-4 text-right">Harga Jual</th>
                    <th className="py-2 px-4 text-right">PnL Terealisasi</th>
                    <th className="py-2 px-4 text-center">Tanggal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {summary?.closed_trades && summary.closed_trades.length > 0 ? (
                    summary.closed_trades.map(t => (
                      <tr key={t.id} className="hover:bg-slate-800/20">
                        <td className="py-2.5 px-4 font-bold text-white">{t.symbol}</td>
                        <td className="py-2.5 px-4 text-right text-slate-400">{t.amount}</td>
                        <td className="py-2.5 px-4 text-right text-slate-400">${t.entry_price?.toLocaleString()}</td>
                        <td className="py-2.5 px-4 text-right text-slate-200">${t.closed_price?.toLocaleString()}</td>
                        <td className={`py-2.5 px-4 text-right font-bold ${
                          t.pnl_amount >= 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}>
                          {t.pnl_amount >= 0 ? '+' : ''}${t.pnl_amount} ({t.pnl_percent >= 0 ? '+' : ''}{t.pnl_percent}%)
                        </td>
                        <td className="py-2.5 px-4 text-center text-slate-500 text-[11px]">{t.executed_at}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" className="p-4 text-center text-xs text-slate-500 font-sans">
                        Belum ada riwayat transaksi yang ditutup.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
