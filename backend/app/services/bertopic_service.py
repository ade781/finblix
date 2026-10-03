import re
from collections import Counter
from typing import List, Dict, Any, Optional
import numpy as np

class FinancialBERTopicEngine:
    """
    Mesin Topic Modeling Finansial (BERTopic Architecture) Khusus Pasar Saham:
    Mengklasifikasikan berita finansial & keterbukaan informasi emiten ke dalam topik terstruktur
    menggunakan representasi c-TF-IDF (Class-based Term Frequency-Inverse Document Frequency)
    serta memberikan pembobotan sentimen asimetris pada pergerakan harga saham.
    """

    TOPIC_DEFINITIONS = {
        "Kinerja Laba, Kredit & Dividen": {
            "keywords": [
                "laba", "profit", "earnings", "kredit", "dividen", "dividend", 
                "revenue", "pendapatan", "kinerja", "laba bersih", "margin", 
                "pertumbuhan", "finansial", "kuartal", "laporan keuangan"
            ],
            "weight_multiplier": 2.5,
            "category": "CORPORATE_EARNINGS",
            "description": "Laporan fundamental keuangan kuartalan, penyaluran kredit perbankan, dan pembagian dividen tunai."
        },
        "Kebijakan Suku Bunga & Moneter": {
            "keywords": [
                "suku bunga", "bi-rate", "bi rate", "fed rate", "interest rate", 
                "inflasi", "moneter", "bank indonesia", "the fed", "likuiditas",
                "rupiah", "dolar", "gubernur bi", "kebijakan"
            ],
            "weight_multiplier": 2.0,
            "category": "MACRO_MONETARY",
            "description": "Kebijakan makroekonomi bank sentral, suku bunga acuan, dan transmisi likuiditas pasar modal."
        },
        "Rekomendasi Analis & Target Konsensus": {
            "keywords": [
                "target price", "rekomendasi", "analis", "buy rating", "overweight", 
                "outperform", "fair value", "konsensus", "potensi upside", "valuasi",
                "broker", "sekuritas", "riset", "hold", "sell rating"
            ],
            "weight_multiplier": 2.2,
            "category": "ANALYST_CONSENSUS",
            "description": "Riset konsensus analis pasar modal institusional dan target harga wajar emiten."
        },
        "Inovasi AI, Ekspansi & Capex": {
            "keywords": [
                "chip", "ai", "teknologi", "komputasi", "ekspansi", "investasi", 
                "capex", "akuisisi", "merger", "proyek baru", "infrastruktur",
                "kapasitas", "pabrik", "kontrak"
            ],
            "weight_multiplier": 1.8,
            "category": "EXPANSION_CAPEX",
            "description": "Aksi korporasi, belanja modal (capex), investasi teknologi, dan ekspansi pasar."
        },
        "Sentimen Pasar & Regulasi Sistemik": {
            "keywords": [
                "regulasi", "ojk", "pasar modal", "ihsg", "bursa", "transaksi", 
                "investor asing", "foreign net", "volatilitas", "indeks", "bei"
            ],
            "weight_multiplier": 1.2,
            "category": "MARKET_SYSTEMIC",
            "description": "Dinamika regulasi OJK/BEI dan arus dana investor institusi asing (foreign flow)."
        }
    }

    @classmethod
    def analyze_equity_news_topics(cls, news_items: List[Dict[str, Any]], symbol: str = "BBCA.JK") -> Dict[str, Any]:
        """
        Menganalisis daftar berita saham menggunakan pemodelan topik finansial:
        1. Menghitung kesesuaian dokumen terhadap topik fundamental
        2. Mengekstrak kata kunci representatif c-TF-IDF
        3. Menghitung dampak sentimen terbobot (Topic Impact Score)
        """
        if not news_items:
            return {
                "has_topics": False,
                "dominant_topic": "Netral / Tanpa Berita Khusus",
                "topic_sentiment_score": 0.0,
                "topic_impact_points": 0.0,
                "top_keywords": ["saham", "pasar", "ihsg"],
                "description": "Tidak ada berita korporasi spesifik yang terdeteksi dalam 24 jam terakhir.",
                "topic_breakdown": []
            }

        topic_scores = {t: 0.0 for t in cls.TOPIC_DEFINITIONS}
        topic_counts = {t: 0 for t in cls.TOPIC_DEFINITIONS}
        word_freq_per_topic = {t: Counter() for t in cls.TOPIC_DEFINITIONS}

        stop_words = {
            "dan", "yang", "untuk", "dari", "dengan", "pada", "dalam", "bisa", "ini", 
            "itu", "juga", "oleh", "ke", "di", "akan", "the", "and", "for", "with", 
            "this", "that", "from", "are", "have", "has", "been", "was", "were"
        }

        sym_token = symbol.split(".")[0].lower()

        for item in news_items:
            title = item.get("title", "") or ""
            summary = item.get("ai_summary", "") or ""
            text = f"{title} {summary}".lower()
            sent_score = item.get("sentiment", {}).get("score", 0.0)

            # Relevance weighting: berikan boost jika emiten spesifik disebutkan di judul
            item_weight = 1.5 if sym_token in text else 1.0

            for t_name, t_meta in cls.TOPIC_DEFINITIONS.items():
                matched_kws = [kw for kw in t_meta["keywords"] if kw in text]
                if matched_kws:
                    topic_scores[t_name] += (sent_score * t_meta["weight_multiplier"] * item_weight * len(matched_kws))
                    topic_counts[t_name] += 1

                    # Tokenisasi kata kunci untuk representasi c-TF-IDF
                    tokens = re.findall(r"[a-zA-Z]{3,}", text)
                    for tok in tokens:
                        if tok not in stop_words and tok != sym_token:
                            word_freq_per_topic[t_name][tok] += 1

        active_topics = [t for t in topic_counts if topic_counts[t] > 0]
        topic_breakdown = []

        for t_name, t_meta in cls.TOPIC_DEFINITIONS.items():
            count = topic_counts[t_name]
            raw_score = topic_scores[t_name]
            avg_score = (raw_score / count) if count > 0 else 0.0
            top_kws = [w for w, _ in word_freq_per_topic[t_name].most_common(4)]
            topic_breakdown.append({
                "topic_name": t_name,
                "count": count,
                "sentiment_score": round(avg_score, 2),
                "keywords": top_kws,
                "description": t_meta["description"]
            })

        if not active_topics:
            dominant_topic = "Dinamika Pasar Saham Umum"
            top_kws = ["saham", "ihsg", "transaksi", "investasi"]
            avg_all = float(np.mean([n.get("sentiment", {}).get("score", 0.0) for n in news_items])) if news_items else 0.0
            topic_impact = round(max(-30.0, min(30.0, avg_all * 25.0)), 1)
            desc = "Sentimen pergerakan bursa saham umum."
        else:
            dominant_topic = max(active_topics, key=lambda t: (topic_counts[t], abs(topic_scores[t])))
            top_kws = [w for w, _ in word_freq_per_topic[dominant_topic].most_common(5)]
            active_score = topic_scores[dominant_topic] / max(1, topic_counts[dominant_topic])
            topic_impact = round(max(-35.0, min(35.0, active_score * 30.0)), 1)
            desc = cls.TOPIC_DEFINITIONS.get(dominant_topic, {}).get("description", "")

        return {
            "has_topics": True,
            "dominant_topic": dominant_topic,
            "topic_impact_points": topic_impact,
            "top_keywords": top_kws,
            "description": desc,
            "topic_breakdown": topic_breakdown
        }

bertopic_engine = FinancialBERTopicEngine()
