import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.news import NewsArticle
from app.services.sentiment_engine import SentimentEngine

RSS_FEEDS = [
    {
        "query": "Bitcoin crypto market",
        "url": "https://news.google.com/rss/search?q=Bitcoin+crypto+market&hl=en-US&gl=US&ceid=US:en",
        "symbols": "BTC/USDT,ETH/USDT,SOL/USDT"
    },
    {
        "query": "saham IHSG Bank Central Asia BBCA",
        "url": "https://news.google.com/rss/search?q=saham+IHSG+BBCA+Bank+Central+Asia&hl=id&gl=ID&ceid=ID:id",
        "symbols": "BBCA.JK,BBRI.JK,IHSG"
    },
    {
        "query": "Nvidia Apple Wall Street stock",
        "url": "https://news.google.com/rss/search?q=Nvidia+Apple+stock+market&hl=en-US&gl=US&ceid=US:en",
        "symbols": "NVDA,AAPL,SPY"
    }
]

class ScraperService:
    @classmethod
    async def scrape_and_store_rss_news(cls, db: Session) -> int:
        """Mengambil berita finansial terkini dan aktual dari RSS Feed resmi dan menyimpannya di DB."""
        new_count = 0
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        for feed in RSS_FEEDS:
            try:
                async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
                    resp = await client.get(feed["url"])
                    if resp.status_code == 200:
                        root = ET.fromstring(resp.text)
                        items = root.findall(".//item")
                        for item in items[:25]:
                            title_el = item.find("title")
                            link_el = item.find("link")
                            pub_el = item.find("pubDate")

                            if title_el is None or not title_el.text:
                                continue

                            title = title_el.text.strip()
                            url = link_el.text.strip() if link_el is not None else ""
                            pub_str = pub_el.text.strip() if pub_el is not None else ""

                            # Parse publish date
                            try:
                                # format: Fri, 02 Oct 2026 17:53:06 GMT
                                dt = datetime.strptime(pub_str[:25].strip(), "%a, %d %b %Y %H:%M:%S")
                            except Exception:
                                dt = datetime.now(timezone.utc).replace(tzinfo=None)

                            # Check if already exists in DB
                            existing = db.query(NewsArticle).filter(NewsArticle.title == title).first()
                            if not existing:
                                sentiment = SentimentEngine.analyze_text(title)
                                article = NewsArticle(
                                    title=title,
                                    source="Google News / Media Finansial",
                                    article_url=url or f"https://finblix.internal/news/{abs(hash(title))}",
                                    summary=title,
                                    published_at=dt,
                                    sentiment_score=sentiment["score"],
                                    sentiment_label=sentiment["label"],
                                    related_symbols=feed["symbols"]
                                )
                                db.add(article)
                                new_count += 1
                        db.commit()
            except Exception as e:
                db.rollback()
                print(f"[ScraperService] RSS scrape warning for {feed['query']}: {e}")

        return new_count

    @classmethod
    async def get_or_seed_news(cls, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        # Cek artikel di DB, jika kurang dari 10 coba scraping live
        count = db.query(NewsArticle).count()
        if count < 10:
            await cls.scrape_and_store_rss_news(db)

        articles = db.query(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit).all()
        result = []
        for art in articles:
            result.append({
                "id": art.id,
                "title": art.title,
                "source": art.source,
                "url": art.article_url or "",
                "summary": art.summary,
                "published_at": art.published_at.strftime("%Y-%m-%d %H:%M:%S") if art.published_at else "",
                "sentiment": {
                    "score": float(art.sentiment_score or 0.0),
                    "label": art.sentiment_label or "neutral"
                },
                "impacted_assets": (art.related_symbols or "").split(",")
            })
        return result

    @classmethod
    def get_date_sentiment_map(cls, db: Session, symbol: str) -> Dict[str, float]:
        """Membuat mapping tanggal YYYY-MM-DD ke rata-rata sentimen berita riil dari DB."""
        sym_clean = symbol.split("/")[0].replace(".JK", "").lower()
        articles = db.query(NewsArticle).all()
        date_scores: Dict[str, List[float]] = {}

        for a in articles:
            if not a.published_at or a.sentiment_score is None:
                continue
            is_relevant = (
                sym_clean in (a.related_symbols or "").lower() or 
                sym_clean in a.title.lower() or 
                "pasar" in a.title.lower() or 
                "market" in a.title.lower()
            )
            if is_relevant:
                d_str = a.published_at.strftime("%Y-%m-%d")
                date_scores.setdefault(d_str, []).append(float(a.sentiment_score))

        sentiment_map = {d: float(sum(scores) / len(scores)) for d, scores in date_scores.items()}
        return sentiment_map

    @classmethod
    async def fetch_fear_greed_index(cls) -> Dict[str, Any]:
        # Cache 15 menit agar tidak menunggu jaringan setiap saat
        import time as _t
        cached = getattr(cls, "_fng_latest", None)
        if cached and (_t.time() - cached[0]) < 900:
            return cached[1]
        result = await cls._fetch_fear_greed_remote()
        cls._fng_latest = (_t.time(), result)
        return result

    @classmethod
    async def _fetch_fear_greed_remote(cls) -> Dict[str, Any]:
        # Alternative.me Crypto Fear & Greed API
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get("https://api.alternative.me/fng/?limit=1")
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    if data:
                        return {
                            "value": int(data[0]["value"]),
                            "value_classification": data[0]["value_classification"],
                            "timestamp": data[0]["timestamp"]
                        }
        except Exception as e:
            print(f"[ScraperService] Fear & Greed API error: {e}")

        # Fallback value
        return {
            "value": 65,
            "value_classification": "Greed",
            "timestamp": str(int(datetime.now().timestamp()))
        }
