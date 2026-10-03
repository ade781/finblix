import React, { useState } from 'react';
import { 
  Calculator, 
  TrendingUp, 
  TrendingDown, 
  ShieldCheck, 
  PieChart, 
  DollarSign, 
  ArrowRight,
  Sparkles,
  Info
} from 'lucide-react';
import { simulateWhatIf, calculateRisk } from '../../api';

export default function WhatIfView({ tickers = [], defaultSymbol = 'BTC/USDT' }) {
  const [subTab, setSubTab] = useState('dca'); // 'dca' or 'risk'

  // DCA State
  const [dcaSymbol, setDcaSymbol] = useState(defaultSymbol);
  const [strategy, setStrategy] = useState('dca');
  const [amount, setAmount] = useState(100);
  const [period, setPeriod] = useState('monthly');
  const [dcaLoading, setDcaLoading] = useState(false);
  const [dcaResult, setDcaResult] = useState(null);

  // Risk Calculator State
  const [capital, setCapital] = useState(10000);
  const [riskPct, setRiskPct] = useState(1.5);
  const [entryPrice, setEntryPrice] = useState(68000);
  const [stopLoss, setStopLoss] = useState(66000);
  const [takeProfit, setTakeProfit] = useState(73000);
  const [riskLoading, setRiskLoading] = useState(false);
  const [riskResult, setRiskResult] = useState(null);

  const handleRunDCA = async () => {
    setDcaLoading(true);
    try {
      const res = await simulateWhatIf({
        symbol: dcaSymbol,
        strategy: strategy,
        amount_per_period: parseFloat(amount),
        period: period,
        start_date: '2023-01-01',
      });
      setDcaResult(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setDcaLoading(false);
    }
  };

  const handleRunRisk = async () => {
    setRiskLoading(true);
    try {
      const res = await calculateRisk({
        total_capital: parseFloat(capital),
        risk_percent: parseFloat(riskPct),
        entry_price: parseFloat(entryPrice),
        stop_loss_price: parseFloat(stopLoss),
        take_profit_price: parseFloat(takeProfit),
      });
      setRiskResult(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setRiskLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Tab Switcher */}
      <div className="flex items-center space-x-2 bg-slate-900 p-1.5 rounded-2xl border border-slate-800 w-fit">
        <button
          onClick={() => setSubTab('dca')}
          className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all flex items-center space-x-2 ${
            subTab === 'dca'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Simulasi What-If (DCA vs Lump-Sum)</span>
        </button>

        <button
          onClick={() => setSubTab('risk')}
          className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all flex items-center space-x-2 ${
            subTab === 'risk'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Kalkulator Ukuran Posisi & Risiko (R:R)</span>
        </button>
      </div>

      {subTab === 'dca' ? (
        /* DCA SubTab */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Input Form */}
          <div className="lg:col-span-5 bg-[#111827] border border-slate-800 rounded-2xl p-6">
            <h3 className="text-base font-bold text-white mb-1 flex items-center space-x-2">
              <Calculator className="w-4 h-4 text-blue-400" />
              <span>Parameter Simulasi Finansial</span>
            </h3>
            <p className="text-xs text-slate-400 mb-6">
              Uji performa investasi historis jika Anda rutin menabung atau menyetor modal di awal.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5 font-mono">
                  Pilih Instrumen Aset
                </label>
                <select
                  value={dcaSymbol}
                  onChange={(e) => setDcaSymbol(e.target.value)}
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
                  Strategi Pembelian
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setStrategy('dca')}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold font-mono border transition-all ${
                      strategy === 'dca'
                        ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                        : 'bg-slate-950 border-slate-800 text-slate-400'
                    }`}
                  >
                    DCA (Rutin Berkala)
                  </button>
                  <button
                    type="button"
                    onClick={() => setStrategy('lump_sum')}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold font-mono border transition-all ${
                      strategy === 'lump_sum'
                        ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                        : 'bg-slate-950 border-slate-800 text-slate-400'
                    }`}
                  >
                    Lump-Sum (Sekali Beli)
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5 font-mono">
                  {strategy === 'dca' ? 'Nominal per Periode' : 'Total Modal Sekali Beli'}
                </label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-sm font-mono">$</span>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-8 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
                  />
                </div>
              </div>

              {strategy === 'dca' && (
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5 font-mono">
                    Frekuensi Pembelian
                  </label>
                  <select
                    value={period}
                    onChange={(e) => setPeriod(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
                  >
                    <option value="weekly">Mingguan (Tiap 7 Hari)</option>
                    <option value="monthly">Bulanan (Tiap 30 Hari)</option>
                  </select>
                </div>
              )}

              <button
                onClick={handleRunDCA}
                disabled={dcaLoading}
                className="w-full mt-4 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold text-sm transition-all shadow-lg shadow-blue-600/30 flex items-center justify-center space-x-2"
              >
                {dcaLoading ? (
                  <span>Menghitung Data Historis...</span>
                ) : (
                  <>
                    <span>Jalankan Simulasi What-If</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results Output */}
          <div className="lg:col-span-7 bg-[#111827] border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
            {dcaResult ? (
              <div>
                <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-6">
                  <div>
                    <span className="text-xs text-slate-500 uppercase font-mono">Hasil Analisis</span>
                    <h4 className="text-xl font-bold text-white font-mono">{dcaResult.symbol} ({dcaResult.strategy.toUpperCase()})</h4>
                  </div>
                  <div className={`text-right font-mono px-3 py-1.5 rounded-xl border ${
                    dcaResult.roi_percent >= 0 
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
                      : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                  }`}>
                    <div className="text-xs font-semibold">RETURN INVESTASI (ROI)</div>
                    <div className="text-2xl font-black">
                      {dcaResult.roi_percent >= 0 ? '+' : ''}{dcaResult.roi_percent}%
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6 font-mono">
                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <div className="text-[11px] text-slate-500 uppercase">Modal Disetor</div>
                    <div className="text-base font-bold text-slate-200 mt-0.5">
                      ${dcaResult.total_invested?.toLocaleString()}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <div className="text-[11px] text-slate-500 uppercase">Nilai Portofolio</div>
                    <div className="text-base font-bold text-blue-400 mt-0.5">
                      ${dcaResult.current_portfolio_value?.toLocaleString()}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <div className="text-[11px] text-slate-500 uppercase">Net Profit / Loss</div>
                    <div className={`text-base font-bold mt-0.5 ${
                      dcaResult.total_profit_loss >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {dcaResult.total_profit_loss >= 0 ? '+' : ''}${dcaResult.total_profit_loss?.toLocaleString()}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <div className="text-[11px] text-slate-500 uppercase">Total Unit Koin</div>
                    <div className="text-base font-bold text-slate-200 mt-0.5">
                      {dcaResult.total_units_bought}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <div className="text-[11px] text-slate-500 uppercase">Rata-rata Beli</div>
                    <div className="text-base font-bold text-amber-300 mt-0.5">
                      ${dcaResult.average_buy_price?.toLocaleString()}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <div className="text-[11px] text-slate-500 uppercase">Harga Terkini</div>
                    <div className="text-base font-bold text-slate-200 mt-0.5">
                      ${dcaResult.current_price?.toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Progress / History Curve Mini Visual */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs font-semibold text-slate-400 mb-3 flex items-center justify-between font-mono">
                    <span>RIWAYAT PERTUMBUHAN MODAL VS NILAI ASET</span>
                    <span className="text-[10px] text-slate-500">{dcaResult.history_curve?.length} Titik Waktu</span>
                  </div>
                  <div className="max-h-48 overflow-y-auto space-y-1.5 font-mono text-xs pr-2">
                    {dcaResult.history_curve?.slice(-6).map((c, idx) => (
                      <div key={idx} className="flex justify-between items-center py-1 border-b border-slate-900 last:border-0">
                        <span className="text-slate-500">{c.date}</span>
                        <span className="text-slate-400">Modal: ${c.invested}</span>
                        <span className={`font-semibold ${c.portfolio_value >= c.invested ? 'text-emerald-400' : 'text-rose-400'}`}>
                          Nilai: ${c.portfolio_value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate-500">
                <PieChart className="w-12 h-12 mb-3 text-slate-700" />
                <h5 className="font-semibold text-slate-300 text-sm">Belum Ada Simulasi Berjalan</h5>
                <p className="text-xs max-w-sm mt-1">
                  Pilih aset dan klik "Jalankan Simulasi What-If" untuk melihat hasil kalkulasi perbandingan keuntungan.
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Risk Calculator SubTab */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5 bg-[#111827] border border-slate-800 rounded-2xl p-6">
            <h3 className="text-base font-bold text-white mb-1 flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Kalkulator Manajemen Risiko Trading</span>
            </h3>
            <p className="text-xs text-slate-400 mb-6">
              Hitung ukuran lot / jumlah unit yang aman dibeli agar risiko tidak melebihi modal toleransi.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5 font-mono">
                  Total Modal Portofolio ($)
                </label>
                <input
                  type="number"
                  value={capital}
                  onChange={(e) => setCapital(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5 font-mono">
                  Maksimal Toleransi Risiko (% Modal)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={riskPct}
                  onChange={(e) => setRiskPct(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5 font-mono">
                  Harga Beli (Entry Price)
                </label>
                <input
                  type="number"
                  value={entryPrice}
                  onChange={(e) => setEntryPrice(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold uppercase text-rose-400 mb-1.5 font-mono">
                    Stop Loss Price
                  </label>
                  <input
                    type="number"
                    value={stopLoss}
                    onChange={(e) => setStopLoss(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-rose-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase text-emerald-400 mb-1.5 font-mono">
                    Take Profit Price
                  </label>
                  <input
                    type="number"
                    value={takeProfit}
                    onChange={(e) => setTakeProfit(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>
              </div>

              <button
                onClick={handleRunRisk}
                disabled={riskLoading}
                className="w-full mt-4 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-semibold text-sm transition-all shadow-lg shadow-emerald-600/30 flex items-center justify-center space-x-2"
              >
                <span>Hitung Ukuran Posisi Ideal</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="lg:col-span-7 bg-[#111827] border border-slate-800 rounded-2xl p-6">
            {riskResult ? (
              <div className="space-y-6">
                <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                  <div>
                    <span className="text-xs text-slate-500 uppercase font-mono">Evaluasi Risiko</span>
                    <h4 className="text-lg font-bold text-white font-mono">Hasil Ukuran Posisi</h4>
                  </div>
                  <div className="text-right">
                    <span className="px-3 py-1.5 rounded-xl text-xs font-bold font-mono bg-blue-500/10 text-blue-400 border border-blue-500/30">
                      R : R = {riskResult.risk_to_reward_ratio}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 font-mono">
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400 uppercase">Posisi Maksimal yang Aman</div>
                    <div className="text-2xl font-black text-emerald-400 mt-1">
                      {riskResult.recommended_position_size} Unit
                    </div>
                    <div className="text-[11px] text-slate-500 mt-1">
                      Total Biaya: ${riskResult.total_position_cost?.toLocaleString()}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400 uppercase">Maksimal Resiko Dollar</div>
                    <div className="text-2xl font-black text-rose-400 mt-1">
                      ${riskResult.max_dollar_risk?.toLocaleString()}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-1">
                      Jika menyentuh Stop Loss
                    </div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400 uppercase">Potensi Keuntungan</div>
                    <div className="text-2xl font-black text-blue-400 mt-1">
                      ${riskResult.potential_profit?.toLocaleString()}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-1">
                      Jika menyentuh Take Profit
                    </div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400 uppercase">Resiko per Unit</div>
                    <div className="text-2xl font-black text-amber-300 mt-1">
                      ${riskResult.risk_per_unit?.toLocaleString()}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-1">
                      Jarak Entry ke Stop Loss
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 flex items-start space-x-3">
                  <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs font-bold text-slate-200 uppercase font-mono">Rekomendasi Eksekusi</div>
                    <div className="text-xs text-slate-300 mt-0.5">{riskResult.recommendation}</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-500">
                <ShieldCheck className="w-12 h-12 mb-3 text-slate-700" />
                <h5 className="font-semibold text-slate-300 text-sm">Kalkulator Siap Digunakan</h5>
                <p className="text-xs max-w-sm mt-1">
                  Masukkan target harga entry, batasan stop loss, dan take profit untuk menghitung alokasi ukuran trading Anda.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
