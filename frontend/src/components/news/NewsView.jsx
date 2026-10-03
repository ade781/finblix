import React, { useEffect, useState } from 'react';
import { 
  Newspaper, 
  ExternalLink, 
  Sparkles, 
  Flame, 
  TrendingUp, 
  TrendingDown, 
  RefreshCw,
  Tag
} from 'lucide-react';
import { getNewsFeed, getFearGreed } from '../../api';

export default function NewsView() {
  const [articles, setArticles] = useState([]);
  const [fearGreed, setFearGreed] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchNewsData = async () => {
    setLoading(true);
    try {
      const [newsRes, fgRes] = await Promise.all([
        getNewsFeed(10),
        getFearGreed(),
      ]);
      setArticles(newsRes.data.articles || []);
      setFearGreed(fgRes.data);
    } catch (e) {
      console.error('Error fetching news:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNewsData();
  }, []);

  const getSentimentPill = (label, score) => {
    if (label.toLowerCase() === 'bullish') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          <TrendingUp className="w-3 h-3" />
          BULLISH (+{score})
        </span>
      );
    } else if (label.toLowerCase() === 'bearish') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold font-mono bg-rose-500/10 text-rose-400 border border-rose-500/30">
          <TrendingDown className="w-3 h-3" />
          BEARISH ({score})
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold font-mono bg-slate-500/10 text-slate-400 border border-slate-500/30">
        NEUTRAL ({score})
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Banner: Fear & Greed Index + Market Pulse */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Fear & Greed Index Widget */}
        <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5 flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              <Flame className="w-4 h-4 text-amber-500" />
              <span>Fear & Greed Index</span>
            </div>
            <div className="text-3xl font-black font-mono text-white mt-1">
              {fearGreed ? fearGreed.value : 65} <span className="text-sm font-normal text-slate-400">/ 100</span>
            </div>
            <div className="text-xs font-bold uppercase tracking-wider text-amber-400 mt-1 font-mono">
              {fearGreed ? fearGreed.value_classification : 'Greed'}
            </div>
          </div>

          <div className="w-20 h-20 rounded-full border-4 border-slate-800 border-t-amber-500 flex items-center justify-center font-mono font-bold text-lg text-slate-200">
            {fearGreed ? `${fearGreed.value}%` : '65%'}
          </div>
        </div>

        {/* Sentiment Overview Card */}
        <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5 md:col-span-2 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Distribusi Polaritas Sentimen Terkini
            </span>
            <button
              onClick={fetchNewsData}
              disabled={loading}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
              title="Segarkan Berita"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-400' : ''}`} />
            </button>
          </div>
          <div className="grid grid-cols-3 gap-3 font-mono text-center">
            <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
              <div className="text-[11px] text-emerald-400 font-bold uppercase">Bullish</div>
              <div className="text-lg font-black text-white mt-0.5">
                {articles.filter(a => a.sentiment.label.toLowerCase() === 'bullish').length} Berita
              </div>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
              <div className="text-[11px] text-slate-400 font-bold uppercase">Netral</div>
              <div className="text-lg font-black text-white mt-0.5">
                {articles.filter(a => a.sentiment.label.toLowerCase() === 'neutral').length} Berita
              </div>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
              <div className="text-[11px] text-rose-400 font-bold uppercase">Bearish</div>
              <div className="text-lg font-black text-white mt-0.5">
                {articles.filter(a => a.sentiment.label.toLowerCase() === 'bearish').length} Berita
              </div>
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Pemindaian teks real-time dianalisis menggunakan NLP & FinTech keyword weighting.
          </p>
        </div>
      </div>

      {/* News Articles Feed */}
      <div className="space-y-4">
        <h3 className="text-base font-bold text-white flex items-center space-x-2">
          <Newspaper className="w-5 h-5 text-blue-400" />
          <span>Feed Berita Finansial & AI Summaries</span>
        </h3>

        <div className="grid grid-cols-1 gap-4">
          {articles.map((art) => (
            <div
              key={art.id}
              className="bg-[#111827] border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all duration-200 shadow-sm"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2.5">
                <div className="flex items-center space-x-2 text-xs font-mono">
                  <span className="font-bold text-blue-400">{art.source}</span>
                  <span className="text-slate-600">•</span>
                  <span className="text-slate-500">{new Date(art.published_at).toLocaleDateString('id-ID', { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <div>
                  {getSentimentPill(art.sentiment.label, art.sentiment.score)}
                </div>
              </div>

              <h4 className="text-base font-bold text-white mb-2 leading-snug">
                <a 
                  href={art.url} 
                  target="_blank" 
                  rel="noreferrer" 
                  className="hover:text-blue-400 transition-colors inline-flex items-center gap-1.5"
                >
                  <span>{art.title}</span>
                  <ExternalLink className="w-3.5 h-3.5 opacity-60 shrink-0" />
                </a>
              </h4>

              {/* AI 3-Bullet Summary Box */}
              {art.ai_summary && (
                <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 my-3 text-xs text-slate-300 leading-relaxed font-sans">
                  <div className="flex items-center space-x-1.5 text-blue-400 font-semibold mb-2 font-mono text-[11px] uppercase tracking-wider">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>AI Executive Summary (TL;DR)</span>
                  </div>
                  <div className="whitespace-pre-line text-slate-300 space-y-1">
                    {art.ai_summary}
                  </div>
                </div>
              )}

              {/* Impacted Symbols & Keywords */}
              <div className="flex flex-wrap items-center justify-between gap-2 mt-3 pt-3 border-t border-slate-800/60 text-xs font-mono">
                <div className="flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5 text-slate-500" />
                  <span className="text-slate-500 text-[11px]">Aset Terkait:</span>
                  {art.impacted_assets.map(sym => (
                    <span key={sym} className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300 text-[10px] font-bold">
                      {sym}
                    </span>
                  ))}
                </div>

                {art.sentiment.keywords && art.sentiment.keywords.length > 0 && (
                  <div className="text-[11px] text-slate-500 hidden sm:block">
                    Kata Kunci: {art.sentiment.keywords.join(', ')}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
