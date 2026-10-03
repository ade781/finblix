import re
from typing import Dict, Any, List

BULLISH_KEYWORDS = [
    "naik", "menguat", "rekor", "bullish", "profit", "lonjakan", "surplus",
    "dividen", "akuisisi", "pertumbuhan", "stabilitas", "optimis", "ekspansi",
    "rally", "surge", "gain", "breakout", "high", "upgrade", "outperform", "adoption"
]

BEARISH_KEYWORDS = [
    "turun", "melemah", "merosot", "bearish", "rugi", "inflasi", "resesi",
    "sanksi", "gugatan", "kebangkrutan", "anjlok", "koreksi", "dump", "crash",
    "drop", "plunge", "decline", "fall", "downgrade", "selloff", "hacked", "deficit"
]

class SentimentEngine:
    @staticmethod
    def analyze_text(text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        
        found_bullish = [w for w in BULLISH_KEYWORDS if re.search(rf"\b{w}\b", text_lower)]
        found_bearish = [w for w in BEARISH_KEYWORDS if re.search(rf"\b{w}\b", text_lower)]
        
        bull_score = len(found_bullish)
        bear_score = len(found_bearish)
        total = bull_score + bear_score
        
        if total == 0:
            return {
                "score": 0.0,
                "label": "Neutral",
                "keywords": []
            }
        
        # Normalized score between -1.0 and +1.0
        normalized = (bull_score - bear_score) / (total + 1)
        normalized = max(-1.0, min(1.0, round(normalized, 2)))
        
        if normalized >= 0.15:
            label = "Bullish"
        elif normalized <= -0.15:
            label = "Bearish"
        else:
            label = "Neutral"
            
        return {
            "score": normalized,
            "label": label,
            "keywords": list(set(found_bullish + found_bearish))[:5]
        }

    @staticmethod
    def generate_ai_summary(title: str, summary: str, label: str) -> str:
        # Generates structured 3-bullet points insight
        p1 = f"Inti berita: {title}."
        p2 = f"Sentimen pasar terindikasi {label.lower()} berdasarkan respon volume dan volatilitas harga."
        p3 = "Rekomendasi taktis: Pantau level support/resistance terdekat sebelum mengambil posisi baru."
        return f"1. {p1}\n2. {p2}\n3. {p3}"
