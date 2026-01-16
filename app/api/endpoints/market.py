from fastapi import APIRouter, Depends, HTTPException
from app.services.stock_client import StockSystemClient
from app.core.config import settings

router = APIRouter()

@router.get("/check/{symbol}")
async def check_market_data(symbol: str):
    """
    특정 주식의 시장 데이터(OHLCV 및 재무제표)를 확인합니다.
    """
    client = StockSystemClient(base_url=settings.TRADING_SYSTEM_URL)
    
    ohlcv_data = await client.get_ohlcv(symbol, days=30)
    fundamentals_data = await client.get_fundamentals(symbol)
    
    if "오류" in ohlcv_data or "오류" in fundamentals_data:
        raise HTTPException(status_code=500, detail="트레이딩 시스템과의 통신 중 오류가 발생했습니다.")
    
    return {
        "status": "connected",
        "symbol": symbol,
        "ohlcv_data": ohlcv_data,
        "fundamentals_data": fundamentals_data
    }