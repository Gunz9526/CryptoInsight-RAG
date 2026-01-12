import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings
from app.models.document import Document as DBDocument

logger = logging.getLogger(__name__)

class IngestionService:
    """
    데이터 수집 처리 서비스
    """
    def __init__(self, db:AsyncSession):
        self.db = db
        self.embedding = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    async def ingest_articles(self, title: str, content:str, url: str | None = None) -> bool:
        """
        데이터 수집 및 저장
        """
        try:
            raw_document = Document(page_content=content, metadata={"title": title})
            chunks: List[Document] = self.text_splitter.split_documents([raw_document])

            if not chunks:
                logger.warning(f'{title} 문서에서 추출된 청크가 없습니다.')
                return False
            
            chunk_texts = [chunk.page_content for chunk in chunks]
            vectors = await self.embedding.aembed_documents(chunk_texts)

            db_objects = []
            for i, chunk in enumerate(chunks):
                db_document = DBDocument(
                    title=title,
                    content=chunk.page_content,
                    url=url,
                    embedding=vectors[i]
                )
                db_objects.append(db_document)

            self.db.add_all(db_objects)
            await self.db.commit()

            logger.info(f'{title} 문서가 성공적으로 수집 및 저장되었습니다. 총 청크 수: {len(chunks)}')
            return True
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error during text splitting: {e}")
            return False