from fastapi import FastAPI
from app.core.config import settings
from app.api.endpoints import market
from app.api.endpoints import chat

app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/")
async def root():
    return {"message": "시스템 가동. 준비완료."}

app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])