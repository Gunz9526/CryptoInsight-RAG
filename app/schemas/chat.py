from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    query: str = Field(..., description="질문")
    symbol: Optional[str] = Field(None, description="주식 심볼 (예: AAPL, TSLA)")

class SourceDoc(BaseModel):
    title: str = Field(..., description="문서 제목")
    content: str = Field(..., description="문서 내용")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="답변")
    references: List[SourceDoc] = Field([], description="참고 문서 목록")