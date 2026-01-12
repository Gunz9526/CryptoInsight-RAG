from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings
from app.models.document import Document

class RetrievalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY
        )

    async def search_vectors(self, query: str, top_k: int = 5) -> List[Document]:
        """
        벡터 유사도 검색을 통해 관련 문서를 검색
        """
        query_vector = await self.embedding_model.aembed_query(query)

        stmt = select(Document).order_by(
            Document.embedding.cosine_distance(query_vector)
        ).limit(top_k)

        resullt = await self.db.execute(stmt)
        docs = resullt.scalars().all()

        return docs