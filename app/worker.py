import asyncio
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.services.finnhub_service import FinnhubService

celery_app = Celery(
    'worker',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    timezone='UTC',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)

@celery_app.task(name='ingest_finnhub_news')
def task_ingest_finnhub_news():
    """
    Finnhub 뉴스 데이터를 주기적으로 수집하는 작업
    """
    service = FinnhubService()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(service.fetch_and_process_news())
    return {"status": "succeess", "processed_news_count": result}

celery_app.conf.beat_schedule = {
    'ingest-finnhub-news-every-hour': {
        'task': 'ingest_finnhub_news',
        'schedule': crontab(minute=0, hour='*'),
    },
}