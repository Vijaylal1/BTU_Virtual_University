"""Global application settings – loaded once from environment / .env file."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Anthropic ────────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str
    CLAUDE_MODEL: str = "claude-opus-4-6"
    HAIKU_MODEL: str = "claude-haiku-4-5"
    THINKING_BUDGET: int = 8000          # adaptive thinking tokens for Opus

    # ── Embeddings (sentence-transformers, free & local) ───────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:your_password@localhost:5432/BTU_VU"

    # ── FAISS (local persistent, no server needed) ───────────────────────────
    FAISS_PERSIST_DIR: str = ".faiss_store"

    # ── Auth ─────────────────────────────────────────────────────────────────
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # ── RAG ──────────────────────────────────────────────────────────────────
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 64
    RAG_TOP_K: int = 5
    RAG_THRESHOLD: float = 0.30

    # ── Sprint / Wheel ──────────────────────────────────────────────────────
    SPRINT_TARGET_HOURS: float = 15.0
    WHEEL_REQUIRE_SPRINT: bool = True      # set False in .env to skip eligibility check

    # ── App ──────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    SUMMARISE_EVERY_N: int = 5           # trigger upward summarisation


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
