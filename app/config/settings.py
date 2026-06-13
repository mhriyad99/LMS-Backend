import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

base_dir = Path(__file__).resolve().parent.parent.parent
env_path = base_dir / ".env"

load_dotenv(env_path)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    DB_NAME: str
    DB_HOST: str
    DB_PORT: str
    DB_PASSWORD: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    EMBEDDING_MODEL_NAME: str
    EMBEDDING_DIM: int

    LLM_PROVIDER: str = "openai"
    LLM_MODEL_NAME: str = "gpt-4o-mini"
    LLM_BASE_URL: str | None = None

    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None

settings = Settings()