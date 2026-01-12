import logging
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.config import settings
from app.services.retrieval_service import RetrievalService
from app.services.stock_client import StockSystemClient
from app.schemas.chat import SourceDoc

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: AsyncSession):
        self.retrieval_service = RetrievalService(db)
        
        self.stock_client = StockSystemClient()

        self.llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1
        )

    async def generate_response(self, query: str, symbol: str = None) -> dict:
        """
        1. 뉴스 검색 (RAG)
        2. 주가 조회 (API)
        3. 종합 분석 (LLM)
        """
        docs = await self.retrieval_service.search_vectors(query)

        news_contents = "뉴스 없음"
        if docs:
            news_contents = "\n\n".join(
                [f"문서 {i+1} {d.title}: {d.content}" for i, d in enumerate(docs)]
            )

        market_context = "종목코드가 없음"
        if symbol:
            try:
                ohlcv_text = await self.stock_client.get_ohlcv(symbol, days=7)
                fund_text = await self.stock_client.get_fundamentals(symbol)
                market_context = f"{ohlcv_text}\n\n{fund_text}"
            except Exception as e:
                logger.error(f"주가 데이터 조회 오류: {str(e)}")
                market_context = "주가 데이터를 가져오는 중 오류가 발생했습니다."

        template = """
        당신은 수석 투자 분석가 AI입니다.
        아래의 [시장 데이터]와 [관련 뉴스]를 바탕으로 사용자 질문에 답변하세요.

        [시장 데이터]
        {market_context}

        [관련 뉴스]
        {news_context}

        질문: {question}

        답변 작성 규칙:
        1. 제공된 데이터에 있는 수치(가격, PER 등)를 근거로 사용하세요.
        2. 뉴스의 내용이 시장 데이터와 어떻게 연결되는지 논리적으로 설명하세요.
        3. 데이터가 부족하면 솔직하게 "정보가 부족합니다"라고 말하세요. 추측성 답변은 금지입니다.
        """
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()

        answer = await chain.ainvoke({
            "market_context": market_context,
            "news_context": news_contents,
            "question": query   
        })

        return {
            "answer": answer,
            "references": [SourceDoc(title=d.title, content=d.content) for d in docs]
        }
