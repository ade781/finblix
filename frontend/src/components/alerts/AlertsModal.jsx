import React, { useEffect, useState } from 'react';
import { 
  Bell, 
  X, 
  ShieldAlert, 
  Zap, 
  TrendingUp, 
  TrendingDown, 
  Check, 
  RefreshCw,
  Send,
  MessageSquare,
  Bot
} from 'lucide-react';
import { getAlerts, scanAnomalies, markAlertRead } from '../../api';
import api from '../../api';

export default function AlertsModal({ isOpen, onClose }) {
  const [activeSubTab, setActiveSubTab] = useState('list'); // 'list' or 'webhook'
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanLoading, setScanLoading] = useState(false);

  // Webhook settings
  const [channel, setChannel] = useState('discord');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [botToken, setBotToken] = useState('');
  const [chatId, setChatId] = useState('');
  const [webhookStatus, setWebhookStatus] = useState(null);
  const [webhookLoading, setWebhookLoading] = useState(false);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await getAlerts();
      setAlerts(res.data.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchAlerts();
    }
  }, [isOpen]);

  const handleScan = async () => {
    setScanLoading(true);
    try {
      await scanAnomalies();
      await fetchAlerts();
    } catch (e) {
      console.error(e);
    } finally {
      setScanLoading(false);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await markAlertRead(id);
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a));
    } catch (e) {
      console.error(e);
    }
  };

  const handleTestWebhook = async (e) => {
    e.preventDefault();
    setWebhookLoading(true);
    setWebhookStatus(null);
    try {
      const res = await api.post('/alerts/webhook-test', {
        channel,
        webhook_url: webhookUrl,
        bot_token: botToken,
        chat_id: chatId,
        message: '🚨 Tes Notifikasi Finblix: Sistem berhasil tersambung ke webhook Anda!'
      });
      setWebhookStatus(res.data);
    } catch (err) {
      setWebhookStatus({ status: 'error', message: err.response?.data?.detail || 'Gagal mengirim pesan' });
    } finally {
      setWebhookLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-[#111827] border border-slate-800 rounded-2xl w-full max-w-xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden font-sans">
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white font-mono">PUSAT DETEKSI ANOMALI & ALERTS</h3>
              <p className="text-xs text-slate-400">Peringatan lonjakan volume, breakout tajam, dan level teknikal ekstrem.</p>
            </div>
          </div>

          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Sub-tab Switcher */}
        <div className="flex border-b border-slate-800 bg-slate-950 px-5 pt-2 space-x-4 text-xs font-mono">
          <button
            onClick={() => setActiveSubTab('list')}
            className={`pb-2.5 border-b-2 font-bold transition-all ${
              activeSubTab === 'list'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Daftar Peringatan ({alerts.length})
          </button>
          <button
            onClick={() => setActiveSubTab('webhook')}
            className={`pb-2.5 border-b-2 font-bold transition-all flex items-center space-x-1.5 ${
              activeSubTab === 'webhook'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Send className="w-3.5 h-3.5" />
            <span>Webhook Integrasi (Discord / Telegram)</span>
          </button>
        </div>

        {activeSubTab === 'list' ? (
          <>
            {/* Action bar */}
            <div className="px-5 py-3 bg-slate-950 border-b border-slate-800 flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">
                Total {alerts.length} Notifikasi Tercatat
              </span>
              <button
                onClick={handleScan}
                disabled={scanLoading}
                className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white flex items-center space-x-1.5 transition-colors font-semibold"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${scanLoading ? 'animate-spin' : ''}`} />
                <span>Pindai Anomali Sekarang</span>
              </button>
            </div>

            {/* Alert List */}
            <div className="flex-1 overflow-y-auto p-5 space-y-3">
              {alerts.length > 0 ? (
                alerts.map((al) => (
                  <div
                    key={al.id}
                    className={`p-4 rounded-xl border transition-all text-xs font-mono ${
                      al.is_read 
                        ? 'bg-slate-950/40 border-slate-800/60 opacity-60' 
                        : al.severity === 'critical'
                        ? 'bg-rose-500/10 border-rose-500/40 text-rose-200'
                        : 'bg-amber-500/10 border-amber-500/40 text-amber-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-sm text-white">{al.symbol}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          al.severity === 'critical' ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'
                        }`}>
                          {al.alert_type.replace('_', ' ')}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-400">{al.triggered_at}</span>
                    </div>

                    <p className="text-slate-300 font-sans text-xs leading-relaxed mb-2">
                      {al.message}
                    </p>

                    {!al.is_read && (
                      <div className="flex justify-end pt-1">
                        <button
                          onClick={() => handleMarkRead(al.id)}
                          className="inline-flex items-center space-x-1 text-[11px] text-slate-400 hover:text-white hover:underline"
                        >
                          <Check className="w-3.5 h-3.5 text-blue-400" />
                          <span>Tandai Sudah Dibaca</span>
                        </button>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-500 font-sans">
                  <ShieldAlert className="w-10 h-10 mx-auto mb-2 text-slate-700" />
                  <p className="font-semibold text-slate-400 text-sm">Tidak Ada Anomali Kritis</p>
                  <p className="text-xs mt-1">Kondisi likuiditas dan volatilitas pasar saat ini berada dalam rentang normal.</p>
                </div>
              )}
            </div>
          </>
        ) : (
          /* Webhook Configuration Sub-Tab */
          <div className="p-5 flex-1 overflow-y-auto space-y-4 font-mono text-xs">
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-slate-300 leading-relaxed font-sans">
              Hubungkan sistem notifikasi pasar otomatis ke server Discord atau grup Telegram Anda agar setiap lonjakan volume anomali langsung terkirim ke ponsel Anda.
            </div>

            <form onSubmit={handleTestWebhook} className="space-y-4">
              <div>
                <label className="block text-xs uppercase text-slate-400 mb-1.5 font-bold">Pilih Kanal Notifikasi</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setChannel('discord')}
                    className={`py-2 px-3 rounded-xl border transition-all flex items-center justify-center space-x-2 ${
                      channel === 'discord' ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-400'
                    }`}
                  >
                    <MessageSquare className="w-4 h-4" />
                    <span>Discord Webhook</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setChannel('telegram')}
                    className={`py-2 px-3 rounded-xl border transition-all flex items-center justify-center space-x-2 ${
                      channel === 'telegram' ? 'bg-blue-600/20 border-blue-500 text-blue-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-400'
                    }`}
                  >
                    <Bot className="w-4 h-4" />
                    <span>Telegram Bot</span>
                  </button>
                </div>
              </div>

              {channel === 'discord' ? (
                <div>
                  <label className="block text-xs uppercase text-slate-400 mb-1.5 font-bold">URL Webhook Discord</label>
                  <input
                    type="text"
                    placeholder="https://discord.com/api/webhooks/..."
                    value={webhookUrl}
                    onChange={(e) => setWebhookUrl(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                  />
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs uppercase text-slate-400 mb-1.5 font-bold">Telegram Bot Token</label>
                    <input
                      type="text"
                      placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                      value={botToken}
                      onChange={(e) => setBotToken(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs uppercase text-slate-400 mb-1.5 font-bold">Chat ID Telegram</label>
                    <input
                      type="text"
                      placeholder="-100123456789 atau ID Pribadi"
                      value={chatId}
                      onChange={(e) => setChatId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
              )}

              {webhookStatus && (
                <div className={`p-3 rounded-xl border text-xs font-sans ${
                  webhookStatus.status === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                }`}>
                  {webhookStatus.message}
                </div>
              )}

              <button
                type="submit"
                disabled={webhookLoading || (channel === 'discord' ? !webhookUrl : (!botToken || !chatId))}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-xl font-bold transition-all shadow-md flex items-center justify-center space-x-2"
              >
                <Send className="w-4 h-4" />
                <span>{webhookLoading ? 'Mengirim Tes...' : 'Kirim Notifikasi Uji Coba'}</span>
              </button>
            </form>
          </div>
        )}

        {/* Modal Footer */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl font-mono transition-colors"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
}
