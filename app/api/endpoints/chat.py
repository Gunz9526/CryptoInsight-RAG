from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.chat_service import ChatService
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_rag_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    RAG 기반 챗봇 엔드포인트
    - query: 사용자의 질문
    - symbol: (선택사항) 주식 심볼
    """
    service = ChatService(db)
    try:
        result = await service.generate_response(request.query, request.symbol)

        return ChatResponse(
            answer=result["answer"],
            references=result["references"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG 응답 생성 중 오류: {str(e)}")
