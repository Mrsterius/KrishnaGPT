from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str
    faiss_index_path: str = "faiss_index"
    pdf_data_path: str = "data"
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retriever_k: int = 5


@lru_cache()
def get_settings() -> Settings:
    return Settings()
