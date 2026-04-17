import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    qdrant_url: str
    qdrant_api_key: str
    openai_api_key: str
    collection_name: str = "gabes_knowledge"
    embedding_model: str = "text-embedding-3-large"
    llm_model: str = "gpt-4o-mini"
    top_k: int = 5

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
