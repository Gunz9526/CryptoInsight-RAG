import finnhub
import logging
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)

class FinnhubService:
    """
    Finnhub API 서비스
    """
    def __init__(self):
        self.client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)

    async def fetch_and_process_news(self, category: str = 'general') -> int:
        """
        Finnhub에서 뉴스 데이터를 가져와서 처리
        """
        try:
            logger.info("Finnhub에서 뉴스 데이터를 가져오는 중...")
            news_data = self.client.general_news(category, min_id=0)
            if not news_data:
                logger.warning("Finnhub에서 뉴스 데이터를 가져오지 못했습니다.")
                return False

            async with AsyncSessionLocal() as db:
                ingestion_service = IngestionService(db)
                for news in news_data:
                    title = news.get('headline', 'No Title')
                    content = news.get('summary', '')
                    url = news.get('url', None)

                    if content:
                        success = await ingestion_service.ingest_articles(title, content, url)
                        if not success:
                            logger.error(f"{title} 뉴스 기사를 수집하는 데 실패했습니다.")
                    
            return len(news_data)
        except Exception as e:
            logger.error(f"Finnhub 뉴스 처리 중 오류 발생: {e}")
            return 0
