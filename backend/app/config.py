"""Application settings, read from environment variables."""

import os
from dataclasses import dataclass, field


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./mindlattice.db"
    llm_provider: str = "mock"
    seed_demo_data: bool = True
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])


def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./mindlattice.db"),
        llm_provider=os.getenv("LLM_PROVIDER", "mock"),
        seed_demo_data=os.getenv("SEED_DEMO_DATA", "true").lower() == "true",
        cors_origins=_split(os.getenv("CORS_ORIGINS", "http://localhost:5173")),
    )
