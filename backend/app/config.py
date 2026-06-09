from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI Small Business Content Studio API"
    app_version: str = "0.1.0"
    database_path: Path = PROJECT_ROOT / "data" / "app.db"
    ai_provider: str = "mock"

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = os.getenv("DATABASE_URL")
        database_path = (
            Path(database_url.removeprefix("sqlite:///")).resolve()
            if database_url
            else cls.database_path
        )
        return cls(
            database_path=database_path,
            ai_provider=os.getenv("TEXT_AI_PROVIDER", "mock"),
        )

