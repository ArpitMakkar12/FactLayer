from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    judge_model: str = "gpt-4o-mini"
    embed_model: str = "token-jaccard"
    llm_base_url: str = "https://api.openai.com/v1"
    max_upload_mb: int = 25
    batch_pages: int = 3
    block_threshold: float = 0.32
    llm_concurrency: int = 3
    min_fact_confidence: float = 0.4
    database_url: str = "sqlite:///./app.db"
    upload_dir: str = str(ROOT / "data" / "uploads")


settings = Settings()
