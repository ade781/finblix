import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import time as _t
from sqlalchemy.orm import Session
from app.models.news import NewsArticle
from app.services.sentiment_engine import SentimentEngine

RSS_FEEDS = [
    # Kripto
    {
        "query": "Bitcoin crypto market",
        "url": "https://news.google.com/rss/search?q=Bitcoin+crypto+market&hl=en-US&gl=US&ceid=US:en",
        "symbols": "BTC/USDT,ETH/USDT,SOL/USDT,XRP/USDT"
    },
    {
        "query": "Ethereum blockchain smart contract",
        "url": "https://news.google.com/rss/search?q=Ethereum+crypto+blockchain&hl=en-US&gl=US&ceid=US:en",
        "symbols": "ETH/USDT,BTC/USDT"
    },
    {
        "query": "Solana crypto Web3 ecosystem",
        "url": "https://news.google.com/rss/search?q=Solana+crypto+Web3&hl=en-US&gl=US&ceid=US:en",
        "symbols": "SOL/USDT,BTC/USDT"
    },
    # Saham Indonesia (IDX / BEI)
    {
        "query": "saham IHSG Bank Central Asia BBCA",
        "url": "https://news.google.com/rss/search?q=saham+IHSG+BBCA+Bank+Central+Asia&hl=id&gl=ID&ceid=ID:id",
        "symbols": "BBCA.JK,BBRI.JK,BMRI.JK,IHSG"
    },
    {
        "query": "saham Bank Rakyat Indonesia BBRI laba dividen",
        "url": "https://news.google.com/rss/search?q=saham+BBRI+Bank+Rakyat+Indonesia+laba&hl=id&gl=ID&ceid=ID:id",
        "symbols": "BBRI.JK,BBCA.JK,IHSG"
    },
    {
        "query": "saham Bank Mandiri BMRI kinerja kredit",
        "url": "https://news.google.com/rss/search?q=saham+BMRI+Bank+Mandiri+kinerja&hl=id&gl=ID&ceid=ID:id",
        "symbols": "BMRI.JK,BBCA.JK,IHSG"
    },
    {
        "query": "saham Telkom Indonesia TLKM infrastruktur digital",
        "url": "https://news.google.com/rss/search?q=saham+TLKM+Telkom+Indonesia&hl=id&gl=ID&ceid=ID:id",
        "symbols": "TLKM.JK,IHSG"
    },
    {
        "query": "saham Astra International ASII otomotif ekuitas",
        "url": "https://news.google.com/rss/search?q=saham+ASII+Astra+International&hl=id&gl=ID&ceid=ID:id",
        "symbols": "ASII.JK,IHSG"
    },
    {
        "query": "saham Indofood ICBP konsumsi",
        "url": "https://news.google.com/rss/search?q=saham+ICBP+Indofood+CBP&hl=id&gl=ID&ceid=ID:id",
        "symbols": "ICBP.JK,IHSG"
    },
    # Makro & Saham Global
    {
        "query": "Federal Reserve interest rate inflation Wall Street",
        "url": "https://news.google.com/rss/search?q=Federal+Reserve+interest+rates+Wall+Street&hl=en-US&gl=US&ceid=US:en",
        "symbols": "SPY,QQQ,AAPL,NVDA,BTC/USDT"
    },
    {
        "query": "Nvidia Apple semiconductor tech market",
        "url": "https://news.google.com/rss/search?q=Nvidia+Apple+stock+market&hl=en-US&gl=US&ceid=US:en",
        "symbols": "NVDA,AAPL,MSFT,SPY"
    }
]

class ScraperService:
    @classmethod
    async def scrape_and_store_rss_news(cls, db: Session, limit_per_feed: int = 25) -> int:
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
                        for item in items[:limit_per_feed]:
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
                                dt = datetime.strptime(pub_str[:25].strip(), "%a, %d %b %Y %H:%M:%S")
                            except Exception:
                                dt = datetime.now(timezone.utc).replace(tzinfo=None)

                            # Check if already exists in DB
                            if url:
                                existing = db.query(NewsArticle).filter((NewsArticle.title == title) | (NewsArticle.article_url == url)).first()
                            else:
                                existing = db.query(NewsArticle).filter(NewsArticle.title == title).first()

                            if not existing:
                                sentiment = SentimentEngine.analyze_text(title)
                                article_url = url if url else f"https://finblix.internal/news/{abs(hash(title))}"
                                article = NewsArticle(
                                    title=title,
                                    source="Google News / Media Finansial",
                                    article_url=article_url,
                                    summary=title,
                                    published_at=dt,
                                    sentiment_score=sentiment["score"],
                                    sentiment_label=sentiment["label"],
                                    related_symbols=feed["symbols"]
                                )
                                try:
                                    db.add(article)
                                    db.commit()
                                    new_count += 1
                                except Exception:
                                    db.rollback()
            except Exception as e:
                db.rollback()
                print(f"[ScraperService] RSS scrape warning for {feed['query']}: {e}")

        return new_count

    @classmethod
    async def scrape_bulk_daily_news(cls, db: Session, limit_per_feed: int = 35) -> Dict[str, Any]:
        """
        Melakukan scraping massal berita finansial harian dari seluruh feed pasar modal & kripto.
        Menghasilkan koleksi artikel berita harian berjumlah banyak untuk analisis sentimen mendalam.
        """
        start_time = _t.time()
        new_stored = await cls.scrape_and_store_rss_news(db, limit_per_feed=limit_per_feed)
        total_in_db = db.query(NewsArticle).count()
        
        # Ambil sampel 30 berita terbaru untuk analisis agregat
        recent_articles = db.query(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(30).all()
        avg_sentiment = float(sum(float(a.sentiment_score or 0.0) for a in recent_articles) / len(recent_articles)) if recent_articles else 0.0
        
        positive_count = sum(1 for a in recent_articles if float(a.sentiment_score or 0.0) > 0.05)
        negative_count = sum(1 for a in recent_articles if float(a.sentiment_score or 0.0) < -0.05)
        neutral_count = len(recent_articles) - positive_count - negative_count

        duration = round(_t.time() - start_time, 2)
        return {
            "status": "success",
            "new_articles_scraped": new_stored,
            "total_articles_in_db": total_in_db,
            "duration_seconds": duration,
            "sentiment_summary": {
                "average_score": round(avg_sentiment, 3),
                "label": "BULLISH" if avg_sentiment > 0.08 else "BEARISH" if avg_sentiment < -0.08 else "NEUTRAL",
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count
            }
        }

    @classmethod
    async def get_or_seed_news(cls, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
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
    def get_recent_news_for_asset(cls, db: Session, symbol: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Mengambil berita harian terbaru yang spesifik relevan dengan simbol aset tertentu."""
        sym_clean = symbol.split("/")[0].replace(".JK", "").lower()
        articles = db.query(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(100).all()
        
        matched = []
        for a in articles:
            is_relevant = (
                sym_clean in (a.related_symbols or "").lower() or 
                sym_clean in a.title.lower() or 
                "market" in a.title.lower() or 
                "pasar" in a.title.lower() or
                "ihsg" in a.title.lower()
            )
            if is_relevant:
                matched.append({
                    "id": a.id,
                    "title": a.title,
                    "source": a.source,
                    "published_at": a.published_at.strftime("%Y-%m-%d %H:%M:%S") if a.published_at else "",
                    "sentiment_score": round(float(a.sentiment_score or 0.0), 3),
                    "sentiment_label": a.sentiment_label or "neutral"
                })
                if len(matched) >= limit:
                    break
        return matched

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
        cached = getattr(cls, "_fng_latest", None)
        if cached and (_t.time() - cached[0]) < 900:
            return cached[1]
        result = await cls._fetch_fear_greed_remote()
        cls._fng_latest = (_t.time(), result)
        return result

    @classmethod
    async def _fetch_fear_greed_remote(cls) -> Dict[str, Any]:
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

        return {
            "value": 65,
            "value_classification": "Greed",
            "timestamp": str(int(datetime.now().timestamp()))
        }
