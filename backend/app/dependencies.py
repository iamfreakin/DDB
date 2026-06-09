from __future__ import annotations

from functools import lru_cache

from backend.app.config import Settings
from backend.app.db import Database
from backend.app.providers.mock import MockTextGenerationProvider
from backend.app.repositories import AnalysisRepository, BrandRepository
from backend.app.services import AnalysisService, BrandService


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()


@lru_cache
def get_database() -> Database:
    database = Database(get_settings().database_path)
    database.initialize()
    return database


def get_brand_service() -> BrandService:
    return BrandService(BrandRepository(get_database()))


def get_analysis_service() -> AnalysisService:
    database = get_database()
    return AnalysisService(
        BrandRepository(database),
        AnalysisRepository(database),
        MockTextGenerationProvider(),
    )

