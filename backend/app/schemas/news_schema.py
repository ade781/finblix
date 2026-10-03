from pydantic import BaseModel
from typing import List, Optional

class NewsSentiment(BaseModel):
    score: float
    label: str
    keywords: List[str] = []

class NewsArticleItem(BaseModel):
    id: int
    title: str
    source: str
    url: str
    published_at: str
    ai_summary: Optional[str] = None
    sentiment: NewsSentiment
    impacted_assets: List[str] = []

class NewsFeedResponse(BaseModel):
    status: str = "success"
    count: int
    articles: List[NewsArticleItem]

class FearGreedItem(BaseModel):
    value: int
    value_classification: str
    timestamp: str
