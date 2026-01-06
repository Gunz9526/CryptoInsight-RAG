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
        
        self.stock_client = StockSystemClient(base_url=settings.TRADING_SYSTEM_URL)

        self.llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.2
        )

    async def generate_response(self, query: str, symbol: str = None) -> dict:
        """
        RAG 파이프라인 = 질문 -> 뉴스검색, 주가조회 -> 프롬프트 -> LLM
        """
        docs = await self.retrieval_service.retrieve_documents(query)

        news_contents = "뉴스 없음"
        if docs:
            news_contents = "\n\n".join(
                [f"문서 {i+1} {id.title}: {d.content}" for i, d in enumerate(docs)]
            )

        market_context = "종목코드가 없습니다"
        if symbol:
            try:
                ohlcv_text = await self.stock_client.get_ohlcv(symbol, days=7)
                fund_text = await self.stock_client.get_fundamentals(symbol)
                market_context = f"{ohlcv_text}\n{fund_text}"
            except Exception as e:
                logger.error(f"주가 데이터 조회 오류: {str(e)}")
                market_context = "주가 데이터를 가져오는 중 오류가 발생했습니다."

        template = """
        당신은 금융 전문가입니다. 아래 제공된 [시장 데이터]와 [관련 뉴스]를 종합하여 사용자의 질문에 답변하세요.

        [시장 데이터]
        {market_context}

        [관련 뉴스]
        {news_context}

        질문: {question}

        작성 가이드:
        1. '시장 데이터'의 수치(가격, PER 등)를 구체적으로 인용하세요.
        2. 뉴스의 내용이 주가에 미칠 영향을 논리적으로 설명하세요.
        3. 매수/매도 추천을 직접적으로 하지 말고, 긍정적/부정적 요인을 정리해 주세요.
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