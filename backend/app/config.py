from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    APP_NAME: str = "Single Source Retrieval API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"

    # Environment & CORS configuration
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    FAISS_INDEX_PATH: str = "./faiss_index"
    EVAL_LOG_PATH: str = "./logs/ragas_eval.jsonl"
    LOG_LEVEL: str = "INFO"

    # RAG & Model Configuration
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    VECTOR_INDEX_DIR: str = "data/vector_store"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150


    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "google/gemini-2.5-flash"

    @property
    def allowed_origins_list(self) -> List[str]:
        if not self.ALLOWED_ORIGINS:
            return ["http://localhost:3000"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

