from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "StockRAG-FastAPI"
    GOOGLE_API_KEY: str
    DATABASE_URL: str

    EMBEDDING_MODEL : str = "models/gemini-embedding-001"
    LLM_MODEL : str = "gemini-3-flash-preview"

    #TRADING_SYSTEM_URL: str = "http://host.docker.internal:8000"
    TRADING_SYSTEM_URL: str = "http://localhost:8000/api/v1/rag"
    TRADING_SYSTEM_API_KEY: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    FINNHUB_API_KEY: str
    REDIS_URL: str

    class Config:
        env_file = ".env"

settings = Settings()