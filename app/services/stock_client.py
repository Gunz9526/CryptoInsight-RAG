import httpx
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class StockSystemClient:
    """
    주식 트레이딩 시스템이랑 통신하는 클라이언트
    """
    def __init__(self, base_url: str = "localhost:8000"): #http://host.docker.internal:8000
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0, read=20.0)
        self.headers = {
            "Content-Type": "application/json",
            "X-API-KEY": settings.TRADING_SYSTEM_API_KEY
        }

    async def _get_request(
            self,
            endpoint: str,
            params: Dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=self.timeout) as client:
            try:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP 오류 {e.response.status_code} - {e.response.text}")
                return None
            except httpx.RequestError as e:
                logger.error(f"요청 오류 - {str(e)}")
                return None
            except Exception as e:
                logger.error(f"알 수 없는 오류 - {str(e)}")
                return None

    async def get_ohlcv(self, symbol: str, days: int = 30) -> str:
        """
        특정 주식의 OHLCV 데이터를 가져옵니다.
        """
        endpoint = f"/ohlcv/{symbol}"
        data = await self._get_request(endpoint, params={"days": days})

        if not data:
            return f"{symbol} 종목의 주가 데이터를 불러올 수 없습니다 (통신 오류 또는 권한 없음)."

        try:
            summary = data.get("summary", {})
            return (
                f"[{symbol} 주가 요약 ({days}일)]\n"
                f"- 최신 종가: {summary.get('latest_price', 'N/A')}원\n"
                f"- 기간 최고가: {summary.get('highest', 'N/A')}원\n"
                f"- 기간 최저가: {summary.get('lowest', 'N/A')}원\n"
                f"- 총 거래량: {summary.get('total_volume', 'N/A')}"
            )
        except Exception as e:
            logger.error(f"Data parsing error for {symbol}: {e}")
            return f"{symbol} 데이터 형식이 올바르지 않습니다."

    async def get_fundamentals(self, symbol: str) -> str:
        """
        재무 데이터
        """
        endpoint = f"/fundamentals/{symbol}"
        data = await self._get_request(endpoint)

        if not data:
            return f"{symbol} 종목의 재무 데이터를 불러올 수 없습니다."

        try:
            val_summary = data.get("valuation_summary", {})
            undervalued = "저평가" if val_summary.get("undervalued") else "적정/고평가"
            growth = "성장주" if val_summary.get("growth_stock") else "일반"

            return (
                f"[{symbol} 재무/펀더멘털]\n"
                f"- PER: {data.get('per', 'N/A')}\n"
                f"- PBR: {data.get('pbr', 'N/A')}\n"
                f"- ROE: {data.get('roe', 'N/A')}\n"
                f"- 시가총액: {data.get('market_cap', 'N/A')}\n"
                f"- 업종: {data.get('sector', 'N/A')}\n"
                f"- 평가: {undervalued}, {growth}"
            )
        except Exception as e:
            logger.error(f"Data parsing error for {symbol}: {e}")
            return f"{symbol} 재무 데이터 형식이 올바르지 않습니다."