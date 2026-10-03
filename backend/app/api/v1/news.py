from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.news_schema import NewsFeedResponse, FearGreedItem, NewsArticleItem, NewsSentiment
from app.services.scraper_service import ScraperService

router = APIRouter()

@router.get("/feed", response_model=NewsFeedResponse)
async def get_news_feed(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    articles_data = await ScraperService.get_or_seed_news(db, limit=limit)
    items = []
    for a in articles_data:
        items.append(NewsArticleItem(
            id=a["id"],
            title=a["title"],
            source=a["source"],
            url=a["url"],
            published_at=a["published_at"],
            ai_summary=a.get("ai_summary") or a.get("title") or "",
            sentiment=NewsSentiment(**a["sentiment"]),
            impacted_assets=a["impacted_assets"]
        ))
    return NewsFeedResponse(
        status="success",
        count=len(items),
        articles=items
    )

@router.get("/fear-greed", response_model=FearGreedItem)
async def get_fear_greed():
    data = await ScraperService.fetch_fear_greed_index()
    return FearGreedItem(**data)
