from fastapi import APIRouter
from app.worker import task_ingest_finnhub_news

router = APIRouter()

@router.post("/ingest/finnhub-news", name="Ingest Finnhub News")
async def ingest_finnhub_news():
    """
    Finnhub 뉴스 데이터를 수집하는 엔드포인트
    """
    result = task_ingest_finnhub_news.apply_async()
    return {"task_id": result.id, "status": "ingestion_started"}