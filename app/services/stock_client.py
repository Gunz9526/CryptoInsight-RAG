import httpx

class StockSystemClient:
    """
    주식 트레이딩 시스템이랑 통신하는 클라이언트
    """
    def __init__(self, base_url: str = "http://host.docker.internal:8000"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0, read=20.0)

    async def get_ohlcv(self, symbol: str, days: int = 30) -> str:
        """
        특정 주식의 OHLCV 데이터를 가져옵니다.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/rag/ohlcv/{symbol}",
                    params={"days": days},
                    timeout=self.timeout
                    )
                if response.status_code == 200:
                    data = response.json()
                    summary = data.get("summary", {})
                    return (
                        f"[ {symbol} 주가 데이터 ({days}일) ]\n"
                        f"- 최신 종가: {summary.get('latest_price')}원\n"
                        f"- 기간 최고가: {summary.get('highest')}원\n"
                        f"- 기간 최저가: {summary.get('lowest')}원\n"
                        f"- 총 거래량: {summary.get('total_volume')}주\n"
                    )
                return f"{symbol} 주가 데이터를 가져오는 데 실패했습니다. 상태 코드: {response.status_code}"

            except Exception as e:
                return f"시스템 오류: {str(e)}"

    async def get_fundamentals(self, symbol: str) -> str:
        """
        재무 데이터
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/rag/fundamentals/{symbol}",
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    data = response.json()                    
                    return (
                        f"[ {symbol} 재무제표 데이터 ]\n"
                        f"- PER: {data.get('per')}\n"
                        f"- PBR: {data.get('pbr')}\n"
                        f"- ROE: {data.get('roe')}\n"
                        f"- 시가총액: {data.get('market_cap')}원\n"
                        f"- 업종: {data.get('sector')}\n"
                    )
                return f"{symbol} 재무제표 데이터를 가져오는 데 실패했습니다. 상태 코드: {response.status_code}"
            except Exception as e:
                return f"시스템 오류: {str(e)}"