import React, { useState } from 'react';
import { ShieldCheck, Send, Settings, Save, AlertTriangle, Zap, Activity } from 'lucide-react';
import { executeWebhookSignal } from '../../api';

const WebhookConfigView = ({ symbol = "BTC/USDT" }) => {
  const [targetUrl, setTargetUrl] = useState("https://api.telegram.org/bot<TOKEN>/sendMessage");
  const [minProbability, setMinProbability] = useState(65);
  const [token, setToken] = useState("FINBLIX_SECRET_XYZ");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastPayload, setLastPayload] = useState(null);

  const handleTestWebhook = async () => {
    setLoading(true);
    setStatus("");
    try {
      const response = await executeWebhookSignal({
        symbol,
        target_url: targetUrl,
        min_probability: minProbability / 100.0,
        secret_token: token
      });
      
      setStatus(`Status: ${response.status} - ${response.message || response.reason}`);
      if (response.trade_signal) {
        setLastPayload(response.trade_signal);
      } else {
        setLastPayload(null);
      }
    } catch (err) {
      setStatus(`Error: ${err.message || "Failed to execute webhook"}`);
    }
    setLoading(false);
  };

  return (
    <div className="bg-slate-900 border border-indigo-500/30 rounded-xl p-6 relative overflow-hidden">
      <div className="absolute top-0 right-0 p-4 opacity-10">
        <Zap size={120} />
      </div>
      
      <div className="flex items-center space-x-3 mb-6 relative z-10">
        <div className="p-2 bg-indigo-500/20 text-indigo-400 rounded-lg">
          <Settings size={24} />
        </div>
        <div>
          <h3 className="text-xl font-bold text-white">Algorithmic Trade Bot (Webhook)</h3>
          <p className="text-sm text-slate-400">Automate Finblix High-Conviction signals directly to your exchange or Telegram.</p>
        </div>
      </div>

      <div className="space-y-5 relative z-10">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">Target Webhook URL</label>
          <input 
            type="text" 
            className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg p-3 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Min. Conviction Threshold (%)</label>
            <div className="flex items-center space-x-3">
              <input 
                type="range" 
                min="50" max="95" 
                className="w-full accent-indigo-500"
                value={minProbability}
                onChange={(e) => setMinProbability(e.target.value)}
              />
              <span className="text-white font-mono bg-slate-800 px-3 py-1 rounded border border-slate-700">
                {minProbability}%
              </span>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Security Token</label>
            <input 
              type="password" 
              className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg p-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
          </div>
        </div>

        <div className="pt-4 flex justify-between items-center border-t border-slate-800">
          <div className="text-sm text-slate-400 flex items-center">
            <ShieldCheck size={16} className="mr-2 text-emerald-400" />
            Payload will include dynamic leverage and confidence score.
          </div>
          <button 
            onClick={handleTestWebhook}
            disabled={loading}
            className="flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white px-5 py-2.5 rounded-lg font-medium transition-all transform hover:scale-105 active:scale-95 disabled:opacity-50"
          >
            {loading ? <Activity className="animate-spin" size={18} /> : <Send size={18} />}
            <span>{loading ? 'Executing...' : 'Test Webhook Push'}</span>
          </button>
        </div>

        {status && (
          <div className={`p-4 rounded-lg border text-sm flex flex-col space-y-2 ${status.includes('Error') || status.includes('skipped') ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'}`}>
            <div className="flex items-center">
              <AlertTriangle size={16} className="mr-2" />
              <strong>{status}</strong>
            </div>
            {lastPayload && (
              <div className="mt-2 p-3 bg-slate-900 rounded border border-slate-800 font-mono text-xs overflow-x-auto text-slate-300">
                <div className="text-emerald-400 mb-1">// Fired Payload:</div>
                {JSON.stringify(lastPayload, null, 2)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default WebhookConfigView;
